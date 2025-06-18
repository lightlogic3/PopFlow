import asyncio
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime

from knowledge_api.framework.database.database import get_thread_local_session, get_session, get_db_session
from knowledge_api.mapper.conversations.base import Conversation

from knowledge_api.mapper.conversations.crud import ConversationCRUD
from knowledge_api.utils.log_config import get_logger
from plugIns.memory_system.model import UserMetadata, MemoryContext

logger = get_logger()

class MemoryInterface(ABC):
    """
    长期记忆系统的抽象接口
    所有记忆系统实现必须继承此接口
    """
    dialog_batch_size = 1  # 默认批次大小，子类可以覆盖

    @abstractmethod
    async def store(self, data: MemoryContext, user_metadata: Optional[UserMetadata] = None) -> bool:
        """
        存储数据到记忆系统
        
        Args:
            data: 要存储的数据，MemoryContext类型
            user_metadata: 用户元数据，必须包含user_id和role_id两个必填字段
            
        Returns:
            bool: 存储是否成功
        """
        pass

    @abstractmethod
    async def retrieve(self, query: str, top_k: int = 5, user_metadata: Optional[UserMetadata] = None, **kwargs) -> \
            List[Dict[str, Any]]:
        """
        从记忆系统中检索相关信息
        
        Args:
            query: 查询字符串
            top_k: 返回结果数量
            user_metadata: 用户元数据，必须包含user_id和role_id两个必填字段
            **kwargs: 额外的检索参数
            
        Returns:
            List[Dict[str, Any]]: 检索结果列表
        """
        pass

    @abstractmethod
    async def update(self, memory_id: str, data: Dict[str, Any], user_metadata: Optional[UserMetadata] = None) -> bool:
        """
        更新已存在的记忆
        
        Args:
            memory_id: 记忆ID
            data: 更新的数据
            user_metadata: 用户元数据，必须包含user_id和role_id两个必填字段
            
        Returns:
            bool: 更新是否成功
        """
        pass

    @abstractmethod
    async def delete(self, memory_id: str, user_metadata: Optional[UserMetadata] = None) -> bool:
        """
        删除记忆
        
        Args:
            memory_id: 记忆ID
            user_metadata: 用户元数据，必须包含user_id和role_id两个必填字段
            
        Returns:
            bool: 删除是否成功
        """
        pass

    async def sync_from_database(self, user_metadata: UserMetadata, start_time: Optional[datetime] = None,
                                 end_time: Optional[datetime] = None) -> AsyncGenerator[List[Conversation], None]:
        """
        从关系数据库同步数据到记忆系统（通用实现）
        
        子类只需要实现store方法，这个方法会自动处理批次分组、对话合并等逻辑

        Args:
            user_metadata: 用户元数据，必须包含user_id和role_id两个必填字段
            start_time: 同步的起始时间，如果为None则从上次同步时间开始
            end_time: 同步的结束时间，如果为None则到当前时间

        Yields:
            List[Conversation]: 每次成功处理的对话批次
        """
        # 获取待同步的对话列表
        conversations = getattr(user_metadata, 'conversations', [])
        if not conversations:
            logger.info(f"没有待同步的对话，用户: {user_metadata.user_id}, 角色: {user_metadata.role_id}")
            return

        logger.info(f"开始同步对话数据到{self.name}，总数: {len(conversations)}, 批次大小: {self.dialog_batch_size}, 用户: {user_metadata.user_id}")
        
        # 按dialog_batch_size分批处理，每个批次合并成一个MemoryContext
        batch_size = self.dialog_batch_size
        total_batches = (len(conversations) + batch_size - 1) // batch_size
        
        for batch_index in range(0, len(conversations), batch_size):
            # 获取当前批次的对话
            batch_conversations = conversations[batch_index:batch_index + batch_size]
            current_batch_num = (batch_index // batch_size) + 1
            
            logger.info(f"处理第 {current_batch_num}/{total_batches} 批次，包含 {len(batch_conversations)} 条对话")
            
            try:
                # 构建格式化的对话内容
                formatted_dialogs = []
                dialog_roles = set()
                source_dialogs = []
                
                # 按时间排序确保对话顺序正确
                sorted_batch = sorted(batch_conversations, key=lambda x: x.created_at)
                
                for conv in sorted_batch:
                    # 确定角色显示名称
                    if conv.role.lower() == 'user':
                        role_display = '用户'
                    elif conv.role.lower() == 'assistant':
                        role_display = 'AI'
                    else:
                        role_display = conv.role
                    
                    # 添加到格式化对话
                    formatted_dialogs.append(f"{role_display}：{conv.content}")
                    dialog_roles.add(role_display)
                    
                    # 转换为字典保存原始数据
                    conv_dict = {
                        "id": conv.id,
                        "user_id": conv.user_id,
                        "session_id": conv.session_id,
                        "chat_role_id": conv.chat_role_id,
                        "conversation_id": conv.conversation_id,
                        "message_id": conv.message_id,
                        "parent_message_id": conv.parent_message_id,
                        "role": conv.role,
                        "content": conv.content,
                        "prompt_tokens": conv.prompt_tokens,
                        "completion_tokens": conv.completion_tokens,
                        "total_tokens": conv.total_tokens,
                        "model_name": conv.model_name,
                        "created_at": conv.created_at.isoformat() if conv.created_at else None,
                        "is_sync": conv.is_sync
                    }
                    source_dialogs.append(conv_dict)
                
                # 合并对话内容
                combined_content = "\n\n".join(formatted_dialogs)
                
                # 获取历史记录（往前推10条）
                history_dialogs = []
                if batch_index > 0:
                    # 计算历史记录的起始位置
                    history_start = max(0, batch_index - 10)
                    history_conversations = conversations[history_start:batch_index]
                    
                    for hist_conv in history_conversations:
                        hist_role_display = '用户' if hist_conv.role.lower() == 'user' else 'AI' if hist_conv.role.lower() == 'assistant' else hist_conv.role
                        history_dialogs.append({
                            "role": hist_role_display,
                            "content": hist_conv.content,
                            "timestamp": hist_conv.created_at.isoformat() if hist_conv.created_at else None,
                            "conversation_id": hist_conv.conversation_id,
                            "message_id": hist_conv.message_id
                        })
                
                # 确定session_id - 使用批次中第一个对话的session_id
                batch_session_id = sorted_batch[0].session_id if sorted_batch else None
                
                # 创建MemoryContext对象，包含子类特定的元数据
                base_metadata = {
                    "batch_index": current_batch_num,
                    "batch_size": len(batch_conversations),
                    "sync_timestamp": datetime.now().isoformat(),
                    "is_synced_from_db": True,
                    "total_tokens": sum(conv.total_tokens or 0 for conv in sorted_batch),
                    "conversation_ids": [conv.conversation_id for conv in sorted_batch],
                    "message_ids": [conv.message_id for conv in sorted_batch]
                }
                
                # 允许子类添加特定的元数据
                custom_metadata = self._get_custom_metadata(batch_conversations, current_batch_num)
                base_metadata.update(custom_metadata)
                
                memory_context = MemoryContext(
                    content=combined_content,
                    source="dialog_batch",  # 标识这是对话批次
                    timestamp=sorted_batch[-1].created_at if sorted_batch else datetime.now(),  # 使用最后一条对话的时间
                    dialog_roles=list(dialog_roles),
                    source_dialog=source_dialogs,
                    history=history_dialogs,
                    conversation_id=sorted_batch[0].conversation_id if sorted_batch else None,
                    session_id=batch_session_id,
                    is_summarized=True,
                    summary_count=len(batch_conversations),
                    metadata=base_metadata
                )
                
                logger.info(f"{self.name}批次 {current_batch_num} 对话合并完成:")
                logger.info(f"  - 内容长度: {len(combined_content)}")
                logger.info(f"  - 包含角色: {list(dialog_roles)}")
                logger.info(f"  - 历史记录: {len(history_dialogs)} 条")
                logger.info(f"  - 会话ID: {batch_session_id}")
                
                # 调用子类的store方法存储合并后的MemoryContext
                store_success = await self.store(memory_context, user_metadata)
                
                if store_success:
                    logger.info(f"{self.name}批次 {current_batch_num} 存储成功，包含 {len(batch_conversations)} 条对话")
                    # yield 当前批次的原始对话列表，供父类更新同步状态
                    yield batch_conversations
                else:
                    logger.error(f"{self.name}批次 {current_batch_num} 存储失败")
                    
            except Exception as e:
                logger.error(f"处理{self.name}第 {current_batch_num} 批次时发生错误: {e}")
                import traceback
                traceback.print_exc()
                # 继续处理下一个批次
                continue
        
        logger.info(f"{self.name}对话同步任务完成，用户: {user_metadata.user_id}, 角色: {user_metadata.role_id}")

    def _get_custom_metadata(self, batch_conversations: List[Conversation], batch_num: int) -> Dict[str, Any]:
        """
        子类可以重写此方法来添加特定的元数据
        
        Args:
            batch_conversations: 当前批次的对话列表
            batch_num: 批次编号
            
        Returns:
            Dict[str, Any]: 子类特定的元数据
        """
        return {}

    async def sync_to_database(self, user_metadata: UserMetadata, start_time: Optional[datetime] = None,
                               end_time: Optional[datetime] = None) -> bool:
        """
        将向量数据库中的数据同步回关系数据库

        Args:
            user_metadata: 用户元数据，必须包含user_id和role_id两个必填字段
            start_time: 同步的起始时间，如果为None则从上次同步时间开始
            end_time: 同步的结束时间，如果为None则到当前时间
            run_in_background: 是否在后台运行同步过程

        Returns:
            bool: 同步是否成功启动
        """
        # 验证用户元数据
        async def _sync_task():
            if not hasattr(user_metadata, 'user_id') or not user_metadata.user_id:
                raise ValueError("user_metadata必须包含user_id")
            if not hasattr(user_metadata, 'role_id') or not user_metadata.role_id:
                raise ValueError("user_metadata必须包含role_id")
            crud = ConversationCRUD(get_thread_local_session())
            conversations = await crud.get_all_conversations_by_not_syncing(user_id=user_metadata.user_id,role_id=user_metadata.role_id)
            user_metadata.conversations = conversations

            async for conversation in self.sync_from_database(user_metadata,
                                                                    start_time=start_time,
                                                                    end_time=end_time):
                await crud.update_sync_status([c.id for c in conversation])

        asyncio.create_task(_sync_task())


        return True

    @abstractmethod
    async def get_sync_status(self, user_metadata: UserMetadata) -> Dict[str, Any]:
        """
        获取同步状态
        
        Args:
            user_metadata: 用户元数据，必须包含user_id和role_id两个必填字段
            
        Returns:
            Dict[str, Any]: 同步状态信息，包括是否正在同步、进度等
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """记忆系统名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """记忆系统描述"""
        pass

    @property
    @abstractmethod
    def performance_metrics(self) -> Dict[str, float]:
        """
        获取记忆系统性能指标
        
        Returns:
            Dict[str, float]: 性能指标字典，如延迟、吞吐量等
        """
        pass
