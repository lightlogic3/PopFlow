import pickle
import base64
import json
from typing import Dict, Any, Optional
from datetime import datetime

from knowledge_api.framework.redis.connection import get_async_redis
from knowledge_api.framework.memory.enhanced_chat_memory_manager import EnhancedChatMemoryManager
from knowledge_api.utils.log_config import get_logger

logger = get_logger()


class SessionCacheManager:
    """Session cache manager for storing and restoring session data in Redis"""

    # Redis key prefix
    KEY_PREFIX = "chat:session:"
    # Default expiration time (7 days)
    DEFAULT_EXPIRY = 86400 * 7

    @staticmethod
    async def save_session(session_id: str, session_data: Dict[str, Any], expiry: int = None) -> bool:
        """Save session data to Redis

Args:
session_id: Session ID
session_data: Session Data Dictionary
Expiry: expiration time (seconds), default is 7 days

Returns:
Did you save successfully?"""
        if not session_id:
            logger.warning("Saving session failed: Session ID is empty")
            return False

        try:
            # Serialize session data
            serialized = SessionCacheManager.serialize_session(session_data)

            # Save to Redis
            redis = await get_async_redis()
            key = f"{SessionCacheManager.KEY_PREFIX}{session_id}"

            # Set expiration time
            expiry_time = expiry if expiry is not None else SessionCacheManager.DEFAULT_EXPIRY
            await redis.set(key, serialized, ex=expiry_time)

            logger.debug(f"会话已保存到Redis: {session_id}")
            return True
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"保存会话到Redis出错: {str(e)}")
            return False

    @staticmethod
    async def load_session(session_id: str) -> Optional[Dict[str, Any]]:
        """Loading session data from Redis

Args:
session_id: Session ID

Returns:
Session data dictionary, return None if none exists"""
        if not session_id:
            logger.warning("Loading session failed: Session ID is empty")
            return None

        try:
            redis = await get_async_redis()
            key = f"{SessionCacheManager.KEY_PREFIX}{session_id}"

            # Get serialized session data
            serialized = await redis.get(key)
            if not serialized:
                logger.debug(f"Redis中不存在会话数据: {session_id}")
                return None

            # deserialization
            session_data = SessionCacheManager.deserialize_session(serialized)
            logger.debug(f"从Redis加载会话: {session_id}")
            return session_data
        except Exception as e:
            logger.error(f"从Redis加载会话出错: {str(e)}")
            return None

    @staticmethod
    async def delete_session(session_id: str) -> bool:
        """Delete session data from Redis

Args:
session_id: Session ID

Returns:
Whether the deletion was successful"""
        if not session_id:
            return False

        try:
            redis = await get_async_redis()
            key = f"{SessionCacheManager.KEY_PREFIX}{session_id}"

            # Delete session
            await redis.delete(key)
            logger.debug(f"已从Redis删除会话: {session_id}")
            return True
        except Exception as e:
            logger.error(f"从Redis删除会话出错: {str(e)}")
            return False

    @staticmethod
    async def clean_expired_sessions(pattern: str = None, max_age_days: int = 30) -> int:
        """Clean up expired session data

Args:
Pattern: Redis key mode, defaults to all sessions
max_age_days: Maximum retention days, default 30 days

Returns:
Number of sessions cleared"""
        try:
            redis = await get_async_redis()
            pattern = pattern or f"{SessionCacheManager.KEY_PREFIX}*"

            # Get all matching keys
            keys = await redis.keys(pattern)

            # Clean session count
            cleaned_count = 0

            for key in keys:
                # Get the expiration time of the key
                ttl = await redis.ttl(key)

                # If the TTL has expired or is close to the maximum retention days, remove it
                if ttl < 0 or ttl > (max_age_days * 86400):
                    await redis.delete(key)
                    cleaned_count += 1

            logger.info(f"已清理过期会话: {cleaned_count}个")
            return cleaned_count
        except Exception as e:
            logger.error(f"清理过期会话出错: {str(e)}")
            return 0

    @staticmethod
    async def get_all_sessions(pattern: str = None) -> Dict[str, Dict[str, Any]]:
        """Get all session data

Args:
Pattern: Redis key mode, defaults to all sessions

Returns:
Session ID to Session Data Mapping"""
        try:
            redis = await get_async_redis()
            pattern = pattern or f"{SessionCacheManager.KEY_PREFIX}*"

            # Get all matching keys
            keys = await redis.keys(pattern)

            # session data
            sessions = {}

            for key in keys:
                # Extract session ID
                session_id = key.replace(SessionCacheManager.KEY_PREFIX, "")

                # Get session data
                serialized = await redis.get(key)
                if serialized:
                    session_data = SessionCacheManager.deserialize_session(serialized)
                    sessions[session_id] = session_data

            return sessions
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"获取所有会话出错: {str(e)}")
            return {}

    @staticmethod
    def serialize_memory_manager(memory_manager):
        """Serializing Memory Manager Objects

Args:
memory_manager: Examples EnhancedChatMemoryManager

Returns:
Serialized dictionary"""
        if not memory_manager:
            return None
        try:
            return {
                "type": "memory_manager",
                "data": base64.b64encode(pickle.dumps(memory_manager)).decode('utf-8')
            }
        except Exception as e:
            logger.error(f"序列化内存管理器出错: {str(e)}")
            return None

    @staticmethod
    def deserialize_memory_manager(data):
        """deserializing a memory manager object

Args:
Data: Serialized data

Returns:
Examples EnhancedChatMemoryManager"""
        if not data:
            return None
        try:
            return pickle.loads(base64.b64decode(data.encode('utf-8')))
        except Exception as e:
            logger.error(f"反序列化内存管理器出错: {str(e)}")
            return None

    @staticmethod
    def serialize_session(session_data: Dict[str, Any]) -> str:
        """Serialize session data into a JSON string

Args:
session_data: Session Data Dictionary

Returns:
JSON string"""
        if not session_data:
            return "{}"

        serializable_data = {}

        # Process each key-value pair
        for key, value in session_data.items():
            # Special Processing Memory Manager
            if key == "memory_manager" and isinstance(value, EnhancedChatMemoryManager):
                serializable_data[key] = SessionCacheManager.serialize_memory_manager(value)
            # Handling common data types
            elif isinstance(value, (dict, list, str, int, float, bool)) or value is None:
                serializable_data[key] = value
            # Handling datetime objects
            elif isinstance(value, datetime):
                serializable_data[key] = {
                    "type": "datetime",
                    "data": value.isoformat()
                }
            # Attempt to serialize other objects using pickle
            else:
                try:
                    serializable_data[key] = {
                        "type": "pickle_obj",
                        "class": value.__class__.__name__,
                        "data": base64.b64encode(pickle.dumps(value)).decode('utf-8')
                    }
                except:
                    # Objects that cannot be serialized are skipped and logged
                    logger.warning(f"无法序列化的对象被跳过: {key}, 类型: {value.__class__.__name__}")
                    serializable_data[key] = {
                        "type": "unserializable",
                        "class": value.__class__.__name__
                    }

        return json.dumps(serializable_data)

    @staticmethod
    def deserialize_session(json_str: str) -> Dict[str, Any]:
        """Deserialize JSON strings to session data

Args:
json_str: JSON string

Returns:
session data dictionary"""
        if not json_str:
            return {}

        try:
            serialized_data = json.loads(json_str)
            restored_data = {}

            for key, value in serialized_data.items():
                # Handling object types
                if isinstance(value, dict) and "type" in value:
                    obj_type = value["type"]

                    if obj_type == "memory_manager":
                        restored_data[key] = SessionCacheManager.deserialize_memory_manager(value["data"])
                    elif obj_type == "datetime":
                        restored_data[key] = datetime.fromisoformat(value["data"])
                    elif obj_type == "pickle_obj":
                        try:
                            restored_data[key] = pickle.loads(base64.b64decode(value["data"].encode('utf-8')))
                        except Exception as e:
                            logger.error(f"反序列化对象出错: {key}, 错误: {str(e)}")
                            restored_data[key] = None
                    else:
                        restored_data[key] = None
                # Handling common data types
                else:
                    restored_data[key] = value

            return restored_data
        except Exception as e:
            logger.error(f"反序列化会话数据出错: {str(e)}")
            return {}