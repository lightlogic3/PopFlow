"""
Copyright 2024, Zep Software, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import json
import logging
import re
import typing
from typing import ClassVar

from pydantic import BaseModel

from ..config import LLMConfig, DEFAULT_MAX_TOKENS, ModelSize
from ..prompts.models import Message
from .client import  LLMClient
from knowledge_api.framework.redis.cache_manager import CacheManager

from knowledge_api.utils.log_config import get_logger
logger = get_logger()

DEFAULT_MODEL = 'doubao-pro-32k-functioncall-241028'
DEFAULT_SMALL_MODEL = 'doubao-pro-32k-functioncall-241028'


class CustomLLMClient(LLMClient):
    """
    DoubaoClient是豆包API的客户端实现类。
    
    这个类继承了LLMClient，提供了与豆包AI模型交互的方法，包括初始化客户端、
    获取响应、处理错误等功能。
    
    属性:
        client (BaseLLM): 豆包AI客户端实例
        model (str): 使用的模型名称
        temperature (float): 生成响应的随机度
        max_tokens (int): 生成响应的最大token数量
    """

    # 类级常量
    MAX_RETRIES: ClassVar[int] = 2

    def __init__(
        self,
        config: LLMConfig | None = None,
        cache: bool = False,
        client: typing.Any = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        model_id: str = ""
    ):
        """
        初始化DoubaoClient，设置配置、缓存和客户端参数。
        
        参数:
            config (LLMConfig | None): 包含API密钥、模型、基础URL、温度和最大tokens的配置
            cache (bool): 是否启用缓存，目前豆包实现暂不支持缓存
            client (Any | None): 可选的客户端实例，如果不提供，将通过CacheManager获取
            max_tokens (int): 响应生成的最大token数
        """
        # 暂不实现缓存功能
        if cache:
            raise NotImplementedError('缓存功能暂未在豆包客户端中实现')

        if config is None:
            config = LLMConfig()

        super().__init__(config, cache)

        # 客户端将在第一次请求时从CacheManager获取
        self.client = client
        self.max_tokens = max_tokens
        self.cache_manager = CacheManager()
        self.model_id=model_id

    async def _get_ai_client(self, model: str = None):
        """
        获取豆包AI客户端实例，如果尚未初始化则从CacheManager获取。
        
        参数:
            model (str): 要使用的模型ID，如果未提供则使用配置中的模型
            
        返回:
            BaseLLM: 豆包AI客户端实例
        """
        model_id = model or self.model or DEFAULT_MODEL
        if not self.client:
            # 通过CacheManager获取AI对象
            self.client = await self.cache_manager.get_ai_by_model_id(model_id)
            if not self.client:
                raise ValueError(f"无法获取模型ID为{model_id}的AI实例")
        return self.client

    async def _generate_response(
        self,
        messages: list[Message],
        response_model: type[BaseModel] | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        model_size: ModelSize = ModelSize.medium,
    ) -> dict[str, typing.Any]:
        """
        生成AI响应的实现方法。
        
        参数:
            messages: 对话消息列表
            response_model: 可选的响应模型类型
            max_tokens: 响应生成的最大token数
            model_size: 模型大小，决定使用哪个模型
            
        返回:
            dict[str, Any]: 响应结果字典
        """
        # 转换消息格式，从Message对象转为字典
        formatted_messages = []
        for m in messages:
            m.content = self._clean_input(m.content)
            formatted_messages.append({
                "role": m.role,
                "content": m.content
            })

        try:
            # 根据模型大小选择合适的模型
            # if model_size == ModelSize.small:
            #     model_id = self.small_model or DEFAULT_SMALL_MODEL
            # else:
            #     model_id = self.model or DEFAULT_MODEL
            #
            # 获取AI客户端
            ai_client = await self._get_ai_client(self.model_id)
            
            # 设置请求参数
            params = {
                "temperature": self.temperature,
                "max_tokens": max_tokens or self.max_tokens,
                "application_scenario": "memory_system",
                "response_format":response_model.model_json_schema() if response_model else None,
            }
            
            # 调用chat_completion方法获取响应
            response = await ai_client.chat_completion(
                messages=formatted_messages,
                **params
            )
            
            # 如果指定了响应模型，尝试将响应解析为模型实例
            if response_model and hasattr(response, "content") and response.content:
                try:

                    parsed_data = fix_json(response.content)
                    logger.info(f"大模型响应内容: {parsed_data}", )
                    return response_model.model_validate(parsed_data).model_dump()
                except Exception as e:
                    logger.error(f"响应内容: {response.content}，要求响应模型: {response_model.model_json_schema()}")
                    raise Exception(f"无法将响应解析为指定模型: {e}")
            # 返回响应数据
            return response.model_dump() if hasattr(response, "model_dump") else response
                
        except Exception as e:
            logger.error(f"生成豆包AI响应时出错: {e}")
            import traceback
            traceback.print_exc()
            raise



def fix_json(json_string):
    # 查找字段值中未转义的引号
    fixed_json = re.sub(r'(:\s*")(.+?)("(?=\s*[,}]))', lambda m: m.group(1) + m.group(2).replace('"', '\\"') + m.group(3), json_string)
    # 有时候会出现Python 布尔值，需要转为JSON的布尔值
    fixed_json = fixed_json.replace('True', 'true').replace('False', 'false')
    return json.loads(fixed_json)