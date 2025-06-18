from datetime import datetime
from typing import Any, Dict, Optional, Tuple, AsyncGenerator, Union

from app_rag_chat.model.chat_models import UserInfo
from knowledge_api.chat.base_chat import BaseChat
from knowledge_api.mapper.character_prompt_config.base import CharacterPromptConfig
from knowledge_api.model.llm_model import ChatTestInput
from knowledge_api.utils.constant import LLMApplication
from knowledge_api.utils.log_config import get_logger
from plugIns.memory_system import MemoryManager, MemoryLevel
from plugIns.memory_system.model import MemoryContext
import json
logger = get_logger()


class RAGChatStreamManage(BaseChat):
    """RAG Managed Streaming Chat Service"""
    
    def __init__(self):
        """Initialize RAG streaming chat service"""
        super().__init__(chat_type="stream")
    
    async def chat_stream(self, input_data: ChatTestInput) -> AsyncGenerator[str, None]:
        """streaming chat

Args:
input_data: Chat Input Data

Yields:
generated text fragment"""
        # Make sure the service and context manager are initialized
        await self.ensure_initialized()
            
        async for token in self.chat_stream_internal(input_data):
            yield token
            
    async def chat_stream_internal(self, input_data: ChatTestInput) -> AsyncGenerator[str, None]:
        """internal streaming chat processing

Args:
input_data: Chat Input Data

Yields:
generated text fragment"""
        # Initialize chat
        is_message, role_data, prologue = await self.init_chat(input_data)
        
        if is_message:
            # If the user sent an empty message, reply to the opening statement
            yield prologue
        else:
            # Create a prompt word template
            sources, contexts, prompt = await self.create_template(
                query=input_data.message,
                top_k=input_data.top_k,
                session_id=input_data.session_id,
                role_data=role_data
            )
            
            # Collect complete responses
            collected_response = ""
            
            try:
                # Acquire AI models
                ai, messages = await self.get_ai(msg=input_data.message, prompt=prompt, session_id=input_data.session_id)
                
                # stream generated responses
                if input_data.way == "half":
                    # Half-stream output (batch output)
                    half_tem = []
                    async for chunk in ai.chat_completion_stream(messages, application_scenario=self.llm_application):
                        if chunk.content:
                            collected_response += chunk.content
                            half_tem.append(chunk.content)
                            if len(half_tem) > 10:
                                tem = half_tem.copy()
                                half_tem.clear()
                                yield "".join(tem)
                        else:
                            yield "".join(half_tem)
                else:
                    # full streaming output
                    async for chunk in ai.chat_completion_stream(messages, application_scenario=self.llm_application):
                        if chunk.content:
                            collected_response += chunk.content
                            yield chunk.content
                yield "<div>"
                # Processing Text To Speech
                if role_data.get("timbre"):
                    from knowledge_api.utils.string_tool import remove_parentheses_content
                    tts = await self.bytedance_tts.text_to_speech(
                        remove_parentheses_content(collected_response),
                        role_data.get("timbre")
                    )

                    yield json.dumps(tts.get("data"))

                yield "<div>"
                yield json.dumps(sources)
            except Exception as e:
                error_msg = f"生成回答时出错: {e}"
                logger.error(error_msg)
                import traceback
                traceback.print_exc()
                yield error_msg
        
        # Update chat history
        await self.update_chat(response=collected_response, msg=input_data.message, session_id=input_data.session_id)

    async def init_chat(self, input_data: ChatTestInput) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """Initialize chat

Args:
input_data: Chat Test Input Data

Returns:
(is_message, role_data, prologue) tuple"""
        # Make sure the service and context manager are initialized
        await self.ensure_initialized()
            
        # Create user information
        user_info = UserInfo(
            role_id=input_data.role_id,
            level=input_data.level,
            user_level=input_data.user_level,
            user_id="admin_test",
            user=input_data.user_name,
            relationship_level=input_data.relationship_level,
            long_term_memory=input_data.long_term_memory,
            memory_level=input_data.memory_level
        ).model_dump()
        
        # Initiate session
        await self.init_session(input_data.session_id)
        
        # Update user information in the session
        if input_data.session_id:
            await self.session_manager.update_session(
                input_data.session_id,
                {"user_info": user_info}
            )
        
        # Create Role Data
        role_data = CharacterPromptConfig(
            role_id=input_data.role_id,
            level=input_data.level,
            prompt_text=input_data.role_prompt,
            prologue=input_data.role_prologue,
            dialogue=input_data.role_dialogue,
            timbre="",
            status=1,
            type="role",
        ).model_dump()
        
        # Get the opening statement
        is_message, prologue = await self.get_prologue(input_data.message, input_data.session_id)
        
        # Get role information
        role_info = await self.cache.get_role(user_info.get("role_id"))
        
        # Update role information in the session
        if input_data.session_id:
            await self.session_manager.update_session(
                input_data.session_id,
                {"role_info": role_info}
            )
        
        return is_message, role_data, prologue

    async def create_template(self, query, top_k, session_id, role_data):
        """Create a retrieval template and ensure that the context manager is initialized

Args:
Query: query text
top_k: Number of similar documents returned
session_id: Session ID
role_data: Role Data

Returns:
Sources, contexts, prompt tuples"""
        # Make sure the service and context manager are initialized
        await self.ensure_initialized()
        
        # Acquire user information
        user_info = await self.get_user_info(session_id)
            
        # Call the create_retrieval_template method of the context manager, paying attention to the parameter order and name
        return await self.context_manager.create_retrieval_template(
            query=query,
            top_k=top_k,
            prompt_type="system_prompt",
            user_info=user_info,
            extended=None,
            role_data=role_data
        )

    async def save_session(self, session_id: str):
        """Save session data to database

Args:
session_id: Session ID"""
        logger.info(f"后台管理：{session_id}: 保存会话数据")
        # Subclasses can implement specific database storage logic here

    async def search_db_session(self, session_id: str):
        """Query session history from the database

Args:
session_id: Session ID

Returns:
session memory manager object"""
        logger.info(f"后台管理：{session_id} 历史记录查询")
        # Subclasses can implement specific database query logic here
        return None



    async def update_chat(self, response: Union[str, Any], msg: str, session_id: Optional[str] = None):
        """Update chat history

Args:
Response: AI generated response
Msg: Message sent by user
session_id: Session ID"""
        await super().update_chat(
            response=response,
            msg=msg,
            session_id=session_id,
        )
        user_info = await self.get_user_info(session_id)
        # Add long-term memory
        if user_info.get("long_term_memory", False):
            memory_manager = MemoryManager()
            await memory_manager.set_memory_level(MemoryLevel(user_info.get("memory_level", 6)))
            user_id=user_info.get("user_id")
            role_id = user_info.get("role_id")
            # Store user issues (a bit earlier, ensure order)
            user_memory_context = MemoryContext(
                content=msg,
                source="user",
                metadata={
                    "message_id": f"user_{datetime.now()}",
                    "conversation_pair": True  # Tag as conversation pair
                },
                timestamp=datetime.now()
            )

            await memory_manager.store(
                memory_context=user_memory_context,
                user_id=user_id,
                role_id=role_id,
            )

            # Store AI responses (later, ensure order)
            ai_timestamp = datetime.now()
            ai_msg = response
            if not isinstance(response, str):
                ai_msg=response.content

            ai_memory_context = MemoryContext(
                content=ai_msg,
                source="assistant",
                metadata={
                    "message_id": f"ai_{ai_timestamp.timestamp()}",
                    "model": "test",
                    "conversation_pair": True  # Tag as conversation pair
                },
                timestamp=ai_timestamp
            )

            await memory_manager.store(
                memory_context=ai_memory_context,
                user_id=user_id,
                role_id=role_id,
            )

