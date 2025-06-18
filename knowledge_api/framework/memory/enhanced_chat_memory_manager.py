import json
from typing import Optional, Dict, Any, List, Union
from langchain.memory import (
    ConversationBufferWindowMemory,
    ConversationSummaryMemory,
    ConversationEntityMemory,
)
from langchain.llms.base import BaseLLM
from langchain.schema import AIMessage, HumanMessage, SystemMessage, BaseMessage, FunctionMessage
from langchain_community.memory.kg import ConversationKGMemory
import time

class EnhancedChatMemoryManager:
    """Enhanced Chat Memory Manager
A memory management system customized for AI conversation scenarios to ensure that SystemMessage is permanently retained"""

    def __init__(self,
                 system_message: str,
                 memory_type: str = 'buffer_window',
                 llm: Optional[BaseLLM] = None,
                 summary_message: str = "Dialogue summary: There is no dialogue content yet.",
                 **kwargs):
        """Initialize Enhanced Chat Memory Manager

@Param system_message: System prompt message defining AI roles and behaviors
@Param memory_type: type of memory ('buffer_window', 'summary', 'entity', 'knowledge_graph')
@Param llm: Language model instances for summarization and knowledge extraction
@Param summary_message: Initial summary message content
@Param kwargs: other configuration parameters"""
        self.memory_type = memory_type
        self.llm = llm
        self.kwargs = kwargs
        self.system_message = system_message
        self.summary_message = summary_message
        self.exchange_count = 0  # Record conversation rounds to trigger automatic summaries
        self._initialize_memory()

    def _initialize_memory(self) -> None:
        """Initialize Memory Manager"""
        if self.memory_type == 'buffer_window':
            self.memory = ConversationBufferWindowMemory(
                k=self.kwargs.get('k', 2),
                return_messages=True
            )
        elif self.memory_type == 'summary':
            if self.llm is None:
                raise ValueError("Abstract Memory requires language model (llm) parameters")
            self.memory = ConversationSummaryMemory(
                llm=self.llm,
                max_token_limit=self.kwargs.get('max_token_limit', 2000),
                return_messages=True
            )
        elif self.memory_type == 'entity':
            if self.llm is None:
                raise ValueError("Entity memory requires language model (llm) parameters")
            self.memory = ConversationEntityMemory(
                llm=self.llm,
                k=self.kwargs.get('k', 3),
                return_messages=True
            )
        elif self.memory_type == 'knowledge_graph':
            if self.llm is None:
                raise ValueError("Knowledge Graph memory requires language model (llm) parameters")
            self.memory = ConversationKGMemory(
                llm=self.llm,
                k=self.kwargs.get('k', 3),
                return_messages=True
            )
        else:
            raise ValueError(f"不支持的记忆类型: {self.memory_type}")

        # Add system messages and summary messages immediately after initialization
        self._initialize_system_and_summary()

    def _initialize_system_and_summary(self) -> None:
        """Initialization system message and summary message
Make sure the system message is in the first place and the summary message is in the second place"""
        # Save the current message
        current_messages = self.memory.chat_memory.messages.copy()
        
        # Clear the current message list
        self.memory.chat_memory.clear()
        
        # Add the system message as the first message
        self.memory.chat_memory.messages.append(SystemMessage(content=self.system_message))
        
        # Add summary message as second message
        self.memory.chat_memory.messages.append(SystemMessage(content=self.summary_message))
        
        # Restore previous messages (excluding system messages and summary messages)
        for msg in current_messages:
            if not isinstance(msg, SystemMessage):
                self.memory.chat_memory.messages.append(msg)

    def _add_system_message_to_memory(self) -> None:
        """Add system messages to memory
(Internal method to ensure that system messages are always at the beginning of the conversation)"""
        # Now use a more comprehensive initialization method to ensure that both the system message and the summary message are present
        self._ensure_system_and_summary_present()

    def _ensure_system_and_summary_present(self) -> None:
        """Make sure that both the system message and the summary message exist
The system message should be in the first place, and the summary message should be in the second place"""
        messages = self.memory.chat_memory.messages
        
        # Check for system messages and summary messages
        has_system = any(isinstance(msg, SystemMessage) and msg.content == self.system_message 
                         for msg in messages)
        has_summary = any(isinstance(msg, SystemMessage) and msg.content.startswith("Dialogue summary:") 
                          for msg in messages)
        
        if not (has_system and has_summary):
            # Save non-system messages
            non_system_messages = [msg for msg in messages 
                                  if not isinstance(msg, SystemMessage)]
            
            # clear message list
            self.memory.chat_memory.clear()
            
            # Add system messages and summary messages
            self.memory.chat_memory.messages.append(SystemMessage(content=self.system_message))
            self.memory.chat_memory.messages.append(SystemMessage(content=self.summary_message))
            
            # Add other messages
            self.memory.chat_memory.messages.extend(non_system_messages)

    def update_system_message(self, new_system_message: str) -> None:
        """Update system message

@Param new_system_message: new system message content"""
        self.system_message = new_system_message

        # Find and update system messages
        for i, message in enumerate(self.memory.chat_memory.messages):
            if isinstance(message, SystemMessage) and i == 0:
                self.memory.chat_memory.messages[i] = SystemMessage(content=new_system_message)
                return

        # If no system message is found, initialize the system and summarize the message
        self._initialize_system_and_summary()

    def update_summary_message(self, new_summary: str) -> None:
        """Update summary message

@Param new_summary: New summary content"""
        # Make sure the summary content has a standard prefix
        if not new_summary.startswith("Dialogue summary:"):
            new_summary = f"对话总结：{new_summary}"
            
        self.summary_message = new_summary
        
        # Find and update summary messages (should be in second place)
        if len(self.memory.chat_memory.messages) >= 2:
            if isinstance(self.memory.chat_memory.messages[1], SystemMessage):
                self.memory.chat_memory.messages[1] = SystemMessage(content=new_summary)
                return
                
        # If the summary message is not in the second place, reinitialize the message order
        self._initialize_system_and_summary()

    def add_user_message(self, message: str) -> None:
        """Add user messages to memory

@param message: user message text"""
        self.memory.chat_memory.add_user_message(message)
        self._ensure_system_and_summary_present()
        
        # Increase interaction count
        self.exchange_count += 0.5
        # Note: The summary is not automatically triggered here, and the external summary service is responsible for it.

    def add_ai_message(self, message: str) -> None:
        """Add AI reply to memory

@param message: AI reply text"""
        self.memory.chat_memory.add_ai_message(message)
        self._ensure_system_and_summary_present()
        
        # Increase interaction count
        self.exchange_count += 0.5
        # Note: The summary is not automatically triggered here, and the external summary service is responsible for it.

    def add_ai_tool_call(self, tool_call: Dict[str, Any]) -> None:
        """Add AI tool calls to memory

@Param tool_call: AI tool call information, including tool name, ID and parameters"""
        # Create tool call message
        # Note: LangChain uses a different tool call format from Doubao/OpenAI
        # Need to adjust the format
        
        # Extract tool call information
        tool_call_id = tool_call.get("id", "")
        function_name = tool_call.get("function", {}).get("name", "")
        function_args = tool_call.get("function", {}).get("arguments", "{}")
        
        # Building LangChain-compatible tool calls
        langchain_tool_call = {
            "id": tool_call_id,
            "name": function_name,
            "args": function_args
        }
        
        # Create AIMessage
        ai_message = AIMessage(content="")
        # Add tool call information to additional_kwargs
        ai_message.additional_kwargs = {
            "tool_calls": [langchain_tool_call]
        }
        
        # Add to memory
        self.memory.chat_memory.messages.append(ai_message)
        self._ensure_system_and_summary_present()

    def add_tool_result(self, tool_call_id: str, content: str, name: str = None) -> None:
        """Add tool call result to memory

@Param tool_call_id: Tool call ID to associate request and response
@Param content: the result content of the tool call
@Param name: optional tool name"""
        # Create tool result message
        # Using FunctionMessage in LangChain to represent tool results
        function_message = FunctionMessage(
            name=name or "",
            content=content
        )

        # Add additional properties for use when formatting
        function_message.additional_kwargs = {
            "tool_call_id": tool_call_id
        }

        # Add to memory
        self.memory.chat_memory.messages.append(function_message)
        self._ensure_system_and_summary_present()

    def add_function_call_exchange(self, ai_response: Dict[str, Any], content: str) -> None:
        """Add complete function call interaction (model call + result) to memory
Function call format for LLM APIs such as Volcano Engine

@Param ai_response: Full response returned by the model, including tool_calls
@Param tool_result: Tool call result"""
        # First add the AI message (with tool call).
        # if "content" in ai_response and ai_response["content"]:
        #     #If the AI returns both normal content and tool calls
        #     self.add_ai_message(ai_response["content"])

        # Add tool call
        if "tool_calls" in ai_response and ai_response["tool_calls"]:
            tool_call = ai_response["tool_calls"][0]  # Get the first tool call
            # Add tool call
            self.add_ai_tool_call(tool_call)
            # Add corresponding tool results
            self.add_tool_result(
                tool_call_id=tool_call["id"],
                content=content,
                name=tool_call["function"]["name"]
            )


    def add_exchange(self, user_message: str, ai_message: str) -> None:
        """Add a complete conversation to your memory

@Param user_message: user message text
@Param ai_message: AI reply text"""
        self.add_user_message(user_message)
        self.add_ai_message(ai_message)

    def _ensure_system_message_present(self) -> None:
        """Make sure the system message exists
Guarantee that system messages are not lost when the memory manager performs an internal reset or purge"""
        # Upgrade to ensure that both system messages and summary messages exist
        self._ensure_system_and_summary_present()

    def get_chat_history(self) -> List[BaseMessage]:
        """Get the full conversation history (including system messages and k-restricted conversations).

@Return: Message object list"""
        # First get the message with the k window limit applied
        memory_variables = self.memory.load_memory_variables({})
        window_limited_messages = memory_variables.get('history', [])

        # Make sure the system message exists
        system_message = next((msg for msg in self.memory.chat_memory.messages
                               if isinstance(msg, SystemMessage)), None)

        if system_message and not any(isinstance(msg, SystemMessage) for msg in window_limited_messages):
            # The system message exists but is not in the window limit message, add it to the beginning of the return list
            return [system_message] + (window_limited_messages if isinstance(window_limited_messages, list) else [])

        return window_limited_messages if isinstance(window_limited_messages, list) else []

    def get_formatted_history(self) -> List[Dict[str, Any]]:
        """Get the formatted chat history and adapt it to the AI model interface
Convert the langchain message object to a dictionary format suitable for sending to the API

@Return: Formatted list of messages, each with a dictionary containing'role 'and'content'"""
        # Get chat history
        messages = self.get_chat_history()
        
        # Format message
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                formatted_messages.append({
                    "role": "system",
                    "content": msg.content
                })
            elif isinstance(msg, HumanMessage):
                formatted_messages.append({
                    "role": "user",
                    "content": msg.content
                })
            elif isinstance(msg, AIMessage):
                # basic message structure
                formatted_msg = {
                    "role": "assistant",
                    "content": msg.content if msg.content else "\n"  # Use newline instead of empty string
                }
                
                # Check if a tool call is included
                if hasattr(msg, "additional_kwargs") and "tool_calls" in msg.additional_kwargs:
                    # Convert from LangChain format to Volcano Engine /Doubao format
                    volcano_tool_calls = []
                    for tool_call in msg.additional_kwargs["tool_calls"]:
                        # Must contain id, name and args
                        if "id" in tool_call and "name" in tool_call and "args" in tool_call:
                            # Make sure arguments is a valid JSON string
                            arguments = tool_call["args"]
                            # Do not handle arguments that are already strings
                            if not isinstance(arguments, str):
                                import json
                                arguments = json.dumps(arguments, ensure_ascii=False)
                                
                            # Note: The order here is important and must match exactly the format required by the API
                            volcano_tool_call = {
                                "id": tool_call["id"],
                                "function": {
                                    "arguments": arguments,
                                    "name": tool_call["name"]
                                },
                                "type": "function"
                            }
                            volcano_tool_calls.append(volcano_tool_call)
                    
                    if volcano_tool_calls:
                        formatted_msg["tool_calls"] = volcano_tool_calls
                
                formatted_messages.append(formatted_msg)
            elif isinstance(msg, FunctionMessage):
                # tool result message
                tool_message = {
                    "role": "tool",
                    "content": msg.content
                }
                
                # Add tool call ID and name - ensure the order meets API requirements
                if hasattr(msg, "additional_kwargs") and "tool_call_id" in msg.additional_kwargs:
                    tool_message["tool_call_id"] = msg.additional_kwargs["tool_call_id"]
                
                # Add name
                if msg.name:
                    tool_message["name"] = msg.name
                
                formatted_messages.append(tool_message)
                
        return formatted_messages

    def get_conversation_string(self) -> str:
        """Get conversation history string representation, follow k window limit

@Return: formatted dialogue history string"""
        result = ""
        for message in self.get_chat_history():
            if isinstance(message, SystemMessage):
                result += f"系统: {message.content}\n"
            elif isinstance(message, HumanMessage):
                result += f"用户: {message.content}\n"
            elif isinstance(message, AIMessage):
                result += f"AI: {message.content}\n"
            elif isinstance(message, FunctionMessage):
                result += f"工具({message.name}): {message.content}\n"
        return result

    def get_context_for_llm(self) -> Dict[str, Any]:
        """Get the context that can be provided directly to the LLM
Make sure that system messages are always at the beginning of a conversation and adhere to the k window limit

@Return: Context dictionary containing dialogue history"""
        # Directly return memory variables with window restrictions
        return self.memory.load_memory_variables({})

    def get_all_messages(self) -> List[BaseMessage]:
        """Get all stored messages without applying window restrictions
For debugging or special scenarios only

@Return: List of all stored messages"""
        return self.memory.chat_memory.messages

    def change_memory_type(self, memory_type: str, **kwargs) -> None:
        """dynamically switching memory types

@Param memory_type: New Types of Memory
@Param kwargs: new configuration parameters"""
        # Save the current conversation history
        current_history = self.get_all_messages()

        # Update the configuration and reinitialize the memory manager
        self.memory_type = memory_type
        self.kwargs.update(kwargs)
        self._initialize_memory()

        # Restore conversation history
        for message in current_history:
            if isinstance(message, SystemMessage):
                # System message has been added at initialization, skip
                continue
            elif isinstance(message, HumanMessage):
                self.memory.chat_memory.add_user_message(message.content)
            elif isinstance(message, AIMessage):
                self.memory.chat_memory.add_ai_message(message.content)

    def clear(self) -> None:
        """Clear all conversation memory content, but keep system messages and summary messages"""
        # Staging system messages and summary messages
        system_msg = self.system_message
        summary_msg = self.summary_message
        
        # Clear all content
        self.memory.clear()
        
        # Reset interaction count
        self.exchange_count = 0
        
        # Re-add system messages and summary messages
        self.system_message = system_msg
        self.summary_message = summary_msg
        self._initialize_system_and_summary()

    def add_function_call_example(self, func_name: str = "function_judge_answer",arguments:Dict[str,Any]=None) -> None:
        """Add an example to the conversation history that shows how to use function calls
This helps train AI to always use specific function calls to answer questions

@Param func_name: The name of the function to example, the default is function_judge_answer"""
        # Add a user example question
        example_question ="This is an example question that you need to call a function to answer"
        self.add_user_message(example_question)
        arguments_str=json.dumps(arguments, ensure_ascii=False)
        # Create AI reply with function call
        tool_call = {
            "id": f"call_example_{int(time.time())}",
            "function": {
                "name": func_name,
                "arguments": arguments_str,
            },
            "type": "function"
        }

        # Example of function call for adding AI
        self.add_ai_tool_call(tool_call)

        # Add Tool Response Example
        self.add_tool_result(
            tool_call_id=tool_call["id"],
            content=arguments_str,
            name=func_name
        )
        
        # Add instructions that emphasize function calls to system messages
        current_system = self.system_message
        if "It must be answered by calling a function" not in current_system:
            enhanced_system = current_system + "\ nSpecial attention: you must pass the call" + func_name + "Function to answer questions, do not output text answers directly."
            self.update_system_message(enhanced_system)

    def get_memory_stats(self) -> Dict[str, Any]:
        """Retrieve memory statistics

@Return: Dictionary containing memory statistics"""
        # Get messages after window limit
        windowed_messages = self.get_chat_history()
        # Get all stored messages
        all_messages = self.get_all_messages()

        stats = {
            "memory_type": self.memory_type,
            "stored_message_count": len(all_messages),
            "window_message_count": len(windowed_messages),
            "window_size": self.kwargs.get('k', 2),
            "user_messages_in_window": sum(1 for m in windowed_messages if isinstance(m, HumanMessage)),
            "ai_messages_in_window": sum(1 for m in windowed_messages if isinstance(m, AIMessage)),
            "has_system_message": any(isinstance(m, SystemMessage) for m in windowed_messages),
            "exchange_count": self.exchange_count,
            "summary_message": self.summary_message
        }

        # Add specific statistics for different memory types
        if self.memory_type == 'entity':
            stats["entities"] = list(self.memory.entity_store.keys())
        elif self.memory_type == 'knowledge_graph':
            stats["kg_triplets_count"] = len(self.memory.kg.get_triples())

        return stats

    def get_exchange_count(self) -> float:
        """Get the current conversation round count

@Return: Number of conversation rounds (1 round per complete user-AI interaction)"""
        return self.exchange_count
    
    def should_summarize(self, trigger_interval: int = 5) -> bool:
        """Check if the summary should be triggered

@Param trigger_interval: Interval of conversation rounds that trigger summary
@Return: Should a summary be made?"""
        return self.exchange_count > 0 and self.exchange_count % trigger_interval < 0.5