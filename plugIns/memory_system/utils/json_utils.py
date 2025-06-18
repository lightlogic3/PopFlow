import json
from datetime import datetime
from typing import Any


class DateTimeEncoder(json.JSONEncoder):
    """处理datetime对象的JSON编码器"""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def serialize_with_datetime(obj: Any) -> str:
    """
    序列化包含datetime对象的数据
    
    Args:
        obj: 要序列化的对象
        
    Returns:
        str: JSON字符串
    """
    return json.dumps(obj, cls=DateTimeEncoder, ensure_ascii=False)


def deserialize_datetime_aware(json_str: str) -> Any:
    """
    反序列化可能包含datetime字符串的JSON
    
    Args:
        json_str: JSON字符串
        
    Returns:
        Any: 反序列化后的对象
    """
    return json.loads(json_str) 