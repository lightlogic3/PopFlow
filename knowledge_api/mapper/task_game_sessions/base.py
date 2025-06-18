"""Game task session data model definition"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlmodel import Field, SQLModel, JSON
from pydantic import BaseModel


class TaskGameSessionBase(SQLModel):
    """Game Quest Session Basic Model"""
    user_id: str = Field(description="user ID")
    subtask_id: str = Field(description="subtask ID")
    task_id: str = Field(description="main task ID")
    status: int = Field(default=0, description="Session Status: 0 - In Progress 1 - Completed 2 - Interrupted 3 - Timed Out")
    current_score: int = Field(default=0, description="Current score")
    current_round: int = Field(default=1, description="Current round")
    max_rounds: int = Field(default=5, description="Maximum round")
    target_score: int = Field(default=100, description="Target score")
    last_message_time: Optional[datetime] = Field(default=None, description="Last message time")
    summary: Optional[str] = Field(default=None, description="Session summary or summary of results")


class TaskGameSession(TaskGameSessionBase, table=True):
    """database model"""
    __tablename__ = "task_game_sessions"
    
    id: str = Field(primary_key=True, description="Session ID")
    create_time: datetime = Field(
        default_factory=datetime.now,
        description="creation time"
    )
    update_time: datetime = Field(
        default_factory=datetime.now,
        description="update time"
    )


class TaskGameSessionCreate(TaskGameSessionBase):
    """Create a session request model"""
    pass


class TaskGameSessionUpdate(SQLModel):
    """Update session request model"""
    user_id: Optional[str] = None
    subtask_id: Optional[str] = None
    task_id: Optional[str] = None
    status: Optional[int] = None
    current_score: Optional[int] = None
    current_round: Optional[int] = None
    max_rounds: Optional[int] = None
    target_score: Optional[int] = None
    last_message_time: Optional[datetime] = None
    summary: Optional[str] = None


class TaskGameSessionResponse(TaskGameSessionBase):
    """response model"""
    id: str
    create_time: datetime
    update_time: datetime
    
    class Config:
        """Configure the ORM mode so that the model can be used with fastapi-pagination"""
        orm_mode = True
        from_attributes = True


class TaskGameSessionFilter(BaseModel):
    """session filter"""
    user_id: Optional[str] = None
    subtask_id: Optional[str] = None
    task_id: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    min_score: Optional[int] = None
    max_score: Optional[int] = None
    
    def dict(self, **kwargs):
        """Convert to dictionary, exclude null values"""
        result = super().dict(**kwargs)
        if 'exclude_none' in kwargs and kwargs['exclude_none']:
            return {k: v for k, v in result.items() if v is not None}
        return result
    
    class Config:
        from_attributes = True


class TaskGameSessionStats(BaseModel):
    """Session Statistical Response Model"""
    total_sessions: int
    completed_sessions: int
    interrupted_sessions: int
    timed_out_sessions: int
    in_progress_sessions: int
    average_score: float
    average_rounds: float
    sessions_by_task: Dict[str, int]
    sessions_by_status: Dict[int, int]
    
    class Config:
        from_attributes = True 