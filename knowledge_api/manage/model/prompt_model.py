# api/models.py
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, HttpUrl, Field

class CharacterPromptConfigInput(BaseModel):
    """Role Input Model"""
    role_id: str = Field(..., description="Role ID")
    level: float = Field(..., description="grade")
    prompt_text: str = Field(..., description="prompt word content")
    prologue: Optional[List[str]] = Field(default=None, description="opening statement")
    dialogue: Optional[str] = Field(default="", description="Line example")
    timbre: Optional[str] = Field(default="", description="character timbre")
    status: int = Field(default=1, description="Status: 1-enabled 0-disabled")
    type:str=Field(default="role",description="Cue word template type")
    title:str=Field(default="",description="title")




class CharacterPromptConfigUpdateInput(BaseModel):
    """Role Input Model"""
    """Update prompt word configuration request model"""
    prompt_text: Optional[str] = Field(default=None, description="copywriting")
    status: Optional[int] = Field(default=1, description="state")
    prologue: Optional[List[str]] = Field(default=None, description="opening statement")
    dialogue: Optional[str] = Field(default="", description="Line example")
    timbre: Optional[str] = Field(default=None, description="character timbre")
    level: float = Field(..., description="grade")
    title:str=Field(default="",description="title")