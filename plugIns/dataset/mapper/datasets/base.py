from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

# 数据集基础模型
class DatasetBase(SQLModel):
    """数据集基础模型"""
    name: str = Field(..., max_length=255, description="数据集名称")
    type: str = Field(..., max_length=50, description="数据集类型: SFT, CONVERSATION, FUNCTION_CALL, DPO, OTHER")
    description: Optional[str] = Field(None, description="数据集描述")
    tags: Optional[str] = Field(None, max_length=255, description="数据集标签，逗号分隔")

# 数据集数据库模型
class Dataset(DatasetBase, table=True):
    """数据集数据库模型"""
    __tablename__ = "datasets"
    
    id: int = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now})

# 请求和响应模型
class DatasetCreate(DatasetBase):
    """创建数据集请求模型"""
    pass

class DatasetUpdate(SQLModel):
    """更新数据集请求模型"""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None)
    tags: Optional[str] = Field(None, max_length=255)

class DatasetResponse(DatasetBase):
    """数据集响应模型"""
    id: int
    created_at: datetime
    updated_at: datetime 