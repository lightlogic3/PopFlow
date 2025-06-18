from datetime import datetime
from typing import Dict, Any
from sqlmodel import SQLModel, Field, JSON

# DPO条目基础模型
class DpoEntryBase(SQLModel):
    """DPO条目基础模型"""
    dataset_id: int = Field(..., description="所属数据集ID")
    query: str = Field(..., description="查询/问题内容")
    chosen_response: str = Field(..., description="首选回复")
    rejected_response: str = Field(..., description="被拒绝的回复")

# DPO条目数据库模型
class DpoEntry(DpoEntryBase, table=True):
    """DPO条目数据库模型"""
    __tablename__ = "dpo_entries"
    
    id: int = Field(default=None, primary_key=True)
    raw_data: Dict[str, Any] = Field(..., description="完整原始数据", sa_type=JSON)
    created_at: datetime = Field(default_factory=datetime.now)

# 请求和响应模型
class DpoEntryCreate(DpoEntryBase):
    """创建DPO条目请求模型"""
    raw_data: Dict[str, Any] = Field(..., description="完整原始数据")

class DpoEntryResponse(DpoEntryBase):
    """DPO条目响应模型"""
    id: int
    raw_data: Dict[str, Any]
    created_at: datetime 