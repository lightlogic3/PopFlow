from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

from knowledge_api.mapper.model_base import StandardModelBase


class AudioTimbreBase(SQLModel):
    """timbre base model"""
    alias: Optional[str] = Field(None, max_length=255, description="alias")
    speaker_id: Optional[str] = Field(None, max_length=64, description="Voice ID")
    version: Optional[str] = Field(None, max_length=32, description="training version")
    expire_time: Optional[datetime] = Field(None, description="sound expiration time")
    state: Optional[str] = Field(None, max_length=32, description="state")
    audition: Optional[str] = Field(None, description="Sound B64")


class AudioTimbre(AudioTimbreBase, StandardModelBase, table=True):
    """timbre database model"""
    __tablename__ = "llm_audio_timbre"

    id: Optional[int] = Field(default=None, primary_key=True)
    create_time: datetime = Field(default_factory=datetime.now)
    craete_at: Optional[str] = Field(None, max_length=255)  # Note: There are spelling errors in SQL, which are consistent here
    update_time: datetime = Field(default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now})
    update_at: Optional[str] = Field(None, max_length=255)


class AudioTimbreCreate(AudioTimbreBase):
    """Create a timbre request model"""
    craete_at: Optional[str] = Field(None, max_length=255)


class AudioTimbreUpdate(SQLModel):
    """Update the timbre request model"""
    alias: Optional[str] = Field(None, max_length=255)
    speaker_id: Optional[str] = Field(None, max_length=64)
    version: Optional[str] = Field(None, max_length=32)
    expire_time: Optional[datetime] = None
    state: Optional[str] = Field(None, max_length=32)
    audition: Optional[str] = None
    update_at: Optional[str] = Field(None, max_length=255)


class AudioTimbreResponse(AudioTimbreBase):
    """timbre response model"""
    id: int
    create_time: datetime
    craete_at: Optional[str]
    update_time: datetime
    update_at: Optional[str] 