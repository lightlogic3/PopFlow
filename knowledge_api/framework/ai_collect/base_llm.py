from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, AsyncGenerator, ClassVar, Type
import aiohttp
from contextlib import asynccontextmanager
import uuid
import time
from pydantic import BaseModel, Field, root_validator
from decimal import Decimal

from knowledge_api.framework.ai_collect.message import Message
from knowledge_api.framework.ai_collect.function_call.tool_registry import ToolRegistry
from knowledge_api.model.llm_token_model import LLMTokenResponse


class BaseLLM(ABC):
    """AI language model base class, defining common interfaces and methods"""
    # Class attributes that store all LLM type mappings
    _registry: ClassVar[Dict[str, Type['BaseLLM']]] = {}

    # LLM type identifier (subclasses must override this attribute)
    llm_type: ClassVar[str] = None

    # This method is automatically called when a subclass is created
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Checks if the subclass defines llm_type
        if cls.llm_type is not None:
            print(f"automatic registration of llm types: {cls.llm_type} -> {cls.__name__}")
            BaseLLM._registry[cls.llm_type] = cls

    def __init__(self, api_key: str, base_url: str = None, model: str = None, format_response: bool = True):
        """Initialize basic configuration

Args:
api_key: API Key
Model: model name
format_response: Whether the response format is uniform, the default is True"""
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.format_response = format_response
        self._session = None
        self._initialize()
        self.is_function_call = False

    @abstractmethod
    def _initialize(self) -> None:
        """Initial model configuration"""
        pass

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an AIOHTTP session to optimize performance using connection pooling

