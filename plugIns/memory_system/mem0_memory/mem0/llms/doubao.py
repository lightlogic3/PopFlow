from typing import Dict, List, Optional

from plugIns.memory_system.mem0_memory.mem0.configs.llms.base import BaseLlmConfig
from plugIns.memory_system.mem0_memory.mem0.llms.base import LLMBase

from knowledge_api.framework.redis.cache_manager import CacheManager
from knowledge_api.model.llm_token_model import LLMTokenResponse
from knowledge_api.framework.ai_collect import BaseLLM


class DoubaoLLM(LLMBase):
    def __init__(self, config: Optional[BaseLlmConfig] = None):
        super().__init__(config)
        if not self.config.model:
            self.config.model = "doubao-1-5-lite-32k-250115"
        self.cache_manager = CacheManager()
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        response_format=None,
        tools: Optional[List[Dict]] = None,
        tool_choice: str = "auto",
    ):
        """
        Generate a response based on the given messages using Doubao.

        Args:
            messages (list): List of message dicts containing 'role' and 'content'.
            response_format (str or object, optional): Format of the response. Defaults to "text".
            tools (list, optional): List of tools that the model can call. Defaults to None.
            tool_choice (str, optional): Tool choice method. Defaults to "auto".

        Returns:
            str: The generated response content.
        """
        ai= await self.cache_manager.get_ai_by_model_id(self.config.model)
        # 调用AI聊天
        response: LLMTokenResponse = await ai.chat_completion(
            messages=messages,
            temperature= self.config.temperature,
            max_tokens=self.config.max_tokens,
            application_scenario="memory_test",
            response_format=response_format,
        )
        result=response.content
        return result