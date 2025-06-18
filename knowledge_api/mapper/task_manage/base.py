"""Timed Task Management Data Model"""
from datetime import datetime
from typing import Dict, Optional, Any, List
from enum import Enum
import json
from pydantic import Field, validator
from sqlmodel import SQLModel, Field as SQLField, Column, JSON


class TaskStatus(str, Enum):
    """task state enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class TriggerType(str, Enum):
    """trigger type enumeration"""
    DATE = "date"
    INTERVAL = "interval"
    CRON = "cron"


class TaskManageBase(SQLModel):
    """Timed Task Basic Model"""
    name: str = Field(..., description="task name")
    task_type: str = Field(..., description="task type")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="task status")
    trigger_type: TriggerType = Field(..., description="trigger type")
    func_path: str = Field(..., description="execution function path")
    next_run_time: Optional[datetime] = Field(default=None, description="next runtime")
    max_instances: int = Field(default=1, description="maximum number of instances")
    description: Optional[str] = Field(default=None, description="task description")


class TaskManage(TaskManageBase, table=True):
    """Timed Task Management Table Model"""
    __tablename__ = "task_manage"
    
    id: str = SQLField(primary_key=True)
    trigger_args: Dict[str, Any] = SQLField(sa_column=Column(JSON), default_factory=dict, description="trigger parameters")
    func_args: Dict[str, Any] = SQLField(sa_column=Column(JSON), default_factory=dict, description="function parameter")
    create_time: datetime = SQLField(default_factory=datetime.now, description="creation time")
    update_time: datetime = SQLField(default_factory=datetime.now, description="update time")


class TaskManageCreate(TaskManageBase):
    """Create a timed task request model"""
    id: Optional[str] = Field(default="", description="ID")
    trigger_args: Dict[str, Any] = Field(default_factory=dict, description="trigger parameters")
    func_args: Dict[str, Any] = Field(default_factory=dict, description="function parameter")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "sample task",
                "task_type": "notification",
                "trigger_type": "interval",
                "trigger_args": {"hours": 1},
                "func_path": "knowledge_api.framework.task_manage.example_tasks.simple_task",
                "func_args": {"message": "Hello World"},
                "max_instances": 1,
                "description": "Example tasks performed hourly"
            }
        }


class TaskManageUpdate(SQLModel):
    """Update the timed task request model"""
    name: Optional[str] = None
    task_type: Optional[str] = None
    status: Optional[TaskStatus] = None
    trigger_type: Optional[TriggerType] = None
    trigger_args: Optional[Dict[str, Any]] = None
    func_path: Optional[str] = None
    func_args: Optional[Dict[str, Any]] = None
    next_run_time: Optional[datetime] = None
    max_instances: Optional[int] = None
    description: Optional[str] = None


class TaskManageResponse(TaskManageBase):
    """Timed Task Response Model"""
    id: str
    trigger_args: Dict[str, Any]
    func_args: Dict[str, Any]
    create_time: datetime
    update_time: datetime


class TaskExecutionLog(SQLModel, table=True):
    """Task execution log table model"""
    __tablename__ = "task_execution_log"
    
    id: str = SQLField(primary_key=True)
    task_id: str = SQLField(foreign_key="task_manage.id", index=True)
    start_time: datetime = SQLField(default_factory=datetime.now)
    end_time: Optional[datetime] = SQLField(default=None)
    status: TaskStatus = SQLField(default=TaskStatus.RUNNING)
    result: Optional[str] = SQLField(default=None)
    error: Optional[str] = SQLField(default=None)


class TaskExecutionLogCreate(SQLModel):
    """Create a task execution log request model"""
    task_id: str
    status: TaskStatus = TaskStatus.RUNNING
    result: Optional[str] = None
    error: Optional[str] = None


class TaskExecutionLogResponse(SQLModel):
    """Task Execution Log Response Model"""
    id: str
    task_id: str
    start_time: datetime
    end_time: Optional[datetime]
    status: TaskStatus
    result: Optional[str]
    error: Optional[str] 