"""
批量处理辅助函数模块
提供批量处理工具所需的通用辅助函数和常量
"""

from datetime import datetime

from pydantic import BaseModel

from knowledge_api.utils.log_config import get_logger

logger = get_logger()

# 批处理块大小
CHUNK_SIZE = 10


class RawEpisode(BaseModel):
    """原始剧情数据模型"""
    name: str
    content: str
    source_description: str
    source: int  # EpisodeType
    reference_time: datetime


def compress_uuid_map(uuid_map: dict[str, str]) -> dict[str, str]:
    """压缩UUID映射，确保所有UUID值不会映射到其他UUID
    
    参数:
        uuid_map: UUID映射字典
        
    返回:
        压缩后的UUID映射字典
    """
    # 确保所有uuid值不会映射到其他uuid
    compressed_map = {}
    for key, uuid in uuid_map.items():
        curr_value = uuid
        while curr_value in uuid_map:
            curr_value = uuid_map[curr_value]

        compressed_map[key] = curr_value
    
    logger.debug(f"压缩UUID映射，原始大小: {len(uuid_map)}，压缩后大小: {len(compressed_map)}")
    return compressed_map 