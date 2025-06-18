from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlmodel import SQLModel, Field, JSON

# 对话条目基础模型
class ConversationEntryBase(SQLModel):
    """对话条目基础模型"""
    dataset_id: int = Field(..., description="所属数据集ID")
    conversation_id: str = Field(..., max_length=100, description="对话ID，用于分组多轮对话")
    sequence_order: int = Field(..., description="消息在对话中的顺序")
    role: str = Field(..., max_length=50, description="角色：system, user, assistant, tool")
    content: Optional[str] = Field(None, description="消息内容")
    has_tool_calls: bool = Field(default=False, description="是否包含工具调用")
    tool_name: Optional[str] = Field(None, max_length=255, description="工具名称，当role为tool时使用")
    loss_weight: Optional[float] = Field(default=1.0, description="损失权重")

# 对话条目数据库模型
class ConversationEntry(ConversationEntryBase, table=True):
    """对话条目数据库模型"""
    __tablename__ = "conversation_entries"
    
    id: int = Field(default=None, primary_key=True)
    tool_calls: Optional[Dict[str, Any]] = Field(None, description="工具调用数据", sa_type=JSON)
    raw_message: Dict[str, Any] = Field(..., description="原始消息完整数据", sa_type=JSON)
    created_at: datetime = Field(default_factory=datetime.now)

# 请求和响应模型
class ConversationEntryCreate(ConversationEntryBase):
    """创建对话条目请求模型"""
    tool_calls: Optional[Dict[str, Any]] = Field(None, description="工具调用数据")
    raw_message: Dict[str, Any] = Field(..., description="原始消息完整数据")

class ConversationEntryResponse(ConversationEntryBase):
    """对话条目响应模型"""
    id: int
    tool_calls: Optional[Dict[str, Any]]
    raw_message: Dict[str, Any]
    created_at: datetime

# 批量操作模型
class ConversationBatchCreate(SQLModel):
    """批量创建对话条目请求模型"""
    dataset_id: int = Field(..., description="所属数据集ID")
    conversation_id: Optional[str] = Field(None, max_length=100, description="对话ID，如果不提供将自动生成")
    messages: List[ConversationEntryCreate] = Field(..., description="对话消息列表") 