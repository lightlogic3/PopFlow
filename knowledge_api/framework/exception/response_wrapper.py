from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from typing import Any, Dict
import logging
import json

from knowledge_api.framework.exception.error_codes import get_error_message

# configuration log
logger = logging.getLogger(__name__)


class StandardResponse:
    """standard response format encapsulation"""
    @staticmethod
    def success(data: Any = None, message: str = "Operation successful", code: int = 200) -> Dict:
        """successful response
: param data: response data
: param message: response message
: param code: response code
: return: standard response format"""
        return {
            "code": code,
            "message": message,
            "data": data
        }
    
    @staticmethod
    def error(message: str = "Operation failed", code: int = 500, data: Any = None) -> Dict:
        """error response
: param message: error message
: param code: BigInt
: Param data: error detail data
: return: standard response format"""
        return {
            "code": code,
            "message": message,
            "data": data
        }


class ResponseWrapperMiddleware(BaseHTTPMiddleware):
    """Response Format Unified Processing Middleware"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """request distribution
: param request: request object
: Param call_next: next middleware
: return: response object"""
        # Skip paths that do not require processing
        if self._should_skip_by_path(request):
            return await call_next(request)
        
        # execution request
        response = await call_next(request)
        
        # Skip responses that do not require processing
        if self._should_skip_by_response(response):
            return response
        
        # Try packaging response
        try:
            # Read response content
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            
            # Parsing JSON
            json_body = json.loads(body)
            
            # Check if it is already in standard format
            if isinstance(json_body, dict) and "code" in json_body and "message" in json_body:
                # It already conforms to the standard format, recreate the response
                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )
            
            # Packaged in standard format
            if response.status_code == 200:
                # successful response
                standard_body = StandardResponse.success(data=json_body)
            else:
                # Error response, get error message
                message = get_error_message(response.status_code)
                
                # If there is an error message in the JSON body, use it first
                if isinstance(json_body, dict) and "detail" in json_body:
                    message = json_body.get("detail", message)
                
                # Create an error response body
                standard_body = StandardResponse.error(
                    message=message,
                    code=response.status_code,
                    data=json_body if not isinstance(json_body, dict) or "detail" not in json_body else None
                )
            
            # Create a new response
            return JSONResponse(
                content=standard_body,
                status_code=response.status_code,
                headers={
                    k: v for k, v in response.headers.items()
                    if k.lower() != "content-length"
                }
            )
            
        except Exception as e:
            # Log errors when processing fails and return the original response
            logger.error(f"响应封装失败: {str(e)}")
            
            # The response must be rebuilt because it has consumed body_iterator
            return Response(
                content=body if 'body' in locals() else b"",
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
    
    def _should_skip_by_path(self, request: Request) -> bool:
        """Determine whether to skip processing according to the path"""
        skip_paths = ["/docs", "/redoc", "/openapi.json", "/static"]
        
        for path in skip_paths:
            if request.url.path.startswith(path):
                return True
                
        return False
    
    def _should_skip_by_response(self, response: Response) -> bool:
        """Determine whether to skip processing based on the response"""
        # No more skipping non-200 responses, all status codes need to be formatted
        # if response.status_code != 200:
        #     return True
            
        # Skip only non-JSON responses
        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type.lower():
            return True
            
        return False


def setup_response_wrapper(app: FastAPI) -> None:
    """Setup Response Uniform Format Middleware
: param app: FastAPI app"""
    app.add_middleware(ResponseWrapperMiddleware) 