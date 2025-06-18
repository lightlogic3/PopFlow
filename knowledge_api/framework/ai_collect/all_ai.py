from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ChatMessage
from typing import Optional, List, Dict, Any, AsyncGenerator
import asyncio
import json
import time

from knowledge_api.framework.ai_collect.base_llm import BaseLLM
from knowledge_api.framework.ai_collect.function_call.tool_registry import ToolRegistry
from knowledge_api.model.llm_token_model import LLMTokenResponse


class AllAI(BaseLLM):
    """The AI model implementation based on LangChain supports a variety of LLM operations."""

    # Set the LLM type identifier
    llm_type = "all"
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        base_url: str = None,
        format_response: bool = True,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """Initializing the LangChain-based AI model

Args:
api_key: OpenAI API Key
Model: model name
base_url: Optional API base URL
format_response: Whether to format the response
Temperature: temperature parameters, control randomness
max_tokens: Maximum number of tokens generated
** kwargs: Other parameters passed to ChatOpenAI"""
        # Set temperature and other properties before calling the parent class to initialize
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.kwargs = kwargs
        
        # Invoke parent class initialization
        super().__init__(api_key, model=model, base_url=base_url, format_response=format_response)
        
        # Set HTTP headers
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Initializing LangChain Model in _initialize
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize the LangChain model"""
        # Create a LangChain ChatOpenAI instance
        model_kwargs = {}
        if self.base_url:
            model_kwargs["openai_api_base"] = self.base_url
            
        self.llm = ChatOpenAI(
            model=self.model,
            openai_api_key=self.api_key,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            **model_kwargs,
        )
        
        # Initialize the embedding model
        try:
            from langchain_openai import OpenAIEmbeddings
            self.embedding_model = OpenAIEmbeddings(
                openai_api_key=self.api_key,
                model="text-embedding-3-large"
            )
        except ImportError:
            self.embedding_model = None
            print("Warning: OpenAI Embeddings is not installed. Embedding is not available.")
        
        # tag function call capability
        self.is_function_call = True

    def _convert_to_langchain_messages(self, messages):
        """Convert a generic message format to a LangChain message object

Args:
Messages: A list of messages, which can be a dict or already a LangChain message object

Returns:
List of converted LangChain message objects"""
        langchain_messages = []
        
        for msg in messages:
            # If it is already a LangChain message object, add it directly.
            if isinstance(msg, (HumanMessage, AIMessage, SystemMessage, ChatMessage)):
                langchain_messages.append(msg)
                continue
                
            # Handling dictionary formats
            if isinstance(msg, dict):
                role = msg.get("role", "")
                content = msg.get("content", "")
                
                if role == "user":
                    langchain_messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    langchain_messages.append(AIMessage(content=content))
                elif role == "system":
                    langchain_messages.append(SystemMessage(content=content))
                else:
                    # Handle other roles
                    langchain_messages.append(ChatMessage(role=role, content=content))
        
        return langchain_messages

    def _format_chat_response(self, response) -> LLMTokenResponse:
        """Format LangChain responses into a uniform format

Args:
Response: LangChain Response Object

Returns:
Formatted Response Dictionary"""
        if not self.format_response:
            return response

        # Handling langchain_core.messages.ai. AIMessage types
        if isinstance(response, AIMessage):
            token_usage = getattr(response, "usage_metadata", {}) or {}
            input_tokens = token_usage.get("input_tokens", -1)
            output_tokens = token_usage.get("output_tokens", -1)
            total_tokens = input_tokens + output_tokens if input_tokens > 0 and output_tokens > 0 else -1
            
            return LLMTokenResponse(
                id="langchain-" + str(id(response)),
                model=self.model,
                content=response.content,
                role="assistant",
                finish_reason="stop",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=total_tokens,
                elapsed_time=0.0,  # Set by the caller
            )
        else:
            # Handling other types of responses
            content = response.content if hasattr(response, "content") else str(response)
            return LLMTokenResponse(
                id="langchain-" + str(id(response)),
                model=self.model,
                content=content,
                role="assistant",
                finish_reason="stop",
                input_tokens=-1,
                output_tokens=-1,
                total_tokens=-1,
                elapsed_time=0.0,  # Set by the caller
            )

    def _format_stream_response(self, chunk) -> LLMTokenResponse:
        """Format streaming response snippets

Args:
Chunk: Streaming response snippets

Returns:
Formatted response fragment"""
        if not self.format_response:
            return chunk
            
        # Processing LangChain streaming output
        content = chunk.content if hasattr(chunk, "content") else str(chunk)
        
        return LLMTokenResponse(
            id=f"langchain-stream-{id(chunk)}",
            model=self.model,
            content=content,
            role="assistant",
            finish_reason=None,
            input_tokens=-1,
            output_tokens=-1,
            total_tokens=-1,
            elapsed_time=0.0,  # Set by the caller
        )

    async def _chat_completion_impl(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMTokenResponse:
        """Actual chat completion API call implementation

Args:
Messages: conversation history
Temperature: temperature parameters, control randomness
max_tokens: Maximum number of tokens generated
** kwargs: other model-specific parameters

