from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class RelationshipLevelBase(SQLModel):
    """Relationship Hierarchy Basic Model"""
    role_id: str = Field(description="Role ID")
    relationship_name: str = Field(description="relationship name")
    relationship_level: int = Field(description="relationship hierarchy")
    prompt_text: str = Field(description="Relational cue word")
    status: int = Field(default=1, description="Status: 1-enabled, 0-disabled")
    created_at: str = Field(description="founder")
    updated_at: str = Field(description="Update Person")

class RelationshipLevelCreate(RelationshipLevelBase):
    """Create a relationship hierarchy request model"""
    pass

class RelationshipLevelUpdate(SQLModel):
    """Update the relationship hierarchy request model"""
    relationship_name: Optional[str] = Field(None, description="relationship name")
    relationship_level: Optional[int] = Field(None, description="relationship hierarchy")
    prompt_text: Optional[str] = Field(None, description="Relational cue word")
    status: Optional[int] = Field(None, description="Status: 1-enabled, 0-disabled")
    updated_at: Optional[str] = Field(None, description="Update Person")

class RelationshipLevel(RelationshipLevelBase, table=True):
    """Relational hierarchical database model"""
    __tablename__ = "relationship_level"
    
    id: Optional[int] = Field(default=None, primary_key=True, description="primary key ID")
    create_time: datetime = Field(default_factory=datetime.now, description="creation time")
    updated_time: datetime = Field(default_factory=datetime.now, description="update time")

class RelationshipLevelResponse(RelationshipLevelBase):
    """hierarchical response model"""
    id: int = Field(description="primary key ID")
    create_time: datetime = Field(description="creation time")
    updated_time: datetime = Field(description="update time") 