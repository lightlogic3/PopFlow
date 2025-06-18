"""Redis-based session management system
Used to store user session information, used with the slimmed-down version of JWT"""
from typing import Dict, Any, Optional, List
import json
import time
from datetime import datetime, timedelta

from knowledge_api.framework.redis.cache import RedisCache
from knowledge_api.framework.redis.connection import get_async_redis
from knowledge_api.utils.log_config import get_logger

logger = get_logger()

class UserSession:
    """user session data model"""
    
    def __init__(
        self,
        user_id: int,
        username: str,
        session_id: str,
        roles: List[str] = None,
        permissions: List[str] = None,
        user_info: Dict[str, Any] = None,
        created_at: float = None,
        last_active_at: float = None,
        expire_at: float = None,
        metadata: Dict[str, Any] = None
    ):
        """Initialize a user session

Args:
user_id: User ID
Username: username
session_id: Session ID
Roles: list of roles
Permissions: list of permissions
user_info: Additional User Information
created_at: Create timestamp
last_active_at: Last active timestamp
expire_at: Expiretimestamp
Metadata: metadata, which can store any session-related information"""
        self.user_id = user_id
        self.username = username
        self.session_id = session_id
        self.roles = roles or []
        self.permissions = permissions or []
        self.user_info = user_info or {}
        self.created_at = created_at or time.time()
        self.last_active_at = last_active_at or time.time()
        self.expire_at = expire_at
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary

Returns:
Dict: Conversational Dictionary"""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "session_id": self.session_id,
            "roles": self.roles,
            "permissions": self.permissions,
            "user_info": self.user_info,
            "created_at": self.created_at,
            "last_active_at": self.last_active_at,
            "expire_at": self.expire_at,
            "metadata": self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserSession':
        """Create a session object from a dictionary

Args:
Data: conversation dictionary

Returns:
UserSession: session object"""
        return cls(
            user_id=data.get("user_id"),
            username=data.get("username"),
            session_id=data.get("session_id"),
            roles=data.get("roles", []),
            permissions=data.get("permissions", []),
            user_info=data.get("user_info", {}),
            created_at=data.get("created_at"),
            last_active_at=data.get("last_active_at"),
            expire_at=data.get("expire_at"),
            metadata=data.get("metadata", {})
        )
        
    def update_activity(self):
        """Update last active time"""
        self.last_active_at = time.time()
        
    def is_expired(self) -> bool:
        """Check if the session has expired

Returns:
Bool: Has it expired?"""
        if not self.expire_at:
            return False
        return time.time() > self.expire_at


class SessionManager:
    """Session manager for managing user sessions"""
    
    def __init__(self, ttl: int = 14400):  # Default 4 hours
        """Initialize Session Manager

Args:
TTL: Session valid period (seconds)"""
        self.prefix = "session"
        self.ttl = ttl
        self.cache = RedisCache(prefix=self.prefix, default_ttl=ttl)
        
    def _get_session_key(self, session_id: str) -> str:
        """Get session cache key

Args:
session_id: Session ID

Returns:
Str: cache key"""
        return f"user:{session_id}"
        
    def _get_user_sessions_key(self, user_id: int) -> str:
        """Get the cache key for all user sessions

Args:
user_id: User ID

Returns:
Str: cache key"""
        return f"user_sessions:{user_id}"
    
    async def create_session(
        self, 
        user_id: int,
        username: str,
        session_id: str,
        roles: List[str] = None,
        permissions: List[str] = None,
        user_info: Dict[str, Any] = None,
        ttl: Optional[int] = None
    ) -> UserSession:
        """Create a user session

Args:
user_id: User ID
Username: username
session_id: Session ID
Roles: list of roles
Permissions: list of permissions
user_info: User Information
TTL: Session valid period (seconds)

Returns:
UserSession: session object"""
        expire_seconds = ttl or self.ttl
        expire_at = time.time() + expire_seconds
        
        # Create session object
        session = UserSession(
            user_id=user_id,
            username=username,
            session_id=session_id,
            roles=roles,
            permissions=permissions,
            user_info=user_info,
            expire_at=expire_at
        )
        
        # Save Session
        session_key = self._get_session_key(session_id)
        await self.cache.set(session_key, json.dumps(session.to_dict()), ttl=expire_seconds)
        
        # Add session ID to user session collection
        user_sessions_key = self._get_user_sessions_key(user_id)
        redis = await get_async_redis()
        await redis.sadd(user_sessions_key, session_id)
        # Make sure that the user session collection also has an expiration date
        await redis.expire(user_sessions_key, max(expire_seconds, 86400 * 7))  # Set to expire in at least 7 days
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[UserSession]:
        """Get session

