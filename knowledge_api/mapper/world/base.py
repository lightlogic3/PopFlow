from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class WorldBase(SQLModel):
    """World view basic model"""
    title: str = Field(..., max_length=100, description="Worldview title")
    type: str = Field(..., max_length=50, description="Worldview type")
    description: str = Field(..., description="Worldview description")
    image_url: Optional[str] = Field(None, max_length=255, description="image URL")
    sort: int = Field(default=0, description="sort")
    knowledge_count: int = Field(default=0, description="Number of knowledge items")

class World(WorldBase, table=True):
    """World View Database Model"""
    __tablename__ = "worlds"

    id: str = Field(default=None, primary_key=True, max_length=36)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now})

class WorldCreate(WorldBase):
    """Create a worldview request model"""
    pass

class WorldUpdate(SQLModel):
    """Update Worldview Request Model"""
    title: Optional[str] = Field(None, max_length=100)
    type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=255)
    sort: Optional[int] = None
    knowledge_count: Optional[int] = None

class WorldResponse(WorldBase):
    """Worldview Response Model"""
    id: str
    created_at: datetime
    updated_at: datetime