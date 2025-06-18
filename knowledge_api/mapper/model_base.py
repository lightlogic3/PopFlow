"""database model base class"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class ModelBase(SQLModel):
    """Database model base class, containing commonly used public fields

All models that inherit this class automatically receive the following fields:
- id: primary key ID (declared in subclass when needed)
- create_time: Creation time
- update_time: Update time"""


class TimestampBase(SQLModel):
    """Database model base class with timestamp

Contains creation time and update time fields"""
    create_time: datetime = Field(default_factory=datetime.now, description="creation time")
    update_time: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"onupdate": datetime.now},
        description="update time"
    )
    create_user: Optional[str] = Field(default=None, description="creator")
    update_user: Optional[str] = Field(default=None, description="Updater")


class IDModelBase(ModelBase):
    """Database Model Base Class with Incremental ID

Models that inherit this class will automatically obtain integer-incrementing primary key IDs."""
    id: Optional[int] = Field(default=None, primary_key=True, description="primary key ID")


class StandardModelBase(IDModelBase, TimestampBase):
    """Standard database model base class

Includes ID and timestamp for most tables"""
    pass 