"""Role subtask basic model"""
from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import Field
from sqlmodel import SQLModel, Field as SQLModelField


class RoleSubtaskBase(SQLModel):
    """subtask base model"""
    task_id: str = Field(..., description="main task ID")
    task_personality: Optional[str] = Field(None, description="subtask persona")
    task_goal_judge: Optional[str] = Field(None, description="Sub-task referee judgment standard")
    hide_designs: Optional[str] = Field(None, description="Subtask hidden settings (comma separated)")
    task_level: Optional[int] = Field(None, description="Subtask difficulty level (reserved)")
    prologues: Optional[str] = Field(None, description="Subtask opening remarks, separated by multiple commas")
    task_description:Optional[str] = Field(None, description="task description")
    task_goal:Optional[str] = Field(None, description="mission objective")


class RoleSubtask(RoleSubtaskBase, table=True):
    """Subtask Database Model"""
    __tablename__ = "llm_role_subtasks"

    id: str = SQLModelField(default_factory=lambda: str(uuid4()), primary_key=True)
    create_time: datetime = SQLModelField(default_factory=datetime.now)
    update_time: datetime = SQLModelField(default_factory=datetime.now)
    create_at: Optional[str] = Field(None, description="creator")
    update_at: Optional[str] = Field(None, description="Updater")


class RoleSubtaskCreate(RoleSubtaskBase):
    """subtask creation model"""
    create_at: Optional[str] = Field(None, description="creator")


class RoleSubtaskUpdate(SQLModel):
    """Subtask update model"""
    task_id: Optional[str] = Field(None, description="main task ID")
    task_personality: Optional[str] = Field(None, description="subtask persona")
    task_goal_judge: Optional[str] = Field(None, description="Sub-task referee judgment standard")
    hide_designs: Optional[str] = Field(None, description="Subtask hidden settings (comma separated)")
    task_level: Optional[int] = Field(None, description="Subtask difficulty level (reserved)")
    prologues: Optional[str] = Field(None, description="Subtask opening remarks, separated by multiple commas")
    update_at: Optional[str] = Field(None, description="Updater")
    task_description:Optional[str] = Field(None, description="task description")
    task_goal:Optional[str] = Field(None, description="mission objective")



class RoleSubtaskResponse(RoleSubtaskBase):
    """subtask response model"""
    id: str
    create_time: datetime
    update_time: datetime
    create_at: Optional[str] = None
    update_at: Optional[str] = None
    task_description:Optional[str] = Field(None, description="task description")
    task_goal:Optional[str] = Field(None, description="mission objective")


class UserSubtaskRelationBase(SQLModel):
    """User Subtask Association Basic Model"""
    user_id: str = Field(..., description="user ID")
    subtask_id: str = Field(..., description="subtask ID")
    task_id: str = Field(..., description="main task ID")
    status: int = Field(default=1, description="Status: 0 - Not Completed 1 - Completed")
    score: Optional[int] = Field(None, description="user score")


class UserSubtaskRelation(UserSubtaskRelationBase, table=True):
    """User subtask associative database model"""
    __tablename__ = "user_subtask_relations"
    
    id: int = SQLModelField(primary_key=True, default=None)
    start_time: datetime = SQLModelField(default_factory=datetime.now)
    complete_time: Optional[datetime] = SQLModelField(default=None)
    create_time: datetime = SQLModelField(default_factory=datetime.now)
    update_time: datetime = SQLModelField(default_factory=datetime.now)


class UserSubtaskRelationCreate(UserSubtaskRelationBase):
    """User subtask association creation model"""
    pass


class UserSubtaskRelationUpdate(SQLModel):
    """User Subtask Association Update Model"""
    status: Optional[int] = Field(None, description="Status: 0 - Not Completed 1 - Completed")
    score: Optional[int] = Field(None, description="user score")
    complete_time: Optional[datetime] = Field(None, description="completion time") 