Returns:
AioHTTPS. ClientSession: HTTP session object"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(
                limit=100,  # Connection pool size
                ttl_dns_cache=300,  # DNS cache time
                use_dns_cache=True,
                keepalive_timeout=60
            )
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes timeout
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=self.headers
            )
        return self._session

    @asynccontextmanager
    async def _get_streaming_response(self, url: str, payload: Dict) -> AsyncGenerator[str, None]:
        """Get a context manager for streaming responses

Args:
URL: API endpoint
Payload: request parameters

Yields:
AsyncGenerator: Streaming Response Generator"""
        session = await self._get_session()
        messages = payload.get("messages", [])
        if len(messages) > 1 and isinstance(messages[0], Message):
            messages = [msg.to_dict() for msg in payload.get("messages", [])]
        payload["messages"] = messages
        try:
            async with session.post(url, json=payload) as response:
                yield response
        except Exception as e:
            print(f"there was an error with the streaming request: {e}")
            raise

    async def chat_completion(
            self,
            messages: List[Dict[str, str]],
            temperature: float = 0.7,
            max_tokens: Optional[int] = None,
            application_scenario: Optional[str] = None,
            **kwargs
    ) -> LLMTokenResponse:
        """Chat completes the interface template method, the child class realizes the specific API call, and the parent class is responsible for the general process

Args:
Messages: conversation history
Temperature: temperature parameters, control randomness
max_tokens: Maximum number of tokens generated
application_scenario: Application Scenario Identification
** kwargs: other model-specific parameters

Returns:
LLMTokenResponse: Standardized model response results"""
        # Record start time
        start_time = time.time()
        
        # Call the actual API call of the subclass implementation
        response_data = await self._chat_completion_impl(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )

        # Log token statistics
        price=await self._log_token_stats(response_data, start_time, messages, application_scenario)
        response_data.price = price
        return response_data
    
    @abstractmethod
    async def _chat_completion_impl(
            self,
            messages: List[Dict[str, str]],
            temperature: float = 0.7,
            max_tokens: Optional[int] = None,
            **kwargs
    ) ->LLMTokenResponse:
        """The actual chat completion API call is implemented by subclasses

Args:
Messages: conversation history
Temperature: temperature parameters, control randomness
max_tokens: Maximum number of tokens generated
** kwargs: other model-specific parameters

Returns:
Dict [str, Any]: Raw model response result"""
        pass

    async def _log_token_stats(self, response: LLMTokenResponse, start_time=None, messages=None, application_scenario=None) -> float:
        """Record token statistics and save to database

Args:
Response: Standardized response results
start_time: start time, use elapsed_time in response if not provided
Messages: request a list of messages, save the context if provided
application_scenario: Application Scenario Identification"""
        # Simple printing implementation
        current_time = time.time()
        elapsed = current_time - start_time if start_time else response.elapsed_time
        
        # Print basic information
        print(f"[{self.llm_type}] token statistics input={response.input_tokens}, output={response.output_tokens}, total={response.total_tokens}, take={elapsed:.2f}seconds")
        
        # Attempt to save the record to the database
        try:
            # Dynamic import to avoid circular dependencies
            from knowledge_api.framework.database.database import get_session
            from knowledge_api.mapper.llm_usage_records.crud import LLMUsageRecordCRUD
            from knowledge_api.mapper.llm_usage_contexts.crud import LLMUsageContextCRUD
            from knowledge_api.framework.redis.cache_manager import CacheManager
            # Get database session
            session = next(get_session())
            
            # Create master record
            record_crud = LLMUsageRecordCRUD(session)
            
            # Building responsive data
            response_data = {
                "id": response.id,
                "content": response.content,
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
                "total_tokens": response.total_tokens,
                "role": response.role,
                "finish_reason": response.finish_reason,
                "elapsed_time": elapsed,
                "model_id": self.model,
                "total_price": 0.0,
            }
            # Get the model configuration in the cache based on the model ID
            model_config = await CacheManager().get_model_config(response.model)
            if model_config:
                # Using Decimal to Handle Accuracy Issues
                output_price = Decimal(str(model_config.output_price)) * Decimal(str(response.output_tokens)) / Decimal('1000')
                input_price = Decimal(str(model_config.input_price)) * Decimal(str(response.input_tokens)) / Decimal('1000')
                # Calculate the total price, keeping 8 decimal places
                response_data["total_price"] = float(output_price + input_price)
            else:
                # If no model configuration is found, set to 0.
                response_data["total_price"] = 0.0
            
            # Create usage record
            record = await record_crud.create_from_response(
                response_data=response_data,
                vendor_type=self.llm_type,
                model_id=self.model,
                application_scenario=application_scenario
            )
            
            # If messages are provided, a context record is created
            if messages and record:
                context_crud = LLMUsageContextCRUD(session)
                
                # Prepare additional data
                additional_data = {
                    "model_config": {
                        "model": self.model,
                        "vendor_type": self.llm_type
                    }
                }
                
                # Create context record
                await context_crud.create_from_messages(
                    record_id=record.id,
                    messages=messages,
                    additional_data=additional_data
                )
            return response_data["total_price"]
                
        except Exception as e:
            print(f"保存LLM使用记录失败: {str(e)}")
            import traceback
            traceback.print_exc()
            # Only errors are printed here, but no exceptions are thrown to avoid affecting the normal process.
        return 0.0

    @abstractmethod
    async def _function_call_impl(self, messages, tools: ToolRegistry, model: str = "doubao-pro-32k-functioncall-241028"):
        pass

    async def function_call(self, messages: List[Dict[str, str]], tools: ToolRegistry, model: str = "doubao-pro-32k-functioncall-241028"
                            , application_scenario:str="base") -> (List[Dict[str, Any]], Dict[str, Any], LLMTokenResponse):
        """function call interface

Args:
Messages: conversation history
Tools: tools regedit
Model: model name
application_scenario: application scenarios

Returns:
LLMTokenResponse: Standardized model response results"""
        # Record start time
        start_time = time.time()
        # Call the actual API call of the subclass implementation
        tool_results, assistant_message,completion = await self._function_call_impl(
            messages=messages,
            tools=tools,
            model=model
        )

        # Log token statistics
        price=await self._log_token_stats(completion, start_time, messages,f"{application_scenario}-function_call")
        completion.price = price
        return tool_results, assistant_message,completion

    async def chat_completion_stream(
            self,
            messages: List[Dict[str, str]],
            temperature: float = 0.7,
            max_tokens: Optional[int] = None,
            application_scenario: Optional[str] = None,
            **kwargs
    ) -> AsyncGenerator[LLMTokenResponse, None]:
        """Asynchronous streaming chat interface template method, the child class realizes the specific API call, and the parent class is responsible for the general process

Args:
Messages: conversation history
Temperature: temperature parameters, control randomness
max_tokens: Maximum number of tokens generated
application_scenario: Application Scenario Identification
** kwargs: other model-specific parameters

Yields:
LLMTokenResponse: Streaming response fragment"""
        # Record start time
        start_time = time.time()
        
        # Store the last response fragment for statistical purposes
        last_chunk = None
        accumulated_content = ""
        
        # Call the streaming API call implemented by the subclass
        try:
            async for chunk in self._chat_completion_stream_impl(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            ):

                # Set request time
                current_time = time.time()
                chunk.elapsed_time = current_time - start_time
                
                # cumulative content
                if hasattr(chunk, "content"):
                    accumulated_content += chunk.content
                
                # Save the last fragment for final statistics
                last_chunk = chunk
                
                yield chunk
                
            # Statistics after the end of the streaming response
            if last_chunk:
                # Log token statistics
                await self._log_token_stats(
                    last_chunk,
                    start_time, 
                    messages, 
                    application_scenario
                )
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            # Generate an error response when an exception occurs
            error_response = LLMTokenResponse(
                id=f"error-{time.time()}",
                model=self.model,
                content=f"there was an error with the streaming request: {str(e)}",
                role="assistant",
                finish_reason="error",
                elapsed_time=time.time() - start_time
            )
            yield error_response
            
            # Log error statistics
            await self._log_token_stats(error_response, start_time, messages, application_scenario)


    def _build_final_response_from_stream(self, last_chunk: Dict[str, Any], accumulated_content: str) -> Dict[str, Any]:
        """Build the final response object from the streaming response for statistical purposes

Args:
last_chunk: Last response snippet
accumulated_content: Cumulative full content

Returns:
Dict [str, Any]: Constructed full response object"""
        # Building a complete response based on the last fragment
        final_response = {
            "id": last_chunk.get("id", f"stream-{time.time()}"),
            "model": last_chunk.get("model", self.model),
            "choices": [{
                "message": {
                    "content": accumulated_content,
                    "role": "assistant"
                },
                "finish_reason": last_chunk.get("choices", [{}])[0].get("finish_reason", "stop") 
                                 if "choices" in last_chunk and len(last_chunk.get("choices", [])) > 0 else "stop"
            }],
            "usage": last_chunk.get("usage", {})
        }
        
        return final_response

    @abstractmethod
    async def _chat_completion_stream_impl(
            self,
            messages: List[Dict[str, str]],
            temperature: float = 0.7,
            max_tokens: Optional[int] = None,
            **kwargs
    ) -> AsyncGenerator[LLMTokenResponse, None]:
        """The actual streaming chat is completed API call implementation, implemented by subclasses

Args:
Messages: conversation history
Temperature: temperature parameters, control randomness
max_tokens: Maximum number of tokens generated
** kwargs: other model-specific parameters

Yields:
Dict [str, Any]: Raw streaming response fragment"""
        pass

    @abstractmethod
    def completion(
            self,
            prompt: str,
            temperature: float = 0.7,
            max_tokens: Optional[int] = None,
            **kwargs
    ) -> Dict[str, Any]:
        """synchronous text completion interface

Args:
Prompt: Enter prompt text
Temperature: temperature parameters, control randomness
max_tokens: Maximum number of tokens generated
** kwargs: other model-specific parameters

Returns:
Dict [str, Any]: model response result"""
        pass

    @abstractmethod
    def embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get text embedding vector

