from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, UniqueConstraint


class RolesWorldBase(SQLModel):
    """Roles and Worldview Association Basic Model"""
    world_konwledge_id: str = Field(..., max_length=64, description="World view knowledge point ID")
    role_id: str = Field(..., max_length=255, description="Role ID")
    world_id: str = Field(..., description="World ID")
    create_at: Optional[str] = Field(None, max_length=64, description="creator")
    update_at: Optional[str] = Field(None, max_length=64, description="Updater")


class RolesWorld(RolesWorldBase, table=True):
    """Role World Associated Database Model"""
    __tablename__ = "roles_world"
    
    id: int = Field(default=None, primary_key=True)
    create_time: Optional[datetime] = Field(default_factory=datetime.now)
    
    # Set joint unique constraints
    __table_args__ = (
        UniqueConstraint("role_id", "world_konwledge_id", name="uix_role_world_knowledge"),
    )


class RolesWorldCreate(SQLModel):
    """Create a role world association request model"""
    world_konwledge_id: str
    role_id: str
    world_id: str
    create_at: Optional[str] = None
    update_at: Optional[str] = None


class RolesWorldUpdate(SQLModel):
    """Update the Role World Association Request Model"""
    world_konwledge_id: Optional[str] = None
    role_id: Optional[str] = None
    world_id: Optional[str] = None
    update_at: Optional[str] = None


class RolesWorldResponse(RolesWorldBase):
    """Role world relational response model"""
    id: int
    create_time: datetime 