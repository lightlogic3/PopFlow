import functools
from typing import List, Callable, Dict, Any, Optional
from fastapi import HTTPException, Request, Depends
from knowledge_api.framework.auth.jwt_utils import JWTBearer
from knowledge_api.framework.auth.token_util import TokenUtil
from knowledge_api.utils.log_config import get_logger

logger = get_logger()
jwt_bearer = JWTBearer()
get_request = Request

def skip_auth():
    """Skip Authentication Decorator
Used to flag interfaces that do not require authentication"""
    def decorator(func: Callable) -> Callable:
        setattr(func, "skip_auth", True)
        return func
    return decorator

def require_permissions(permissions: List[str]):
    """permission check decorator

Args:
Permissions: List of required permissions"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Check if authentication is skipped
            if getattr(func, "skip_auth", False):
                return await func(*args, **kwargs)
            
            # Automatic injection of Request objects into kwargs
            if 'request' not in kwargs:
                # Create a request dependency
                request_dependency = Depends(lambda: Request)
                request = await request_dependency()
                kwargs['request'] = request
            
            # Get request object
            request = kwargs.get('request')
            
            # If you still can't get the request, try looking it up from the location parameter
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            # If the request object is still not found, log the error and return
            if not request:
                logger.warning(f"unable to get the requested information: {func.__name__}, args: {args}, kwargs keys: {list(kwargs.keys())}")
                
                # Build a default request object (for the testing environment)
                from starlette.datastructures import Headers
                request = Request(
                    scope={
                        "type": "http",
                        "method": "GET",
                        "path": "/",
                        "headers": Headers([(b"authorization", b"")]).raw,
                    }
                )
                request.state.token_data = {"user_id": 0, "username": "", "session_id": ""}
                
                # In a production environment, errors should be thrown
                raise HTTPException(status_code=500, detail="Unable to get request information, make sure the routing function contains the Request parameter")
            
            # Check User Token Information
            token_data = getattr(request.state, "token_data", None)
            if not token_data:
                raise HTTPException(status_code=401, detail="unauthorized")
                
            token = getattr(request.state, "token", None)
            if not token:
                raise HTTPException(status_code=401, detail="unauthorized")
                
            # Get user permissions from the session
            session = getattr(request.state, "session", None)
            
            # If the session does not exist, try to retrieve it from the token
            if not session:
                session = await TokenUtil.get_session(token)
                
            # Check if it is an administrator role (with all permissions)
            if session and "admin" in session.roles:
                return await func(*args, **kwargs)
                
            # Check if you have the required permissions
            user_permissions = session.permissions if session else []
            
            for required_perm in permissions:
                if required_perm not in user_permissions:
                    raise HTTPException(status_code=403, detail=f"lack of permissions: {required_perm}")
            
            return await func(*args, **kwargs)
        
        # Add Dependency Injection
        original_dependencies = getattr(func, "dependencies", [])
        request_dependency = Depends(lambda: Request)
        all_dependencies = original_dependencies + [request_dependency]
        setattr(wrapper, "dependencies", all_dependencies)
        
        return wrapper
    
    return decorator

def require_roles(roles: List[str]):
    """Character Validation Decorator

Args:
Roles: List of required roles"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Check if authentication is skipped
            if getattr(func, "skip_auth", False):
                return await func(*args, **kwargs)
            
            # Automatic injection of Request objects into kwargs
            if 'request' not in kwargs:
                # Create a request dependency
                request_dependency = Depends(lambda: Request)
                request = await request_dependency()
                kwargs['request'] = request
            
            # Get request object
            request = kwargs.get('request')
            
            # If you still can't get the request, try looking it up from the location parameter
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            # If the request object is still not found, log the error and return
            if not request:
                logger.warning(f"unable to get the requested information: {func.__name__}, args: {args}, kwargs keys: {list(kwargs.keys())}")
                raise HTTPException(status_code=500, detail="Unable to get request information, make sure the routing function contains the Request parameter")
            
            # Check User Token Information
            token_data = getattr(request.state, "token_data", None)
            if not token_data:
                raise HTTPException(status_code=401, detail="unauthorized")
                
            token = getattr(request.state, "token", None)
            if not token:
                raise HTTPException(status_code=401, detail="unauthorized")
                
            # Acquire user roles from a session
            session = getattr(request.state, "session", None)
            
            # If the session does not exist, try to retrieve it from the token
            if not session:
                session = await TokenUtil.get_session(token)
                
            # Check if it is an administrator role (with all permissions)
            if session and "admin" in session.roles:
                return await func(*args, **kwargs)
                
            # Check if you have the required role
            user_roles = session.roles if session else []
            
            for required_role in roles:
                if required_role not in user_roles:
                    raise HTTPException(status_code=403, detail=f"do not have the required role: {required_role}")
            
            return await func(*args, **kwargs)
        
        # Add Dependency Injection
        original_dependencies = getattr(func, "dependencies", [])
        request_dependency = Depends(lambda: Request)
        all_dependencies = original_dependencies + [request_dependency]
        setattr(wrapper, "dependencies", all_dependencies)
        
        return wrapper
    
    return decorator

async def get_current_user(request: Request) -> Dict[str, Any]:
    """Get dependencies on the current logged-in user information

Args:
Request: request object

Returns:
Dict [str, Any]: Current user information"""
    if not hasattr(request.state, "token_data"):
        raise HTTPException(status_code=401, detail="unauthorized")
        
    # Get full user information from the session first
    session = getattr(request.state, "session", None)
    if session:
        return {
            "user_id": session.user_id,
            "username": session.username,
            "roles": session.roles,
            "permissions": session.permissions,
            "user_info": session.user_info,
            "session_id": session.session_id
        }
        
    # If the session does not exist, try to parse the basic information from the token
    token = getattr(request.state, "token", None)
    if token:
        try:
            # Attempt to obtain conversation information
            session = await TokenUtil.get_session(token)
            if session:
                return {
                    "user_id": session.user_id,
                    "username": session.username,
                    "roles": session.roles,
                    "permissions": session.permissions,
                    "user_info": session.user_info,
                    "session_id": session.session_id
                }
        except Exception as e:
            logger.error(f"failed to get user session information: {str(e)}")
            
    # Back to base Token data
    return request.state.token_data
    
async def get_current_user_session(request: Request) -> Optional[Dict[str, Any]]:
    """Get the dependency for the current user session information, or return None if none exists

Args:
Request: request object

Returns:
Optional [Dict [str, Any]]: Current user session information"""
    # Get priority from request status
    session = getattr(request.state, "session", None)
    if session:
        return {
            "user_id": session.user_id,
            "username": session.username,
            "roles": session.roles,
            "permissions": session.permissions,
            "user_info": session.user_info,
            "session_id": session.session_id,
            "created_at": session.created_at,
            "last_active_at": session.last_active_at,
            "expire_at": session.expire_at,
            "metadata": session.metadata
        }
        
    # Try to get from Token
    token = getattr(request.state, "token", None)
    if token:
        try:
            session = await TokenUtil.get_session(token)
            if session:
                return {
                    "user_id": session.user_id,
                    "username": session.username,
                    "roles": session.roles,
                    "permissions": session.permissions,
                    "user_info": session.user_info,
                    "session_id": session.session_id,
                    "created_at": session.created_at,
                    "last_active_at": session.last_active_at,
                    "expire_at": session.expire_at,
                    "metadata": session.metadata
                }
        except Exception as e:
            logger.error(f"failed to get user session information: {str(e)}")
            
    return None 