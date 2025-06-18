from typing import Callable, List
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import re
import asyncio

from knowledge_api.framework.auth.jwt_utils import JWTUtils
from knowledge_api.framework.auth.token_util import TokenUtil
from knowledge_api.framework.exception.response_wrapper import StandardResponse
from knowledge_api.utils.log_config import get_logger

logger = get_logger()

# Define a list of paths that do not require validation (whitelist)
AUTH_WHITELIST = [
    "/docs",
    "/redoc",
    "/openapi.json",
    "/auth/login",
    "/auth/register",
]

class JWTAuthMiddleware(BaseHTTPMiddleware):
    """JWT authentication middleware, intercept requests for JWT verification"""

    def __init__(
        self,
        app: FastAPI,
        exclude_paths: List[str] = None
    ):
        super().__init__(app)
        self.exclude_paths = exclude_paths or AUTH_WHITELIST
        self._exclude_path_regexes = [re.compile(path) for path in self.exclude_paths]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Intercept processing requests

Args:
Request: request object
call_next: subsequent processing functions

Returns:
Response: Response object"""
        if request.method == "OPTIONS":
            return await call_next(request)
            
        # Check if the request path is in the exclusion list
        path = request.url.path
        # Check if the path matches the exclusion pattern
        for pattern in self._exclude_path_regexes:
            if pattern.match(path):
                return await call_next(request)

        # Check if the endpoint is skip_auth marked
        endpoint = request.scope.get("endpoint", None)
        if endpoint and hasattr(endpoint, "skip_auth") and endpoint.skip_auth:
            return await call_next(request)

        # Get JWT Token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            response = JSONResponse(
                content=StandardResponse.error(
                    message="unauthorized",
                    code=401
                ),
                status_code=401
            )
            # Add CORS header
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "*"
            return response

        token = auth_header.replace("Bearer ", "")

        # verification token
        if not JWTUtils.verify_token(token):
            response = JSONResponse(
                content=StandardResponse.error(
                    message="Invalid token",
                    code=401
                ),
                status_code=401
            )
            # Add CORS header
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "*"
            return response

        # Parse the token to obtain basic user information
        try:
            # Parsing JWT Token Data
            token_data = JWTUtils.decode_token(token)
            
            # Gets the session ID to verify that the session exists
            session_id = token_data.get("session_id")
            
            # Verify that session data exists
            if session_id:
                # Use TokenUtil to get detailed session data
                session = await TokenUtil.get_session(token)
                
                if not session:
                    # The session does not exist and may have expired or been deleted
                    response = JSONResponse(
                        content=StandardResponse.error(
                            message="The session has expired or does not exist. Please log in again",
                            code=50014
                        ),
                        status_code=401
                    )
                    response.headers["Access-Control-Allow-Origin"] = "*"
                    response.headers["Access-Control-Allow-Methods"] = "*"
                    response.headers["Access-Control-Allow-Headers"] = "*"
                    return response
                    
                # The session data is stored in the request state
                request.state.session = session
            
            # Store basic token data in the request state
            request.state.token_data = token_data
            request.state.token = token
            
            # Asynchronous refresh session active time (without waiting to complete to avoid blocking requests)
            if session_id:
                asyncio.create_task(self._refresh_session_activity(token))
                
        except Exception as e:
            logger.error(f"token validation error: {str(e)}")
            response = JSONResponse(
                content=StandardResponse.error(
                    message=f"token parsing error: {str(e)}",
                    code=401
                ),
                status_code=401
            )
            # Add CORS header
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "*"
            return response

        # Proceed with the request
        return await call_next(request)
        
    async def _refresh_session_activity(self, token: str):
        """Refresh session active time

Args:
Token: JWT token"""
        try:
            async with TokenUtil.refresh_session_context(token) as _:
                pass  # Only update active time, no additional processing required
        except Exception as e:
            logger.warning(f"failed to refresh session active time: {str(e)}")


def setup_auth_middleware(app: FastAPI, exclude_paths: List[str] = None):
    """Set up authentication middleware to FastAPI application

Args:
App: FastAPI Application Example
exclude_paths: List of excluded paths (no authentication required)"""
    # Add JWT Certified Middleware
    app.add_middleware(
        JWTAuthMiddleware,
        exclude_paths=exclude_paths
    ) 