Args:
session_id: Session ID

Returns:
Optional [UserSession]: Session object, returns None if it does not exist"""
        session_key = self._get_session_key(session_id)
        session_data = await self.cache.get(session_key)
        
        if not session_data:
            return None
            
        try:
            session_dict = json.loads(session_data)
            session = UserSession.from_dict(session_dict)
            
            # Check if it has expired.
            if session.is_expired():
                await self.delete_session(session_id)
                return None
                
            return session
        except Exception as e:
            logger.error(f"解析会话数据失败: {e}")
            return None
    
    async def update_session(self, session: UserSession, extend_ttl: bool = True) -> bool:
        """Update session

Args:
Session: session object
extend_ttl: Whether to extend the expiration time

Returns:
Bool: whether the operation was successful"""
        session.update_activity()
        
        # If you need to extend the expiration time
        if extend_ttl:
            session.expire_at = time.time() + self.ttl
            
        # Save Session
        session_key = self._get_session_key(session.session_id)
        ttl = int(session.expire_at - time.time()) if session.expire_at else self.ttl
        
        return await self.cache.set(
            session_key, 
            json.dumps(session.to_dict()), 
            ttl=max(ttl, 60)  # Make sure there is a valid period of at least 60 seconds
        )
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session

Args:
session_id: Session ID

Returns:
Bool: whether the operation was successful"""
        # Get the session first in order to remove it from the user session collection
        session = await self.get_session(session_id)
        if session:
            user_sessions_key = self._get_user_sessions_key(session.user_id)
            redis = await get_async_redis()
            await redis.srem(user_sessions_key, session_id)
        
        # Delete session
        session_key = self._get_session_key(session_id)
        return await self.cache.delete(session_key)
    
    async def get_user_sessions(self, user_id: int) -> List[UserSession]:
        """Get all user sessions

Args:
user_id: User ID

Returns:
List [UserSession]: Session list"""
        user_sessions_key = self._get_user_sessions_key(user_id)
        redis = await get_async_redis()
        session_ids = await redis.smembers(user_sessions_key)
        
        sessions = []
        for session_id in session_ids:
            session = await self.get_session(session_id.decode("utf-8"))
            if session:
                sessions.append(session)
        
        return sessions
    
    async def delete_user_sessions(self, user_id: int, exclude_session_id: Optional[str] = None) -> int:
        """Delete all user sessions

Args:
user_id: User ID
exclude_session_id: Excluded session IDs

Returns:
Int: number of sessions deleted"""
        user_sessions_key = self._get_user_sessions_key(user_id)
        redis = await get_async_redis()
        session_ids = await redis.smembers(user_sessions_key)
        
        delete_count = 0
        for session_id in session_ids:
            sid = session_id.decode("utf-8")
            if exclude_session_id and sid == exclude_session_id:
                continue
                
            success = await self.delete_session(sid)
            if success:
                delete_count += 1
        
        return delete_count
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions

Returns:
Int: number of sessions cleared"""
        # Attention: This method is not efficient and is only suitable for small-scale applications
        # For large-scale applications, Redis' expiration events or separate cleanup tasks should be used
        redis = await get_async_redis()
        
        # Scan all sessions
        cleanup_count = 0
        cursor = 0
        pattern = f"{self.prefix}:user:*"
        
        while True:
            cursor, keys = await redis.scan(cursor, match=pattern, count=100)
            
            for key in keys:
                try:
                    key_str = key.decode("utf-8")
                    session_id = key_str.split(":")[-1]
                    
                    # Check if the session has expired
                    session = await self.get_session(session_id)
                    if not session or session.is_expired():
                        await self.delete_session(session_id)
                        cleanup_count += 1
                except Exception as e:
                    logger.error(f"清理会话时出错: {e}")
            
            # If the scan is complete, exit the loop
            if cursor == 0:
                break
        
        return cleanup_count


# Session Manager Singleton
_session_manager = None

def get_session_manager() -> SessionManager:
    """Get Session Manager

Returns:
SessionManager: Session Manager"""
    global _session_manager
    
    if _session_manager is None:
        _session_manager = SessionManager()
        
    return _session_manager 