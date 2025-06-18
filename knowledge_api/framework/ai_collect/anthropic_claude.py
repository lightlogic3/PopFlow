import json
from typing import List, Dict, Any, Optional, AsyncGenerator
from anthropic import AsyncAnthropic

from knowledge_api.framework.ai_collect.base_llm import BaseLLM
from knowledge_api.framework.ai_collect.function_call.tool_manager import ToolManager
from knowledge_api.framework.ai_collect.function_call.tool_registry import ToolRegistry
from knowledge_api.model.llm_token_model import LLMTokenResponse


class AnthropicClaude(BaseLLM):
    """Anthropic Claude AI Implementation Class"""

    # Set the LLM type identifier
    llm_type = "anthropic"

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022",
                 base_url: str = "https://api.anthropic.com", format_response: bool = True):
        """Anthropic Claude client side

Args:
api_key: API Key
Model: model name, default is' claude-3-5-sonnet-20241022 '
base_url: API base URL
format_response: Whether the response format is uniform, the default is True"""
        super().__init__(api_key, model=model, format_response=format_response, base_url=base_url)
        self.client = AsyncAnthropic(
            api_key=api_key,
            base_url=base_url
        )
        self.is_function_call = True

    def _initialize(self) -> None:
        """initialization configuration"""
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

    def _convert_messages_to_anthropic_format(self, messages: List[Dict[str, str]]) -> tuple:
        """Convert standard message formats to Anthropic format

Args:
Messages: A list of messages in standard format

Returns:
Tuple: (system_prompt, converted_messages)"""
        system_prompt = ""
        converted_messages = []
        
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            
            if role == "system":
                # Anthropic treats system messages as separate system parameters
                if system_prompt:
                    system_prompt += "\n\n" + content
                else:
                    system_prompt = content
            elif role in ["user", "assistant"]:
                # Keep user and assistant messages
                converted_messages.append({
                    "role": role,
                    "content": content
                })
            elif role == "tool":
                # Tool call results require special handling
                converted_messages.append({
                    "role": "user",
                    "content": content
                })
        
        return system_prompt, converted_messages

    async def _chat_completion_impl(
            self,
            messages: List[Dict[str, str]],
            temperature: float = 0.7,
            max_tokens: Optional[int] = None,
            **kwargs
    ) -> LLMTokenResponse:
        """asynchronous chat completion interface"""
        system_prompt, anthropic_messages = self._convert_messages_to_anthropic_format(messages)
        
        # Set default max_tokens, Anthropic requirements must be specified
        if max_tokens is None:
            max_tokens = 4096
            
        try:
            completion = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt if system_prompt else None,
                messages=anthropic_messages,
                **kwargs
            )
            
            return self._format_chat_response(completion.model_dump())
            
        except Exception as e:
            # Return an error response when an error occurs
            return LLMTokenResponse(
                id=f"error-{hash(str(e))}",
                model=self.model,
                content=f"请求失败: {str(e)}",
                role="assistant",
                finish_reason="error",
                input_tokens=0,
                output_tokens=0,
                total_tokens=0
            )

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
LLMTokenResponse: Raw streaming response fragment"""
        system_prompt, anthropic_messages = self._convert_messages_to_anthropic_format(messages)
        
        # Set default max_tokens, Anthropic requirements must be specified
        if max_tokens is None:
            max_tokens = 4096
            
        try:
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt if system_prompt else None,
                messages=anthropic_messages,
                **kwargs
            ) as stream:
                async for chunk in stream:
                    yield self._format_stream_response(chunk.model_dump())
                    
        except Exception as e:
            # Generate an error response when an exception occurs
            error_response = LLMTokenResponse(
                id=f"error-{hash(str(e))}",
                model=self.model,
                content=f"there was an error with the streaming request: {str(e)}",
                role="assistant",
                finish_reason="error",
                input_tokens=0,
                output_tokens=0,
                total_tokens=0
            )
            yield error_response

    def completion(
            self,
            prompt: str,
            temperature: float = 0.7,
            max_tokens: Optional[int] = None,
            **kwargs
    ) -> LLMTokenResponse:
        """synchronous text completion interface"""
        import asyncio
        
        # Converting a synchronous call to an asynchronous call
        messages = [{"role": "user", "content": prompt}]
        
        try:
            # Create an event loop and run asynchronous methods
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If you already have a running event loop, create a new one
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, 
                        self._chat_completion_impl(messages, temperature, max_tokens, **kwargs)
                    )
                    return future.result()
            else:
                return loop.run_until_complete(
                    self._chat_completion_impl(messages, temperature, max_tokens, **kwargs)
                )
        except Exception as e:
            return LLMTokenResponse(
                id=f"error-{hash(str(e))}",
                model=self.model,
                content=f"the synchronization request failed: {str(e)}",
                role="assistant",
                finish_reason="error",
                input_tokens=0,
                output_tokens=0,
                total_tokens=0
            )

    def embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get text embedding vector
Note: Anthropic does not currently provide an embedding API, a null implementation is returned here"""
        # Anthropic does not support embeddings for the time being, returns an empty vector
        print("Warning: Anthropic does not support embeddings API")
        return [[] for _ in texts]

    def _format_chat_response(self, response: Dict[str, Any]) -> LLMTokenResponse:
        """Format chat response"""
        if not self.format_response:
            return response

        # Extract content - Anthropic response format
        content = ""
        if "content" in response and isinstance(response["content"], list):
            for content_block in response["content"]:
                if content_block.get("type") == "text":
                    content += content_block.get("text", "")

        # Extract usage information
        usage = response.get("usage", {})
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        total_tokens = input_tokens + output_tokens

        return LLMTokenResponse(
            id="anthropic-" + response.get("id", ""),
            model=response.get("model", self.model),
            content=content,
            role=response.get("role", "assistant"),
            finish_reason=response.get("stop_reason", "stop"),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens
        )

    def _format_stream_response(self, chunk: Dict[str, Any]) -> LLMTokenResponse:
        """Format streaming response snippets"""
        if not self.format_response:
            return chunk

        content = ""
        finish_reason = None
        input_tokens = -1
        output_tokens = -1
        total_tokens = -1

        # Handling different types of streaming events
        chunk_type = chunk.get("type")
        
        if chunk_type == "content_block_delta":
            # content block increment
            delta = chunk.get("delta", {})
            if delta.get("type") == "text_delta":
                content = delta.get("text", "")
        elif chunk_type == "message_delta":
            # Message increments, usually containing finish_reason
            delta = chunk.get("delta", {})
            finish_reason = delta.get("stop_reason")
        elif chunk_type == "message_start":
            # The message begins with usage information
            message = chunk.get("message", {})
            usage = message.get("usage", {})
            input_tokens = usage.get("input_tokens", -1)
        elif chunk_type == "message_stop":
            # end of message
            finish_reason = "stop"

        return LLMTokenResponse(
            id="anthropic-" + chunk.get("message", {}).get("id", ""),
            model=chunk.get("message", {}).get("model", self.model),
            content=content,
            role="assistant",
            finish_reason=finish_reason,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens
        )

    async def _function_call_impl(self, messages, tools: ToolRegistry, model: str = "claude-3-5-sonnet-20241022"):
        """function call implementation"""
        system_prompt, anthropic_messages = self._convert_messages_to_anthropic_format(messages)
        
        # Conversion tool format to Anthropic format
        anthropic_tools = []
        for tool in tools.get_all_tools():
            anthropic_tool = {
                "name": tool["function"]["name"],
                "description": tool["function"]["description"],
                "input_schema": tool["function"]["parameters"]
            }
            anthropic_tools.append(anthropic_tool)

        try:
            completion = await self.client.messages.create(
                model=model,
                max_tokens=4096,
                system=system_prompt if system_prompt else None,
                messages=self._validate_and_clean_messages(anthropic_messages),
                tools=anthropic_tools if anthropic_tools else None
            )
            
            tool_manager = ToolManager(tools)
            
            # Check if there is a tool call
            if completion.content:
                for content_block in completion.content:
                    if hasattr(content_block, 'type') and content_block.type == "tool_use":
                        # There are tool calls
                        tool_calls = []
                        for block in completion.content:
                            if hasattr(block, 'type') and block.type == "tool_use":
                                tool_calls.append({
                                    'id': block.id,
                                    'type': 'function',
                                    'function': {
                                        'name': block.name,
                                        'arguments': json.dumps(block.input)
                                    }
                                })
                        
                        # Execute tool call
                        tool_results = await tool_manager.handle_tool_calls_async(tool_calls)
                        
                        # Format response
                        call = self._format_chat_response(completion.model_dump())
                        call.content = json.dumps([{
                            'id': tc['id'],
                            'type': tc['type'],
                            'function': tc['function']
                        } for tc in tool_calls], ensure_ascii=False)
                        
                        return tool_results, completion.model_dump(), call

            # No tool calls, returns a normal response
            assistant_message = completion.content[0].text if completion.content else ""
            return assistant_message, None, self._format_chat_response(completion.model_dump())
            
        except Exception as e:
            error_response = LLMTokenResponse(
                id=f"error-{hash(str(e))}",
                model=model,
                content=f"the function call failed: {str(e)}",
                role="assistant",
                finish_reason="error",
                input_tokens=0,
                output_tokens=0,
                total_tokens=0
            )
            return f"there was an error with the function call: {str(e)}", None, error_response