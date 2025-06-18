import asyncio
from typing import Optional
from pydantic import BaseModel, Field


class LLMTokenResponse(BaseModel):
    id: Optional[str]=Field(None, description="unique identifier")
    model: Optional[str]=Field(None, description="Model name")
    created: Optional[int]=Field(int(asyncio.get_event_loop().time()), description="creation time")
    content: Optional[str]=Field(..., description="content")
    role: Optional[str]=Field("assistant", description="role")
    finish_reason: Optional[str]=Field("stop", description="completion reason")
    input_tokens: Optional[int]=Field(-1, description="Enter number of tokens")
    output_tokens: Optional[int]=Field(-1, description="Number of output tokens")
    total_tokens: Optional[int] = Field(-1, description="Total tokens")
    elapsed_time: Optional[float] = Field(0.0, description="Request time (seconds)")
    price: Optional[float] = Field(0.0, description="Price (yuan)")