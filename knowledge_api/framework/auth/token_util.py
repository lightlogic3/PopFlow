from typing import Dict, Any, Optional, List
import asyncio
from contextlib import asynccontextmanager
import time
import uuid

from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.system.crud import (
    SystemUserCRUD, SystemRoleCRUD
)
from knowledge_api.framework.auth.jwt_utils import JWTUtils
from knowledge_api.framework.auth.session_manager import get_session_manager, UserSession
from knowledge_api.utils.log_config import get_logger

logger = get_logger()

class TokenUtil:
    """Token tool class, used to parse and verify tokens and obtain user information"""
    
    @staticmethod
    def parse_token(token: str) -> Dict[str, Any]:
        """Parse the token and obtain basic information (excluding complete session data).

Args:
Token: JWT token

Returns:
Dict [str, Any]: basic user information"""
        if not token or token == "":
            return {}
            
        # If the token contains the Bearer prefix, remove it
        if token.startswith("Bearer "):
            token = token.replace("Bearer ", "")
            
        # parse token
        try:
            return JWTUtils.decode_token(token)
        except Exception as e:
            logger.error(f"解析Token失败: {str(e)}")
            return {}
    
    @staticmethod
    def get_user_id(token: str) -> Optional[int]:
        """Get user ID from token

Args:
Token: JWT token

Returns:
Optional [int]: User ID"""
        token_data = TokenUtil.parse_token(token)
        return token_data.get("user_id")
    
    @staticmethod
    def get_username(token: str) -> Optional[str]:
        """Get username from token

Args:
Token: JWT token

Returns:
Optional [str]: username"""
        token_data = TokenUtil.parse_token(token)
        return token_data.get("username")
    
    @staticmethod
    def get_session_id(token: str) -> Optional[str]:
        """Get Session ID from Token

Args:
Token: JWT token

Returns:
Optional [str]: Session ID"""
        token_data = TokenUtil.parse_token(token)
        return token_data.get("session_id")
    
    @staticmethod
    async def get_session(token: str) -> Optional[UserSession]:
        """Get session data from Token

Args:
Token: JWT token

Returns:
Optional [UserSession]: Session data"""
        session_id = TokenUtil.get_session_id(token)
        if not session_id:
            return None
            
        session_manager = get_session_manager()
        return await session_manager.get_session(session_id)
    
    @staticmethod
    async def get_permissions(token: str) -> List[str]:
        """Get a list of user permissions from a session

Args:
Token: JWT token

Returns:
List [str]: permissions list"""
        session = await TokenUtil.get_session(token)
        if not session:
            return []
            
        return session.permissions
    
    @staticmethod
    async def get_roles(token: str) -> List[str]:
        """Get a list of user roles from a session

Args:
Token: JWT token

Returns:
List [str]: list of roles"""
        session = await TokenUtil.get_session(token)
        if not session:
            return []
            
        return session.roles
    
    @staticmethod
    async def has_permission(token: str, permission: str) -> bool:
        """Check whether the token contains the specified permission

Args:
Token: JWT token
Permissions: permission identifier

Returns:
Bool: Is there permission?"""
        # Super admin has all permissions
        if await TokenUtil.is_admin(token):
            return True
            
        permissions = await TokenUtil.get_permissions(token)
        return permission in permissions
    
    @staticmethod
    async def has_role(token: str, role: str) -> bool:
        """Check whether the token contains the specified role

Args:
Token: JWT token
Role: Role Identity

Returns:
Bool: Is there a role"""
        roles = await TokenUtil.get_roles(token)
        return role in roles
    
    @staticmethod
    async def is_admin(token: str) -> bool:
        """Check if the Token is an administrator

Args:
Token: JWT token

Returns:
Bool: Is it an administrator?"""
        return await TokenUtil.has_role(token, "admin")
    
    @staticmethod
    async def get_user_info(token: str) -> Dict[str, Any]:
        """Get full user information (priority from session cache, failure from database)

Args:
Token: JWT token

Returns:
Dict [str, Any]: user information"""
        # First try to get from the conversation
        session = await TokenUtil.get_session(token)
        if session and session.user_info:
            # Returns user information in the session, including roles and permissions
            return {
                "user": session.user_info,
                "roles": session.roles,
                "permissions": session.permissions
            }
            
        # If there is no complete user information in the session, obtain it from the database
        token_data = TokenUtil.parse_token(token)
        user_id = token_data.get("user_id")
        
        if not user_id:
            return {}
            
        db = next(get_session())
        try:
            # Acquire user information
            user_crud = SystemUserCRUD(db)
            user = user_crud.get_by_id(user_id=user_id)
            if not user:
                return {}
                
            # Get user role
            role_crud = SystemRoleCRUD(db)
            roles = role_crud.get_roles_by_user_id(user_id=user_id)
            role_info = [{"id": role.id, "name": role.name, "code": role.code} for role in roles]
            role_codes = [role.code for role in roles]
            
            # get permission
            permissions = []
            # There should be code for obtaining permissions here, which is implemented according to the actual situation.
            
            # Build user information
            user_info = {
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname,
                "email": user.email,
                "mobile": user.mobile,
                "sex": user.sex,
                "avatar": user.avatar,
                "status": user.status,
                "remark": user.remark,
                "login_date": user.login_date
            }
            
            # If there is a session, update the session information
            if session:
                session.user_info = user_info
                session.roles = role_codes
                session.permissions = permissions
                
                # asynchronous update session
                asyncio.create_task(
                    get_session_manager().update_session(session)
                )
            
            return {
                "user": user_info,
                "roles": role_info,
                "permissions": permissions
            }
        finally:
            db.close()
            
    @staticmethod
    async def create_user_session(
        user_id: int,
        username: str,
        roles: List[str],
        permissions: List[str],
        user_info: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> UserSession:
        """Create a user session and return the session object

Args:
user_id: User ID
Username: username
Roles: list of roles
Permissions: list of permissions
user_info: User Information
session_id: Session ID, automatically generated when None

Returns:
UserSession: session object"""
        # If no session ID is provided, a new UUID is generated.
        if not session_id:
            session_id = str(uuid.uuid4())
            
        session_manager = get_session_manager()
        return await session_manager.create_session(
            user_id=user_id,
            username=username,
            session_id=session_id,
            roles=roles,
            permissions=permissions,
            user_info=user_info
        )
        
    @staticmethod
    async def invalidate_token(token: str) -> bool:
        """To invalidate the token (delete the corresponding session)

Args:
Token: JWT token

Returns:
Bool: whether the operation was successful"""
        session_id = TokenUtil.get_session_id(token)
        if not session_id:
            return False
            
        session_manager = get_session_manager()
        return await session_manager.delete_session(session_id)
        
    @staticmethod
    async def invalidate_user_tokens(user_id: int, current_token: Optional[str] = None) -> int:
        """Make all user tokens invalid (optionally keep the current token)

Args:
user_id: User ID
current_token: Current token (will not be invalidated)

Returns:
Int: the number of tokens that have expired"""
        session_manager = get_session_manager()
        exclude_session_id = None
        
        if current_token:
            exclude_session_id = TokenUtil.get_session_id(current_token)
            
        return await session_manager.delete_user_sessions(user_id, exclude_session_id)
        
    @staticmethod
    @asynccontextmanager
    async def refresh_session_context(token: str):
        """Refresh the session and update the context manager for the last active time
Uses the context manager pattern for easy use in request processing

Args:
Token: JWT token

Yields:
Optional [UserSession]: Session object"""
        session = await TokenUtil.get_session(token)
        
        try:
            yield session
        finally:
            # Update session active time after request ends
            if session:
                asyncio.create_task(
                    get_session_manager().update_session(session, extend_ttl=True)
                )

    @staticmethod
    async def refresh_session(token: str, ttl: Optional[int] = None) -> bool:
        """refresh session expiration time

Args:
Token: JWT token
TTL: new expiration time (seconds), None means the default value is used

Returns:
Bool: whether the operation was successful"""
        session = await TokenUtil.get_session(token)
        if not session:
            return False
            
        session_manager = get_session_manager()
        
        # Calculate the new expiration time
        if ttl is not None:
            session.expire_at = time.time() + ttl
            
        # Update session
        return await session_manager.update_session(session, extend_ttl=True) 