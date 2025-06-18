from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class RoleBase(SQLModel):
    """role-based model"""
    role_id: str = Field(..., max_length=36, description="Role unique ID personalization")
    name: str = Field(..., max_length=50, description="role name")
    sort: int = Field(default=1, description="Character Levels 1-5")
    image_url: Optional[str] = Field(None, max_length=255, description="character image URL")
    knowledge_count: int = Field(default=0, description="Number of knowledge items")
    role_type:str=Field("main",description="character type")
    tags:Optional[str]=Field("",description="character tag")
    llm_choose:Optional[str]=Field(...,description="Large model selection")
    worldview_control:Optional[str]=Field("",description="Worldview control")


class Role(RoleBase, table=True):
    """Role Database Model"""
    __tablename__ = "roles"

    id: str = Field(default=None, primary_key=True, max_length=36)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now})


class RoleCreate(RoleBase):
    """Create a role request model"""
    pass


class RoleUpdate(SQLModel):
    """Update the role request model"""
    name: Optional[str] = Field(None, max_length=50)
    sort: Optional[int] = None
    image_url: Optional[str] = Field(None, max_length=255)
    role_type:str=Field("main",description="character type")
    tags:Optional[str]=Field("",description="character tag")
    llm_choose:Optional[str]=Field(...,description="Large model selection")
    worldview_control:Optional[str]=Field("",description="Worldview control")


class RoleResponse(RoleBase):
    """Role Response Model"""
    id: str
    created_at: datetime
    updated_at: datetime
