"""Card Series Data Model"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

# basic model
class CardSeriesBase(SQLModel):
    """Card Series Basic Model"""
    name: str = Field(..., description="Series name", max_length=50)
    code: str = Field(..., description="serial coding", max_length=50)
    description: Optional[str] = Field(None, description="series description", max_length=255)
    sort_order: int = Field(default=0, description="sort order")
    status: int = Field(default=1, description="Status: 0-disabled, 1-normal")

# database model
class CardSeries(CardSeriesBase, table=True):
    """Card Series Database Model"""
    __tablename__ = "card_series"
    
    id: Optional[int] = Field(default=None, primary_key=True, description="Series ID")
    is_deleted: int = Field(default=0, description="Whether to delete: 0-No, 1-Yes")
    creator_id: Optional[int] = Field(default=None, description="creator ID")
    updater_id: Optional[int] = Field(default=None, description="Updater ID")
    create_time: datetime = Field(default_factory=datetime.now, description="creation time")
    update_time: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"onupdate": datetime.now},
        description="update time"
    )

# Create a model
class CardSeriesCreate(CardSeriesBase):
    """Create a card series model"""
    pass

# update model
class CardSeriesUpdate(SQLModel):
    """Update the card series model"""
    name: Optional[str] = Field(None, description="Series name", max_length=50)
    code: Optional[str] = Field(None, description="serial coding", max_length=50)
    description: Optional[str] = Field(None, description="series description", max_length=255)
    sort_order: Optional[int] = Field(None, description="sort order")
    status: Optional[int] = Field(None, description="Status: 0-disabled, 1-normal")

# response model
class CardSeriesResponse(CardSeriesBase):
    """Card Series Response Model"""
    id: int
    is_deleted: int
    creator_id: Optional[int]
    updater_id: Optional[int]
    create_time: datetime
    update_time: datetime

# filtering model
class CardSeriesFilter(SQLModel):
    """Card series filtering model"""
    name: Optional[str] = Field(None, description="Series name")
    code: Optional[str] = Field(None, description="serial coding")
    status: Optional[int] = Field(None, description="state")
    is_deleted: Optional[int] = Field(default=0, description="Whether to delete") 