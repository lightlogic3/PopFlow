"""LLM uses a data model definition for recording contextual data"""

from datetime import datetime
from typing import Optional, List, Dict, Any
import json
from sqlmodel import Field, SQLModel, Column, JSON
from pydantic import BaseModel


class LLMUsageContextBase(SQLModel):
    """LLM uses the record context base model"""
    record_id: int = Field(description="Associated LLM Usage Record ID")
    messages: Optional[List[Dict[str, Any]]] = Field(
        default=None, 
        sa_column=Column(JSON), 
        description="full context message list"
    )
    system_prompt: Optional[str] = Field(default=None, description="system prompt")
    user_prompt: Optional[str] = Field(default=None, description="user prompt")
    additional_data: Optional[Dict[str, Any]] = Field(
        default=None, 
        sa_column=Column(JSON), 
        description="Extra data (e.g. function call parameters, etc.)"
    )


class LLMUsageContext(LLMUsageContextBase, table=True):
    """database model"""
    __tablename__ = "llm_usage_contexts"
    
    id: Optional[int] = Field(default=None, primary_key=True, description="primary key ID")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="creation time"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="update time"
    )


class LLMUsageContextCreate(LLMUsageContextBase):
    """Create a record request model"""
    pass


class LLMUsageContextUpdate(SQLModel):
    """Update record request model"""
    record_id: Optional[int] = None
    messages: Optional[List[Dict[str, Any]]] = None
    system_prompt: Optional[str] = None
    user_prompt: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


class LLMUsageContextResponse(LLMUsageContextBase):
    """response model"""
    id: int
    created_at: datetime
    updated_at: datetime 