from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlmodel import Field, SQLModel, JSON
from pydantic import BaseModel


class GamePlayTypeBase(SQLModel):
    """Game Type Basic Model"""
    name: str = Field(..., description="Game Type Name")
    description: Optional[str] = Field(default=None, description="Game description")
    setting: Optional[str] = Field(default=None, description="Game settings")
    reference_case: Optional[str] = Field(default=None, description="Reference case")
    game_play_type: Optional[str] = Field(default=None, description="Business ID corresponds to code path")
    form_schema: Optional[Dict[str, Any]] = Field(default=None, description="form structure definition", sa_type=JSON)
    ui_schema: Optional[Dict[str, Any]] = Field(default=None, description="UI rendering related configuration", sa_type=JSON)
    validation_schema: Optional[Dict[str, Any]] = Field(default=None, description="form validation rules", sa_type=JSON)
    version: Optional[str] = Field(default=None, description="version number")
    additional_content: Optional[Dict[str, Any]] = Field(default=None, description="additional content", sa_type=JSON)
    status: Optional[int] = Field(default=1, description="Status: 0-disabled, 1-enabled")
    game_number_max: int = Field(default=2, description="Maximum number of people in the game")
    game_number_min: int = Field(default=1, description="Minimum number of people in the game")


class GamePlayType(GamePlayTypeBase, table=True):
    """Game Type Database Model"""
    __tablename__ = "game_play_type"

    id: Optional[int] = Field(default=None, primary_key=True, description="Game Type ID")
    created_at: str = Field(default=None)
    updated_at: str = Field(default=None)

    class Config:
        """table configuration"""
        schema_extra = {
            "sa_column_kwargs": {
                "game_play_type": {
                    "unique": True
                }
            }
        }


class GamePlayTypeCreate(GamePlayTypeBase):
    """Create a request model for game types"""
    role_relations: Optional[List[dict]] = None  # role association list


class GamePlayTypeUpdate(BaseModel):
    """Update the request model for game types"""
    name: Optional[str] = None
    description: Optional[str] = None
    setting: Optional[str] = None
    reference_case: Optional[str] = None
    game_play_type: Optional[str] = None
    form_schema: Optional[Dict[str, Any]] = None
    ui_schema: Optional[Dict[str, Any]] = None
    validation_schema: Optional[Dict[str, Any]] = None
    version: Optional[str] = None
    additional_content: Optional[Dict[str, Any]] = None
    status: Optional[int] = None
    game_number_max: Optional[int] = None
    game_number_min: Optional[int] = None
    role_relations: Optional[List[dict]] = None  # role association list


class GamePlayTypeResponse(GamePlayTypeBase):
    """Game Type Response Model"""
    id: int
    created_at: Optional[str]
    updated_at: Optional[str] 