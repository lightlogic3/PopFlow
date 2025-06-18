from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class LimitedCardStatsBase(SQLModel):
    """Basic Statistical Model of Limited Card Extraction"""
    card_id: int = Field(..., description="Limited Card ID")
    total_drawn_count: int = Field(default=0, description="The number of draws in the whole server")
    remaining_count: int = Field(default=0, description="remaining extractable times")
    is_sold_out: bool = Field(default=False, description="Sold out: 0-No, 1-Yes")
    first_drawn_time: Optional[datetime] = Field(default=None, description="first draw time")
    last_drawn_time: Optional[datetime] = Field(default=None, description="Last draw time")


class LimitedCardStats(LimitedCardStatsBase, table=True):
    """Statistical Model of Limited Card Extraction"""
    __tablename__ = "limited_card_stats"
    
    id: Optional[int] = Field(default=None, primary_key=True, description="primary key ID")
    creator_id: Optional[int] = Field(default=None, description="creator ID")
    updater_id: Optional[int] = Field(default=None, description="Updater ID")
    create_time: datetime = Field(default_factory=datetime.now, description="creation time")
    update_time: datetime = Field(default_factory=datetime.now, description="update time")


class LimitedCardStatsCreate(LimitedCardStatsBase):
    """Statistical Creation Model for Limited Card Extraction"""
    creator_id: Optional[int] = None


class LimitedCardStatsUpdate(SQLModel):
    """Statistical Update Model of Limited Card Extraction"""
    total_drawn_count: Optional[int] = None
    remaining_count: Optional[int] = None
    is_sold_out: Optional[bool] = None
    first_drawn_time: Optional[datetime] = None
    last_drawn_time: Optional[datetime] = None
    updater_id: Optional[int] = None 