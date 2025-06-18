from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlmodel import SQLModel, Field, JSON
from decimal import Decimal


class LLMModelConfigBase(SQLModel):
    """LLM model configuration base model"""
    provider_id: int = Field(..., description="Supplier ID")
    provider_sign: Optional[str] = Field(default=None, description="Supplier identification")
    model_name: str = Field(..., description="Model name")
    model_id: str = Field(..., description="Model ID")
    model_type: str = Field(..., description="Model Type: chat-conversational, multimodal-multimodal")
    input_price: Decimal = Field(..., description="Enter price (RMB/thousand tokens)")
    output_price: Decimal = Field(..., description="Output price (yuan/thousand tokens)")
    capabilities: Optional[str] = Field(default=None, description="Model functionality, comma separated")
    introduction: Optional[str] = Field(default=None, description="Model introduction")
    icon_url: Optional[str] = Field(default=None, description="Model icon URL")
    status: int = Field(default=1, description="Status: 1-enabled 0-disabled")
    extra_config: Optional[Dict[str, Any]] = Field(default=None, description="additional configuration items", sa_type=JSON)
    total_input_tokens: Optional[int] = Field(default=0, description="Total Input Tokens Consumed")
    total_output_tokens: Optional[int] = Field(default=0, description="Total Number of Output Tokens Consumed")


class LLMModelConfig(LLMModelConfigBase, table=True):
    """LLM model configuration database model"""
    __tablename__ = "llm_model_config"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now})


class LLMModelConfigCreate(LLMModelConfigBase):
    """Create LLM Model Configuration Request Model"""
    pass


class LLMModelConfigUpdate(SQLModel):
    """Update the LLM model configuration request model"""
    provider_id: Optional[int] = None
    provider_sign: Optional[str] = None
    model_name: Optional[str] = None
    model_id: Optional[str] = None
    model_type: Optional[str] = None
    input_price: Optional[Decimal] = None
    output_price: Optional[Decimal] = None
    capabilities: Optional[str] = None
    introduction: Optional[str] = None
    icon_url: Optional[str] = None
    status: Optional[int] = None
    extra_config: Optional[Dict[str, Any]] = None
    total_input_tokens: Optional[int] = None
    total_output_tokens: Optional[int] = None


class LLMModelConfigResponse(LLMModelConfigBase):
    """LLM model configuration response model"""
    id: int
    created_at: datetime
    updated_at: datetime


class UpdateTokensRequest(SQLModel):
    """Update Tokens Request Model"""
    input_tokens: int = Field(..., description="Enter number of tokens")
    output_tokens: int = Field(..., description="Number of output tokens") 