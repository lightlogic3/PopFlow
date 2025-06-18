from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


class UserCardBase(SQLModel):
    user_id: int = Field(..., description="user ID")
    card_id: int = Field(..., description="Card ID")
    obtain_type: str = Field(..., description="Obtaining method: points - points to unlock, blind_box - blind box to get")
    obtain_time: datetime = Field(default_factory=datetime.now, description="acquisition time")
    use_count: int = Field(default=0, description="number of uses")
    last_use_time: Optional[datetime] = Field(default=None, description="Last Usage Time")
    is_favorite: bool = Field(default=False, description="Whether to collect: 0-No, 1-Yes")
    creator_id: Optional[int] = Field(default=None, description="creator ID")


class UserCard(UserCardBase, table=True):
    __tablename__ = "user_card"

    id: Optional[int] = Field(default=None, primary_key=True, description="primary key ID")
    create_time: datetime = Field(default_factory=datetime.now, description="creation time")
    update_time: datetime = Field(default_factory=datetime.now, description="update time")


class UserCardCreate(UserCardBase):
    pass


class UserCardUpdate(BaseModel):
    use_count: Optional[int] = None
    last_use_time: Optional[datetime] = None
    is_favorite: Optional[bool] = None


class UserCardResponse(UserCardBase):
    id: int
    create_time: datetime
    update_time: datetime 