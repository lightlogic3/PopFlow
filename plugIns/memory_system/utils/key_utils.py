from typing import Optional


class MemoryKeyBuilder:
    """记忆系统键值构建器"""
    
    @staticmethod
    def build_user_cache_key(user_id: str, role_id: str, session_id: Optional[str] = None) -> str:
        """
        构建用户缓存键
        
        Args:
            user_id: 用户ID
            role_id: 角色ID  
            session_id: 会话ID，可选
            
        Returns:
            str: 缓存键
        """
        if session_id:
            return f"{user_id}:{role_id}:{session_id}"
        else:
            return f"{user_id}:{role_id}"
    
    @staticmethod
    def build_dialog_cache_key(user_id: str, role_id: str, session_id: Optional[str] = None) -> str:
        """
        构建对话缓存键
        
        Args:
            user_id: 用户ID
            role_id: 角色ID
            session_id: 会话ID，可选
            
        Returns:
            str: 对话缓存键
        """
        base_key = MemoryKeyBuilder.build_user_cache_key(user_id, role_id, session_id)
        return f"memory_manager:dialog_cache:{base_key}"
    
    @staticmethod
    def build_processing_lock_key(user_id: str, role_id: str, session_id: Optional[str] = None) -> str:
        """
        构建处理锁键
        
        Args:
            user_id: 用户ID
            role_id: 角色ID
            session_id: 会话ID，可选
            
        Returns:
            str: 处理锁键
        """
        base_key = MemoryKeyBuilder.build_user_cache_key(user_id, role_id, session_id)
        return f"memory_manager:processing:{base_key}"
    
    @staticmethod
    def build_waiting_queue_key(user_id: str, role_id: str, session_id: Optional[str] = None) -> str:
        """
        构建等待队列键
        
        Args:
            user_id: 用户ID
            role_id: 角色ID
            session_id: 会话ID，可选
            
        Returns:
            str: 等待队列键
        """
        base_key = MemoryKeyBuilder.build_user_cache_key(user_id, role_id, session_id)
        return f"memory_manager:waiting:{base_key}"
    
    @staticmethod
    def build_metadata_lock_key(user_id: str, role_id: str) -> str:
        """
        构建元数据锁键
        
        Args:
            user_id: 用户ID
            role_id: 角色ID
            
        Returns:
            str: 元数据锁键
        """
        return f"memory_manager:metadata:{user_id}:{role_id}"
    
    @staticmethod
    def parse_cache_key(cache_key: str) -> tuple[str, str, Optional[str]]:
        """
        解析缓存键，提取用户ID、角色ID和会话ID
        
        Args:
            cache_key: 缓存键
            
        Returns:
            tuple: (user_id, role_id, session_id)
        """
        parts = cache_key.split(":", 2)
        if len(parts) >= 2:
            user_id = parts[0]
            role_id = parts[1]
            session_id = parts[2] if len(parts) > 2 else None
            return user_id, role_id, session_id
        else:
            raise ValueError(f"无效的缓存键格式: {cache_key}") 