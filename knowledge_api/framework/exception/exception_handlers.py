from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic.error_wrappers import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback
import logging

from .error_codes import get_error_message
from .custom_exceptions import BusinessException
from knowledge_api.framework.exception.response_wrapper import StandardResponse

# configuration log
logger = logging.getLogger(__name__)

async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handling HTTP exceptions
: param request: request object
: param exc: exception object
: return: JSON response"""
    # Get error message
    message = get_error_message(exc.status_code)
    
    # If there are details, use the details
    if exc.detail:
        message = str(exc.detail)
    
    # Building responsive data
    response_data = StandardResponse.error(
        message=message,
        code=exc.status_code
    )
    
    # Log errors
    logger.error(f"HTTP异常: {exc.status_code} - {message}")
    
    # Return response
    response = JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )
    
    # Add CORS header
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handling request parameter validation exceptions
: param request: request object
: param exc: exception object
: return: JSON response"""
    # Get error message
    message = get_error_message(422)
    
    # Detailed error message
    details = []
    for error in exc.errors():
        error_msg = f"{' -> '.join(str(loc) for loc in error['loc'])}: {error['msg']}"
        details.append(error_msg)
    
    # Building responsive data
    response_data = StandardResponse.error(
        message=message,
        code=422,
        data=details
    )
    
    # Log errors
    logger.error(f"参数验证异常: {details}")
    
    # Return response
    response = JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response_data
    )
    
    # Add CORS header
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response

async def business_exception_handler(request: Request, exc: BusinessException) -> JSONResponse:
    """Handling business exceptions
: param request: request object
: param exc: exception object
: return: JSON response"""
    # Building responsive data
    response_data = StandardResponse.error(
        message=exc.detail,
        code=exc.business_code
    )
    
    # Log errors
    logger.error(f"业务异常: {exc.business_code} - {exc.detail}")
    
    # Return response
    response = JSONResponse(
        status_code=exc.status_code,
        content=response_data
    )
    
    # Add CORS header
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handling generic exceptions
: param request: request object
: param exc: exception object
: return: JSON response"""
    # Get error message
    message = get_error_message(500)
    
    # Building responsive data
    response_data = StandardResponse.error(
        message=message,
        code=500,
        data=str(exc) if str(exc) else None
    )
    
    # Logging detailed error logs and stacks
    logger.error(f"未处理异常: {str(exc)}")
    logger.error(traceback.format_exc())
    
    # Return response
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response_data
    )
    
    # Add CORS header
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response

def setup_exception_handlers(app: FastAPI) -> None:
    """Set up exception handlers
: Param app: FastAPI application instance"""
    # Register exception handlers
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(BusinessException, business_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler) 