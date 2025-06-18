# api/models.py
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, HttpUrl, Field



class AutoTaskMode(BaseModel):
    """automated task mode"""
    task_id: str = Field(..., description="Task ID")
    number: int = Field(..., description="number of tasks")
    regular_time:bool = Field(default=False,description="timed task")
    task_time: Optional[datetime] = Field(None, description="task trigger time")