from typing import Any

from pydantic import BaseModel, HttpUrl, Field


class BaseResponse(BaseModel):
    """Text processing response"""
    success: bool = Field(True, description="Is the processing successful?")
    message: str = Field(..., description="Processing result message")
    code: int = Field(200, description="response coding")
    data: Any = Field(None, deprecated="response data")
