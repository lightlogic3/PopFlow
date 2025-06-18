from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, SQLModel


class SystemConfigBase(SQLModel):
    """System Configuration Foundation Model"""
    config_key: str = Field(..., max_length=50, description="configuration key name")
    config_value: Optional[str] = Field(None, description="configuration value")
    description: Optional[str] = Field(None, max_length=255, description="configuration description")
    item_type:Optional[str]=Field("string",description="configuration type")
    use_type:Optional[str]=Field("system",description="type of use")


class SystemConfig(SystemConfigBase, table=True):
    """System configuration database model"""
    __tablename__ = "system_configs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    create_time: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"server_default": "CURRENT_TIMESTAMP"},
        description="creation time"
    )
    update_time: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={
            "server_default": "CURRENT_TIMESTAMP",
            "server_onupdate": "CURRENT_TIMESTAMP",
        },
        description="update time"
    )
    
    class Config:
        table_name = "system_configs"


class SystemConfigCreate(SystemConfigBase):
    """Create a system configuration request model"""
    pass


class SystemConfigUpdate(SQLModel):
    """Update the system configuration request model"""
    config_key: Optional[str] = Field(None, description="configuration key name")
    config_value: Optional[str] = Field(None, description="configuration value")
    description: Optional[str] = Field(None, max_length=255, description="configuration description")
    item_type:Optional[str]=Field("string",description="configuration type")
    use_type:Optional[str]=Field("system",description="type of use")


class SystemConfigResponse(SystemConfigBase):
    """System Configuration Response Model"""
    id: int
    create_time: datetime
    update_time: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SystemConfigBulkUpdate(SQLModel):
    """Batch update configuration request model"""
    configs: List[SystemConfigCreate]