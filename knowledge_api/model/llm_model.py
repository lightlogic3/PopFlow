from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from knowledge_api.mapper.role_subtasks import RoleSubtask
from knowledge_api.mapper.role_tasks.base import RoleTask


class ChatTestInput(BaseModel):
    """chat input model"""
    way: str = Field("half", description="half 半流方式输出，all，全流输出")
    message: str = Field(..., description="user message")
    role_id: str = Field(..., description="role unique identifier")
    level: float = Field(..., description="character level")
    user_level: float = Field(..., description="user level")
    user_name:str=Field(...,description="user name")
    session_id: Optional[str] = Field(None, description="Session ID, create a new session for null")
    top_k: Optional[int] = Field(3, description="Number of similar documents retrieved")
    temperature: Optional[float] = Field(0.7, description="generation temperature")
    role_prompt: str = Field(..., description="role cue")
    role_prologue: str = Field(..., description="character opener")
    role_dialogue: str = Field(..., description="Character line setting")
    relationship_level:int=Field(1,description="relationship hierarchy")
    user_id:Optional[str]=Field("",description="user unique identity")
    # Is long-term memory switched on?
    long_term_memory: Optional[bool] = Field(default=False, description="Is long-term memory switched on?")
    # memory level
    memory_level: Optional[int] = Field(default=6, description="Memory level, 6 is dialogue memory, 7 is memory 0, and 10 is dialogue memory")


class ChatTaskInput(BaseModel):
    """chat input model"""
    message: str = Field(..., description="user message")
    role_id: str = Field(..., description="role unique identifier")
    user_level: float = Field(..., description="user level")
    session_id: Optional[str] = Field(None, description="Session ID, create a new session for null")
    top_k: Optional[int] = Field(3, description="Number of similar documents retrieved")
    temperature: Optional[float] = Field(0.7, description="generation temperature")
    user_id: Optional[str] = Field("", description="user unique identity")
    # Is long-term memory switched on?
    long_term_memory: Optional[bool] = Field(default=False, description="Is long-term memory switched on?")
    # memory level
    memory_level: Optional[int] = Field(default=6, description="Memory level, 6 is dialogue memory, 7 is memory 0, and 10 is dialogue memory")

    level: float = Field(1.0, description="user level")
    user_name: str = Field("Xiaobai", description="user level")
    relationship_level:int=Field(1,description="relationship hierarchy")

    taskDescription: str = Field(..., description="task description")
    taskGoal: str = Field(..., description="mission objective")
    scoreRange: str = Field(..., description="Fractional addition and subtraction range")
    maxRounds: int = Field(..., description="maximum number of conversations")
    targetScore: int = Field(..., description="Target score")
    taskLevel: int = Field(..., description="target level")
    taskPersonality: str = Field(..., description="character setting")
    hideDesigns: str = Field(default="", description="Hide settings")
    taskType: str = Field(default="system_task", description="type setting")
    task_goal_judge:str=Field(default="",description="AI judgment standard")



class ChatStoryInput(BaseModel):
    """chat input model"""
    message: str = Field(..., description="user message")
    role_id: str = Field(..., description="role unique identifier")
    user_level: float = Field(..., description="user level")
    session_id: Optional[str] = Field(None, description="Session ID, create a new session for null")
    top_k: Optional[int] = Field(3, description="Number of similar documents retrieved")
    temperature: Optional[float] = Field(0.7, description="generation temperature")

    input_type: str = Field("chat", description="chat type")  # Chat normal chat chooes user selection
    user_design: str = Field(..., description="user settings")


class ChatSubTaskInput(BaseModel):
    """chat input model"""
    message: str = Field(..., description="user message")
    top_k: Optional[int] = Field(3, description="Number of similar documents retrieved")

    role_id: str = Field('', description="Role unique identifier (background injection)")
    user_level: float = Field(..., description="user level")
    session_id: Optional[str] = Field(None, description="Session ID, create a new session for null (background injection)")

    temperature: Optional[float] = Field(0.7, description="generation temperature")
    user_id: Optional[str] = Field("", description="user unique identity")

    level: float = Field(1.0, description="user level")
    user_name: str = Field("Xiaobai", description="user level")
    relationship_level:int=Field(1,description="relationship hierarchy")

    task_sup_id:str = Field("", description="The user can customize the subtask ID (optional).")



class SubTask(BaseModel):
    """Reassemble task"""
    taskDescription: str = Field(..., description="task description")
    taskGoal: str = Field(..., description="mission objective")
    scoreRange: str = Field(..., description="Fractional addition and subtraction range")
    targetScore: int = Field(..., description="Target score")
    taskPersonality: str = Field(..., description="character setting")
    hideDesigns: str = Field(default="", description="Hide settings")
    taskType: str = Field(default="system_task", description="type setting")
    task_goal_judge:str=Field(default="",description="AI judgment standard")


class TaskSessions(BaseModel):
    """task session"""
    task: RoleTask = Field(..., description="task")
    session_id: Optional[str] = Field(None, description="Session ID")
    sup_task_id: str = Field("", description="subtask ID")
    is_new_task: bool = Field(False, description="Is it a new task?")
    # list of historical conversations
    history: list[Dict[str, Any]] = Field(default_factory=list, description="list of historical conversations")



class SkipTask(BaseModel):
    """skip task"""
    user_id: str
    subtask_id: str
