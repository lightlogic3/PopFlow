"""对话历史缓存插件

提供基于Redis的对话历史缓存功能，支持可配置轮数的FIFO队列管理
"""
from typing import List, Dict, Any, Optional, Union
import json
import asyncio
from datetime import datetime

from knowledge_api.framework.redis.connection import get_async_redis
from knowledge_api.framework.redis.cache import RedisCache
from knowledge_api.framework.redis.redis_lock import RedisLock
from knowledge_api.utils.log_config import get_logger

# 自定义JSON编码器处理datetime对象
class DateTimeEncoder(json.JSONEncoder):
    """处理datetime对象的JSON编码器"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class DialogHistoryCache:
    """对话历史缓存管理器
    
    提供对话历史的缓存管理功能，支持可配置轮数的FIFO队列
    """
    
    def __init__(self, max_history_size: int = 10, ttl: int = 86400 * 7):
        """初始化对话历史缓存管理器
        
        Args:
            max_history_size: 最大历史对话轮数，默认10轮
            ttl: 缓存过期时间（秒），默认7天
        """
        self._logger = get_logger()
        self._max_history_size = max_history_size
        self._ttl = ttl
        self._cache_prefix = "dialog_history:"
        self._redis_cache = RedisCache(prefix=self._cache_prefix, default_ttl=ttl)
        
    def _get_history_key(self, user_id: str, namespace: str) -> str:
        """获取历史对话缓存键
        
        Args:
            user_id: 用户ID
            namespace: 命名空间（格式为role_id:session_key）
            
        Returns:
            str: 缓存键
        """
        return f"{user_id}:{namespace}:history"
    
    async def add_dialog(self, user_id: str, namespace: str, dialog: Dict[str, Any]) -> bool:
        """添加对话到历史缓存
        
        Args:
            user_id: 用户ID
            namespace: 命名空间（格式为role_id:session_key）
            dialog: 对话数据
            
        Returns:
            bool: 操作是否成功
        """
        # 解析namespace获取role_id和session_key用于日志
        parts = namespace.split(":", 1)
        role_id = parts[0] if len(parts) > 0 else "unknown"
        session_key = parts[1] if len(parts) > 1 else "all_sessions"
        
        history_key = self._get_history_key(user_id, namespace)
        lock_key = f"lock:{history_key}"
        
        # 使用分布式锁确保原子操作
        async with RedisLock(lock_key, expire=10) as lock_acquired:
            if not lock_acquired:
                self._logger.error(f"无法获取锁，添加对话失败: 用户={user_id}, 角色={role_id}, 会话={session_key}")
                return False
                
            try:
                redis = await get_async_redis()
                
                # 序列化对话数据
                dialog_json = json.dumps(dialog, cls=DateTimeEncoder, ensure_ascii=False)
                
                # 添加到列表尾部
                await redis.rpush(history_key, dialog_json)
                
                # 设置过期时间
                await redis.expire(history_key, self._ttl)
                
                # 检查并维持最大历史大小
                length = await redis.llen(history_key)
                if length > self._max_history_size:
                    # 移除多余的对话（从头部移除最旧的）
                    to_remove = length - self._max_history_size
                    await redis.ltrim(history_key, to_remove, -1)
                    self._logger.debug(f"已移除 {to_remove} 条最旧的对话历史，用户: {user_id}, 角色: {role_id}, 会话: {session_key}")
                
                self._logger.debug(f"成功添加对话到历史缓存，当前历史大小: {min(length, self._max_history_size)}，用户: {user_id}, 角色: {role_id}, 会话: {session_key}")
                return True
            except Exception as e:
                self._logger.error(f"添加对话到历史缓存失败: {e}, 用户: {user_id}, 角色: {role_id}, 会话: {session_key}")
                return False
    
    async def get_dialog_history(self, user_id: str, namespace: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取对话历史
        
        Args:
            user_id: 用户ID
            namespace: 命名空间（格式为role_id:session_key）
            limit: 获取的最大条数，None表示获取全部
            
        Returns:
            List[Dict[str, Any]]: 对话历史列表，按时间从旧到新排序
        """
        # 解析namespace获取role_id和session_key用于日志
        parts = namespace.split(":", 1)
        role_id = parts[0] if len(parts) > 0 else "unknown"
        session_key = parts[1] if len(parts) > 1 else "all_sessions"
        
        history_key = self._get_history_key(user_id, namespace)
        
        try:
            redis = await get_async_redis()
            
            # 确定获取范围
            if limit is None or limit >= self._max_history_size:
                # 获取全部历史
                start = 0
                end = -1
            else:
                # 获取最近的limit条
                start = -limit
                end = -1
                
            # 获取对话历史
            dialog_jsons = await redis.lrange(history_key, start, end)
            
            if not dialog_jsons:
                self._logger.debug(f"未找到对话历史，用户: {user_id}, 角色: {role_id}, 会话: {session_key}")
                return []
                
            # 解析JSON数据
            dialogs = []
            for dialog_json in dialog_jsons:
                try:
                    dialog = json.loads(dialog_json)
                    dialogs.append(dialog)
                except Exception as e:
                    self._logger.error(f"解析对话历史JSON失败: {e}, 用户: {user_id}, 角色: {role_id}, 会话: {session_key}")
            
            self._logger.debug(f"成功获取 {len(dialogs)} 条对话历史，用户: {user_id}, 角色: {role_id}, 会话: {session_key}")
            return dialogs
        except Exception as e:
            self._logger.error(f"获取对话历史失败: {e}, 用户: {user_id}, 角色: {role_id}, 会话: {session_key}")
            return []
    
    async def clear_dialog_history(self, user_id: str, namespace: str) -> bool:
        """清空对话历史
        
        Args:
            user_id: 用户ID
            namespace: 命名空间（格式为role_id:session_key）
            
        Returns:
            bool: 操作是否成功
        """
        # 解析namespace获取role_id和session_key用于日志
        parts = namespace.split(":", 1)
        role_id = parts[0] if len(parts) > 0 else "unknown"
        session_key = parts[1] if len(parts) > 1 else "all_sessions"
        
        history_key = self._get_history_key(user_id, namespace)
        
        try:
            redis = await get_async_redis()
            await redis.delete(history_key)
            self._logger.debug(f"成功清空对话历史，用户: {user_id}, 角色: {role_id}, 会话: {session_key}")
            return True
        except Exception as e:
            self._logger.error(f"清空对话历史失败: {e}, 用户: {user_id}, 角色: {role_id}, 会话: {session_key}")
            return False
    
    async def get_history_size(self, user_id: str, namespace: str) -> int:
        """获取当前对话历史大小
        
        Args:
            user_id: 用户ID
            namespace: 命名空间（格式为role_id:session_key）
            
        Returns:
            int: 当前历史大小
        """
        # 解析namespace获取role_id和session_key用于日志
        parts = namespace.split(":", 1)
        role_id = parts[0] if len(parts) > 0 else "unknown"
        session_key = parts[1] if len(parts) > 1 else "all_sessions"
        
        history_key = self._get_history_key(user_id, namespace)
        
        try:
            redis = await get_async_redis()
            size = await redis.llen(history_key)
            return size
        except Exception as e:
            self._logger.error(f"获取对话历史大小失败: {e}, 用户: {user_id}, 角色: {role_id}, 会话: {session_key}")
            return 0
    
    def set_max_history_size(self, size: int) -> None:
        """设置最大历史对话轮数
        
        Args:
            size: 最大历史对话轮数
        """
        if size < 1:
            self._logger.warning(f"最大历史大小不能小于1，设置为默认值1")
            size = 1
        self._max_history_size = size
        self._logger.info(f"已设置最大历史对话轮数为: {size}")
    
    def get_max_history_size(self) -> int:
        """获取最大历史对话轮数
        
        Returns:
            int: 最大历史对话轮数
        """
        return self._max_history_size