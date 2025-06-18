from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import Field
from sqlmodel import SQLModel, Field as SQLModelField


class RoleTaskBase(SQLModel):
    """Task-based model"""
    title: str = Field(..., description="task title")
    description: str = Field(..., description="task description")
    task_goal: str = Field(..., description="mission objective")
    max_rounds: int = Field(5, description="Maximum number of conversation rounds")
    target_score: int = Field(100, description="target score")
    score_range: str = Field("-10~+10", description="add and subtract each time")
    task_level: int = Field(1, description="Mission difficulty level (1-5)")
    task_personality: Optional[str] = Field(None, description="task person")
    hide_designs: Optional[str] = Field(None, description="Hide Settings (Comma Separated)")
    task_type: str = Field("standard", description="task type")
    user_level_required: int = Field(1, description="user level requirement")
    role_id: str = Field(..., description="associated role ID")
    task_goal_judge:Optional[str]=Field(default="",description="AI judgment standard")
    prologues:Optional[str]=Field(...,description="opening statement")
    task_cover:Optional[str]=Field("",description="task cover")


class RoleTask(RoleTaskBase, table=True):
    """Task Database Model"""
    __tablename__ = "llm_role_tasks"

    id: str = SQLModelField(default_factory=lambda: str(uuid4()), primary_key=True)
    create_time: datetime = SQLModelField(default_factory=datetime.now)
    update_time: datetime = SQLModelField(default_factory=datetime.now)
    create_at: Optional[str] = Field(None, description="creator")
    update_at: Optional[str] = Field(None, description="Updater")


class RoleTaskCreate(RoleTaskBase):
    """Task creation model"""
    create_at: Optional[str] = Field(None, description="creator")


class RoleTaskUpdate(SQLModel):
    """task update model"""
    title: Optional[str] = Field(None, description="task title")
    description: Optional[str] = Field(None, description="task description")
    task_goal: Optional[str] = Field(None, description="mission objective")
    max_rounds: Optional[int] = Field(None, description="Maximum number of conversation rounds")
    target_score: Optional[int] = Field(None, description="target score")
    score_range: Optional[str] = Field(None, description="add and subtract each time")
    task_level: Optional[int] = Field(None, description="Mission difficulty level (1-5)")
    task_personality: Optional[str] = Field(None, description="task person")
    hide_designs: Optional[str] = Field(None, description="Hide Settings (Comma Separated)")
    task_type: Optional[str] = Field(None, description="task type")
    user_level_required: Optional[int] = Field(None, description="user level requirement")
    role_id: Optional[str] = Field(None, description="associated role ID")
    update_at: Optional[str] = Field(None, description="Updater")
    task_goal_judge:str=Field(default="",description="AI judgment standard")
    prologues: Optional[str] = Field(..., description="opening statement")
    task_cover: Optional[str] = Field("", description="task cover")


class RoleTaskResponse(RoleTaskBase):
    """Task Response Model"""
    id: str
    create_time: datetime
    update_time: datetime
    create_at: Optional[str] = None
    update_at: Optional[str] = None 