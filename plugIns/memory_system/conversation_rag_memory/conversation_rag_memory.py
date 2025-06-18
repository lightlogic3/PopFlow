from typing import Dict, Any, List, Optional, AsyncGenerator
import time
import asyncio
from datetime import datetime
import logging
import json
import uuid
import os

from knowledge_manage.embeddings.factory import EmbeddingFactory
from knowledge_manage.vectorstores.factory import VectorStoreFactory
from knowledge_api.mapper.conversations.base import ConversationBase, Conversation
from knowledge_api.mapper.conversations.crud import ConversationCRUD
from knowledge_api.framework.database.database import get_thread_local_session
from knowledge_api.framework.redis.cache_manager import CacheManager

from ..memory_interface import MemoryInterface, UserMetadata
from ..model import MemoryContext  # 导入 MemoryContext 模型


class ConversationRAGMemory(MemoryInterface):
    """
    聊天记忆系统实现 - 基于对话历史的RAG检索
    
    特点：
    1. 支持用户ID隔离
    2. 支持角色ID隔离
    3. 支持会话ID隔离（可选）
    4. 支持历史会话检索（可控制是否包含）
    """
    dialog_batch_size = 2

    def __init__(self,
                 collection_name: str = None,
                 embedding_type: str = "huggingface",
                 store_type: str = "dashvector",
                 **kwargs):
        """
        初始化聊天记忆系统

        Args:
            collection_name: 集合名称
            embedding_type: 嵌入模型类型
            store_type: 向量存储类型
            **kwargs: 其他参数
        """
        # 使用环境变量或默认值设置集合名称
        self._collection_name = collection_name or os.getenv("USER_CONVERSATIONS", "long_term_memory_user_test")
        self._embedding_type = embedding_type
        self._store_type = store_type
        self._embedding_engine = None
        self._vector_store = None
        self._is_initialized = False
        self._kwargs = kwargs

        # 性能指标
        self._metrics = {
            "latency": 0.0,
            "throughput": 0.0,
            "accuracy": 0.0
        }

        # 同步状态管理
        self._sync_status = {}  # 用户ID -> 同步状态
        self._sync_locks = {}  # 用户ID -> 锁
        self._logger = logging.getLogger("ConversationRAGMemory")

    async def _initialize(self, is_init_collection: bool = True):
        """初始化向量存储和嵌入引擎"""
        if self._is_initialized:
            return

        try:
            # 初始化嵌入引擎
            self._embedding_engine = EmbeddingFactory.create_embedding(
                embedding_type=self._embedding_type,
                model_name="BAAI/bge-small-zh-v1.5"  # 使用支持的模型
            )

            # 定义向量存储的字段结构
            fields_schema = {
                "text": "STRING",  # 对话内容
                "user_id": "STRING",  # 用户ID
                "role_id": "STRING",  # 角色ID
                "session_id": "STRING",  # 会话ID
                "conversation_id": "STRING",  # 对话ID
                "message_id": "STRING",  # 消息ID
                "parent_message_id": "STRING",  # 父消息ID
                "role": "STRING",  # 消息角色（用户/AI）
                "timestamp": "STRING",  # 消息时间戳
                "metadata": "STRING",  # 其他元数据
            }

            # 准备DashVector所需的额外参数
            extra_kwargs = {}
            if self._store_type.lower() == "dashvector":
                extra_kwargs = {
                    "api_key": await CacheManager().get_system_config_value("DASHVECTOR_API_KEY"),
                    "endpoint": await CacheManager().get_system_config_value("DASHVECTOR_ENDPOINT"),
                    "metric": "cosine",
                    "dimension": 512  # bge-small 模型的维度
                }

            # 合并额外参数
            vector_kwargs = {**self._kwargs, **extra_kwargs}

            # 初始化向量存储
            self._vector_store = await VectorStoreFactory.create_vector_store(
                store_type=self._store_type,
                collection_name=self._collection_name,
                fields_schema=fields_schema,
                create_if_not_exists=True,
                is_init_collection=is_init_collection,
                **vector_kwargs
            )
            self._is_initialized = True
            self._logger.info(f"聊天记忆系统初始化完成，使用集合: {self._collection_name}")
        except Exception as e:
            self._logger.error(f"初始化聊天记忆系统失败: {e}")
            import traceback
            traceback.print_exc()
            raise

    async def store(self, data: MemoryContext, user_metadata: Optional[UserMetadata] = None) -> bool:
        """
        存储对话数据到记忆系统
        
        Args:
            data: 要存储的对话数据，MemoryContext类型
            user_metadata: 用户元数据，必须包含user_id和role_id两个必填字段
            
        Returns:
            bool: 存储是否成功
        """
        if not self._is_initialized:
            await self._initialize()
            
        try:
            # 验证user_metadata是否有效
            if not user_metadata:
                self._logger.error("存储失败: 必须提供user_metadata")
                return False
            
            # 确保user_id和role_id存在
            if not user_metadata.user_id:
                self._logger.error("存储失败: user_metadata中缺少必填字段user_id")
                return False
                
            if not user_metadata.role_id:
                self._logger.error("存储失败: user_metadata中缺少必填字段role_id")
                return False
            
            # 直接使用MemoryContext对象属性
            text = data.content
            if not text:
                self._logger.warning("内容为空，跳过存储")
                return True
            
            # 构建文档
            document = {
                "text": text,
                "user_id": user_metadata.user_id,
                "role_id": user_metadata.role_id,
                "session_id": user_metadata.session_id or "",
                "conversation_id": data.conversation_id or "",
                "message_id": data.message_id or str(uuid.uuid4()),
                "parent_message_id": data.parent_message_id or "",
                "role": data.source,  # 使用source作为role
                "timestamp": data.timestamp.isoformat() if data.timestamp else datetime.now().isoformat(),
                "metadata": json.dumps(data.metadata or {})
            }
            
            # 生成嵌入向量
            embeddings = self._embedding_engine.embed_documents([text])
            
            # 存储到向量数据库
            await self._vector_store.add_documents([document], embeddings)
            
            self._logger.info(f"成功存储对话记录，用户:{user_metadata.user_id}，角色:{user_metadata.role_id}")
            return True
        except Exception as e:
            self._logger.error(f"存储对话记录失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def retrieve(self, query: str, top_k: int = 5, user_metadata: Optional[UserMetadata] = None, **kwargs) -> \
            List[Dict[str, Any]]:
        """
        从记忆系统中检索相关对话
        
        Args:
            query: 查询字符串
            top_k: 返回结果数量
            user_metadata: 用户元数据，必须包含user_id和role_id两个必填字段
            **kwargs: 额外的检索参数
            
        Returns:
            List[Dict[str, Any]]: 检索结果列表
        """
        if not self._is_initialized:
            await self._initialize(False)

        # 验证user_metadata是否有效
        if not user_metadata:
            self._logger.error("检索失败: 必须提供user_metadata")
            return []
        
        # 确保user_id和role_id存在
        if not user_metadata.user_id:
            self._logger.error("检索失败: user_metadata中缺少必填字段user_id")
            return []
            
        if not user_metadata.role_id:
            self._logger.error("检索失败: user_metadata中缺少必填字段role_id")
            return []

        if hasattr(self._vector_store, 'is_init_collection'):
            self._vector_store.is_init_collection = False
            
        start_time = time.time()
        
        try:
            # 生成查询向量
            query_embedding = self._embedding_engine.embed_query(query)
            
            # 构建过滤条件
            filter_str = self._build_filter_string(user_metadata)
            
            # 执行向量检索
            results = await self._vector_store.search(
                query_embedding, 
                top_k=top_k, 
                filter_str=filter_str
            )
            
            # 处理结果
            processed_results = []
            for result in results:
                # 解析元数据
                try:
                    metadata = json.loads(result.get("metadata", "{}"))
                except:
                    metadata = {}
                    
                # 构建结果对象
                processed_result = {
                    "content": result.get("text", ""),
                    "user_id": result.get("user_id", ""),
                    "role_id": result.get("role_id", ""),
                    "session_id": result.get("session_id", ""),
                    "conversation_id": result.get("conversation_id", ""),
                    "message_id": result.get("message_id", ""),
                    "parent_message_id": result.get("parent_message_id", ""),
                    "role": result.get("role", ""),
                    "timestamp": result.get("timestamp", ""),
                    "score": result.get("score", 0.0),
                    "metadata": metadata
                }
                processed_results.append(processed_result)
            
            # 更新性能指标
            query_time = time.time() - start_time
            self._metrics["latency"] = query_time
            self._metrics["throughput"] = 1.0 / query_time if query_time > 0 else 0
            
            self._logger.info(f"检索完成，用户:{user_metadata.user_id}，角色:{user_metadata.role_id}，查询:'{query}'，结果数:{len(processed_results)}")
            return processed_results
        except Exception as e:
            self._logger.error(f"检索对话记录失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _build_filter_string(self, user_metadata: UserMetadata) -> Optional[str]:
        """
        构建过滤字符串
        
        Args:
            user_metadata: 用户元数据对象
            
        Returns:
            Optional[str]: 过滤字符串
        """
        filters = []
        
        # 添加用户ID过滤
        if user_metadata.user_id:
            filters.append(f'user_id="{user_metadata.user_id}"')
            
        # 添加角色ID过滤
        if user_metadata.role_id:
            filters.append(f'role_id="{user_metadata.role_id}"')
            
        # 添加会话ID过滤
        if user_metadata.session_id:
            filters.append(f'session_id="{user_metadata.session_id}"')
            
        return " AND ".join(filters) if filters else None
    
    async def update(self, data: MemoryContext, user_metadata: Optional[UserMetadata] = None, **kwargs) -> bool:
        """
        更新记忆系统中的对话记录
        """
        if not self._is_initialized:
            await self._initialize(False)

        # 验证user_metadata是否有效
        if not user_metadata:
            self._logger.error("更新失败: 必须提供user_metadata")
            return False
        
        # 确保user_id和role_id存在
        if not user_metadata.user_id:
            self._logger.error("更新失败: user_metadata中缺少必填字段user_id")
            return False
            
        if not user_metadata.role_id:
            self._logger.error("更新失败: user_metadata中缺少必填字段role_id")
            return False

        # 验证数据类型
        if not isinstance(data, MemoryContext):
            self._logger.error("更新失败: data必须是MemoryContext类型")
            return False

        # 使用data对象的属性
        if not data.message_id:
            self._logger.error("更新失败: MemoryContext中缺少message_id")
            return False

        try:
            # 构建更新文档
            update_doc = {
                "text": data.content,
                "user_id": user_metadata.user_id,
                "role_id": user_metadata.role_id,
                "session_id": user_metadata.session_id or "",
                "conversation_id": data.conversation_id or "",
                "message_id": data.message_id,
                "parent_message_id": data.parent_message_id or "",
                "role": data.metadata.get("role", "") if data.metadata else "",
                "timestamp": data.timestamp or self._get_timestamp(),
                "metadata": json.dumps(data.metadata) if data.metadata else "{}"
            }

            # 构建更新条件
            filter_dict = {
                "message_id": data.message_id,
                "user_id": user_metadata.user_id,
                "role_id": user_metadata.role_id
            }

            # 执行更新
            success = await self._vector_store.update(filter_dict, update_doc)
            
            if success:
                self._logger.info(f"更新成功，用户:{user_metadata.user_id}，角色:{user_metadata.role_id}，消息ID:{data.message_id}")
            else:
                self._logger.warning(f"更新失败，用户:{user_metadata.user_id}，角色:{user_metadata.role_id}，消息ID:{data.message_id}")
                
            return success
        except Exception as e:
            self._logger.error(f"更新对话记录失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def delete(self, memory_id: str, user_metadata: Optional[UserMetadata] = None, **kwargs) -> bool:
        """
        删除指定的记忆

        Args:
            memory_id: 记忆ID（消息ID）
            user_metadata: 用户元数据，必须包含user_id和role_id两个必填字段
            **kwargs: 额外参数

        Returns:
            bool: 删除是否成功
        """
        if not self._is_initialized:
            await self._initialize(False)

        # 验证user_metadata是否有效
        if not user_metadata:
            self._logger.error("删除失败: 必须提供user_metadata")
            return False
        
        # 确保user_id和role_id存在
        if not user_metadata.user_id:
            self._logger.error("删除失败: user_metadata中缺少必填字段user_id")
            return False
            
        if not hasattr(user_metadata, 'role_id') or not user_metadata.role_id:
            self._logger.error("删除失败: user_metadata中缺少必填字段role_id")
            return False
            
        # 这个方法尚未实现，可以根据需要添加实现
        self._logger.warning(f"删除记忆功能尚未实现，用户:{user_metadata.user_id}，角色:{user_metadata.role_id}")
        return False
    
    async def get_sync_status(self, user_metadata: UserMetadata) -> Dict[str, Any]:
        """
        获取同步状态
        
        Args:
            user_metadata: 用户元数据，必须包含user_id和role_id两个必填字段
            
        Returns:
            Dict[str, Any]: 同步状态信息
        """
        # 验证user_metadata是否有效
        if not user_metadata:
            self._logger.error("获取同步状态失败: 必须提供user_metadata")
            return {
                "is_syncing": False,
                "progress": 0.0,
                "last_sync_time": None,
                "error": "缺少用户元数据"
            }
        
        # 确保user_id存在
        if not hasattr(user_metadata, 'user_id') or not user_metadata.user_id:
            self._logger.error("获取同步状态失败: user_metadata中缺少必填字段user_id")
            return {
                "is_syncing": False,
                "progress": 0.0,
                "last_sync_time": None,
                "error": "缺少用户ID"
            }
            
        user_id = user_metadata.user_id
        
        if user_id not in self._sync_status:
            return {
                "is_syncing": False,
                "progress": 0.0,
                "last_sync_time": getattr(user_metadata, 'last_sync_time', None),
                "error": None
            }
        
        self._logger.debug(f"获取同步状态，用户:{user_id}, 角色:{user_metadata.role_id}, 进度:{getattr(self._sync_status.get(user_id, {}), 'progress', 0):.1f}%")
        return self._sync_status.get(user_id, {
            "is_syncing": False,
            "progress": 0.0,
            "last_sync_time": None,
            "error": None
        })
    
    @property
    def name(self) -> str:
        return "对话记忆系统"
    
    @property
    def description(self) -> str:
        return "基于对话历史的RAG记忆系统，支持用户隔离、角色隔离和会话隔离"
    
    @property
    def performance_metrics(self) -> Dict[str, float]:
        return self._metrics 