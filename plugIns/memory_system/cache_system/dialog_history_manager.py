"""对话历史管理器

管理对话历史缓存，提供与记忆系统集成的接口
"""
from typing import List, Dict, Any, Optional

from knowledge_api.utils.log_config import get_logger
from plugIns.memory_system.cache_system.dialog_history_cache import DialogHistoryCache

class DialogHistoryManager:
    """对话历史管理器
    
    管理对话历史缓存，提供与记忆系统集成的接口
    """
    
    _instance = None
    
    @classmethod
    def get_instance(cls, max_history_size: int = 10, ttl: int = 86400 * 7):
        """获取单例实例
        
        Args:
            max_history_size: 最大历史对话轮数，默认10轮
            ttl: 缓存过期时间（秒），默认7天
            
        Returns:
            DialogHistoryManager: 单例实例
        """
        if cls._instance is None:
            cls._instance = DialogHistoryManager(max_history_size, ttl)
        return cls._instance
    
    def __init__(self, max_history_size: int = 10, ttl: int = 86400 * 7):
        """初始化对话历史管理器
        
        Args:
            max_history_size: 最大历史对话轮数，默认10轮
            ttl: 缓存过期时间（秒），默认7天
        """
        self._logger = get_logger()
        self._cache = DialogHistoryCache(max_history_size, ttl)
        self._logger.info(f"对话历史管理器初始化完成，最大历史轮数: {max_history_size}, TTL: {ttl}秒")
    
    async def store_dialog(self, user_id: str, role_id: str, session_id: Optional[str] = None, dialog: Dict[str, Any] = None) -> bool:
        """存储对话到历史缓存
        
        Args:
            user_id: 用户ID，必填
            role_id: 角色ID，必填，用于角色隔离
            session_id: 会话ID，可选，为None时表示全部会话
            dialog: 对话数据
            
        Returns:
            bool: 操作是否成功
        """
        if not user_id or not role_id:
            self._logger.error(f"存储对话失败: user_id={user_id}, role_id={role_id}，必须提供这两个字段")
            return False
            
        if not dialog:
            self._logger.warning(f"存储对话失败: dialog为空")
            return False
            
        # 处理session_id为None的情况
        session_key = session_id if session_id else "all_sessions"
        namespace = f"{role_id}:{session_key}"
        
        self._logger.debug(f"存储对话到历史缓存，用户: {user_id}, 角色: {role_id}, 会话: {session_key}")
        return await self._cache.add_dialog(user_id, namespace, dialog)
    
    async def store_dialog_batch(self, user_id: str, role_id: str, session_id: Optional[str] = None, dialog_batch: List[Dict[str, Any]] = None) -> bool:
        """存储对话批次到历史缓存
        
        Args:
            user_id: 用户ID，必填
            role_id: 角色ID，必填，用于角色隔离
            session_id: 会话ID，可选，为None时表示全部会话
            dialog_batch: 对话批次
            
        Returns:
            bool: 操作是否成功
        """
        if not user_id or not role_id:
            self._logger.error(f"存储对话批次失败: user_id={user_id}, role_id={role_id}，必须提供这两个字段")
            return False
            
        if not dialog_batch:
            return True
            
        # 处理session_id为None的情况
        session_key = session_id if session_id else "all_sessions"
        namespace = f"{role_id}:{session_key}"
            
        self._logger.debug(f"存储 {len(dialog_batch)} 条对话到历史缓存，用户: {user_id}, 角色: {role_id}, 会话: {session_key}")
        
        success_count = 0
        for dialog in dialog_batch:
            if await self._cache.add_dialog(user_id, namespace, dialog):
                success_count += 1
                
        success_rate = success_count / len(dialog_batch)
        self._logger.debug(f"对话批次存储完成，成功率: {success_rate:.2%}，用户: {user_id}, 角色: {role_id}, 会话: {session_key}")
        
        # 如果大部分成功，则认为整体成功
        return success_rate >= 0.8
    
    async def get_dialog_history(self, user_id: str, role_id: str, session_id: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取对话历史
        
        Args:
            user_id: 用户ID，必填
            role_id: 角色ID，必填，用于角色隔离
            session_id: 会话ID，可选，为None时表示全部会话
            limit: 获取的最大条数，None表示获取全部
            
        Returns:
            List[Dict[str, Any]]: 对话历史列表，按时间从旧到新排序
        """
        if not user_id or not role_id:
            self._logger.error(f"获取对话历史失败: user_id={user_id}, role_id={role_id}，必须提供这两个字段")
            return []
            
        # 处理session_id为None的情况
        session_key = session_id if session_id else "all_sessions"
        namespace = f"{role_id}:{session_key}"
            
        self._logger.debug(f"获取对话历史，用户: {user_id}, 角色: {role_id}, 会话: {session_key}, 限制: {limit or '全部'}")
        return await self._cache.get_dialog_history(user_id, namespace, limit)
    
    async def clear_dialog_history(self, user_id: str, role_id: str, session_id: Optional[str] = None) -> bool:
        """清空对话历史
        
        Args:
            user_id: 用户ID，必填
            role_id: 角色ID，必填，用于角色隔离
            session_id: 会话ID，可选，为None时表示全部会话
            
        Returns:
            bool: 操作是否成功
        """
        if not user_id or not role_id:
            self._logger.error(f"清空对话历史失败: user_id={user_id}, role_id={role_id}，必须提供这两个字段")
            return False
            
        # 处理session_id为None的情况
        session_key = session_id if session_id else "all_sessions"
        namespace = f"{role_id}:{session_key}"
            
        self._logger.debug(f"清空对话历史，用户: {user_id}, 角色: {role_id}, 会话: {session_key}")
        return await self._cache.clear_dialog_history(user_id, namespace)
    
    async def get_history_size(self, user_id: str, role_id: str, session_id: Optional[str] = None) -> int:
        """获取当前对话历史大小
        
        Args:
            user_id: 用户ID，必填
            role_id: 角色ID，必填，用于角色隔离
            session_id: 会话ID，可选，为None时表示全部会话
            
        Returns:
            int: 当前历史大小
        """
        if not user_id or not role_id:
            self._logger.error(f"获取对话历史大小失败: user_id={user_id}, role_id={role_id}，必须提供这两个字段")
            return 0
            
        # 处理session_id为None的情况
        session_key = session_id if session_id else "all_sessions"
        namespace = f"{role_id}:{session_key}"
            
        return await self._cache.get_history_size(user_id, namespace)
    
    def set_max_history_size(self, size: int) -> None:
        """设置最大历史对话轮数
        
        Args:
            size: 最大历史对话轮数
        """
        self._cache.set_max_history_size(size)
    
    def get_max_history_size(self) -> int:
        """获取最大历史对话轮数
        
        Returns:
            int: 最大历史对话轮数
        """
        return self._cache.get_max_history_size()
    
    def get_cache(self) -> DialogHistoryCache:
        """获取对话历史缓存实例
        
        Returns:
            DialogHistoryCache: 缓存实例
        """
        return self._cache