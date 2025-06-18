from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class PromptPrologueBase(SQLModel):
    """Cue word opening statement basic model"""
    prompt_id: Optional[int] = Field(None, description="Cue Relation ID")
    prologue: Optional[str] = Field(None, max_length=500, description="opening statement")
    create_at: Optional[str] = Field(None, max_length=255, description="creator")


class PromptPrologue(PromptPrologueBase, table=True):
    """Cue opening line database model"""
    __tablename__ = "prompt_prologue"

    id: Optional[int] = Field(default=None, primary_key=True)
    create_time: Optional[datetime] = Field(default_factory=datetime.now)


class PromptPrologueCreate(PromptPrologueBase):
    """Create a prompt opening line request model"""
    pass


class PromptPrologueUpdate(SQLModel):
    """Update prompt word opener request model"""
    prompt_id: Optional[int] = None
    prologue: Optional[str] = Field(None, max_length=500)
    create_at: Optional[str] = Field(None, max_length=255)


class PromptPrologueResponse(PromptPrologueBase):
    """Cue Word Opening Response Model"""
    id: int
    create_time: datetime 