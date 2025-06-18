"""The LLM model uses a documented data model definition"""

from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from sqlmodel import Field, SQLModel
from pydantic import BaseModel, validator


class LLMUsageRecordBase(SQLModel):
    """LLM uses a record-based model"""
    request_id: Optional[str] = Field(default=None, description="request unique identity")
    vendor_type: str = Field(description="Type of supplier (e.g. doubao, openai, etc.)")
    model_id: str = Field(description="Model ID")
    input_tokens: int = Field(default=0, description="Enter number of tokens")
    output_tokens: int = Field(default=0, description="Number of output tokens")
    total_tokens: int = Field(default=0, description="Total tokens")
    application_scenario: Optional[str] = Field(default=None, description="application scenario")
    total_price: Optional[Decimal] = Field(default=Decimal("0.00000000"), description="total price")
    related_record_id: Optional[str] = Field(default=None, description="associated record ID")
    content: Optional[str] = Field(default=None, description="response content")
    role: Optional[str] = Field(default="assistant", description="role")
    finish_reason: Optional[str] = Field(default="stop", description="completion reason")
    elapsed_time: Optional[float] = Field(default=0.0, description="Request time (seconds)")


class LLMUsageRecord(LLMUsageRecordBase, table=True):
    """database model"""
    __tablename__ = "llm_usage_records"
    
    id: Optional[int] = Field(default=None, primary_key=True, description="primary key ID")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="creation time"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="update time"
    )


class LLMUsageRecordCreate(LLMUsageRecordBase):
    """Create a record request model"""
    @validator('total_tokens', pre=True, always=True)
    def calculate_total_tokens(cls, v, values):
        """If no total_tokens is provided, it is calculated from input_tokens and output_tokens"""
        if v == 0 and 'input_tokens' in values and 'output_tokens' in values:
            return values['input_tokens'] + values['output_tokens']
        return v


class LLMUsageRecordUpdate(SQLModel):
    """Update record request model"""
    request_id: Optional[str] = None
    vendor_type: Optional[str] = None
    model_id: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    application_scenario: Optional[str] = None
    total_price: Optional[Decimal] = None
    related_record_id: Optional[str] = None
    content: Optional[str] = None
    role: Optional[str] = None
    finish_reason: Optional[str] = None
    elapsed_time: Optional[float] = None


class LLMUsageRecordResponse(LLMUsageRecordBase):
    """response model"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Configure the ORM mode so that the model can be used with fastapi-pagination"""
        orm_mode = True
        from_attributes = True


class LLMUsageRecordFilter(BaseModel):
    """record filter"""
    vendor_type: Optional[str] = None
    model_id: Optional[str] = None
    application_scenario: Optional[str] = None
    related_record_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_tokens: Optional[int] = None
    max_tokens: Optional[int] = None
    
    def dict(self, **kwargs):
        """Convert to dictionary, exclude null values"""
        result = super().dict(**kwargs)
        if 'exclude_none' in kwargs and kwargs['exclude_none']:
            return {k: v for k, v in result.items() if v is not None}
        return result
    
    class Config:
        from_attributes = True


class LLMUsageRecordStats(BaseModel):
    """Using statistical response models"""
    total_records: int
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    total_price: Decimal
    average_elapsed_time: float
    records_by_model: dict
    records_by_vendor: dict
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v)
        } 