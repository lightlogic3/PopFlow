"""记忆管理器与对话历史缓存集成

提供记忆管理器与对话历史缓存的集成功能
"""
from typing import List, Dict, Any, Optional

from knowledge_api.utils.log_config import get_logger
from plugIns.memory_system.cache_system.dialog_history_manager import DialogHistoryManager

class MemoryManagerIntegration:
    """记忆管理器与对话历史缓存集成
    
    提供记忆管理器与对话历史缓存的集成功能
    """
    
    def __init__(self, max_history_size: int = 10):
        """初始化集成器
        
        Args:
            max_history_size: 最大历史对话轮数，默认10轮
        """
        self._logger = get_logger()
        self._history_manager = DialogHistoryManager.get_instance(max_history_size=max_history_size)
        self._logger.info(f"记忆管理器与对话历史缓存集成初始化完成，最大历史轮数: {max_history_size}")
    
    async def store_dialog_history(self, user_id: str, namespace: str, dialog_batch: List[Dict[str, Any]]) -> bool:
        """存储对话批次到历史缓存
        
        Args:
            user_id: 用户ID
            namespace: 命名空间
            dialog_batch: 对话批次
            
        Returns:
            bool: 操作是否成功
        """
        if not dialog_batch:
            return True
            
        self._logger.info(f"存储 {len(dialog_batch)} 条对话到历史缓存，用户: {user_id}")
        return await self._history_manager.store_dialog_batch(user_id, namespace, dialog_batch)
    
    async def get_dialog_history(self, user_id: str, namespace: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取对话历史
        
        Args:
            user_id: 用户ID
            namespace: 命名空间
            limit: 获取的最大条数，None表示获取全部
            
        Returns:
            List[Dict[str, Any]]: 对话历史列表，按时间从旧到新排序
        """
        return await self._history_manager.get_dialog_history(user_id, namespace, limit)
    
    def set_max_history_size(self, size: int) -> None:
        """设置最大历史对话轮数
        
        Args:
            size: 最大历史对话轮数
        """
        self._history_manager.set_max_history_size(size)
    
    def get_max_history_size(self) -> int:
        """获取最大历史对话轮数
        
        Returns:
            int: 最大历史对话轮数
        """
        return self._history_manager.get_max_history_size()
    
    def get_history_manager(self) -> DialogHistoryManager:
        """获取对话历史管理器
        
        Returns:
            DialogHistoryManager: 对话历史管理器
        """
        return self._history_manager