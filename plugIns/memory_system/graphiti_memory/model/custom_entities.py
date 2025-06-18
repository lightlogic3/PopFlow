from typing import Dict, Any, List, Optional, Union, Tuple
from pydantic import BaseModel, Field
# 自定义实体类型定义
class PersonEntity(BaseModel):
    """实体类型：人物。用于表示对话中提到的人物，包括游戏角色、NPC等。"""
    description: Optional[str] = Field(default="游戏中的人物角色", description="人物描述")
    role: Optional[str] = Field(default="未知角色", description="人物角色")


class LocationEntity(BaseModel):
    """实体类型：地点。用于表示对话中提到的地点，如城市、区域等。"""
    description: Optional[str] = Field(default="游戏中的地点", description="地点描述")
    region: Optional[str] = Field(default="未知区域", description="所属区域")


class ItemEntity(BaseModel):
    """实体类型：物品。用于表示对话中提到的物品，如武器、材料等。"""
    description: Optional[str] = Field(default="游戏中的物品", description="物品描述")
    category: Optional[str] = Field(default="未知类别", description="物品类别")


class EventEntity(BaseModel):
    """实体类型：事件。用于表示对话中提到的事件或活动。"""
    description: Optional[str] = Field(default="游戏中的事件", description="事件描述")
    time_period: Optional[str] = Field(default="未知时间", description="事件发生时间")


class DialogueEntity(BaseModel):
    """实体类型：对话。表示用户和助手之间的对话内容。"""
    role: Optional[str] = Field(default="未知角色", description="发言角色：user或assistant")
    content: Optional[str] = Field(default="", description="对话内容")
    timestamp: Optional[str] = Field(default="", description="对话时间戳")