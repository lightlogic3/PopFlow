"""Card Data Model"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


# basic model
class CardBase(SQLModel):
    """Card Basic Model"""
    name: str = Field(..., description="Card Name", max_length=100)
    series_id: int = Field(..., description="Card Series ID")
    rarity: int = Field(default=1, description="Rarity: 1-Common, 2-Rare, 3-Epic, 4-Legendary")
    description: Optional[str] = Field(None, description="Card Description (Rich Text)")
    image_url: Optional[str] = Field(None, description="Card image URL", max_length=255)
    sort_order: int = Field(default=0, description="sort order")
    unlock_type: str = Field(..., description="Unlock type: both-points and blind box unlock, box_only-only blind box unlock", max_length=50)
    points_required: Optional[int] = Field(None, description="Points purchase price (valid unlock_type both)")
    duplicate_points: int = Field(default=1000, description="Integrals converted on repeated acquisition")
    status: int = Field(default=1, description="Status: 0-disabled, 1-normal")
    role_id: Optional[str] = Field(None, description="Role ID", max_length=36)
    blind_box_id: Optional[int] = Field(None, description="Bind blind box ID")
    box_drop_rate: Optional[float] = Field(default=5, description="Blind box drop probability (%)")
    victory_points: Optional[int] = Field(default=100, description="Earn points for victory")
    game_cost_points: Optional[int] = Field(default=10, description="Game deduction points")
    limited_count: Optional[int] = Field(None, description="Limited number of draws: NULL means unlimited, and the number means the limited number of draws for the whole server")
    is_limited: int = Field(default=0, description="Whether to qualify the card: 0-No, 1-Yes")


class CardAlg(CardBase):
    """Create a card model"""
    id: int = Field(default=1, description="Status: 0-disabled, 1-normal")
    weight: int = Field(default=1, description="Status: 0-disabled, 1-normal")
    series_id: int = Field(default=0, description="Series ID")
    unlock_type: int = Field(default=0, description="Unlock type")


# database model
class Card(CardBase, table=True):
    """Card Database Model"""
    __tablename__ = "card"

    id: Optional[int] = Field(default=None, primary_key=True, description="Card ID")
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
class CardCreate(CardBase):
    """Create a card model"""
    pass


# update model
class CardUpdate(SQLModel):
    """Update Card Model"""
    name: Optional[str] = Field(None, description="Card Name", max_length=100)
    series_id: Optional[int] = Field(None, description="Card Series ID")
    rarity: Optional[int] = Field(None, description="Rarity: 1-Common, 2-Rare, 3-Epic, 4-Legendary")
    description: Optional[str] = Field(None, description="Card Description (Rich Text)")
    image_url: Optional[str] = Field(None, description="Card image URL", max_length=255)
    sort_order: Optional[int] = Field(None, description="sort order")
    unlock_type: Optional[str] = Field(None, description="Unlock type", max_length=50)
    points_required: Optional[int] = Field(None, description="Points purchase price")
    duplicate_points: Optional[int] = Field(None, description="Integrals converted on repeated acquisition")
    status: Optional[int] = Field(None, description="Status: 0-disabled, 1-normal")
    role_id: Optional[str] = Field(None, description="Role ID", max_length=36)
    blind_box_id: Optional[int] = Field(None, description="Bind blind box ID")
    box_drop_rate: Optional[float] = Field(None, description="Blind box drop probability (%)")
    victory_points: Optional[int] = Field(None, description="Earn points for victory")
    game_cost_points: Optional[int] = Field(None, description="Game deduction points")
    limited_count: Optional[int] = Field(None, description="limited number of times")
    is_limited: Optional[int] = Field(None, description="Whether to qualify the card: 0-No, 1-Yes")


# response model
class CardResponse(CardBase):
    """Card Response Model"""
    id: int
    is_deleted: int
    creator_id: Optional[int]
    updater_id: Optional[int]
    create_time: datetime
    update_time: datetime


# filtering model
class CardFilter(SQLModel):
    """Card filtering model"""
    name: Optional[str] = Field(None, description="Card Name")
    series_id: Optional[int] = Field(None, description="Card Series ID")
    rarity: Optional[int] = Field(None, description="rarity")
    unlock_type: Optional[str] = Field(None, description="Unlock type")
    status: Optional[int] = Field(None, description="state")
    role_id: Optional[str] = Field(None, description="Role ID")
    blind_box_id: Optional[int] = Field(None, description="Bind blind box ID")
    is_limited: Optional[int] = Field(None, description="Whether to qualify the card")
    is_deleted: Optional[int] = Field(default=0, description="Whether to delete")


# rarity enumeration
RARITY_CHOICES = {
    1: "ordinary",
    2: "rare",
    3: "epic",
    4: "legend"
}

# Unlock type enumeration
UNLOCK_TYPE_CHOICES = {
    "both": "Points and blind box unlock",
    "box_only": "Only the blind box can be unlocked."
}
