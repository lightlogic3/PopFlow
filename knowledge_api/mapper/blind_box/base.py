"""Blind Box Data Model"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from decimal import Decimal

# basic model
class BlindBoxBase(SQLModel):
    """Blind box basic model"""
    name: str = Field(..., description="Blind box name", max_length=100)
    description: Optional[str] = Field(None, description="Blind Box Description (Rich Text)")
    image_url: Optional[str] = Field(None, description="Blind box image URL", max_length=255)
    price: Optional[int] = Field(None, description="Blind box price (points)")
    probability_rules: str = Field(..., description="Probability rules (JSON format, including guarantee rules)")
    guarantee_count: Optional[int] = Field(None, description="guaranteed number of draws")
    guarantee_rarity: Optional[int] = Field(None, description="Guaranteed Rarity: 1-Common, 2-Rare, 3-Epic, 4-Legendary")
    status: int = Field(default=1, description="Status: 0-disabled, 1-normal")

# database model
class BlindBox(BlindBoxBase, table=True):
    """Blind Box Database Model"""
    __tablename__ = "blind_box"
    
    id: Optional[int] = Field(default=None, primary_key=True, description="blind box ID")
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
class BlindBoxCreate(BlindBoxBase):
    """Create a blind box model"""
    pass

# update model
class BlindBoxUpdate(SQLModel):
    """Update the blind box model"""
    name: Optional[str] = Field(None, description="Blind box name", max_length=100)
    description: Optional[str] = Field(None, description="Blind Box Description (Rich Text)")
    image_url: Optional[str] = Field(None, description="Blind box image URL", max_length=255)
    price: Optional[int] = Field(None, description="Blind box price (points)")
    probability_rules: Optional[str] = Field(None, description="Probability rules (JSON format)")
    guarantee_count: Optional[int] = Field(None, description="guaranteed number of draws")
    guarantee_rarity: Optional[int] = Field(None, description="guaranteed rarity")
    status: Optional[int] = Field(None, description="Status: 0-disabled, 1-normal")

# response model
class BlindBoxResponse(BlindBoxBase):
    """blind box response model"""
    id: int
    is_deleted: int
    creator_id: Optional[int]
    updater_id: Optional[int]
    create_time: datetime
    update_time: datetime

# filtering model
class BlindBoxFilter(SQLModel):
    """Blind box filtering model"""
    name: Optional[str] = Field(None, description="Blind box name")
    status: Optional[int] = Field(None, description="state")
    guarantee_rarity: Optional[int] = Field(None, description="guaranteed rarity")
    is_deleted: Optional[int] = Field(default=0, description="Whether to delete")

# Blind Box Card Association Model
class BlindBoxCardBase(SQLModel):
    """Blind Box Card Association Basic Model"""
    blind_box_id: int = Field(..., description="blind box ID")
    card_id: int = Field(..., description="Card ID")
    probability: Decimal = Field(..., description="% probability of winning")
    weight: int = Field(default=100, description="weight")
    is_special_reward: int = Field(default=0, description="Whether there is a special reward: 0-No, 1-Yes")

class BlindBoxCard(BlindBoxCardBase, table=True):
    """Blind Box Card Association Database Model"""
    __tablename__ = "blind_box_card"
    
    id: Optional[int] = Field(default=None, primary_key=True, description="primary key ID")
    creator_id: Optional[int] = Field(default=None, description="creator ID")
    updater_id: Optional[int] = Field(default=None, description="Updater ID")
    create_time: datetime = Field(default_factory=datetime.now, description="creation time")
    update_time: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"onupdate": datetime.now},
        description="update time"
    )

class BlindBoxCardCreate(BlindBoxCardBase):
    """Create a blind box card association model"""
    pass

class BlindBoxCardUpdate(SQLModel):
    """Update blind box card association model"""
    probability: Optional[Decimal] = Field(None, description="% probability of winning")
    weight: Optional[int] = Field(None, description="weight")
    is_special_reward: Optional[int] = Field(None, description="Is it a special reward?")

class BlindBoxCardResponse(BlindBoxCardBase):
    """Blind Box Card Association Response Model"""
    id: int
    creator_id: Optional[int]
    updater_id: Optional[int]
    create_time: datetime
    update_time: datetime

# rarity enumeration
GUARANTEE_RARITY_CHOICES = {
    1: "ordinary",
    2: "rare", 
    3: "epic",
    4: "legend"
} 