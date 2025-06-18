"""
情节类型模块
定义系统可以处理的不同类型的情节
"""

import logging
from enum import Enum

logger = logging.getLogger(__name__)

class EpisodeType(Enum):
    """
    不同类型情节的枚举
    
    此枚举定义了系统可以处理的各种情节源或格式。
    用于对不同类型的输入数据进行分类和处理。
    
    属性:
    -----------
    message : str
        表示标准消息类型的情节。此类型的内容应格式化为"actor: content"。
        例如，"user: 你好，最近怎么样？"或"assistant: 我很好，谢谢你的问候。"
    json : str
        表示包含JSON字符串对象的情节，具有结构化数据。
    text : str
        表示纯文本情节。
    """

    message = 'message'
    json = 'json'
    text = 'text'

    @staticmethod
    def from_str(episode_type: str) -> 'EpisodeType':
        """
        从字符串转换为情节类型枚举
        
        Args:
            episode_type: 情节类型字符串
            
        Returns:
            对应的情节类型枚举值
            
        Raises:
            NotImplementedError: 如果情节类型未实现
        """
        if episode_type == 'message':
            return EpisodeType.message
        if episode_type == 'json':
            return EpisodeType.json
        if episode_type == 'text':
            return EpisodeType.text
        logger.error(f'情节类型: {episode_type} 未实现')
        raise NotImplementedError 