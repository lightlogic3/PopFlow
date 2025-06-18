"""
Graphiti记忆系统插件 - 基于知识图谱的长期记忆

这个插件使用Graphiti框架实现了基于知识图谱的长期记忆系统，
支持多用户隔离，以用户ID作为根节点和group_id，能够存储和检索对话历史。
"""

import asyncio
import json
import traceback
import os
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
import time
import logging

from tenacity import sleep

from knowledge_api.mapper.conversations.base import Conversation
from plugIns.memory_system.memory_interface import MemoryInterface, UserMetadata
from plugIns.memory_system.model import MemoryContext  # 导入 MemoryContext 模型
from knowledge_api.utils.log_config import get_logger

# Graphiti核心组件
from plugIns.memory_system.graphiti_memory.graphiti_core.graphiti import Graphiti
from .graphiti_core.neo4j_mapper.models.search_models import SearchFilters, EdgeReranker, EdgeSearchMethod, \
    SearchConfig, EdgeSearchConfig
from .graphiti_core.neo4j_mapper.nodes import EntityNode, EpisodeType
from .graphiti_core.neo4j_mapper.search.recipes import EDGE_HYBRID_SEARCH_CROSS_ENCODER
from .model.custom_entities import PersonEntity, ItemEntity, EventEntity, DialogueEntity, LocationEntity
# 本地配置

# 工具函数
from .utils import (
    to_local_time,
    from_local_time,
    format_datetime,
)

logger = get_logger()


