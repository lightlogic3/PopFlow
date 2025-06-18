from typing import Dict, Any, Optional, List
import time
import asyncio
from datetime import datetime

from knowledge_api.framework.redis.cache_system.session_cache import SessionCacheManager
from knowledge_api.framework.memory.enhanced_chat_memory_manager import EnhancedChatMemoryManager
from knowledge_api.utils import generate_id
from knowledge_api.utils.log_config import get_logger

logger = get_logger()

class ChatSessionManager:
    """chat session manager

Handles the storage, loading, and management of sessions, using Redis as backend storage"""
    
    # default session prefix
    DEFAULT_SESSION_PREFIX = "chat:session:"
    
    # Session prefixes for different scenarios
    CHAT_PREFIXES = {
        "default": "chat:session:",
        "task": "chat:task_session:",
        "subtask": "chat:subtask_session:",
        "stream": "chat:stream_session:",
        "backend": "chat:backend_session:"
    }
    
    # session cleanup configuration
    SESSION_MAX_IDLE_TIME = 60 * 60  # 1 hour inactive automatic cleaning
    SESSION_MAX_COUNT = 1000  # Maximum number of sessions
    
    def __init__(self, chat_type: str = "default"):
        """Initialize Session Manager

Args:
chat_type: chat type to determine Redis key prefix"""
        self.chat_type = chat_type
        self.session_prefix = self.CHAT_PREFIXES.get(chat_type, self.DEFAULT_SESSION_PREFIX)
        
        # Set the prefix of the SessionCacheManager
        SessionCacheManager.KEY_PREFIX = self.session_prefix
        
        # Last cleaning time
        self.last_cleanup_time = time.time()
        
        # Set Session Cleanup Timed Tasks
        self._setup_session_cleanup()
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data

Args:
session_id: Session ID

