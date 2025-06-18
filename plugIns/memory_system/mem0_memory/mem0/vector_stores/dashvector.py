import httpx
import json
import logging
import os
from typing import Dict, List, Optional, Any
import uuid
import numpy as np

from plugIns.memory_system.mem0_memory.mem0.vector_stores.base import VectorStoreBase
from knowledge_manage.vectorstores.dashvector_http_store import DashVectorHTTPStore
from knowledge_manage.vectorstores.factory import VectorStoreFactory
from knowledge_api.framework.redis.cache_manager import CacheManager


logger = logging.getLogger(__name__)


class OutputData:
    def __init__(self, id=None, score=None, payload=None):
        self.id = id
        self.score = score
        self.payload = payload or {}


class DashVectorAdapter(VectorStoreBase):
    """DashVector 适配器类，将 DashVectorHTTPStore 适配到 VectorStoreBase 接口"""

    def __init__(
        self,
        api_key: str = None,
        endpoint: str = None,
        dimension: int = 512,
        metric: str = "cosine",
        collection_name="long_term_memory_user_m0_test_v1",
        dtype: str = "FLOAT",
    ):
        """
        初始化 DashVector 适配器
        
        Args:
            collection_name: 集合名称
            api_key: DashVector API 密钥
            endpoint: DashVector 端点
            dimension: 向量维度
            metric: 距离度量
            dtype: 数据类型
        """
        self.collection_name = collection_name
        self.api_key = api_key
        self.endpoint = endpoint
        self.dimension = dimension
        self.metric = metric
        self.dtype = dtype
        self.vector_store = None
        self.is_initialized = False
        
    async def _ensure_initialized(self):
        """确保向量存储已初始化"""
        if not self.is_initialized:
            # 如果没有提供 API 密钥和端点，则从缓存管理器获取
            api_key = self.api_key
            endpoint = self.endpoint
            
            if api_key is None:
                try:
                    api_key = await CacheManager().get_system_config_value("DASHVECTOR_API_KEY")
                    logger.info("从系统配置获取 DashVector API 密钥")
                except Exception as e:
                    logger.warning(f"从系统配置获取 API 密钥失败: {e}")
                    api_key = os.environ.get("DASHVECTOR_API_KEY")
                    
            if endpoint is None:
                try:
                    endpoint = await CacheManager().get_system_config_value("DASHVECTOR_ENDPOINT")
                    logger.info("从系统配置获取 DashVector 端点")
                except Exception as e:
                    logger.warning(f"从系统配置获取端点失败: {e}")
                    endpoint = os.environ.get("DASHVECTOR_ENDPOINT")
            
            if api_key is None or endpoint is None:
                raise ValueError("必须提供 DashVector API 密钥和端点，可以通过参数、环境变量或系统配置提供")
            
            # 定义向量存储的字段结构
            fields_schema = {
                "data": "STRING",         # 记忆内容
                "memory": "STRING",       # 记忆内容的别名
                "hash": "STRING",         # 记忆哈希值
                "created_at": "STRING",   # 创建时间
                "updated_at": "STRING",   # 更新时间
                
                # 从 metadata 中提取的重要查询字段
                "user_id": "STRING",      # 用户ID
                "session_id": "STRING",   # 会话ID
                "role_id": "STRING",      # 角色ID
                "agent_id": "STRING",     # 代理ID
                "run_id": "STRING",       # 运行ID
                "actor_id": "STRING",     # 行为者ID
                "role": "STRING",         # 角色
                "conversation_id": "STRING", # 对话ID
                "message_id": "STRING",   # 消息ID
                "parent_message_id": "STRING", # 父消息ID
                "timestamp": "STRING",    # 时间戳
                "memory_type": "STRING",  # 记忆类型
                
                # 将 metadata 中的嵌套结构序列化为字符串存储
                "metadata_json": "STRING",  # 将整个 metadata 序列化为 JSON 字符串
            }
                
            # 使用工厂创建实际的 DashVectorHTTPStore 实例
            self.vector_store = await VectorStoreFactory.create_vector_store(
                store_type="dashvector",
                collection_name=self.collection_name,
                dimension=self.dimension,
                api_key=api_key,
                endpoint=endpoint,
                metric=self.metric,
                dtype=self.dtype,
                is_init_collection=True,
                fields_schema=fields_schema,
                create_if_not_exists=True
            )
            self.is_initialized = True
            logger.info(f"DashVector 存储初始化完成: {self.collection_name}")
    
    async def create_col(self, name, vector_size=None, distance=None):
        """创建一个新集合"""
        await self._ensure_initialized()
        
        # 这里可能需要额外的初始化逻辑，但主要由底层的 DashVectorHTTPStore 处理
        logger.info(f"使用现有的 DashVectorHTTPStore 创建集合: {name}")
        return self.vector_store
    
    async def insert(self, vectors, payloads=None, ids=None):
        """插入向量到集合"""
        try:
            await self._ensure_initialized()
            
            # 确保 payloads 和 ids 是合适的格式
            if payloads is None:
                payloads = [{} for _ in range(len(vectors))]
                
            # 如果 ids 为 None，生成 UUID
            if ids is None:
                ids = [str(uuid.uuid4()) for _ in range(len(vectors))]
                
            # 确保 vectors 是列表格式
            if not isinstance(vectors, list):
                vectors = [vectors]
                
            # 确保每个向量都是正确的格式（列表或数组）
            processed_vectors = []
            for vec in vectors:
                if not isinstance(vec, (list, tuple, np.ndarray)):
                    logger.warning(f"向量格式不正确，尝试转换为列表: {type(vec)}")
                    try:
                        # 尝试转换为列表
                        if hasattr(vec, "tolist"):
                            processed_vec = vec.tolist()
                        else:
                            processed_vec = [float(vec)]
                    except Exception as e:
                        logger.error(f"向量格式转换失败: {e}")
                        # 用零向量替代，避免插入失败
                        processed_vec = [0.0] * self.dimension
                else:
                    processed_vec = vec
                processed_vectors.append(processed_vec)
                
            # 准备文档
            documents = []
            for i, (payload, vector_id) in enumerate(zip(payloads, ids)):
                # 确保 payload 是字典类型
                if hasattr(payload, 'model_dump'):
                    # 如果是 MemoryItem 或 Pydantic 模型，使用 model_dump 转换为字典
                    doc = payload.model_dump()
                    # 确保 id 字段存在
                    if 'id' not in doc and vector_id:
                        doc['id'] = vector_id
                else:
                    # 普通字典情况
                    doc = dict(payload)
                    # 确保 id 字段存在
                    if vector_id:
                        doc["id"] = vector_id
                
                # 再次确认 id 字段存在
                if 'id' not in doc:
                    logger.warning(f"文档缺少 id 字段，使用索引作为 id: {i}")
                    doc['id'] = str(i)
                
                # 处理 metadata 字段
                if 'metadata' in doc and isinstance(doc['metadata'], dict):
                    metadata = doc['metadata']
                    
                    # 将整个 metadata 序列化为 JSON 字符串，保存为 metadata_json 字段
                    try:
                        doc['metadata_json'] = json.dumps(metadata)
                    except Exception as e:
                        logger.warning(f"序列化 metadata 失败: {e}")
                        doc['metadata_json'] = "{}"
                    
                    # 从 metadata 中提取重要字段到顶层
                    for key in [
                        'user_id', 'session_id', 'role_id', 'agent_id', 'run_id',
                        'actor_id', 'role', 'conversation_id', 'message_id',
                        'parent_message_id', 'timestamp', 'memory_type'
                    ]:
                        if key in metadata:
                            doc[key] = metadata[key]
                    
                    # 处理 memory 字段（可能来自 metadata.data）
                    if 'memory' not in doc and 'data' in metadata:
                        doc['memory'] = metadata['data']
                    
                    # 删除原始的 metadata 字段，避免嵌套结构
                    del doc['metadata']
                
                # 过滤掉文档中的所有 null 值，替换为空字符串或默认值
                filtered_doc = {}
                for k, v in doc.items():
                    if v is None:
                        if k in ['score']:
                            filtered_doc[k] = 0.0  # 用 0.0 替代 null
                        else:
                            filtered_doc[k] = ""  # 对其他字段，用空字符串替代 null
                    elif isinstance(v, dict):
                        # 如果值是字典类型，序列化为 JSON 字符串
                        try:
                            filtered_doc[k] = json.dumps(v)
                        except Exception as e:
                            logger.warning(f"序列化字段 {k} 失败: {e}")
                            filtered_doc[k] = "{}"
                    else:
                        filtered_doc[k] = v

                documents.append(filtered_doc)
                
            logger.debug(f"准备插入 {len(documents)} 个文档，向量维度: {len(processed_vectors[0]) if processed_vectors else 'unknown'}")
                
            # 使用底层 vector_store 的 add_documents 方法
            result = await self.vector_store.add_documents(documents, processed_vectors)
            logger.info(f"向 DashVector 集合插入 {len(vectors)} 个向量成功")
            return result
        except Exception as e:
            logger.error(f"向 DashVector 集合插入向量失败: {e}")
            import traceback
            traceback.print_exc()
            raise

    async def search(self, query, vectors, limit=5, filters=None):
        """搜索相似向量"""
        try:
            await self._ensure_initialized()
            
            # 构建过滤字符串
            filter_str = None
            if filters:
                filter_parts = []
                for key, value in filters.items():
                    # 如果键是 metadata 的嵌套字段，转换为顶层字段
                    if key.startswith('metadata.'):
                        actual_key = key.split('.', 1)[1]
                        filter_parts.append(f'{actual_key}="{value}"')
                    else:
                        filter_parts.append(f'{key}="{value}"')
                filter_str = " AND ".join(filter_parts)
            
            # 确保 vectors 是正确的格式
            query_embedding = None
            if vectors is not None:
                if isinstance(vectors, list):
                    if len(vectors) > 0:
                        if isinstance(vectors[0], (list, tuple, np.ndarray)):
                            # 如果是向量列表，取第一个向量
                            query_embedding = vectors[0]
                        else:
                            # 如果是单个向量，直接使用
                            query_embedding = vectors
                else:
                    # 如果不是列表，可能是单个向量
                    query_embedding = vectors
                    
                # 确保 query_embedding 是列表或数组类型
                if query_embedding is not None and not isinstance(query_embedding, (list, tuple, np.ndarray)):
                    logger.warning(f"向量格式不正确，尝试转换为列表: {type(query_embedding)}")
                    try:
                        # 尝试转换为列表
                        if hasattr(query_embedding, "tolist"):
                            query_embedding = query_embedding.tolist()
                        else:
                            query_embedding = [float(query_embedding)]
                    except Exception as e:
                        logger.error(f"向量格式转换失败: {e}")
                        query_embedding = None
            
            logger.debug(f"搜索向量类型: {type(query_embedding)}, 过滤条件: {filter_str}")
            
            # 调用底层 vector_store 的搜索方法
            results = await self.vector_store.search(
                query_embedding=query_embedding,
                top_k=limit,
                filter_str=filter_str
            )
            
            # 转换结果格式
            processed_results = []
            for result in results:
                # 处理可能被序列化为JSON字符串的字段
                payload = {}
                for k, v in result.items():
                    if k not in ["id", "score"]:
                        # 尝试反序列化 JSON 字符串字段
                        if k == "metadata_json" or (isinstance(v, str) and v.startswith('{')):
                            try:
                                parsed_json = json.loads(v)
                                # 如果是 metadata_json，添加到 metadata 字段
                                if k == "metadata_json":
                                    payload["metadata"] = parsed_json
                                else:
                                    payload[k] = parsed_json
                            except:
                                # 如果不是有效的 JSON，保持原样
                                payload[k] = v
                        else:
                            payload[k] = v
                
                # 创建一个 OutputData 对象
                processed_result = OutputData(
                    id=result.get("id", ""),
                    score=result.get("score", 0.0),
                    payload=payload
                )
                processed_results.append(processed_result)
            
            logger.info(f"搜索完成，找到 {len(processed_results)} 条结果")
            return processed_results
        except Exception as e:
            logger.error(f"搜索向量时出错: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def delete(self, vector_id):
        """删除向量"""
        await self._ensure_initialized()
        
        # 调用底层 vector_store 的删除方法
        result = await self.vector_store.delete_by_ids([vector_id])
        logger.info(f"从 DashVector 集合删除向量: {vector_id}")
        return result
    
    async def update(self, vector_id, vector=None, payload=None):
        """更新向量"""
        try:
            await self._ensure_initialized()
            
            # 当前 DashVectorHTTPStore 可能没有直接的更新方法
            # 这里采用删除后重新插入的策略
            
            # 首先删除
            await self.delete(vector_id)
            
            # 然后重新插入
            if vector and payload:
                # 处理 payload，确保不包含 null 值
                document = dict(payload)
                document["id"] = vector_id
                
                # 处理 metadata 字段
                if 'metadata' in document and isinstance(document['metadata'], dict):
                    metadata = document['metadata']
                    
                    # 将整个 metadata 序列化为 JSON 字符串，保存为 metadata_json 字段
                    try:
                        document['metadata_json'] = json.dumps(metadata)
                    except Exception as e:
                        logger.warning(f"序列化 metadata 失败: {e}")
                        document['metadata_json'] = "{}"
                    
                    # 从 metadata 中提取重要字段到顶层
                    for key in [
                        'user_id', 'session_id', 'role_id', 'agent_id', 'run_id',
                        'actor_id', 'role', 'conversation_id', 'message_id',
                        'parent_message_id', 'timestamp', 'memory_type'
                    ]:
                        if key in metadata:
                            document[key] = metadata[key]
                    
                    # 处理 memory 字段（可能来自 metadata.data）
                    if 'memory' not in document and 'data' in metadata:
                        document['memory'] = metadata['data']
                    
                    # 删除原始的 metadata 字段，避免嵌套结构
                    del document['metadata']
                
                # 过滤掉文档中的所有 null 值，替换为空字符串或默认值
                filtered_document = {}
                for k, v in document.items():
                    if v is None:
                        if k in ['score']:
                            filtered_document[k] = 0.0  # 用 0.0 替代 null
                        else:
                            filtered_document[k] = ""  # 对其他字段，用空字符串替代 null
                    elif isinstance(v, dict):
                        # 如果值是字典类型，序列化为 JSON 字符串
                        try:
                            filtered_document[k] = json.dumps(v)
                        except Exception as e:
                            logger.warning(f"序列化字段 {k} 失败: {e}")
                            filtered_document[k] = "{}"
                    else:
                        filtered_document[k] = v
                
                # 确保向量格式正确
                processed_vector = vector
                if not isinstance(vector, (list, tuple, np.ndarray)):
                    logger.warning(f"向量格式不正确，尝试转换为列表: {type(vector)}")
                    try:
                        # 尝试转换为列表
                        if hasattr(vector, "tolist"):
                            processed_vector = vector.tolist()
                        else:
                            processed_vector = [float(vector)]
                    except Exception as e:
                        logger.error(f"向量格式转换失败: {e}")
                        # 用零向量替代，避免更新失败
                        processed_vector = [0.0] * self.dimension
                
                result = await self.vector_store.add_documents([filtered_document], [processed_vector])
                logger.info(f"更新 DashVector 集合中的向量: {vector_id}")
                return True
            else:
                logger.error(f"更新向量失败，缺少向量或载荷数据: {vector_id}")
                return False
        except Exception as e:
            logger.error(f"更新向量时出错: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def get(self, vector_id: str):
        """Get a memory by its ID."""
        try:
            logger.info(f"正在获取向量记忆: {vector_id}")
            await self._ensure_initialized()
            
            # 确保 vector_id 是字符串类型
            if not isinstance(vector_id, str):
                vector_id = str(vector_id)
                
            result = await self.vector_store.get(vector_id)
            
            if not result:
                logger.warning(f"找不到ID为 {vector_id} 的向量记忆")
                return None
                
            logger.debug(f"成功获取记忆: {vector_id}")
            
            # 处理结果，转换为 OutputData 格式
            if isinstance(result, dict):
                # 如果结果是字典格式
                # 创建一个标准的 OutputData 对象
                return OutputData(
                    id=vector_id,
                    score=1.0,  # 精确匹配的得分为 1.0
                    payload={k: v for k, v in result.items() if k != "id"}
                )
            else:
                # 如果结果已经是某种对象格式
                return result
                
        except Exception as e:
            logger.error(f"获取向量记忆时出错 ID={vector_id}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def list_cols(self):
        """列出所有集合"""
        # 这个方法可能需要直接访问底层客户端
        # 暂时只返回当前集合
        return [{"name": self.collection_name}]
    
    async def delete_col(self):
        """删除集合"""
        if not self.is_initialized:
            return
            
        # 获取统计信息
        stats = await self.vector_store.get_stats()
        logger.info(f"删除集合前统计: {stats}")
        
        # 由于 DashVectorHTTPStore 可能没有直接的删除集合方法
        # 这里我们暂时标记为未初始化并关闭连接
        self.is_initialized = False
        await self.vector_store.close()
        logger.info(f"已关闭 DashVector 集合连接: {self.collection_name}")
        return True
    
    async def col_info(self):
        """获取集合信息"""
        await self._ensure_initialized()
        
        # 获取统计信息
        stats = await self.vector_store.get_stats()
        return stats
    
    async def list(self, filters=None, limit=None):
        """列出所有向量"""
        await self._ensure_initialized()
        
        # 构建过滤字符串
        filter_str = None
        if filters:
            filter_parts = []
            for key, value in filters.items():
                filter_parts.append(f'{key}="{value}"')
            filter_str = " AND ".join(filter_parts)
        
        # 这里使用搜索但不提供向量，相当于列出所有符合条件的向量
        results = await self.vector_store.search(
            query_embedding=None,
            top_k=limit or 100,
            filter_str=filter_str
        )
        
        # 转换结果格式
        processed_results = []
        for result in results:
            # 创建一个类似 OutputData 的对象结构
            processed_result = type('OutputData', (), {
                'id': result.get("id", ""),
                'score': result.get("score", 0.0),
                'payload': {k: v for k, v in result.items() if k not in ["id", "score"]}
            })
            processed_results.append(processed_result)
            
        return processed_results
    
    async def reset(self):
        """重置集合"""
        # 标记为未初始化
        if self.is_initialized and self.vector_store:
            # 关闭连接
            await self.vector_store.close()
            
        self.is_initialized = False
        
        # 重新初始化
        await self._ensure_initialized()
        logger.info(f"已重置 DashVector 集合: {self.collection_name}")
        return True

    async def close(self):
        """关闭客户端连接"""
        if hasattr(self, 'client') and self.client:
            await self.client.aclose()
            logger.info("DashVector 客户端已关闭") 