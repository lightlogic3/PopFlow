from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlmodel import Field, SQLModel, JSON
from pydantic import BaseModel


class TaskBase(SQLModel):
    """Task-based model"""
    title: str = Field(..., description="task title")
    description: Optional[str] = Field(default=None, description="task description")
    setting: Optional[str] = Field(default=None, description="task setting")
    max_dialogue_rounds: Optional[int] = Field(default=None, description="Task Maximum Number of Dialogue Rounds")
    status: Optional[int] = Field(default=1, description="Status: 1-enabled 0-disabled")
    task_type: str = Field(..., description="task type")
    difficulty: str = Field(..., description="task difficulty")
    time_period: Optional[str] = Field(default=None, description="limited time period")
    required_user_level: Optional[int] = Field(default=None, description="user level requirement")
    reference_case: Optional[str] = Field(default=None, description="Reference case")
    game_type: Optional[str] = Field(default=None, description="Game Type")
    game_number_max: Optional[int] = Field(default=None, description="maximum number of players")
    game_number_min: Optional[int] = Field(default=None, description="minimum number of players")
    rule_data: Optional[Dict[str, Any]] = Field(default=None, description="JSON field", sa_type=JSON)


class Task(TaskBase, table=True):
    """Task Database Model"""
    __tablename__ = "tasks"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TaskCreate(TaskBase):
    """Create a request model for tasks"""
    role_relations: Optional[List[dict]] = Field(default=None, description="associated role list")


class TaskUpdate(BaseModel):
    """Request model for updating tasks"""
    title: Optional[str] = None
    description: Optional[str] = None
    setting: Optional[str] = None
    max_dialogue_rounds: Optional[int] = None
    status: Optional[int] = None
    task_type: Optional[str] = None
    difficulty: Optional[str] = None
    time_period: Optional[str] = None
    required_user_level: Optional[int] = None
    reference_case: Optional[str] = None
    game_type: Optional[str] = None
    game_number_max: Optional[int] = None
    game_number_min: Optional[int] = None
    rule_data: Optional[Dict[str, Any]] = None
    """Create a request model for tasks"""
    role_relations: Optional[List[dict]] = Field(default=None, description="associated role list")


class TaskResponse(TaskBase):
    """Task Response Model"""
    id: int
    created_at: datetime
    updated_at: datetime 