Returns:
Session data dictionary, None if it doesn't exist"""
        if not session_id:
            return None
            
        # Loading a session from Redis
        session_data = await SessionCacheManager.load_session(session_id)
        
        # Update last active time
        if session_data:
            session_data["last_activity"] = datetime.now().isoformat()
            await self.save_session(session_id, session_data)
            
        return session_data
    
    async def create_session(self, session_id: Optional[str] = None, 
                           memory_manager: Optional[EnhancedChatMemoryManager] = None,
                           user_info: Optional[Dict[str, Any]] = None,
                           additional_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new session

Args:
session_id: Session ID, if empty, automatically generated
memory_manager: Memory Manager
user_info: User Information
additional_data: Additional data

Returns:
Newly created session data"""
        # Generate session ID
        new_session_id = session_id or str(generate_id())
        
        # If no memory manager is provided, create one
        if memory_manager is None:
            memory_manager = EnhancedChatMemoryManager(
                k=20,
                system_message="",
                memory_type='buffer_window',
            )
        
        # Create session data
        session_data = {
            "id": new_session_id,
            "memory_manager": memory_manager,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "message_count": 0,
        }
        
        # Add user information
        if user_info:
            session_data["user_info"] = user_info
            
        # Add additional data
        if additional_data:
            session_data.update(additional_data)
        
        # Save to Redis
        await self.save_session(new_session_id, session_data)
        
        logger.info(f"已创建新会话: {new_session_id}, 类型: {self.chat_type}")
        
        return session_data
    
    async def save_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """Save session data

Args:
session_id: Session ID
session_data: Session Data

Returns:
Did you save successfully?"""
        if not session_id:
            logger.warning("Save session failed: Session ID is empty")
            return False
        
        # Make sure the last activity time is updated
        if "last_activity" not in session_data:
            session_data["last_activity"] = datetime.now().isoformat()
        
        # Save to Redis
        return await SessionCacheManager.save_session(session_id, session_data)
    
    async def update_session(self, session_id: str, 
                           updates: Dict[str, Any], 
                           create_if_not_exists: bool = False) -> Optional[Dict[str, Any]]:
        """Update session data

Args:
session_id: Session ID
Updates: Fields to be updated
create_if_not_exists: whether to create if the session does not exist

Returns:
Updated session data, None on failure"""
        if not session_id:
            logger.warning("Update session failed: Session ID is empty")
            return None
        
        # Get an existing session
        session_data = await self.get_session(session_id)
        
        # If the conversation does not exist
        if not session_data:
            if create_if_not_exists:
                # Create a new session
                session_data = await self.create_session(session_id, additional_data=updates)
                return session_data
            else:
                logger.warning(f"更新会话失败: 会话不存在 {session_id}")
                return None
        
        # update field
        session_data.update(updates)
        
        # Update last active time
        session_data["last_activity"] = datetime.now().isoformat()
        
        # Save the updated session
        success = await self.save_session(session_id, session_data)
        
        if success:
            return session_data
        else:
            logger.error(f"更新会话失败: 无法保存 {session_id}")
            return None
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session

Args:
session_id: Session ID

Returns:
Whether the deletion was successful"""
        if not session_id:
            return False
            
        return await SessionCacheManager.delete_session(session_id)
    
    async def clear_session_data(self, session_id: str) -> bool:
        """Clear the session history, but keep the session itself

Args:
session_id: Session ID

Returns:
Is the clearance successful?"""
        session_data = await self.get_session(session_id)
        
        if not session_data:
            logger.warning(f"清除会话历史失败: 会话不存在 {session_id}")
            return False
        
        # Get Memory Manager
        memory_manager = session_data.get("memory_manager")
        
        if memory_manager:
            # Clear history
            memory_manager.clear()
            
            # Save Session
            session_data["message_count"] = 0
            session_data["last_activity"] = datetime.now().isoformat()
            
            await self.save_session(session_id, session_data)
            
            return True
        else:
            logger.warning(f"清除会话历史失败: 会话{session_id}没有内存管理器")
            return False
    
    async def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Get all sessions

Returns:
Session ID to Session Data Mapping"""
        pattern = f"{self.session_prefix}*"
        return await SessionCacheManager.get_all_sessions(pattern)
    
    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all sessions of the user

Args:
user_id: User ID

Returns:
user's session list"""
        all_sessions = await self.get_all_sessions()
        
        user_sessions = []
        for session_id, session_data in all_sessions.items():
            if session_data and session_data.get("user_info", {}).get("user_id") == user_id:
                user_sessions.append(session_data)
        
        return user_sessions
    
    async def clean_expired_sessions(self) -> int:
        """Clean up expired sessions

Returns:
Number of sessions cleaned up"""
        pattern = f"{self.session_prefix}*"
        
        # Get all sessions
        all_sessions = await SessionCacheManager.get_all_sessions(pattern)
        
        # Current time
        now = datetime.now()
        
        # expired session count
        expired_count = 0
        
        # Check each session
        for session_id, session_data in all_sessions.items():
            if not session_data:
                continue
                
            # Get last active time
            last_activity_str = session_data.get("last_activity")
            
            if last_activity_str:
                try:
                    last_activity = datetime.fromisoformat(last_activity_str)
                    
                    # Calculate idle time (seconds)
                    idle_time = (now - last_activity).total_seconds()
                    
                    # If the maximum idle time is exceeded, delete it
                    if idle_time > self.SESSION_MAX_IDLE_TIME:
                        await self.delete_session(session_id)
                        expired_count += 1
                except Exception as e:
                    logger.error(f"解析会话最后活动时间出错: {e}")
        
        logger.info(f"已清理过期会话: {expired_count}个")
        
        return expired_count
    
    def _setup_session_cleanup(self):
        """Set Session Cleanup Timed Tasks"""
        async def cleanup_task():
            while True:
                try:
                    # Check every 10 minutes
                    await asyncio.sleep(600)
                    
                    # Clean up expired sessions
                    await self.clean_expired_sessions()
                except Exception as e:
                    logger.error(f"会话清理任务出错: {e}")
                    # After the error, wait a moment and try again.
                    await asyncio.sleep(60)
        
        # Create a cleanup task
        # asyncio.create_task(cleanup_task())
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics

Returns:
session statistics"""
        # Get all sessions
        all_sessions = await self.get_all_sessions()
        
        # number of sessions
        session_count = len(all_sessions)
        
        # Number of active sessions (active within 24 hours)
        active_sessions = 0
        
        # total messages
        total_messages = 0
        
        # Current time
        now = datetime.now()
        
        for session_data in all_sessions.values():
            if not session_data:
                continue
                
            # number of messages
            total_messages += session_data.get("message_count", 0)
            
            # Check active status
            last_activity_str = session_data.get("last_activity")
            
            if last_activity_str:
                try:
                    last_activity = datetime.fromisoformat(last_activity_str)
                    
                    # If there is activity within 24 hours, it is considered active
                    if (now - last_activity).total_seconds() < 86400:
                        active_sessions += 1
                except:
                    pass
        
        return {
            "total_sessions": session_count,
            "active_sessions": active_sessions,
            "total_messages": total_messages
        } 