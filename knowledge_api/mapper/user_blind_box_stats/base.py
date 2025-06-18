from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class UserBlindBoxStatsBase(SQLModel):
    """Statistical Basic Model of User Blind Box Extraction"""
    user_id: int = Field(..., description="user ID")
    blind_box_id: int = Field(..., description="blind box ID")
    total_count: int = Field(default=0, description="total number of draws")
    last_guaranteed_time: Optional[datetime] = Field(default=None, description="Last guarantee time")
    current_count: int = Field(default=0, description="The current number of draws (from the last guarantee)")


class UserBlindBoxStats(UserBlindBoxStatsBase, table=True):
    """Statistical Model of User Blind Box Extraction"""
    __tablename__ = "user_blind_box_stats"
    
    id: Optional[int] = Field(default=None, primary_key=True, description="primary key ID")
    creator_id: Optional[int] = Field(default=None, description="creator ID")
    updater_id: Optional[int] = Field(default=None, description="Updater ID")
    create_time: datetime = Field(default_factory=datetime.now, description="creation time")
    update_time: datetime = Field(default_factory=datetime.now, description="update time")


class UserBlindBoxStatsCreate(UserBlindBoxStatsBase):
    """User Blind Box Extraction Statistical Creation Model"""
    creator_id: Optional[int] = None


class UserBlindBoxStatsUpdate(SQLModel):
    """Statistical Update Model for User Blind Box Extraction"""
    total_count: Optional[int] = None
    last_guaranteed_time: Optional[datetime] = None
    current_count: Optional[int] = None
    updater_id: Optional[int] = None 