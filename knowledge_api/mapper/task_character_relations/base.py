from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel
from pydantic import BaseModel


class TaskCharacterRelationBase(SQLModel):
    """Task Role Association Base Model"""
    task_id: int = Field(..., description="Task ID")
    role_id: str = Field(..., description="Role ID")
    llm_model: Optional[str] = Field(default=None, description="role model")
    voice: Optional[str] = Field(default=None, description="timbre")
    character_setting: Optional[str] = Field(default=None, description="role setting")


class TaskCharacterRelation(TaskCharacterRelationBase, table=True):
    """Task Role Associated Database Model"""
    __tablename__ = "task_character_relations"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TaskCharacterRelationCreate(TaskCharacterRelationBase):
    """Create a request model for task role associations"""
    pass


class TaskCharacterRelationUpdate(BaseModel):
    """Update the request model for task role associations"""
    llm_model: Optional[str] = None
    voice: Optional[str] = None
    character_setting: Optional[str] = None


class TaskCharacterRelationResponse(TaskCharacterRelationBase):
    """Task Role Association Response Model"""
    id: int
    created_at: datetime 