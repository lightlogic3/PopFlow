from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, JSON
from decimal import Decimal


class LLMProviderConfigBase(SQLModel):
    """LLM Provider Configuration Foundation Model"""
    provider_name: str = Field(..., description="Provider name")
    provider_sign: Optional[str] = Field(default=None, description="Supplier identification")
    api_url: str = Field(..., description="API address")
    api_key: str = Field(..., description="API Key")
    model_name: str = Field(..., description="Model name")
    remark: Optional[str] = Field(default=None, description="Remarks")
    status: int = Field(default=1, description="Status: 1-enabled 0-disabled")
    extra_config: Optional[Dict[str, Any]] = Field(default=None, description="additional configuration items", sa_type=JSON)
    total_price: Optional[Decimal] = Field(default=0, description="total price")


class LLMProviderConfig(LLMProviderConfigBase, table=True):
    """LLM Provider Configuration Database Model"""
    __tablename__ = "llm_provider_config"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now})


class LLMProviderConfigCreate(LLMProviderConfigBase):
    """Create an LLM provider configuration request model"""
    pass


class LLMProviderConfigUpdate(SQLModel):
    """Updating the LLM Provider Configuration Request Model"""
    provider_name: Optional[str] = None
    provider_sign: Optional[str] = None
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    remark: Optional[str] = None
    status: Optional[int] = None
    extra_config: Optional[Dict[str, Any]] = None
    total_price: Optional[Decimal] = None


class LLMProviderConfigResponse(LLMProviderConfigBase):
    """LLM Provider Configuration Response Model"""
    id: int
    created_at: datetime
    updated_at: datetime 