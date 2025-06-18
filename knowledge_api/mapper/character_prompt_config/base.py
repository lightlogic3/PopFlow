# models.py
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field

from knowledge_api.mapper.prompt_prologue import PromptPrologue


class CharacterPromptConfigBase(SQLModel):
    """Role cue word configuration basic model"""
    role_id: str = Field(..., description="Role ID")
    level: float = Field(..., description="grade")
    prompt_text: str = Field(..., description="prompt word content")
    prologue: Optional[str] = Field(default="", description="opening statement")
    dialogue: Optional[str] = Field(default="", description="Line example")
    timbre: Optional[str] = Field(default="", description="character timbre")
    status: int = Field(default=1, description="Status: 1-enabled 0-disabled")
    type:str=Field(default="role",description="Tip word template type, role role, system system")
    title:Optional[str]=Field(default="",description="title")


class CharacterPromptConfig(CharacterPromptConfigBase, table=True):
    """Role cue word configuration database model"""
    __tablename__ = "character_prompt_config"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now})


class CharacterPromptConfigCreate(CharacterPromptConfigBase):
    """Create a prompt word configuration request model"""
    pass



class CharacterPromptConfigUpdate(SQLModel):
    """Update prompt word configuration request model"""
    prompt_text: Optional[str] = None
    status: Optional[int] = None
    dialogue: Optional[str] = Field(default="", description="Line example")
    timbre: Optional[str] = Field(default="", description="character timbre")
    level: float = Field(..., description="grade")
    title:Optional[str]=Field(default="",description="title")


class CharacterPromptConfigResponse(CharacterPromptConfigBase):
    """Cue word configuration response model"""
    id: int
    created_at: datetime
    updated_at: datetime
    prologue:Optional[List[PromptPrologue]]=Field(default=[])
