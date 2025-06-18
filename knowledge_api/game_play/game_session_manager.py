"""Game session management system

Redis-based distributed game session management, supporting multiple game types and cross-instance session sharing"""
from typing import Dict, Any, Optional, List, Type, Union
import json
import time
import asyncio
from datetime import datetime
import base64
import pickle
import traceback

from knowledge_api.framework.redis.cache_system.session_cache import SessionCacheManager
from knowledge_api.framework.redis.connection import get_async_redis
from knowledge_api.utils.log_config import get_logger

logger = get_logger()

class GameSessionManager:
    """Game session manager for distributed session storage based on Redis"""
    
    # basic session prefix
    BASE_PREFIX = "game"
    
    # WebSocket Connection Mapping Prefix
    WS_PREFIX = "websockets"
    
    # Local cache - session data
    _local_session_cache: Dict[str, Dict[str, Any]] = {}
    
    # Local cache - Agent object
    _local_agent_cache: Dict[str, Any] = {}
    
    # Last cache cleaning time
    _last_cleanup_time = time.time()
    
    # session cleanup configuration
    SESSION_MAX_IDLE_TIME = 60 * 60 * 24  # 24 hours inactive automatic cleaning
    
    @classmethod
    def get_session_key_prefix(cls, game_type: Optional[str] = None) -> str:
        """Get session key prefix

Args:
game_type: Optional game type to distinguish between sessions of different games

Returns:
STR: session key prefix"""
        if game_type:
            return f"{cls.BASE_PREFIX}:{game_type}:session"
        return f"{cls.BASE_PREFIX}:session"
    
    @classmethod
    def get_websocket_key_prefix(cls, game_type: Optional[str] = None) -> str:
        """Get WebSocket Key Prefix

Args:
game_type: Optional game type for distinguishing WebSocket maps for different games

Returns:
STR: WebSocket key prefix"""
        if game_type:
            return f"{cls.BASE_PREFIX}:{game_type}:{cls.WS_PREFIX}"
        return f"{cls.BASE_PREFIX}:{cls.WS_PREFIX}"
    
    @classmethod
    async def save_game_session(cls, session_id: str, session_data: Dict[str, Any], 
                              game_type: Optional[str] = None) -> bool:
        """Save game session data to Redis

Args:
session_id: Session ID
session_data: Session Data
game_type: Optional game type to distinguish between sessions of different games

Returns:
Bool: successfully saved"""
        if not session_id:
            logger.warning("Save session failed: Session ID is empty")
            return False
            
        # If session_data contains game_type, use it first
        _game_type = session_data.get("game_type", game_type)
        
        # Set Session Prefix
        original_prefix = SessionCacheManager.KEY_PREFIX
        SessionCacheManager.KEY_PREFIX = cls.get_session_key_prefix(_game_type)
        
        try:
            # Make sure the creation/update time field exists
            if "created_at" not in session_data:
                session_data["created_at"] = datetime.now().isoformat()
            session_data["last_activity"] = datetime.now().isoformat()
            
            # Update local cache
            cache_key = f"{session_id}:{_game_type}" if _game_type else session_id
            cls._local_session_cache[cache_key] = session_data.copy()
            
            # Save session data
            result = await SessionCacheManager.save_session(session_id, session_data)
            
            # Check if regular cleaning is required
            current_time = time.time()
            if current_time - cls._last_cleanup_time > 3600:  # Check every hour
                cls._last_cleanup_time = current_time
                asyncio.create_task(cls.cleanup_expired_sessions())
                
            return result
        except Exception as e:
            logger.error(f"保存会话失败: {e}")
            return False
        finally:
            # Restore original prefix
            SessionCacheManager.KEY_PREFIX = original_prefix
    
    @classmethod
    async def load_game_session(cls, session_id: str, game_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Loading game session data from Redis using a secondary caching system

Args:
session_id: Session ID
game_type: Optional game type to distinguish between sessions of different games

Returns:
Optional [Dict [str, Any]]: Session data, return None if it doesn't exist"""
        if not session_id:
            return None
            
        # Check the local cache first
        cache_key = f"{session_id}:{game_type}" if game_type else session_id
        if cache_key in cls._local_session_cache:
            logger.debug(f"从本地缓存加载会话: {cache_key}")
            return cls._local_session_cache[cache_key]
        
        # If no game_type is specified, try loading from all possible game types
        if not game_type:
            # First try loading from the generic prefix
            session_data = await cls._load_from_prefix(session_id, None)
            if session_data:
                # Update local cache
                cls._local_session_cache[cache_key] = session_data
                return session_data
                
            # If the generic prefix is not found, try loading from a specific game type
            # This requires a list of all active game types
            game_types = await cls.get_active_game_types()
            for gt in game_types:
                session_data = await cls._load_from_prefix(session_id, gt)
                if session_data:
                    # Update local cache
                    cls._local_session_cache[f"{session_id}:{gt}"] = session_data
                    return session_data
            return None
        else:
            # Load directly from the specified game type
            session_data = await cls._load_from_prefix(session_id, game_type)
            if session_data:
                # Update local cache
                cls._local_session_cache[cache_key] = session_data
            return session_data
    
    @classmethod
    async def get_session(cls, session_id: str, game_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get session data and update the last active time (compatible with ChatSessionManager)

Args:
session_id: Session ID
game_type: Optional game types

Returns:
Session data dictionary, None if it doesn't exist"""
        if not session_id:
            return None
            
        # Loading a session from Redis
        session_data = await cls.load_game_session(session_id, game_type)
        
        # Update last active time
        if session_data:
            session_data["last_activity"] = datetime.now().isoformat()
            await cls.save_game_session(session_id, session_data, game_type)
            
        return session_data
    
    @classmethod
    async def create_session(cls, session_id: str, game_type: Optional[str] = None, 
                          additional_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new session (compatible with ChatSessionManager)

Args:
session_id: Session ID
game_type: Game Type
additional_data: Additional data

Returns:
Newly created session data"""
        # Create session data
        session_data = {
            "id": session_id,
            "game_type": game_type,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
        }
        
        # Add additional data
        if additional_data:
            session_data.update(additional_data)
        
        # Save to Redis
        await cls.save_game_session(session_id, session_data, game_type)
        
        logger.info(f"已创建新会话: {session_id}, 类型: {game_type}")
        
        return session_data
    
    @classmethod
    async def update_session(cls, session_id: str, updates: Dict[str, Any], 
                          game_type: Optional[str] = None, 
                          create_if_not_exists: bool = False) -> Optional[Dict[str, Any]]:
        """Update session data (compatible with ChatSessionManager)

Args:
session_id: Session ID
Updates: Fields to be updated
game_type: Game Type
create_if_not_exists: whether to create if the session does not exist

Returns:
Updated session data, None on failure"""
        if not session_id:
            logger.warning("Update session failed: Session ID is empty")
            return None
        
        # Get an existing session
        session_data = await cls.get_session(session_id, game_type)
        
        # If the conversation does not exist
        if not session_data:
            if create_if_not_exists:
                # Create a new session
                session_data = await cls.create_session(session_id, game_type, updates)
                return session_data
            else:
                logger.warning(f"更新会话失败: 会话不存在 {session_id}")
                return None
        
        # update field
        session_data.update(updates)
        
        # Update last active time
        session_data["last_activity"] = datetime.now().isoformat()
        
        # Save the updated session
        success = await cls.save_game_session(session_id, session_data, game_type)
        
        if success:
            return session_data
        else:
            logger.error(f"更新会话失败: 无法保存 {session_id}")
            return None
    
    @classmethod
    async def _load_from_prefix(cls, session_id: str, game_type: Optional[str]) -> Optional[Dict[str, Any]]:
        """Load session data from the specified prefix

Args:
session_id: Session ID
game_type: Game Type or None

Returns:
Optional [Dict [str, Any]]: Session Data or None"""
        # Set Session Prefix
        original_prefix = SessionCacheManager.KEY_PREFIX
        SessionCacheManager.KEY_PREFIX = cls.get_session_key_prefix(game_type)
        
        try:
            # Load session data
            return await SessionCacheManager.load_session(session_id)
        finally:
            # Restore original prefix
            SessionCacheManager.KEY_PREFIX = original_prefix
    
    @classmethod
    async def delete_session(cls, session_id: str, game_type: Optional[str] = None) -> bool:
        """Delete game session data

Args:
session_id: Session ID
game_type: Optional game type to distinguish between sessions of different games

Returns:
Bool: successfully deleted"""
        if not session_id:
            return False
            
        if not game_type:
            # If no game type is specified, try loading the session first to get the game type
            session_data = await cls.load_game_session(session_id)
            if session_data:
                game_type = session_data.get("game_type")
                
        # Set Session Prefix
        original_prefix = SessionCacheManager.KEY_PREFIX
        SessionCacheManager.KEY_PREFIX = cls.get_session_key_prefix(game_type)
        
        try:
            # Delete session data
            success = await SessionCacheManager.delete_session(session_id)
            # Simultaneous cleaning of WebSocket records
            await cls.clear_websocket_info(session_id, game_type)
            
            # Clear local cache
            cache_key = f"{session_id}:{game_type}" if game_type else session_id
            if cache_key in cls._local_session_cache:
                del cls._local_session_cache[cache_key]
                
            # Clean proxy cache
            agent_key = f"{session_id}:{game_type}" if game_type else session_id
            if agent_key in cls._local_agent_cache:
                del cls._local_agent_cache[agent_key]
                
            return success
        finally:
            # Restore original prefix
            SessionCacheManager.KEY_PREFIX = original_prefix
    
    @classmethod
    async def get_all_sessions(cls, game_type: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """Get all game sessions

Args:
game_type: Optional game type to filter sessions for specific games

Returns:
Dict [str, Dict [str, Any]]: Mapping session ID to session data"""
        # Set Session Prefix
        original_prefix = SessionCacheManager.KEY_PREFIX
        SessionCacheManager.KEY_PREFIX = cls.get_session_key_prefix(game_type)
        
        try:
            # Get all sessions
            pattern = f"{SessionCacheManager.KEY_PREFIX}*"
            sessions = await SessionCacheManager.get_all_sessions(pattern)
            
            # Update local cache
            for session_id, session_data in sessions.items():
                cache_key = f"{session_id}:{game_type}" if game_type else session_id
                cls._local_session_cache[cache_key] = session_data
                
            return sessions
        finally:
            # Restore original prefix
            SessionCacheManager.KEY_PREFIX = original_prefix
    
    @classmethod
    async def get_active_game_types(cls) -> List[str]:
        """Get all active game types

Returns:
List [str]: List of active game types"""
        redis = await get_async_redis()
        pattern = f"{cls.BASE_PREFIX}:*:session:*"
        keys = []
        
        cursor = 0
        while True:
            cursor, batch = await redis.scan(cursor, match=pattern, count=100)
            keys.extend(batch)
            if cursor == 0:
                break
                
        # Extract the game type from the key
        game_types = set()
        for key in keys:
            parts = key.decode('utf-8').split(':')
            if len(parts) >= 3:
                game_types.add(parts[1])
                
        return list(game_types)
    
    @classmethod
    async def save_agent_objects(cls, session_id: str, agents: Any, game_type: Optional[str] = None) -> bool:
        """Save Agent object to Redis

Args:
session_id: Session ID
Agents: List of Agent objects or a single Agent object
game_type: Optional game types

Returns:
Bool: successfully saved"""
        if not session_id:
            logger.warning("Failed to save Agent object: Session ID is empty")
            return False
            
        try:
            # Update local cache
            cache_key = f"{session_id}:{game_type}" if game_type else session_id
            cls._local_agent_cache[cache_key] = agents
            
            # Extracting key data rather than attempting to serialize the entire object
            agents_data = []
            if isinstance(agents, list):
                for agent in agents:
                    # Extract the basic properties of each agent
                    agent_data = {
                        "agent_id": getattr(agent, "agent_id", None),
                        "identity": getattr(agent, "identity", None),
                        "agent_type": agent.__class__.__name__,
                    }
                    
                    # Attempt to save character information
                    if hasattr(agent, "role") and agent.role:
                        role = agent.role
                        agent_data["role"] = {
                            "role_id": getattr(role, "role_id", None),
                            "model_id": getattr(role, "model_id", None),
                            "setting": getattr(role, "setting", None),
                            "voice": getattr(role, "voice", None),
                            "role_info": getattr(role, "role_info", {})
                        }
                    
                    # Preserve memory information
                    if hasattr(agent, "memory") and agent.memory:
                        try:
                            messages = agent.memory.get_formatted_history()
                            agent_data["memory_messages"] = messages
                        except:
                            agent_data["memory_messages"] = []
                            
                    agents_data.append(agent_data)
            
            # Serialize simplified data
            wrapper_dict = {
                "agents_data": json.dumps(agents_data),
                "agent_type": "json_safe",
                "timestamp": datetime.now().isoformat()
            }
            
            # Serialized Packaging Dictionary
            serialized_agents = SessionCacheManager.serialize_session(wrapper_dict)
            
            # Get session data
            session_data = await cls.load_game_session(session_id, game_type)
            if not session_data:
                logger.error(f"保存Agent对象失败: 找不到会话 {session_id}")
                return False
                
            # Update session data
            session_data["serialized_agents"] = serialized_agents
            session_data["last_activity"] = datetime.now().isoformat()
            
            # Save to Redis
            return await cls.save_game_session(session_id, session_data, game_type)
        except Exception as e:
            traceback.print_exc()
            logger.error(f"保存Agent对象失败: {str(e)}")
            return False
    
    @classmethod
    async def load_agent_objects(cls, session_id: str, game_type: Optional[str] = None) -> Optional[Any]:
        """Loading Agent objects from Redis, using a secondary caching system

Args:
session_id: Session ID
game_type: Optional game types

Returns:
Optional [Any]: Agent object or None"""
        if not session_id:
            return None
            
        # Check the local cache first
        cache_key = f"{session_id}:{game_type}" if game_type else session_id
        if cache_key in cls._local_agent_cache:
            logger.debug(f"从本地缓存加载Agent对象: {cache_key}")
            return cls._local_agent_cache[cache_key]
            
        # Load session data
        session_data = await cls.load_game_session(session_id, game_type)
        if not session_data or "serialized_agents" not in session_data:
            logger.debug(f"未找到Agent对象: {session_id}")
            return None
            
        try:
            # Deserialize Agent Objects
            serialized_agents = session_data["serialized_agents"]
            
            # Deserialization using SessionCacheManager
            deserialized_data = SessionCacheManager.deserialize_session(serialized_agents)
            
            # check format
            if not isinstance(deserialized_data, dict) or "agents_data" not in deserialized_data:
                logger.error("Deserialization failed: Invalid data format")
                return None
                
            # Handling different formats
            agents = []
            agent_type = deserialized_data.get("agent_type", "unknown")
                
            if agent_type == "json_safe":
                # Processing a new format: JSON Secure Format
                try:
                    from knowledge_api.model.agent.game_agent import TurtleSoupGameAgent, GameRole
                    
                    agents_data = json.loads(deserialized_data["agents_data"])
                    
                    for agent_data in agents_data:
                        # Rebuild character
                        role_data = agent_data.get("role", {})
                        role = GameRole(
                            role_id=role_data.get("role_id"),
                            model_id=role_data.get("model_id"),
                            setting=role_data.get("setting", ""),
                            voice=role_data.get("voice", ""),
                            role_info=role_data.get("role_info", {})
                        )
                        
                        # Create proxy
                        identity = agent_data.get("identity", "player")
                        # To simplify, we always create TurtleSoupGameAgent.
                        agent = TurtleSoupGameAgent(role, "", identity)
                        
                        # Restore memory
                        memory_messages = agent_data.get("memory_messages", [])
                        if memory_messages:
                            for msg in memory_messages:
                                if msg["role"] == "system":
                                    # Update system message
                                    agent.memory.update_system_message(msg["content"])
                                elif msg["role"] == "user":
                                    agent.memory.add_user_message(msg["content"])
                                elif msg["role"] == "assistant":
                                    agent.memory.add_ai_message(msg["content"])
                        
                        # Initialize client side
                        await agent.init_client()
                        
                        agents.append(agent)
                except Exception as e:
                    logger.error(f"重建Agent对象失败: {str(e)}")
                    traceback.print_exc()
                    return None
            else:
                # Unable to handle format
                logger.error(f"不支持的Agent序列化格式: {agent_type}")
                return None
            
            # Update local cache
            cls._local_agent_cache[cache_key] = agents
            
            return agents
        except Exception as e:
            logger.error(f"加载Agent对象失败: {str(e)}")
            traceback.print_exc()
            return None
    
    @classmethod
    async def save_websocket_info(cls, session_id: str, websocket_id: str, 
                                game_type: Optional[str] = None) -> bool:
        """Save WebSocket information to Redis Set

Args:
session_id: Session ID
websocket_id: WebSocket Connection ID
game_type: Optional game types

Returns:
Bool: successfully saved"""
        redis = await get_async_redis()
        key = f"{cls.get_websocket_key_prefix(game_type)}:{session_id}"
        
        try:
            await redis.sadd(key, websocket_id)
            # Set a reasonable expiration date, such as 24 hours
            await redis.expire(key, 86400)
            return True
        except Exception as e:
            logger.error(f"保存WebSocket信息出错: {e}")
            return False
    
    @classmethod
    async def remove_websocket_info(cls, session_id: str, websocket_id: str, 
                                  game_type: Optional[str] = None) -> bool:
        """Remove WebSocket Information from Redis Set

Args:
session_id: Session ID
websocket_id: WebSocket Connection ID
game_type: Optional game types

Returns:
Bool: successfully deleted"""
        redis = await get_async_redis()
        key = f"{cls.get_websocket_key_prefix(game_type)}:{session_id}"
        
        try:
            await redis.srem(key, websocket_id)
            return True
        except Exception as e:
            logger.error(f"删除WebSocket信息出错: {e}")
            return False
    
    @classmethod
    async def clear_websocket_info(cls, session_id: str, game_type: Optional[str] = None) -> bool:
        """Clear all WebSocket information related to the session

Args:
session_id: Session ID
game_type: Optional game types

Returns:
Bool: successfully cleared"""
        redis = await get_async_redis()
        key = f"{cls.get_websocket_key_prefix(game_type)}:{session_id}"
        
        try:
            await redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"清空WebSocket信息出错: {e}")
            return False
    
    @classmethod
    async def get_websocket_ids(cls, session_id: str, game_type: Optional[str] = None) -> List[str]:
        """Get all WebSocket IDs associated with the session

Args:
session_id: Session ID
game_type: Optional game types

Returns:
List [str]: WebSocket ID list"""
        redis = await get_async_redis()
        key = f"{cls.get_websocket_key_prefix(game_type)}:{session_id}"
        
        try:
            ws_ids = await redis.smembers(key)
            return [ws_id.decode("utf-8") for ws_id in ws_ids]
        except Exception as e:
            logger.error(f"获取WebSocket信息出错: {e}")
            return []
    
    @classmethod
    async def cleanup_expired_sessions(cls, max_inactive_time: int = None, 
                                     game_type: Optional[str] = None,
                                     pattern: Optional[str] = None) -> int:
        """Clean up expired game sessions

Args:
max_inactive_time: Maximum inactivity time (seconds), None is the default value
game_type: Optional game type to clear only sessions for specific games
Pattern: Optional session key pattern for more precise session filtering

Returns:
Int: Number of sessions cleared"""
        if max_inactive_time is None:
            max_inactive_time = cls.SESSION_MAX_IDLE_TIME
            
        # Get all sessions
        sessions = await cls.get_all_sessions(game_type)
        count = 0
        
        # Current time
        now = datetime.now()
        
        for session_id, session_data in sessions.items():
            # Check the last active time
            last_activity_str = session_data.get("last_activity")
            if last_activity_str:
                try:
                    last_activity = datetime.fromisoformat(last_activity_str)
                    # Calculate inactivity time (seconds)
                    inactive_seconds = (now - last_activity).total_seconds()
                    
                    # If the threshold is exceeded, delete the session
                    if inactive_seconds > max_inactive_time:
                        await cls.delete_session(
                            session_id, 
                            session_data.get("game_type", game_type)
                        )
                        count += 1
                except (ValueError, TypeError) as e:
                    logger.error(f"解析会话{session_id}的最后活动时间出错: {e}")
        
        # Only log when cleaning up a large number of sessions
        if count > 0:
            logger.info(f"已清理{count}个过期游戏会话")
                    
        return count
    
    @classmethod
    def clear_local_cache(cls, session_id: Optional[str] = None, game_type: Optional[str] = None):
        """Clear local cache

Args:
session_id: Optional session ID, if provided only clears the cache for that session
game_type: Optional game types"""
        if session_id:
            # Only clear the cache for a specific session
            cache_key = f"{session_id}:{game_type}" if game_type else session_id
            if cache_key in cls._local_session_cache:
                del cls._local_session_cache[cache_key]
            if cache_key in cls._local_agent_cache:
                del cls._local_agent_cache[cache_key]
                logger.debug(f"已清理会话缓存: {cache_key}")
        else:
            # Clear all caches
            session_count = len(cls._local_session_cache)
            agent_count = len(cls._local_agent_cache)
            cls._local_session_cache.clear()
            cls._local_agent_cache.clear()
            logger.debug(f"已清理所有本地缓存: {session_count}个会话, {agent_count}个Agent对象")
    
    @classmethod
    async def clear_session_data(cls, session_id: str, game_type: Optional[str] = None) -> bool:
        """Clear session data, but keep the session itself (compatible with ChatSessionManager)

Args:
session_id: Session ID
game_type: Game Type

Returns:
Is the clearance successful?"""
        session_data = await cls.get_session(session_id, game_type)
        
        if not session_data:
            logger.warning(f"清除会话数据失败: 会话不存在 {session_id}")
            return False
            
        # Retain basic information and clear other data
        new_session = {
            "id": session_id,
            "game_type": session_data.get("game_type", game_type),
            "created_at": session_data.get("created_at"),
            "last_activity": datetime.now().isoformat(),
        }
        
        # Clear local cache
        cls.clear_local_cache(session_id, game_type)
        
        # Save Session
        return await cls.save_game_session(session_id, new_session, game_type) 