class GraphitiMemory(MemoryInterface):
    """
    基于Graphiti知识图谱的长期记忆系统
    将用户对话历史存储为知识图谱，支持语义检索和关系推理
    """
    dialog_batch_size = 4  # Graphiti系统使用批次大小为4
    def __init__(self,
                neo4j_uri: str = None, 
                neo4j_user: str = None, 
                neo4j_password: str = None,
                store_raw_content: bool = True,
                model_id: str = "doubao-pro-256k-241115",
                # model_id: str = "claude-3-7-sonnet-20250219",
                **kwargs):
        """
        初始化Graphiti记忆系统
        Args:
            neo4j_uri: Neo4j数据库URI，默认从环境变量获取
            neo4j_user: Neo4j用户名，默认从环境变量获取
            neo4j_password: Neo4j密码，默认从环境变量获取
            store_raw_content: 是否存储原始内容，默认为True
            model_id: LLM模型ID，默认为"doubao-pro-256k-241115"
            reranker_model_dir: 重排序模型目录，默认为None使用系统默认路径
            **kwargs: 其他参数
        """
        # 从环境变量或参数获取Neo4j连接信息
        self._neo4j_uri = neo4j_uri or os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        self._neo4j_user = neo4j_user or os.environ.get("NEO4J_USER", "neo4j")
        self._neo4j_password = neo4j_password or os.environ.get("NEO4J_PASSWORD", "password")
        logger.info(f"正在连接Neo4j数据库: {self._neo4j_uri}")
        try:
            logger.info(f"开始初始化Graphiti客户端，连接到Neo4j: {self._neo4j_uri}")
            self._graphiti: Graphiti= Graphiti(
                uri=self._neo4j_uri,
                user=self._neo4j_user,
                password=self._neo4j_password,
                model_id=model_id,  # 使用指定的模型ID
                store_raw_episode_content=store_raw_content
            )
            logger.info(f"Graphiti客户端初始化成功")
        except Exception as e:
            logger.error(f"初始化Graphiti客户端失败: {e}")
            traceback.print_exc()
            raise
        
        # 初始化内部状态
        self._user_nodes = {}  # 缓存用户节点
        self._last_episode_uuids = {}  # 缓存每个用户最后一个episode的UUID
        self._entity_cache = {}  # 按用户ID缓存关键实体节点
        # 自定义实体类型
        self._entity_types = {
            "Person": PersonEntity,
            "Location": LocationEntity,
            "Item": ItemEntity,
            "Event": EventEntity,
            "Dialogue": DialogueEntity
        }
        # 自定义边类型
        self._edge_types = {
            "SPEAKS_AS": "表示对话的发言者，只能是旅行者或派蒙",
            "MENTIONS": "表示发言者在对话中提及了某实体",
            "DESCRIBES": "表示发言者对某实体的描述或评价",
            "QUOTES": "表示发言者引用或转述某实体的言论",
            "LOCATED_AT": "表示实体位于某地点",
            "INTERACTS_WITH": "表示发言者与某实体的互动",
            "REFERS_TO": "表示发言者指代某实体",
            "CLAIMS_ABOUT": "表示发言者关于某实体的声明或断言",
            "DIRECTLY_ADDRESSES": "表示发言者直接对另一个发言者说话",
            "RELATED_TO": "表示实体之间的一般关联关系",
            "HAPPENED_AT": "表示事件发生地点",
            "HAPPENED_BEFORE": "表示时间先后关系",
            "HAPPENED_AFTER": "表示时间先后关系",
            "ACCORDING_TO": "表示信息来源于发言者"
        }
        # 性能指标
        self._metrics = {}
        # 异步初始化Graphiti索引
        asyncio.create_task(self._initialize_graphiti())
        logger.info(f"Graphiti记忆系统初始化完成，连接到: {self._neo4j_uri}，使用模型: {model_id}")
    
    async def _initialize_graphiti(self):
        """初始化Graphiti索引和约束"""
        try:
            logger.info("正在初始化Graphiti索引和约束...")
            await self._graphiti.build_indices_and_constraints()
            logger.info("Graphiti索引和约束初始化完成")
        except Exception as e:
            logger.error(f"初始化Graphiti索引失败: {e}")
            traceback.print_exc()
    
    async def _cache_key_entities(self, user_id: str, nodes: list[EntityNode]) -> None:
        """
        缓存用户的关键实体节点，以便后续构建更深层次的关联
        Args:
            user_id: 用户ID
            nodes: 本次提取的实体节点列表
        """
        if user_id not in self._entity_cache:
            self._entity_cache[user_id] = {}
        
        # 更新缓存中的实体
        for node in nodes:
            # 使用节点名称作为键，保存节点UUID和属性
            self._entity_cache[user_id][node.name] = {
                "uuid": node.uuid,
                "labels": node.labels,
                "attributes": node.attributes if hasattr(node, "attributes") else {},
                "last_updated": datetime.now().isoformat()
            }
        
        logger.info(f"已更新用户 {user_id} 的实体缓存，当前缓存了 {len(self._entity_cache[user_id])} 个实体")
    
    async def _get_previous_episodes(self, user_id: str, limit: int = 5) -> List[str]:
        """
        获取用户最近的几个 episode UUIDs
        
        Args:
            user_id: 用户ID
            limit: 获取的最近记录数量
            
        Returns:
            List[str]: episode UUID列表
        """
        try:
            # 获取当前时间作为参考时间点
            reference_time = datetime.now()
            
            # 确保参考时间有时区信息
            if reference_time.tzinfo is None:
                from datetime import timezone
                reference_time = reference_time.replace(tzinfo=timezone.utc)
                
            logger.info(f"正在获取用户 {user_id} 的历史记录，参考时间: {reference_time.isoformat()}, 数量限制: {limit}")
            
            # 使用 retrieve_episodes 函数获取最近的 episodes
            episodes = await self._graphiti.retrieve_episodes(
                reference_time=reference_time,
                last_n=limit,
                group_ids=[user_id],
                source=None
            )
            
            # 提取UUID
            episode_uuids = [episode.uuid for episode in episodes if hasattr(episode, 'uuid')]
            
            logger.info(f"获取到用户 {user_id} 的 {len(episode_uuids)} 个最近 episodes: {episode_uuids}")
            return episode_uuids
        except Exception as e:
            logger.error(f"获取用户 {user_id} 的最近 episodes 失败: {e}")
            traceback.print_exc()
            return []
    

    async def store(self, data: MemoryContext, user_metadata: Optional[UserMetadata] = None) -> bool:
        """
        存储数据到知识图谱，并建立更深层次的关联
        
        Args:
            data: 要存储的数据，MemoryContext类型
            user_metadata: 用户元数据，必须包含user_id和role_id两个必填字段
            
        Returns:
            bool: 存储是否成功
        """
        # 验证user_metadata是否有效
        if not user_metadata:
            logger.error("存储记忆失败: 必须提供user_metadata")
            return False
        
        # 确保user_id和role_id存在
        if not hasattr(user_metadata, 'user_id') or not user_metadata.user_id:
            logger.error("存储记忆失败: user_metadata中缺少必填字段user_id")
            return False
            
        if not hasattr(user_metadata, 'role_id') or not user_metadata.role_id:
            logger.error("存储记忆失败: user_metadata中缺少必填字段role_id")
            return False
        
        try:
            # 准备episode数据
            user_id = f"{user_metadata.user_id}&&{user_metadata.role_id}"
            
            # 获取内容
            content = data.content if hasattr(data, 'content') else data.get("content", "")
            if not content:
                logger.error("存储记忆失败: 内容为空")
                return False
                
            # 如果是字典，转换为JSON字符串
            if isinstance(content, dict):
                content = json.dumps(content, ensure_ascii=False)
                
            # 处理时间信息
            from datetime import timezone
            
            # 获取时间戳
            timestamp = data.timestamp if hasattr(data, 'timestamp') else data.get("timestamp", datetime.now())
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp)
                except:
                    timestamp = datetime.now()
                
            # 处理有效时间
            valid_at = timestamp
            
            # 处理失效时间
            invalid_at = None
            metadata = data.metadata if hasattr(data, 'metadata') else data.get("metadata", {})
            if metadata and "invalid_at" in metadata:
                try:
                    invalid_at = datetime.fromisoformat(metadata["invalid_at"])
                except:
                    pass

            # 日志记录时间信息 (使用本地时间更易读)
            local_valid_at = to_local_time(valid_at)
            time_info = f"有效时间: {format_datetime(local_valid_at)} (UTC: {valid_at.isoformat()})"
            if invalid_at:
                local_invalid_at = to_local_time(invalid_at)
                time_info += f", 失效时间: {format_datetime(local_invalid_at)} (UTC: {invalid_at.isoformat()})"
            else:
                time_info += ", 持续有效中"
            logger.info(f"存储带时间信息的记忆: {time_info}, 用户:{user_metadata.user_id}, 角色:{user_metadata.role_id}")

            # 获取用户最近的episodes，用于建立时间序列关系
            previous_episode_uuids = await self._get_previous_episodes(user_id, limit=5)

            # 准备边类型映射，定义节点类型间的关系
            edge_type_map = {
                # 对话发言者与对话的关系
                ("Person", "Dialogue"): ["SPEAKS_AS"],

                # 发言者与被提及角色的关系
                ("Dialogue", "Person"): ["MENTIONS", "DESCRIBES", "QUOTES", "REFERS_TO", "CLAIMS_ABOUT"],

                # 发言者之间的直接对话关系
                ("Person", "Person"): ["DIRECTLY_ADDRESSES", "INTERACTS_WITH"],

                # 对话与其他实体的关系
                ("Dialogue", "Location"): ["MENTIONS", "REFERS_TO"],
                ("Dialogue", "Item"): ["MENTIONS", "REFERS_TO"],
                ("Dialogue", "Event"): ["MENTIONS", "REFERS_TO"],

                # 发言者对位置的描述
                ("Person", "Location"): ["LOCATED_AT"],

                # 事件相关关系
                ("Event", "Location"): ["HAPPENED_AT"],
                ("Event", "Person"): ["RELATED_TO"],
                ("Event", "Event"): ["HAPPENED_BEFORE", "HAPPENED_AFTER"],

                # 信息来源关系
                ("*", "*"): ["ACCORDING_TO"]
            }

            try:
                name = f"{content[:30]}..." if len(content) > 30 else content
                # 添加episode到知识图谱
                episode_result = await self._graphiti.add_episode(
                    name=name,
                    episode_body=content,
                    source_description=data.source if hasattr(data, 'source') else data.get("source", "memory_entry"),
                    reference_time=valid_at,  # 使用valid_at作为reference_time (UTC时区)
                    group_id=user_id,  # 使用用户ID作为group_id，确保数据隔离
                    previous_episode_uuids=previous_episode_uuids,  # 显式指定前序episodes
                    update_communities=True,  # 启用社区更新，增强图结构
                    entity_types=self._entity_types,  # 使用自定义实体类型
                    edge_types=self._edge_types,  # 使用自定义边类型
                    edge_type_map=edge_type_map,  # 使用自定义边类型映射
                )

                # 缓存最新episode的UUID，用于下次添加
                if hasattr(episode_result, 'episode') and episode_result.episode and episode_result.episode.uuid:
                    self._last_episode_uuids[user_id] = episode_result.episode.uuid
                    logger.info(f"已缓存用户 {user_id} 的最新 episode UUID: {episode_result.episode.uuid}")

                # 缓存实体以便后续构建更深层次的关联
                if hasattr(episode_result, 'nodes') and episode_result.nodes:
                    await self._cache_key_entities(user_id, episode_result.nodes)

                # 记录生成的节点和边信息
                self._log_episode_result(episode_result, user_id)

                return True
            except Exception as e:
                logger.error(f"存储记忆到知识图谱失败: {e}")
                traceback.print_exc()
                return False

        except Exception as e:
            logger.error(f"存储记忆失败: {e}")
            traceback.print_exc()
            return False

    def _log_episode_result(self, episode_result, user_id):
        """记录添加episode的结果"""
        # 记录节点信息
        nodes_info = []
        for node in episode_result.nodes:
            node_type = "Unknown"
            if hasattr(node, 'labels') and node.labels:
                node_type = ', '.join(node.labels)

            # 记录节点属性
            attrs = ""
            if hasattr(node, 'attributes') and node.attributes:
                attrs = f" - 属性: {node.attributes}"
            nodes_info.append(f"{node.name} ({node_type}){attrs}")

        # 记录边信息
        edges_info = []
        for edge in episode_result.edges:
            if hasattr(edge, 'name') and edge.name:
                edges_info.append(f"{edge.name}: {edge.source_node_uuid} -> {edge.target_node_uuid}")
            else:
                edges_info.append(f"{edge.source_node_uuid} -> {edge.target_node_uuid}")

        logger.info(f"成功存储记忆，用户ID: {user_id}, 生成 {len(episode_result.nodes)} 个节点: {', '.join(nodes_info)}")
        logger.info(f"成功存储记忆，用户ID: {user_id}, 生成 {len(episode_result.edges)} 个关系: {', '.join(edges_info)}")

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        user_metadata: Optional[UserMetadata] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        根据查询文本从图数据库中检索相关的记忆

        Args:
            query: 查询字符串
            top_k: 返回结果数量
            user_metadata: 用户元数据，必须包含user_id和role_id两个必填字段
            **kwargs: 额外的检索参数，支持以下选项:
                entity_type: str - 只搜索特定类型的实体
                entity_names: List[str] - 只搜索特定的实体名称
                min_similarity: float - 最小相似度阈值，默认0.7
                use_reranker: bool - 是否使用重排序，默认True
                reranker_model: str - 自定义重排序模型路径

        Returns:
            List[Dict[str, Any]]: 检索到的记忆列表，每个记忆包含相关信息
        """
        start_time = time.time()
        
        # 验证user_metadata是否有效
        if not user_metadata:
            logger.error("检索失败: 必须提供user_metadata")
            return []
        
        # 确保user_id和role_id存在
        if not hasattr(user_metadata, 'user_id') or not user_metadata.user_id:
            logger.error("检索失败: user_metadata中缺少必填字段user_id")
            return []
            
        if not hasattr(user_metadata, 'role_id') or not user_metadata.role_id:
            logger.error("检索失败: user_metadata中缺少必填字段role_id")
            return []
            
        # 从kwargs中提取过滤条件，兼容旧版filters参数
        filters = kwargs.get('filters', {})
        if not filters:
            filters = {}
        
        # 从kwargs中提取常用过滤条件
        for key in ['entity_type', 'entity_names', 'min_similarity', 'use_reranker', 'reranker_model']:
            if key in kwargs:
                filters[key] = kwargs[key]

        # 确保有group_id
        if not filters.get('group_id'):
            filters['group_id'] = f"{user_metadata.user_id}&&{user_metadata.role_id}"
        
        # 打印详细的检索参数
        logger.info(f"开始记忆检索: 查询='{query}', 用户:{user_metadata.user_id}, 角色:{user_metadata.role_id}, 过滤条件={filters}, 限制={top_k}")

        # 构建SearchFilters对象
        search_filter = SearchFilters()

        # 应用过滤条件
        group_id = filters.get("group_id")
        entity_type = filters.get("entity_type")
        min_similarity = filters.get("min_similarity", 0.7)
        use_reranker = filters.get("use_reranker", True)  # 默认使用重排序
        # 创建或选择搜索配置
        if use_reranker:
            # 使用交叉编码器重排序方法
            logger.info(f"使用交叉编码器重排序器，最小相似度阈值: {min_similarity}")
            search_config = EDGE_HYBRID_SEARCH_CROSS_ENCODER
        else:
            # 创建不使用重排序器的配置
            logger.info("不使用重排序器，仅基于向量相似度排序")
            search_config = SearchConfig(
                edge_config=EdgeSearchConfig(
                    search_methods=[
                        EdgeSearchMethod.bm25,
                        EdgeSearchMethod.cosine_similarity,
                    ],
                    reranker=EdgeReranker.rrf,  # 使用RRF替代交叉编码器
                ),
                limit=top_k * 3  # 为了确保有足够的候选项
            )
        # 应用最小相似度阈值
        search_config.reranker_min_score = min_similarity
        # 处理目标节点类型
        if entity_type:
            target_types = [entity_type]
            logger.info(f"过滤目标节点类型: {target_types}")

        # 处理源节点UUID - 如果指定了实体名称，先获取它们的UUID

        try:
            # 确保搜索参数合理
            search_limit = max(top_k * 3, 15)  # 至少获取15个结果用于重排序
            # 执行边搜索
            logger.info(f"执行边搜索，初始限制: {search_limit}，重排序配置: {search_config.edge_config.reranker}")
            search_results = await self._graphiti.search_(
                query=query,
                config=search_config,
                group_ids=[group_id] if group_id else None,
                search_filter=search_filter
            )

            # 收集所有结果
            all_results = []

            # 处理边结果
            if hasattr(search_results, 'edges') and search_results.edges:
                logger.info(f"找到边结果: {len(search_results.edges)}个")
                for edge in search_results.edges:
                    all_results.append(self._format_edge_result(edge))

            # 处理节点结果
            if hasattr(search_results, 'nodes') and search_results.nodes:
                logger.info(f"找到节点结果: {len(search_results.nodes)}个")
                for node in search_results.nodes:
                    all_results.append(self._format_node_result(node))

            # 处理episode结果
            if hasattr(search_results, 'episodes') and search_results.episodes:
                logger.info(f"找到episode结果: {len(search_results.episodes)}个")
                for episode in search_results.episodes:
                    all_results.append(self._format_episode_result(episode))

            # 限制返回结果数量
            final_results = all_results[:top_k]
            elapsed_time = time.time() - start_time
            logger.info(f"检索完成，用户:{user_metadata.user_id}，角色:{user_metadata.role_id}，返回{len(final_results)}条结果，耗时: {elapsed_time:.2f}秒")
            return final_results
        except Exception as e:
            logger.error(f"检索过程中出错: {e}")
            logger.error(traceback.format_exc())
            return []

    def _format_edge_result(self, edge):
        """格式化边结果"""
        # 提取边的来源信息(edge.source_info)作为元数据
        metadata = {}
        if hasattr(edge, 'source_info'):
            metadata['source'] = edge.source_info
        if hasattr(edge, 'score'):
            metadata['score'] = edge.score

        # 构建每条记忆的完整上下文
        context = edge.fact if hasattr(edge, 'fact') and edge.fact else ""
        if hasattr(edge, 'original_context') and edge.original_context:
            context = edge.original_context

        # 生成用于显示的摘要
        summary = ""
        if hasattr(edge, 'source_node_name') and hasattr(edge, 'target_node_name'):
            summary = f"{edge.source_node_name} 与 {edge.target_node_name} 的关系"
        elif hasattr(edge, 'name') and edge.name:
            summary = edge.name

        return {
            "uuid": edge.uuid,
            "content": context,
            "summary": summary,
            "type": "edge",
            "metadata": metadata
        }

    def _format_node_result(self, node):
        """格式化节点结果"""
        metadata = {}
        if hasattr(node, 'labels'):
            metadata['type'] = ', '.join(node.labels)
        if hasattr(node, 'attributes'):
            metadata['attributes'] = node.attributes

        context = ""
        if hasattr(node, 'summary') and node.summary:
            context = node.summary
        elif hasattr(node, 'attributes') and node.attributes.get('description'):
            context = node.attributes.get('description')

        return {
            "uuid": node.uuid,
            "content": context,
            "summary": node.name,
            "type": "node",
            "metadata": metadata
        }

    def _format_episode_result(self, episode):
        """格式化episode结果"""
        metadata = {}
        if hasattr(episode, 'valid_at'):
            valid_time = episode.valid_at
            # 转换为本地时间
            local_valid_time = to_local_time(valid_time)
            metadata['valid_at'] = valid_time.isoformat()
            metadata['valid_at_local'] = local_valid_time.isoformat()
            metadata['time_description'] = format_datetime(local_valid_time)

        return {
            "uuid": episode.uuid,
            "content": episode.content if hasattr(episode, 'content') else "",
            "summary": episode.name if hasattr(episode, 'name') else "",
            "type": "episode",
            "metadata": metadata
        }

    @property
    def name(self) -> str:
        """获取记忆系统名称"""
        return "Graphiti知识图谱记忆系统"

    @property
    def description(self) -> str:
        """获取记忆系统描述"""
        return "基于Neo4j知识图谱的长期记忆系统，支持语义检索和关系推理"

    @property
    def performance_metrics(self) -> Dict[str, float]:
        """
        获取记忆系统性能指标
        
        Returns:
            Dict[str, float]: 性能指标字典
        """
        # 返回平均存储时间和检索时间等指标
        metrics = {
            "avg_store_time_ms": sum(self._metrics.get("store_times", [0])) / max(len(self._metrics.get("store_times", [1])), 1),
            "avg_retrieve_time_ms": sum(self._metrics.get("retrieve_times", [0])) / max(len(self._metrics.get("retrieve_times", [1])), 1),
            "total_episodes": self._metrics.get("total_episodes", 0),
            "total_entities": self._metrics.get("total_entities", 0),
            "total_edges": self._metrics.get("total_edges", 0),
        }
        
        # 记录性能日志
        logger.debug(f"Graphiti记忆系统性能指标: {metrics}")
        return metrics

    async def close(self):
        """
        关闭连接并清理资源
        """
        try:
            logger.info("正在关闭Graphiti记忆系统连接...")
            if hasattr(self, '_graphiti'):
                await self._graphiti.close()
            logger.info("Graphiti记忆系统连接已关闭")
        except Exception as e:
            logger.error(f"关闭Graphiti连接时发生错误: {e}")
            traceback.print_exc()

    async def update(self, memory_id: str, content: Dict[str, Any], user_metadata: Optional[UserMetadata] = None) -> bool:
        """
        更新已存在的记忆内容
        
        Args:
            memory_id: 记忆ID (UUID)
            content: 更新的内容
            user_metadata: 用户元数据，必须包含user_id和role_id两个必填字段
            
        Returns:
            bool: 更新是否成功
        """
        # 验证user_metadata是否有效
        if not user_metadata:
            logger.error("更新失败: 必须提供user_metadata")
            return False
        
        # 确保user_id和role_id存在
        if not hasattr(user_metadata, 'user_id') or not user_metadata.user_id:
            logger.error("更新失败: user_metadata中缺少必填字段user_id")
            return False
            
        if not hasattr(user_metadata, 'role_id') or not user_metadata.role_id:
            logger.error("更新失败: user_metadata中缺少必填字段role_id")
            return False
        
        # 这个方法尚未实现，可以根据需要添加实现
        logger.warning(f"更新记忆功能尚未实现，用户:{user_metadata.user_id}，角色:{user_metadata.role_id}")
        return False

    async def delete(self, memory_id: str, user_metadata: Optional[UserMetadata] = None) -> bool:
        """
        删除记忆
        
        Args:
            memory_id: 记忆ID (UUID)
            user_metadata: 用户元数据，必须包含user_id和role_id两个必填字段
            
        Returns:
            bool: 删除是否成功
        """
        # 验证user_metadata是否有效
        if not user_metadata:
            logger.error("删除失败: 必须提供user_metadata")
            return False
        
        # 确保user_id和role_id存在
        if not hasattr(user_metadata, 'user_id') or not user_metadata.user_id:
            logger.error("删除失败: user_metadata中缺少必填字段user_id")
            return False
            
        if not hasattr(user_metadata, 'role_id') or not user_metadata.role_id:
            logger.error("删除失败: user_metadata中缺少必填字段role_id")
            return False
            
        # 这个方法尚未实现，可以根据需要添加实现
        logger.warning(f"删除记忆功能尚未实现，用户:{user_metadata.user_id}，角色:{user_metadata.role_id}")
        return False

    def _get_custom_metadata(self, batch_conversations: List, batch_num: int) -> Dict[str, Any]:
        """
        为Graphiti系统添加特定的元数据
        
        Args:
            batch_conversations: 当前批次的对话列表
            batch_num: 批次编号
            
        Returns:
            Dict[str, Any]: Graphiti特定的元数据
        """
        return {
            "graphiti_episode": True,  # 标记这是Graphiti episode
            "knowledge_graph": True,  # 标记这将构建知识图谱
            "entity_extraction": True,  # 标记启用实体提取
            "relationship_inference": True  # 标记启用关系推理
        }

    async def get_sync_status(self, user_metadata: UserMetadata) -> Dict[str, Any]:
        """
        获取同步状态

        Args:
            user_metadata: 用户元数据，必须包含user_id和role_id两个必填字段

        Returns:
            Dict[str, Any]: 当前的同步状态信息
        """
        # 验证user_metadata是否有效
        if not user_metadata:
            logger.error("获取同步状态失败: 必须提供user_metadata")
            return {
                "status": "not_started",
                "progress": 0,
                "error_message": "缺少用户元数据"
            }
        
        # 确保user_id存在
        if not hasattr(user_metadata, 'user_id') or not user_metadata.user_id:
            logger.error("获取同步状态失败: user_metadata中缺少必填字段user_id")
            return {
                "status": "not_started", 
                "progress": 0,
                "error_message": "缺少用户ID"
            }
        
        if not hasattr(self, '_sync_status'):
            return {
                "status": "not_started",
                "progress": 0,
                "total": 0,
                "completed": 0,
                "errors": 0
            }
        
        logger.debug(f"获取同步状态，用户:{user_metadata.user_id}，角色:{user_metadata.role_id}，进度:{self._sync_status.get('progress', 0):.1f}%")
        return self._sync_status