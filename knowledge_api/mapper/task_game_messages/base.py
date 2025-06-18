"""Game task message data model definition"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import Field, SQLModel
from pydantic import BaseModel


class TaskGameMessageBase(SQLModel):
    """Game task message base model"""
    session_id: str = Field(description="Session ID")
    role: str = Field(description="Role: user-user assistant-AI system-system function-function call")
    role_id: Optional[str] = Field(default=None, description="Role ID")
    user_id: Optional[str] = Field(default=None, description="user ID")
    content: str = Field(description="message content")
    round: int = Field(default=1, description="conversation turn")
    score_change: Optional[int] = Field(default=0, description="The score change caused by this message")
    score_reason: Optional[str] = Field(default=None, description="The reason for the change in score")
    input_tokens: Optional[int] = Field(default=None, description="Enter Token")
    output_tokens: Optional[int] = Field(default=None, description="Export Token")
    model_id: Optional[str] = Field(default=None, description="Model ID")


class TaskGameMessage(TaskGameMessageBase, table=True):
    """database model"""
    __tablename__ = "task_game_messages"
    
    id: int = Field(primary_key=True, description="Message ID")
    create_time: datetime = Field(
        default_factory=datetime.now,
        description="creation time"
    )


class TaskGameMessageCreate(TaskGameMessageBase):
    """Create a message request model"""
    pass


class TaskGameMessageUpdate(SQLModel):
    """Update message request model"""
    session_id: Optional[str] = None
    role: Optional[str] = None
    role_id: Optional[str] = None
    user_id: Optional[str] = None
    content: Optional[str] = None
    round: Optional[int] = None
    score_change: Optional[int] = None
    score_reason: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    model_id: Optional[str] = None


class TaskGameMessageResponse(TaskGameMessageBase):
    """response model"""
    id: int
    create_time: datetime
    
    class Config:
        """Configure the ORM mode so that the model can be used with fastapi-pagination"""
        orm_mode = True
        from_attributes = True


class TaskGameMessageFilter(BaseModel):
    """message filter"""
    session_id: Optional[str] = None
    role: Optional[str] = None
    user_id: Optional[str] = None
    role_id: Optional[str] = None
    round: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    def dict(self, **kwargs):
        """Convert to dictionary, exclude null values"""
        result = super().dict(**kwargs)
        if 'exclude_none' in kwargs and kwargs['exclude_none']:
            return {k: v for k, v in result.items() if v is not None}
        return result
    
    class Config:
        from_attributes = True


class TaskGameMessageStats(BaseModel):
    """Message Statistical Response Model"""
    total_messages: int
    messages_by_role: Dict[str, int]
    messages_by_round: Dict[int, int]
    average_score_change: float
    total_input_tokens: int
    total_output_tokens: int
    
    class Config:
        from_attributes = True 