Returns:
Dict [str, Any]: Raw model response result"""
        # Convert message format
        langchain_messages = self._convert_to_langchain_messages(messages)
        
        # set parameters
        params = {}
        if temperature is not None:
            params["temperature"] = temperature
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
            
        # If there are other parameters, add them to the params.
        params.update(kwargs)
        
        # Call the LangChain model
        if params:
            # Create a new model instance with parameters
            temp_llm = self.llm.with_config(**params)
            response = await temp_llm.ainvoke(langchain_messages)
        else:
            # Use default parameters
            response = await self.llm.ainvoke(langchain_messages)
            
        # Return a formatted response
        return self._format_chat_response(response)

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
        # Convert message format
        langchain_messages = self._convert_to_langchain_messages(messages)
        
        # set parameters
        params = {}
        if temperature is not None:
            params["temperature"] = temperature
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
            
        # If there are other parameters, add them to the params.
        params.update(kwargs)
        
        # Call LangChain Model Streaming Interface
        if params:
            # Create a new model instance with parameters
            temp_llm = self.llm.with_config(**params)
            async for chunk in temp_llm.astream(langchain_messages):
                yield self._format_stream_response(chunk)
        else:
            # Use default parameters
            async for chunk in self.llm.astream(langchain_messages):
                yield self._format_stream_response(chunk)

    async def _function_call_impl(self, messages, tools: ToolRegistry, model: str = None) -> tuple:
        """Implement function call interface

Args:
Messages: conversation history
Tools: tools regedit
Model: Model name, if None, use the default model

Returns:
Tuple: (tool_results, assistant_message, completion)"""
        try:
            # Use the specified model or the default model
            model_to_use = model or self.model
            
            # Get tool definition
            tool_configs = tools.get_openai_tools()
            
            # Convert message
            langchain_messages = self._convert_to_langchain_messages(messages)
            
            # Create a temporary LLM with tools
            temp_llm = ChatOpenAI(
                model=model_to_use,
                openai_api_key=self.api_key,
                temperature=self.temperature
            ).bind(tools=tool_configs)
            
            # Invoke the model with tools
            response = await temp_llm.ainvoke(langchain_messages)
            
            # Check if there is a tool call
            tool_calls = []
            if hasattr(response, "additional_kwargs") and "tool_calls" in response.additional_kwargs:
                tool_calls = response.additional_kwargs["tool_calls"]
            
            # Format as standard response
            formatted_response = self._format_chat_response(response)
            
            # If there is a tool call, handle the tool call
            if tool_calls:
                tool_manager = ToolRegistry(tools)
                tool_results = await tool_manager.handle_tool_calls_async(tool_calls)
                
                # Create assistant_message
                assistant_message = {
                    "role": "assistant",
                    "content": response.content,
                    "tool_calls": tool_calls
                }
                
                return tool_results, assistant_message, formatted_response
            else:
                # No tool calls, return content directly
                assistant_message = {
                    "role": "assistant",
                    "content": response.content
                }
                
                return response.content, assistant_message, formatted_response
                
        except Exception as e:
            print(f"函数调用出错: {e}")
            # Return error message
            error_message = {
                "role": "assistant",
                "content": f"函数调用出错: {str(e)}"
            }
            
            error_response = LLMTokenResponse(
                id=f"error-{time.time()}",
                model=self.model,
                content=f"函数调用出错: {str(e)}",
                role="assistant",
                finish_reason="error",
                input_tokens=-1,
                output_tokens=-1,
                total_tokens=-1,
                elapsed_time=0.0
            )
            
            return f"函数调用出错: {str(e)}", error_message, error_response

    def completion(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMTokenResponse:
        """synchronous text completion

Args:
Prompt: Prompt text
Temperature: Optional temperature parameters
max_tokens: Maximum number of tokens available
** kwargs: other parameters

Returns:
complete result"""
        # Convert the prompt to a message format
        messages = [{"role": "user", "content": prompt}]
        langchain_messages = self._convert_to_langchain_messages(messages)
        
        # set parameters
        params = {}
        if temperature is not None:
            params["temperature"] = temperature
        if max_tokens is not None:
            params["max_tokens"] = max_tokens
            
        # If there are other parameters, add them to the params.
        params.update(kwargs)
        
        # Call the LangChain model
        if params:
            # Create a new model instance with parameters
            temp_llm = self.llm.with_config(**params)
            response = temp_llm.invoke(langchain_messages)
        else:
            # Use default parameters
            response = self.llm.invoke(langchain_messages)
        
        # Return a formatted response
        return self._format_chat_response(response)

    def embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get text embedding vector

Args:
Text: List of texts

Returns:
Embedded Vector List"""
        if self.embedding_model is None:
            raise ValueError("The embed model is not initialized. Make sure langchain_openai is installed and a valid API key is configured.")
            
        return self.embedding_model.embed_documents(texts)

    async def close(self):
        """Close sessions and resources"""
        # Call the close method of the parent class
        await super().close()
        
        # Close LangChain related resources
        if hasattr(self.llm, "client") and hasattr(self.llm.client, "close"):
            await self.llm.client.close()
        
        if self.embedding_model and hasattr(self.embedding_model, "client") and hasattr(self.embedding_model.client, "close"):
            await self.embedding_model.client.close()