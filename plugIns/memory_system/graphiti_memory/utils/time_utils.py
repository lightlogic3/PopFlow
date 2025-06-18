"""
时间处理工具函数
"""

from datetime import datetime, timezone, timedelta
from typing import Optional

def to_local_time(utc_time: Optional[datetime], tz_offset: int = 8) -> Optional[datetime]:
    """将UTC时间转换为本地时间

    Args:
        utc_time: UTC时间
        tz_offset: 时区偏移小时数，默认为中国时区(+8)

    Returns:
        本地时间
    """
    if utc_time is None:
        return None
        
    # 确保时间是UTC时间
    # 如果时间没有时区信息，假设是UTC
    if utc_time.tzinfo is None:
        utc_time = utc_time.replace(tzinfo=timezone.utc)
        
    # 转换为本地时区
    local_tz = timezone(timedelta(hours=tz_offset))
    return utc_time.astimezone(local_tz)
    
def from_local_time(local_time: Optional[datetime], tz_offset: int = 8) -> Optional[datetime]:
    """将本地时间转换为UTC时间

    Args:
        local_time: 本地时间
        tz_offset: 时区偏移小时数，默认为中国时区(+8)

    Returns:
        UTC时间
    """
    if local_time is None:
        return None
        
    # 如果时间没有时区信息，假设是本地时间
    if local_time.tzinfo is None:
        local_tz = timezone(timedelta(hours=tz_offset))  # 本地时区
        local_time = local_time.replace(tzinfo=local_tz)
        
    # 转换为UTC
    return local_time.astimezone(timezone.utc)

def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化日期时间

    Args:
        dt: 日期时间对象
        fmt: 格式化字符串

    Returns:
        格式化后的字符串
    """
    if dt is None:
        return ""
    return dt.strftime(fmt)

def parse_datetime(dt_str: str) -> Optional[datetime]:
    """解析日期时间字符串

    Args:
        dt_str: 日期时间字符串，支持ISO格式

    Returns:
        日期时间对象
    """
    if not dt_str:
        return None
        
    try:
        return datetime.fromisoformat(dt_str)
    except ValueError:
        return None 