from typing import Dict, Any, List, Optional
import time
import logging
import uuid
import json
from datetime import datetime
from plugIns.memory_system.mem0_memory.mem0 import AsyncMemory
from plugIns.memory_system.memory_interface import MemoryInterface, UserMetadata
from plugIns.memory_system.model import MemoryContext


class Mem0Memory(MemoryInterface):
    """
    基于mem0框架实现的对话记忆系统
    主要功能：
    - 存储对话历史记录及相关元数据
    - 根据查询检索相关对话记忆
    - 支持按用户、角色、会话等多维度组织记忆
    """
    # 每次处理的对话批次大小
    dialog_batch_size  = 2

    @property
    def performance_metrics(self) -> Dict[str, float]:
        """返回系统性能指标（当前为占位值）"""
        return self._metrics

    @property
    def description(self) -> str:
        """返回系统描述信息"""
        return "基于mem0框架实现的对话记忆系统"

    @property
    def name(self) -> str:
        """返回系统名称"""
        return "Mem0Memory"

    def __init__(
            self,
            collection_name: str = "mem0_memory_user_test",
            embedding_model: str = "BAAI/bge-small-zh-v1.5",
            vector_store_type: str = "dashvector",
            **kwargs
    ):
        """
        初始化mem0记忆系统

        Args:
            collection_name: 向量数据库集合名称
            embedding_model: 嵌入模型名称/路径
            vector_store_type: 向量存储类型（默认chroma）
            **kwargs: 其他配置参数
        """
        self._logger = logging.getLogger("Mem0Memory")
        self._is_initialized = False
        # 性能指标
        self._metrics = {
            "latency": 0.0,  # 响应延迟（毫秒）
            "throughput": 0.0,  # 每秒处理请求数
            "accuracy": 0.0  # 检索准确率
        }

        # 构建mem0配置
        self.config = {
            "llm": {
                "provider": "doubao",
                "config": {"model": "doubao-pro-256k-241115"}
            },
            "embedder": {
                "provider": "huggingface",
                "config": {"model": embedding_model}
            },
            "vector_store": {
                "provider": vector_store_type,
                "config": {
                }
            },
        }

    async def _initialize(self):
        """异步初始化mem0实例"""
        if self._is_initialized:
            return

        try:
            self.memory = await AsyncMemory.from_config(self.config)
            self._is_initialized = True
            self._logger.info("Mem0记忆系统初始化完成")
        except Exception as error:
            self._logger.error(f"初始化失败: {error}")
            raise

    async def store(
            self,
            memory_context: MemoryContext,
            user_metadata: Optional[UserMetadata] = None
    ) -> bool:
        """
        存储对话记录到记忆系统

        Args:
            memory_context: 包含对话内容和元数据的上下文对象
            user_metadata: 用户相关元数据

        Returns:
            bool: 存储是否成功
        """
        self._logger.info("存储对话记录到mem0记忆系统")
        # print(f"memory_context:{memory_context}")
        # 确保系统已初始化
        if not self._is_initialized:
            await self._initialize()

        # 验证用户元数据
        if not user_metadata or not user_metadata.user_id:
            self._logger.error("存储失败: 必须提供有效的用户元数据")
            return False

        # 检查对话内容是否为空
        if not memory_context.source_dialog:
            self._logger.warning("忽略空对话记录")
            return False

        # 构建存储元数据
        storage_metadata = {
            "role_id": user_metadata.role_id or "default",
            "session_id": user_metadata.session_id or "default",
            "conversation_id": memory_context.conversation_id or "",
            "message_id": memory_context.message_id or str(uuid.uuid4()),
            "parent_message_id": memory_context.parent_message_id or "",
            "role": memory_context.source,  # 消息来源角色
            "timestamp": memory_context.timestamp.isoformat() if memory_context.timestamp
            else datetime.now().isoformat(),
            "nested_metadata": json.dumps(memory_context.metadata or {})
        }

        # 格式化对话消息
        dialog_messages = [
            {"role": dialog.get("source", "user"), "content": dialog.get("content", "")}
            for dialog in memory_context.source_dialog
        ]

        try:
            # 存储到记忆系统
            await self.memory.add(
                messages=dialog_messages,
                user_id=user_metadata.user_id,
                metadata=storage_metadata
            )
            self._logger.info("对话记录存储成功")
            return True
        except Exception as error:
            import traceback
            traceback.print_exc()
            self._logger.error(f"存储失败: {error}")
            return False

    async def retrieve(
            self,
            query: str,
            top_k: int = 5,
            user_metadata: Optional[UserMetadata] = None,
            **kwargs
    ) -> List[Dict[str, Any]]:
        """
        从记忆系统中检索相关对话记录

        Args:
            query: 检索查询文本
            top_k: 返回结果数量
            user_metadata: 用户相关元数据

        Returns:
            List[Dict]: 检索结果列表，包含记忆内容和元数据
        """
        self._logger.info("从mem0记忆系统检索对话记录")
        start_time=time.time()
        # 确保系统已初始化
        if not self._is_initialized:
            await self._initialize()

        # 验证用户元数据
        if not user_metadata or not user_metadata.user_id:
            self._logger.error("检索失败: 必须提供有效的用户元数据")
            return []

        # 构建检索过滤器
        retrieval_filters = {}
        if user_metadata.role_id:
            retrieval_filters["role_id"] = user_metadata.role_id
        if user_metadata.session_id:
            retrieval_filters["session_id"] = user_metadata.session_id

        try:
            # 执行检索操作
            if query:
                search_results = await self.memory.search(
                    query=query,
                    user_id=user_metadata.user_id,
                    limit=top_k,
                    filters=retrieval_filters or None
                )
            else:
                # 无查询时获取最近的记录
                search_results = await self.memory.get_all(
                    user_id=user_metadata.user_id,
                    filters=retrieval_filters or None,
                    limit=top_k
                )

            # 处理检索结果
            memory_records = search_results.get("results", [])
            formatted_results = []

            for record in memory_records:
                # 解析嵌套元数据
                nested_metadata = record["metadata"]
                content= record.get("content", "")
                if not content:
                    # 如果没有内容字段，尝试从内存字段获取
                    content = nested_metadata.get("memory", "")
                # 构建结果项
                result_item = {
                    "user_id": user_metadata.user_id,
                    "role": record.get("role", ""),
                    "content": content,
                    "score": 1 / (1 + record.get("score", 0.0)),
                    **record["metadata"],
                    **nested_metadata
                }
                # 移除已单独处理的嵌套元数据
                result_item.pop("nested_metadata", None)

                formatted_results.append(result_item)
            self._logger.info(f"检索到 {len(formatted_results)} 条结果")
            self._logger.info(f"结果: {formatted_results}")
            self._metrics["latency"] = time.time() - start_time
            self._logger.info(f"检索耗时: {self._metrics['latency']:.2f}秒")
            return formatted_results

        except Exception as error:
            import traceback
            traceback.print_exc()
            self._logger.error(f"检索失败: {error}")
            return []

    async def update(self, *args, **kwargs) -> bool:
        """更新记忆记录（当前未实现）"""
        return False

    async def delete(self, *args, **kwargs) -> bool:
        """删除记忆记录（当前未实现）"""
        return False

    async def get_sync_status(self, user_metadata: UserMetadata) -> Dict[str, Any]:
        """获取同步状态（当前未实现）"""
        return {}