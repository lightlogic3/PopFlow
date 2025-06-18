from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import BaseModel
from enum import Enum


class PointChangeType(str, Enum):
    """integral variation type enumeration"""
    REGISTER = "register"                    # sign-up bonus
    AI_CHALLENGE = "ai_challenge"           # AI challenge reward
    UNLOCK_CARD = "unlock_card"             # Unlock Card
    DUPLICATE_CARD = "duplicate_card"       # Repeat card
    BUY_BLIND_BOX = "buy_blind_box"         # Buy the blind box.
    ADMIN_ADJUST = "admin_adjust"           # administrator adjustment
    SYSTEM_REWARD = "system_reward"         # System reward
    DAILY_CHECK = "daily_check"             # daily check-in
    TASK_REWARD = "task_reward"             # mission reward
    EVENT_REWARD = "event_reward"           # event reward
    CARD_SELL = "card_sell"                 # Sell Cards
    CARD_UPGRADE = "card_upgrade"           # Card upgrade consumption
    SHOP_PURCHASE = "shop_purchase"         # store buy
    REFUND = "refund"                       # refund
    PENALTY = "penalty"                     # penalty deduction


class PointRecordBase(SQLModel):
    """Integral Record Basic Model"""
    user_id: int = Field(..., description="user ID", index=True)
    change_amount: int = Field(..., description="Number of changes (positive increase, negative decrease)")
    current_amount: int = Field(..., description="Number of points after change")
    change_type: PointChangeType = Field(..., description="change type", index=True)
    related_id: Optional[int] = Field(default=None, description="Associated ID (e.g. Challenge ID, Task ID, etc.)")
    card_id: Optional[int] = Field(default=None, description="Associated Card ID", index=True)
    description: Optional[str] = Field(default=None, description="describe", max_length=255)
    creator_id: Optional[int] = Field(default=None, description="creator ID")


class PointRecord(PointRecordBase, table=True):
    """Integral Record Database Model"""
    __tablename__ = "point_record"
    
    id: Optional[int] = Field(default=None, primary_key=True, description="primary key ID")
    create_time: datetime = Field(default_factory=datetime.now, description="creation time", index=True)


class PointRecordCreate(PointRecordBase):
    """Integral record creation model"""
    pass


class PointRecordUpdate(BaseModel):
    """Integral record update model (general integral records are not allowed to be modified, only for special cases)"""
    description: Optional[str] = Field(None, description="describe", max_length=255)


class PointRecordFilter(BaseModel):
    """Integral record filtering model"""
    user_id: Optional[int] = Field(None, description="user ID")
    change_type: Optional[PointChangeType] = Field(None, description="change type")
    card_id: Optional[int] = Field(None, description="Associated Card ID")
    related_id: Optional[int] = Field(None, description="Association ID")
    min_amount: Optional[int] = Field(None, description="Minimum number of changes")
    max_amount: Optional[int] = Field(None, description="Maximum number of changes")
    start_time: Optional[datetime] = Field(None, description="start time")
    end_time: Optional[datetime] = Field(None, description="end time")


class PointRecordResponse(PointRecordBase):
    """Integral Record Response Model"""
    id: int = Field(..., description="primary key ID")
    create_time: datetime = Field(..., description="creation time")
    
    # extended field
    change_type_display: Optional[str] = Field(None, description="Change type display name")
    is_income: bool = Field(..., description="Is it income (positive)?")
    
    class Config:
        from_attributes = True


class PointRecordStatistics(BaseModel):
    """Integral Record Statistical Model"""
    total_records: int = Field(..., description="total number of records")
    total_income: int = Field(..., description="Gross Revenue Points")
    total_expense: int = Field(..., description="total spend points")
    net_change: int = Field(..., description="net change")
    most_common_type: str = Field(..., description="The most common types of changes")
    avg_change_amount: float = Field(..., description="Average change")
    daily_stats: list = Field(..., description="Daily statistics")
    type_distribution: dict = Field(..., description="type distribution statistics")


class PointRecordBatchCreate(BaseModel):
    """Batch creation of integral record models"""
    records: list[PointRecordCreate] = Field(..., description="list of points")
    description: Optional[str] = Field(None, description="bulk operation description")


# Integral Variation Type Display Name Mapping
POINT_CHANGE_TYPE_DISPLAY = {
    PointChangeType.REGISTER: "sign-up bonus",
    PointChangeType.AI_CHALLENGE: "AI challenge reward",
    PointChangeType.UNLOCK_CARD: "Unlock Card",
    PointChangeType.DUPLICATE_CARD: "Repeat card",
    PointChangeType.BUY_BLIND_BOX: "Buy the blind box.",
    PointChangeType.ADMIN_ADJUST: "administrator adjustment",
    PointChangeType.SYSTEM_REWARD: "System reward",
    PointChangeType.DAILY_CHECK: "daily check-in",
    PointChangeType.TASK_REWARD: "mission reward",
    PointChangeType.EVENT_REWARD: "event reward",
    PointChangeType.CARD_SELL: "Sell Cards",
    PointChangeType.CARD_UPGRADE: "Card Upgrade",
    PointChangeType.SHOP_PURCHASE: "store buy",
    PointChangeType.REFUND: "refund",
    PointChangeType.PENALTY: "penalty deduction",
} 