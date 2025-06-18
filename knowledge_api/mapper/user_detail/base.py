from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import BaseModel


class UserDetailBase(SQLModel):
    """user details base model"""
    user_id: int = Field(..., description="user ID", index=True)
    total_points: int = Field(default=0, description="total integral")
    available_points: int = Field(default=0, description="available points")
    total_login_count: int = Field(default=0, description="total login count")
    total_ai_challenge_count: int = Field(default=0, description="Total number of AI challenges")
    total_ai_challenge_success_count: int = Field(default=0, description="Number of successful AI challenges")
    total_points_earned: int = Field(default=0, description="Total points earned")
    total_points_spent: int = Field(default=0, description="total spend points")
    total_card_count: int = Field(default=0, description="Total number of cards owned")
    total_blind_box_opened: int = Field(default=0, description="Total number of open blind boxes")
    last_active_time: Optional[datetime] = Field(default=None, description="Last active time")
    creator_id: Optional[int] = Field(default=None, description="creator ID")
    updater_id: Optional[int] = Field(default=None, description="Updater ID")


class UserDetail(UserDetailBase, table=True):
    """User Details Database Model"""
    __tablename__ = "user_detail"
    
    id: Optional[int] = Field(default=None, primary_key=True, description="primary key ID")
    create_time: datetime = Field(default_factory=datetime.now, description="creation time")
    update_time: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"onupdate": datetime.now},
        description="update time"
    )


class UserDetailCreate(UserDetailBase):
    """User details to create a model"""
    pass


class UserDetailUpdate(BaseModel):
    """user details update model"""
    total_points: Optional[int] = Field(None, description="total integral")
    available_points: Optional[int] = Field(None, description="available points")
    total_login_count: Optional[int] = Field(None, description="total login count")
    total_ai_challenge_count: Optional[int] = Field(None, description="Total number of AI challenges")
    total_ai_challenge_success_count: Optional[int] = Field(None, description="Number of successful AI challenges")
    total_points_earned: Optional[int] = Field(None, description="Total points earned")
    total_points_spent: Optional[int] = Field(None, description="total spend points")
    total_card_count: Optional[int] = Field(None, description="Total number of cards owned")
    total_blind_box_opened: Optional[int] = Field(None, description="Total number of open blind boxes")
    last_active_time: Optional[datetime] = Field(None, description="Last active time")
    updater_id: Optional[int] = Field(None, description="Updater ID")


class UserDetailFilter(BaseModel):
    """User details filtering model"""
    user_id: Optional[int] = Field(None, description="user ID")
    min_total_points: Optional[int] = Field(None, description="minimum total integral")
    max_total_points: Optional[int] = Field(None, description="Maximum Total Points")
    min_login_count: Optional[int] = Field(None, description="minimum login count")
    min_challenge_count: Optional[int] = Field(None, description="Minimum number of challenges")
    start_time: Optional[datetime] = Field(None, description="start time")
    end_time: Optional[datetime] = Field(None, description="end time")


class UserDetailResponse(UserDetailBase):
    """User Details Response Model"""
    id: int = Field(..., description="primary key ID")
    create_time: datetime = Field(..., description="creation time")
    update_time: datetime = Field(..., description="update time")
    
    # computational properties
    challenge_success_rate: Optional[float] = Field(None, description="challenge success rate")
    points_usage_rate: Optional[float] = Field(None, description="point usage")
    
    class Config:
        from_attributes = True


class UserDetailStatistics(BaseModel):
    """User Details Statistical Model"""
    total_users: int = Field(..., description="total users")
    total_points_in_system: int = Field(..., description="total system integral")
    average_points_per_user: float = Field(..., description="user average points")
    total_challenges: int = Field(..., description="total number of challenges")
    average_challenge_success_rate: float = Field(..., description="average challenge success rate")
    total_cards_in_system: int = Field(..., description="Total number of cards in the system")
    total_blind_boxes_opened: int = Field(..., description="Total blind box openings")
    most_active_users: list = Field(..., description="list of most active users") 