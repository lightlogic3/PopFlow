import json
from typing import List, Dict, Any, Optional, AsyncGenerator
import requests
from knowledge_api.framework.ai_collect.base_llm import BaseLLM
from volcenginesdkarkruntime import Ark, AsyncArk

from knowledge_api.framework.ai_collect.function_call.tool_manager import ToolManager
from knowledge_api.framework.ai_collect.function_call.tool_registry import ToolRegistry
from knowledge_api.model.llm_token_model import LLMTokenResponse


class DouBao(BaseLLM):
    """Bean bag AI implementation class"""

    # Set the LLM type identifier
    llm_type = "doubao"


    def __init__(self, api_key: str, model: str = "doubao-pro-32k-241215",
                 base_url="https://ark.cn-beijing.volces.com/api/v3", format_response: bool = True):
        """Initialize bean bag AI client side

Args:
api_key: API Key
Model: model name, default is' doubao-pro-32k-241215 '
format_response: Whether the response format is uniform, the default is True"""
        super().__init__(api_key, model=model, format_response=format_response, base_url=base_url)
        self.client = AsyncArk(
            base_url=base_url,
            api_key=api_key
        )
        self.is_function_call = True

    def _initialize(self) -> None:
        """initialization configuration"""
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def _chat_completion_impl(
            self,
            messages: List[Dict[str, str]],
            temperature: float = 0.7,
            max_tokens: Optional[int] = None,
            **kwargs
    ) ->LLMTokenResponse:
        """asynchronous chat completion interface"""
        completion = await self.client.chat.completions.create(
            # Specify the Ark Inference Access Point ID you created, which has been changed to your Inference Access Point ID for you.
            model=self.model,
            messages=messages,
            temperature=temperature,
            stream=False,
            **kwargs
        )
        return self._format_chat_response(completion.model_dump())

    async def _chat_completion_stream_impl(
            self,
            messages: List[Dict[str, str]],
            temperature: float = 0.7,
            max_tokens: Optional[int] = None,
            **kwargs
    ) -> AsyncGenerator[LLMTokenResponse, None]:
        """The actual streaming chat completes the API call implementation

Args:
Messages: conversation history
Temperature: temperature parameters, control randomness
max_tokens: Maximum number of tokens generated
** kwargs: other model-specific parameters

Yields:
Dict [str, Any]: Raw streaming response fragment"""
        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
            "stream_options": {
                "include_usage": True
            }
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        async with self._get_streaming_response(url, payload) as response:
            async for line in response.content:
                if line:
                    try:
                        line = line.decode('utf-8').strip()
                        if line.startswith('data: '):
                            line = line[6:]  # Remove the "data:" prefix
                        if line and line != '[DONE]':
                            chunk = json.loads(line)
                            yield self._format_stream_response(chunk)
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        print(f"处理流式响应出错: {e}")
                        continue
                        
    def completion(
            self,
            prompt: str,
            temperature: float = 0.7,
            max_tokens: Optional[int] = None,
            **kwargs
    ) ->LLMTokenResponse:
        """synchronous text completion interface"""
        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "stream": False
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        response = requests.post(url, headers=self.headers, json=payload)
        return self._format_chat_response(response.json())

    def embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get text embedding vector"""
        url = f"{self.base_url}/embeddings"
        results = []

        for text in texts:
            payload = {
                "model": "text-embedding-v1",
                "input": text
            }
            response = requests.post(url, headers=self.headers, json=payload)
            result = response.json()
            if "data" in result and len(result["data"]) > 0:
                results.append(result["data"][0]["embedding"])

        return results

    def _format_chat_response(self, response: Dict[str, Any])->LLMTokenResponse:
        """Format chat response"""
        if not self.format_response:
            return response

        # Extracting content and finish_reason
        if "choices" in response and len(response["choices"]) > 0:
            choice = response["choices"][0]
            content = choice.get("message", {}).get("content", "")
            finish_reason = choice.get("finish_reason", "stop")
            role = choice.get("message", {}).get("role", "assistant")
        else:
            content = ""
            finish_reason = "error"
            role = "assistant"

        # Extract usage information
        usage = response.get("usage", {})
        if isinstance(usage, dict):
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)
        else:
            prompt_tokens = 0
            completion_tokens = 0
            total_tokens = 0

        return LLMTokenResponse(
            id="doubao-" + response.get("id", ""),
            model=response.get("model", self.model),
            content=content,
            role=role,
            finish_reason=finish_reason,
            input_tokens=prompt_tokens,
            output_tokens=completion_tokens,
            total_tokens=total_tokens
        )

    def _format_stream_response(self, chunk: Dict[str, Any]) -> LLMTokenResponse:
        """Format streaming response snippets"""
        if not self.format_response:
            return chunk

        # Extract delta content
        if "choices" in chunk and len(chunk["choices"]) > 0:
            choice = chunk["choices"][0]
            delta = choice.get("delta", {})
            finish_reason = choice.get("finish_reason")
        else:
            delta = {}
            finish_reason = None
        usage=chunk.get("usage")
        if not isinstance(usage, dict):
            usage = {
                "prompt_tokens": -1,
                "completion_tokens": -1,
                "total_tokens": -1
            }
        return LLMTokenResponse(
            id="doubao-" + chunk.get("id", ""),
            model=chunk.get("model", self.model),
            content=delta.get("content", ""),
            role=delta.get("role", "assistant"),
            finish_reason=finish_reason,
            input_tokens=usage.get("prompt_tokens"),
            output_tokens=usage.get("completion_tokens"),
            total_tokens=usage.get("total_tokens")
        )

    async def _function_call_impl(self, messages, tools: ToolRegistry,model: str = "doubao-pro-32k-functioncall-241028"):
        completion = await self.client.chat.completions.create(
            model=model,
            messages=self._validate_and_clean_messages(messages),
            tools=tools.get_all_tools()
        )
        tool_manager = ToolManager(tools)
        assistant_message = completion.choices[0].message
        if hasattr(assistant_message, 'tool_calls') and assistant_message.tool_calls:
            tool_results = await tool_manager.handle_tool_calls_async(assistant_message.tool_calls)
            call=self._format_chat_response(completion.model_dump())
            call.content=json.dumps([item.model_dump() for item in assistant_message.tool_calls],ensure_ascii=False)
            return tool_results, assistant_message.model_dump(),call

        return assistant_message.content,None,self._format_chat_response(completion.model_dump())