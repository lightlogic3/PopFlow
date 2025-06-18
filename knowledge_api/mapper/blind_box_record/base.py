from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class BlindBoxRecordBase(SQLModel):
    user_id: int = Field(..., description="user ID")
    blind_box_id: int = Field(..., description="blind box ID")
    card_id: int = Field(..., description="Card ID obtained")
    is_duplicate: bool = Field(default=False, description="Whether to duplicate: 0-no, 1-yes")
    points_gained: Optional[int] = Field(default=None, description="Points earned (valid when repeated)")
    is_guaranteed: bool = Field(default=False, description="Guaranteed trigger: 0-No, 1-Yes")
    is_special_reward: bool = Field(default=False, description="Whether there is a special reward: 0-No, 1-Yes")
    source_type: str = Field(..., description="Source type: purchase, reward, gift")
    source_id: Optional[int] = Field(default=None, description="Source ID (e.g. Challenge ID, Event ID, etc.)")
    creator_id: Optional[int] = Field(default=None, description="creator ID")


class BlindBoxRecord(BlindBoxRecordBase, table=True):
    __tablename__ = "blind_box_record"

    id: Optional[int] = Field(default=None, primary_key=True, description="primary key ID")
    create_time: datetime = Field(default_factory=datetime.now, description="creation time")


class BlindBoxRecordCreate(BlindBoxRecordBase):
    pass


class BlindBoxRecordUpdate(BaseModel):
    points_gained: Optional[int] = None
    is_special_reward: Optional[bool] = None


class BlindBoxRecordResponse(BlindBoxRecordBase):
    id: int
    create_time: datetime 