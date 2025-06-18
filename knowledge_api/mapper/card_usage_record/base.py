from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class CardUsageRecordBase(SQLModel):
    user_id: int = Field(..., description="user ID")
    card_id: int = Field(..., description="Card ID")
    usage_type: str = Field(..., description="Type of use: ai_challenge-AI challenge, chat-normal chat")
    related_id: Optional[str] = Field(default=None, description="Association ID (e.g. Challenge ID, Session ID, etc.)")
    start_time: datetime = Field(..., description="start time")
    end_time: Optional[datetime] = Field(default=None, description="end of use time")
    points_earned: Optional[int] = Field(default=None, description="points earned")
    creator_id: Optional[int] = Field(default=None, description="creator ID")
    game_status: int = Field(default=0, description="Game status, 0 default status, 1 win, 2 lose")
    blind_box_id: int = Field(default=-1, description="Get the blind box after winning, depending on the probability -1 means no blind box was obtained.")
    blind_box_record_id: Optional[int] = Field(default=None, description="Open blind box record _Id")


class CardUsageRecord(CardUsageRecordBase, table=True):
    __tablename__ = "card_usage_record"

    id: Optional[int] = Field(default=None, primary_key=True, description="primary key ID")
    create_time: datetime = Field(default_factory=datetime.now, description="creation time")


class CardUsageRecordCreate(CardUsageRecordBase):
    pass


class CardUsageRecordUpdate(BaseModel):
    end_time: Optional[datetime] = None
    points_earned: Optional[int] = None
    game_status: Optional[int] = None
    blind_box_id: Optional[int] = None
    blind_box_record_id: Optional[int] = None


class CardUsageRecordResponse(CardUsageRecordBase):
    id: int
    create_time: datetime 