Args:
Text: input text list

Returns:
List [List [float]]: List of text vectors"""
        pass

    def _format_chat_response(self, response: Dict[str, Any]) -> LLMTokenResponse:
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
        if not self.format_response:
            return response

        return response  # Subclasses need to override this method

    def _format_stream_response(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Uniformly format streaming response snippets

Uniform format:
{
"Id": "Session ID",
"Model": "Model name",
"Created": timestamp,
"Delta": {
"Content": "Current fragment content",
"Role": "assistant"
},
"finish_reason": null or "stop"
}"""
        if not self.format_response:
            return chunk

        return chunk  # Subclasses need to override this method

    async def close(self):
        """Close session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    def _validate_and_clean_messages(self, messages):
        """Verify and clean the message list to ensure that all tool_call_id have corresponding tool_calls.id

Args:
Messages: Message List

Returns:
Cleaned message list"""
        # Collect IDs from all tool_calls
        valid_ids = set()
        for msg in messages:
            if "tool_calls" in msg and msg["tool_calls"]:
                for tool_call in msg["tool_calls"]:
                    if "id" in tool_call:
                        valid_ids.add(tool_call["id"])

        # Filter out all tool messages without corresponding tool_calls.id
        filtered_messages = []
        for msg in messages:
            # System messages are always retained
            if msg.get("role") == "system":
                filtered_messages.append(msg)
                continue

            # Check if the tool_call_id of the tool message has a corresponding id.
            if msg.get("role") == "tool" and "tool_call_id" in msg:
                if msg["tool_call_id"] in valid_ids:
                    filtered_messages.append(msg)
                # If there is no corresponding id, skip this message
            else:
                # Non-tool message retention
                filtered_messages.append(msg)

        return filtered_messages


# Update the LLMTokenResponse model to add additional metrics
class TokenStats(BaseModel):
    """Token Statistical Information Model"""
    input_tokens: Optional[int] = Field(-1, description="Enter number of tokens")
    output_tokens: Optional[int] = Field(-1, description="Number of output tokens")
    total_tokens: Optional[int] = Field(-1, description="Total tokens")
    elapsed_time: Optional[float] = Field(0.0, description="Request time (seconds)")


# Message Model Definition
class GameMessage(BaseModel):
    """Game message model for validating and standardizing message formats"""
    msgId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str
    content: str
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))
    sessionId: Optional[str] = None  # Session ID field
    agentId: Optional[str] = None
    replyTo: Optional[str] = None
    isHint: Optional[bool] = None
    isReveal: Optional[bool] = None
    playerIndex: Optional[int] = None

    @root_validator(pre=True)
    def set_defaults(cls, values):
        """Set default values to ensure that necessary fields are present"""
        if "role" not in values:
            values["role"] = "system"
        if "content" not in values and values.get("role") == "system":
            values["content"] = "System message"
        return values

    class Config:
        # Allow additional fields to support future extensions
        extra = "allow"
