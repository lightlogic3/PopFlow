from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel
from pydantic import BaseModel


class GameCharacterRelationBase(SQLModel):
    """Game Character Association Basic Model"""
    game_id: int = Field(..., description="Game ID")
    role_id: str = Field(..., description="Role ID")
    llm_provider: Optional[str] = Field(default=None, description="Large model provider")
    llm_model: Optional[str] = Field(default=None, description="role model")
    voice: Optional[str] = Field(default=None, description="timbre")
    character_setting: Optional[str] = Field(default=None, description="role setting")


class GameCharacterRelation(GameCharacterRelationBase, table=True):
    """Game Character Associated Database Model"""
    __tablename__ = "game_character_relations"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GameCharacterRelationCreate(GameCharacterRelationBase):
    """Create a request model for game character associations"""
    pass


class GameCharacterRelationUpdate(BaseModel):
    """Update the request model for game character associations"""
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    voice: Optional[str] = None
    character_setting: Optional[str] = None


class GameCharacterRelationResponse(GameCharacterRelationBase):
    """Game Character Correlation Response Model"""
    id: int
    created_at: datetime 