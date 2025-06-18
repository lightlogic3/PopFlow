"""记忆系统模型定义

包含记忆系统使用的各种数据模型
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class UserMetadata(BaseModel):
    """用户元数据
    
    用于在记忆系统中区分不同用户和角色
    """
    user_id: str = Field(..., description="用户ID，必填")
    role_id: str = Field(..., description="角色ID，必填，用于隔离不同角色的记忆")
    session_id: Optional[str] = Field(default=None, description="会话ID，可选，为None时表示全部会话")
    conversations: List[Any] = Field(default_factory=list, description="关联的对话列表")
    

class MemoryContext(BaseModel):
    """记忆内容模型
    
    记忆系统存储的基本数据单元，包含内容、来源和元数据
    """
    content: str = Field(..., description="记忆内容，必填")
    source: str = Field(default="user", description="来源，例如: user, assistant, system, api")
    timestamp: datetime = Field(default_factory=datetime.now, description="记忆创建时间")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="附加元数据")
    summary: Optional[str] = Field(default=None, description="内容摘要，可选")
    is_summarized: bool = Field(default=False, description="是否为汇总内容")
    summary_count: int = Field(default=0, description="汇总的记忆数量，0表示原始记忆")
    dialog_roles: List[str] = Field(default_factory=list, description="对话中包含的角色列表")
    memory_id: Optional[str] = Field(default=None, description="记忆ID，由存储系统分配")
    vector: Optional[List[float]] = Field(default=None, description="向量表示，用于相似度检索")
    source_dialog: Optional[List[Dict[str, Any]]] = Field(default=None, description="未处理过的对话内容列表")
    history: Optional[List[Dict[str, Any]]] = Field(default=None, description="最近n条对话历史")
    
    # 新增字段以支持更多场景
    conversation_id: Optional[str] = Field(default=None, description="对话ID")
    message_id: Optional[str] = Field(default=None, description="消息ID") 
    parent_message_id: Optional[str] = Field(default=None, description="父消息ID")
    role: Optional[str] = Field(default=None, description="角色，兼容字段")
    user_id: Optional[str] = Field(default=None, description="用户ID，兼容字段")
    role_id: Optional[str] = Field(default=None, description="角色ID，兼容字段") 
    session_id: Optional[str] = Field(default=None, description="会话ID，兼容字段")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryContext":
        """从字典创建MemoryContext对象
        
        Args:
            data: 字典数据
            
        Returns:
            MemoryContext: 创建的对象
        """
        # 处理兼容性字段映射
        if "role" in data and "source" not in data:
            data["source"] = data["role"]
            
        # 处理时间戳字段
        if "timestamp" in data:
            if isinstance(data["timestamp"], str):
                try:
                    from datetime import datetime
                    data["timestamp"] = datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
                except:
                    # 如果解析失败，使用当前时间
                    data["timestamp"] = datetime.now()
        
        # 确保metadata字段存在
        if "metadata" not in data:
            data["metadata"] = {}
            
        # 将不在模型字段中的数据添加到metadata中
        model_fields = set(cls.__fields__.keys())
        extra_fields = {}
        
        for key, value in data.items():
            if key not in model_fields:
                extra_fields[key] = value
                
        if extra_fields:
            data["metadata"].update(extra_fields)
            # 移除额外字段，避免pydantic验证错误
            for key in extra_fields.keys():
                if key in data:
                    del data[key]
        
        return cls(**data)
    
    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        """转换为字典
        
        覆盖父类方法，处理datetime类型
        """
        result = super().dict(*args, **kwargs)
        # 处理datetime类型
        if isinstance(result.get("timestamp"), datetime):
            result["timestamp"] = result["timestamp"].isoformat()
        return result
    

class EmbeddingRequest(BaseModel):
    """向量嵌入请求模型
    
    用于向量化服务的请求
    """
    texts: List[str] = Field(..., description="需要向量化的文本列表")
    model: str = Field(default="default", description="使用的向量模型")
    

class EmbeddingResponse(BaseModel):
    """向量嵌入响应模型
    
    向量化服务的响应
    """
    embeddings: List[List[float]] = Field(..., description="文本向量列表")
    model: str = Field(..., description="使用的向量模型")
    dimensions: int = Field(..., description="向量维度")
    

class QueryRequest(BaseModel):
    """记忆检索请求模型
    
    用于检索记忆的请求
    """
    query: str = Field(..., description="查询文本")
    user_id: str = Field(..., description="用户ID")
    role_id: str = Field(..., description="角色ID")
    session_id: Optional[str] = Field(default=None, description="会话ID，可选")
    top_k: int = Field(default=5, description="返回的最大结果数量")
    filters: Dict[str, Any] = Field(default_factory=dict, description="过滤条件")
    
    
class MemoryResponse(BaseModel):
    """记忆响应模型
    
    记忆系统的检索结果
    """
    content: str = Field(..., description="记忆内容")
    memory_id: str = Field(..., description="记忆ID")
    source: str = Field(..., description="来源")
    timestamp: str = Field(..., description="创建时间")
    similarity: float = Field(..., description="与查询的相似度")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="附加元数据")
    summary: Optional[str] = Field(default=None, description="内容摘要")
    

class SyncStatus(BaseModel):
    """同步状态模型
    
    记录记忆系统同步状态
    """
    is_syncing: bool = Field(default=False, description="是否正在同步")
    progress: float = Field(default=0.0, description="同步进度，0-1")
    last_sync_time: Optional[datetime] = Field(default=None, description="上次同步时间")
    total_items: int = Field(default=0, description="总项目数")
    processed_items: int = Field(default=0, description="已处理项目数")
    error_count: int = Field(default=0, description="错误数量")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    

class MemoryStats(BaseModel):
    """记忆统计模型
    
    记录记忆系统的使用统计
    """
    total_memories: int = Field(default=0, description="总记忆数量")
    user_memories: Dict[str, int] = Field(default_factory=dict, description="各用户的记忆数量")
    average_latency: float = Field(default=0.0, description="平均检索延迟")
    queries_count: int = Field(default=0, description="检索次数")
    level_usage: Dict[str, int] = Field(default_factory=dict, description="各级记忆系统使用次数")

