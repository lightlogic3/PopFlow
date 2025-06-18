import json
from typing import List, Dict, Any, Optional, AsyncGenerator
import requests
from knowledge_api.framework.ai_collect.base_llm import BaseLLM
from knowledge_api.framework.ai_collect.function_call.tool_registry import ToolRegistry


class ErnieBot(BaseLLM):
    """Baidu ERNIE Bot API implementation class"""

    # Set the LLM type identifier
    llm_type = "erniebot"
    

    def __init__(self, api_key: str, model: str = "ernie-bot-8k", base_url: str = None, format_response: bool = True):
        """Initialize ERNIE Bot API client side

Args:
api_key: Access token in the format'bce-v3/xxx/xxx'
Model: model name, defaults to'ernie-bot-8k'
base_url: base URL, default to None
format_response: Whether the response format is uniform, the default is True"""
        super().__init__(api_key, model=model, format_response=format_response, base_url=base_url)

    def _initialize(self) -> None:
        """initialization configuration"""
        # Extract access token from API Key
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

    async def _chat_completion_impl(
            self,
            messages: List[Dict[str, str]],
            temperature: float = 0.7,
            max_tokens: Optional[int] = None,
            **kwargs
    ) -> Dict[str, Any]:
        """asynchronous chat completion interface"""
        url = f"{self.base_url}/chat/completions"

        payload = {
            "messages": messages,
            "model": self.model,
            "temperature": temperature,
            "stream": False
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        session = await self._get_session()
        async with session.post(url, json=payload) as response:
            result = await response.json()
            return self._format_chat_response(result)

    async def _chat_completion_impl_stream(
            self,
            messages: List[Dict[str, str]],
            temperature: float = 0.7,
            max_tokens: Optional[int] = None,
            **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """asynchronous streaming chat interface"""
        url = f"{self.base_url}/chat/completions"

        payload = {
            "messages": messages,
            "model": self.model,
            "temperature": temperature,
            "stream": True
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
    ) -> Dict[str, Any]:
        """synchronous text completion interface"""
        url = f"{self.base_url}/chat/completions"

        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "model": self.model,
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
                "input": text,
                "model": "embedding-v1"
            }

            response = requests.post(url, headers=self.headers, json=payload)
            result = response.json()

            if "data" in result and len(result["data"]) > 0:
                results.append(result["data"][0]["embedding"])

        return results

    def _format_chat_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Uniformatted chat response

Uniform format:
{
"Id": "Session ID",
"Model": "Model name",
"Created": timestamp,
"Content": "Content replied by the assistant",
"Role": "assistant",
"finish_reason": "stop",
"Usage": {
"prompt_tokens": the number of prompt word tokens,
"completion_tokens": number of generated tokens,
"total_tokens": Total number of tokens
}
}"""
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

        # Building a unified response format
        return {
            "id": response.get("id", ""),
            "model": response.get("model", self.model),
            "created": response.get("created", 0),
            "content": content,
            "role": role,
            "finish_reason": finish_reason,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            }
        }

    def _format_stream_response(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
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

        # Building a Unified Streaming Response Format
        return {
            "id": chunk.get("id", ""),
            "model": chunk.get("model", self.model),
            "created": chunk.get("created", 0),
            "delta": {
                "content": delta.get("content", ""),
                "role": delta.get("role", "assistant")
            },
            "finish_reason": finish_reason
        }
    async def _function_call_impl(self, messages, tools: ToolRegistry, model: str = "doubao-pro-32k-functioncall-241028"):
        print("test")