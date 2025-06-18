from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, JSON

# SFT条目基础模型
class SftEntryBase(SQLModel):
    """SFT条目基础模型"""
    dataset_id: int = Field(..., description="所属数据集ID")
    instruction: str = Field(..., description="指令内容")
    input: Optional[str] = Field(None, description="输入内容")
    output: str = Field(..., description="输出内容")

# SFT条目数据库模型
class SftEntry(SftEntryBase, table=True):
    """SFT条目数据库模型"""
    __tablename__ = "sft_entries"
    
    id: int = Field(default=None, primary_key=True)
    raw_data: Dict[str, Any] = Field(..., description="完整原始数据", sa_type=JSON)
    created_at: datetime = Field(default_factory=datetime.now)

# 请求和响应模型
class SftEntryCreate(SftEntryBase):
    """创建SFT条目请求模型"""
    raw_data: Dict[str, Any] = Field(..., description="完整原始数据")

class SftEntryResponse(SftEntryBase):
    """SFT条目响应模型"""
    id: int
    raw_data: Dict[str, Any]
    created_at: datetime 