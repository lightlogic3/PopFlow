import json
import random
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple, Union

from app_rag_chat.model.chat_models import UserInfo
from knowledge_api.chat.prompt_utils import find_closest_relationship_level
from knowledge_api.mapper.chat_session.crud import SessionCRUD
from knowledge_api.utils.constant import LLMApplication
from knowledge_api.utils.log_config import get_logger
from knowledge_api.utils.string_tool import remove_parentheses_content
from knowledge_api.framework.memory.enhanced_chat_memory_manager import EnhancedChatMemoryManager
from knowledge_api.framework.tts import ByteDanceTTS
from knowledge_api.mapper.character_prompt_config.crud import CharacterPromptConfigCRUD
from knowledge_api.mapper.conversations.crud import ConversationCRUD
from knowledge_api.mapper.prompt_prologue.crud import PromptPrologueCRUD
from knowledge_api.mapper.relationship_level.crud import RelationshipLevelCRUD
from knowledge_api.framework.redis.cache_manager import CacheManager
from knowledge_api.framework.database.database import get_thread_local_session
from knowledge_api.utils import generate_id
from knowledge_api.chat.session_manager import ChatSessionManager
from knowledge_api.chat.context_manager import ContextManager

# Import a new RAGManager
from knowledge_api.manage.game_knowledge.services.rag_manager import RAGManager

from runtime import ExecutionTimer

logger = get_logger()

class BaseChat:
    """RAG chat service base class"""
    
    # Application scenario identifier, subclasses can be overridden
    llm_application = LLMApplication.BACKEND_CHAT
    
    def __init__(self, chat_type: str = "default"):
        """Initialize RAG chat service

Args:
chat_type: chat type to determine Redis key prefix"""
        # Initialize Session Manager
        self.session_manager = ChatSessionManager(chat_type)
        
        # Get RAG Manager (Singleton Mode)
        self.rag_manager = RAGManager()
        
        # Initialize roles and world services to None, which will be acquired during asynchronous initialization
        self.role_service = None
        self.world_service = None
        
        # database access object
        self.character_prompt_db = CharacterPromptConfigCRUD(get_thread_local_session())
        self.msg_db = ConversationCRUD(get_thread_local_session())
        self.relationship_db = RelationshipLevelCRUD(get_thread_local_session())
        self.prompt_prologue_db = PromptPrologueCRUD(get_thread_local_session())
        self.session_db = SessionCRUD(get_thread_local_session())
        
        # cache manager
        self.cache = CacheManager()
        
        # TTS Engine
        self.bytedance_tts = None
        
        # The context manager needs to be created in asynchronous initialization
        self.context_manager = None
        
    async def ensure_initialized(self):
        """Make sure the service is initialized

Checks if the context manager has been initialized, and if not, calls init_data to initialize
This method can be called by all subclasses to ensure that the necessary initialization has been completed before using the service"""
        if not self.context_manager:
            logger.info(f"The service has not been initialized, and the initialization is performed...")
            await self.init_data()
            logger.info(f"service initialization is complete")
        
    async def init_data(self):
        """Initialize data and obtain service instances"""
        # Initialize TTS configuration
        config = json.loads(await self.cache.get_system_config("BYTE_DANCE_TTS_CONFIG"))
        self.bytedance_tts = ByteDanceTTS(
            appid=config.get("appid"),
            access_token=config.get("access_token"),
            cluster=config.get("cluster")
        )
        
        # Get service through RAG Manager
        logger.info("Acquire roles and world services through RAG Manager")
        self.role_service = await self.rag_manager.get_service("role")
        self.world_service = await self.rag_manager.get_service("world")
        
        # Initialize the context manager
        self.context_manager = ContextManager(self.role_service, self.world_service)
        
        logger.info("RAG service and context manager initialization complete")
    
    async def get_current_session(self, session_id: str) -> Dict[str, Any]:
        """Get current session data

Args:
session_id: Session ID

Returns:
session data dictionary"""
        if not session_id:
            return {}
            
        session_data = await self.session_manager.get_session(session_id)
        return session_data or {}
    
    async def get_user_info(self, session_id: str) -> Dict[str, Any]:
        """Acquire user information

Args:
session_id: Session ID

Returns:
User information dictionary, including user relationship descriptions"""
        session_data = await self.get_current_session(session_id)
        user_info = session_data.get("user_info", {})
        
        # Important: Get a description of the relationship between the role and the user
        # If there is a relationship level, get the corresponding relationship description
        if user_info and "relationship_level" in user_info and user_info["relationship_level"] > 0:
            relationship_data = await self.get_relationship_data(
                user_info.get("role_id"), 
                user_info.get("relationship_level", 0)
            )
            if relationship_data:
                user_info["relationship"] = relationship_data.get("prompt_text", "")
                
        return user_info
    
    async def get_relationship_data(self, role_id: str, relationship_level: int) -> Optional[Dict[str, Any]]:
        """Get Role Relational Data - Get the closest relationship level description from the database

Args:
role_id: Role ID
relationship_level: Relationship Level

Returns:
Role relationship data, including a description field that describes the relationship between the role and the user"""
        if not role_id or relationship_level <= 0:
            return None
            
        # Get all relationship level data for the role
        relationships = await self.relationship_db.get_by_role_id(role_id)
        
        # Find the data closest to the target relationship level
        return find_closest_relationship_level(relationships, relationship_level)
    
    async def init_chat(self, input_data: Any) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """Initialize chat

Args:
input_data: Enter data

Returns:
(is_message, role_data, prologue) tuple"""
        long_term_memory = False
        memory_level= 6
        if hasattr(input_data,"long_term_memory"):
            long_term_memory = input_data.long_term_memory
        if hasattr(input_data, "memory_level"):
            memory_level = input_data.memory_level
        # Create user information
        user_info = UserInfo(
            role_id=input_data.role_id,
            level=input_data.level,
            user_level=input_data.user_level,
            user_id=input_data.user_id,
            user=input_data.user_name,
            relationship_level=input_data.relationship_level,
            long_term_memory=long_term_memory,
            memory_level=memory_level
        ).model_dump()
        
        # Make sure the session ID exists
        if not input_data.session_id:
            input_data.session_id = f"{input_data.user_id}-{generate_id()}"
            logger.info(f"If the session ID is not provided, a new session ID is generated: {input_data.session_id}")
        
        # Initiate session
        await self.init_session(input_data.session_id)
        
        # Update user information in the session
        if input_data.session_id:
            await self.session_manager.update_session(
                input_data.session_id,
                {"user_info": user_info}
            )
        
        # Get character cue word
        role_data = await self.get_role_prompt(input_data.session_id)
        
        # Get the opening statement (if it is an empty message)
        is_message, prologue = await self.get_prologue(input_data.message, input_data.session_id)
        
        # Get role information
        role_info = await self.cache.get_role(user_info.get("role_id"))
        
        # Update the role information of the session
        if input_data.session_id:
            await self.session_manager.update_session(
                input_data.session_id,
                {"role_info": role_info}
            )
        
        return is_message, role_data, prologue
    
    async def chat(self, input_data: Any) -> Dict[str, Any]:
        """Process chat requests

Args:
input_data: Chat Input Data

Returns:
chat response"""
        # Initialize chat
        is_message, role_data, prologue = await self.init_chat(input_data)
        
        # prepare result
        result = {
            "message": "",
            "session_id": input_data.session_id
        }
        
        if is_message:
            # If the user sends an empty message, randomly reply with the opening statement
            result["message"] = prologue
        else:
            # Create a prompt word template
            sources, contexts, prompt = await self.create_template(
                query=input_data.message,
                top_k=input_data.top_k,
                role_data=role_data,
            )
            
            # generate responses
            response = await self._generate_answer(prompt, input_data.temperature, input_data.message)
            
            # Update chat history
            await self.update_chat(response, input_data.message, input_data.session_id)
            
            result["message"] = response
            
            # If necessary, include the source
            if input_data.include_sources:
                result["sources"] = sources
                result["contexts"] = contexts
                
                # Get session record
                session_data = await self.get_current_session(input_data.session_id)
                memory_manager = session_data.get("memory_manager")
                if memory_manager:
                    result["prompt"] = memory_manager.get_chat_history()
        
        # Processing Text To Speech
        if role_data.get("timbre"):
            timer3 = ExecutionTimer("Text To Speech Time:")
            timer3.start()
            tts_data = await self.bytedance_tts.text_to_speech(
                remove_parentheses_content(result["message"]),
                role_data.get("timbre")
            )
            result.update({
                "tts_base64": tts_data.get("data")
            })
            timer3.stop()
        
        return result
    
    async def chat_stream(self, input_data: Any):
        """streaming chat feature

Args:
input_data: Chat Input Data

Yields:
generated text fragment"""
        # Initialize chat
        is_message, role_data, prologue = await self.init_chat(input_data)
        
        # For collecting complete responses
        collected_response = ""
        
        if is_message:
            # If the user sends an empty message, randomly reply with the opening statement
            yield prologue
        else:
            # Create a prompt word template
            sources, contexts, prompt = await self.create_template(
                input_data.message,
                input_data.top_k,
                input_data.session_id,
                role_data=role_data,
            )
            
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
                
                # Processing Text To Speech
                if role_data.get("timbre"):
                    yield "<audio>"
                    tts = await self.bytedance_tts.text_to_speech(
                        remove_parentheses_content(collected_response),
                        role_data.get("timbre")
                    )
                    yield json.dumps(tts.get("data"))
            
            except Exception as e:
                error_msg = f"生成回答时出错: {str(e)}"
                print(error_msg)
                import traceback
                traceback.print_exc()
                yield error_msg
        
        # Update chat history
        await self.update_chat(response=collected_response, msg=input_data.message, session_id=input_data.session_id)
    
    async def init_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Initiate session

Args:
session_id: Session ID

Returns:
session data"""
        # Attempt to resume a session from the database
        memory_manager = await self.search_db_session(session_id)
        
        # If there is no session in the database, load it from Redis
        if session_id:
            session_data = await self.session_manager.get_session(session_id)
            if session_data:
                logger.info(f"从Redis加载会话: {session_id}")
                # return session_data
        
        # If there is no session in Redis, create a new session
        if memory_manager is None:
            memory_manager = EnhancedChatMemoryManager(
                k=20,
                system_message="",
                memory_type='buffer_window',
            )
        
        # Generate session ID
        new_session_id = session_id or str(generate_id())
        
        # Save session to database
        await self.save_session(new_session_id)
        existing_data = await self.get_session_data(session_id)
        # Create a new session
        session_data = await self.session_manager.create_session(
            new_session_id,
            memory_manager=memory_manager,
            additional_data=existing_data
        )
        
        return session_data

    async def get_session_data(self, session_id: str) -> Dict[str, Any]:
        """Helper method for getting session data - adapt to Redis cache

Args:
session_id: Session ID

Returns:
session data dictionary"""
        if not session_id:
            return {}

        # Get session data from session manager
        session_data = await self.session_manager.get_session(session_id)

        # If the session is not found, return an empty dictionary
        return session_data or {}

    async def save_session(self, session_id: str):
        """Save session to database

Args:
session_id: Session ID"""
        # Subclasses can override this method to implement specific saving logic
        pass
    
    async def search_db_session(self, session_id: str) -> Optional[EnhancedChatMemoryManager]:
        """Search sessions from the database

Args:
session_id: Session ID

Returns:
Memory manager, return None if it doesn't exist"""
        # Subclasses can override this method to implement specific query logic
        return None
    
    async def get_role_prompt(self, session_id: str) -> Dict[str, Any]:
        """Get character cue word

Args:
session_id: Session ID

Returns:
Role cue word data"""
        user_info = await self.get_user_info(session_id)
        role = await self.cache.get_nearest_prompt(
            role_id=user_info.get("role_id"),
            current_level=user_info.get("level")
        )
        return role.model_dump()
    
    async def get_prologue(self, message: str, session_id: str) -> Tuple[bool, Optional[str]]:
        """Get the opening statement (when the user sends an empty message)

Args:
Message: User Message
session_id: Session ID

Returns:
(is_message, prologue) tuple"""
        # If the message is empty
        if not message or message == '' or len(message) == 0:
            if not session_id:
                return False, None
            
            # Get session and memory manager
            session_data = await self.get_current_session(session_id)
            if not session_data:
                return False, None
                
            memory_manager = session_data.get("memory_manager")
            if not memory_manager:
                return False, None
            
            # Acquire user information
            user_info = session_data.get("user_info", {})
            
            # Get the first chat history
            prompt = await self.cache.get_nearest_prompt(
                role_id=user_info.get("role_id"),
                current_level=user_info.get("level")
            )
            
            prologue_list = await self.prompt_prologue_db.get_by_prompt_id(prompt_id=prompt.id)
            prologue = random.choice([prologue.prologue for prologue in prologue_list])
            
            # Update Memory Manager
            memory_manager.add_ai_message(prologue)
            
            # Updating a conversation in Redis
            await self.session_manager.update_session(
                session_id,
                {"memory_manager": memory_manager}
            )
            
            return True, prologue
        else:
            return False, None
    
    async def create_template(self, query: str, top_k: int, session_id: Optional[str] = None,
                           prompt_type: str = "system_prompt", extended: Optional[Dict[str, Any]] = None, 
                           role_data: Optional[Dict[str, Any]] = None) -> Tuple[List[Dict[str, Any]], List[str], str]:
        """Create a prompt word template

Args:
Query: user messages
top_k: Number of most similar documents returned
session_id: Session ID
prompt_type: Cue word types
Extended: extended parameters
role_data: Role Data

Returns:
(Sources, contexts, prompts) tuple"""
        user_info = await self.get_user_info(session_id)
        
        # Create templates using the context manager
        return await self.context_manager.create_retrieval_template(
            query, top_k, prompt_type, user_info, extended, role_data
        )
    
    async def update_chat(self, response: Union[str, Any], msg: str, session_id: Optional[str] = None):
        """Update chat history

Args:
Response: AI response
Msg: user messages
session_id: Session ID"""
        if not session_id:
            return
            
        # Get session data
        session_data = await self.get_current_session(session_id)
        if not session_data:
            return
            
        # Get Memory Manager
        memory_manager = session_data.get("memory_manager")
        if not memory_manager:
            return
        # Add user messages to history
        memory_manager.add_user_message(msg)
        # Add a message to history
        if isinstance(response, str):
            memory_manager.add_ai_message(response)
        else:
            try:
                response_content = response.content
                memory_manager.add_ai_message(response_content)
            except AttributeError:
                # Object has no content attribute, try using str
                memory_manager.add_ai_message(str(response))
        
        # Update session message count
        message_count = session_data.get("message_count", 0) + 1

        # Save the updated session
        await self.session_manager.update_session(
            session_id,
            {
                "memory_manager": memory_manager,
                "message_count": message_count,
                "last_activity": datetime.now().isoformat()
            }
        )
    
    async def get_ai(self, msg: str, prompt: str, session_id: Optional[str] = None):
        """Acquire AI models and conversation history

Args:
Msg: user messages
Prompt: prompt word
session_id: Session ID

Returns:
(Ai, messages) tuple"""
        # Get session data
        session_data = await self.get_current_session(session_id)
        if not session_data:
            # Create default memory manager
            memory_manager = EnhancedChatMemoryManager(
                k=20,
                system_message=prompt,
                memory_type='buffer_window',
            )
            memory_manager.add_user_message(msg)
        else:
            # Using the in-session memory manager
            memory_manager = session_data.get("memory_manager")
            if memory_manager:
                memory_manager.update_system_message(prompt)
                memory_manager.add_user_message(msg)
        
        # Acquire role information and choose the appropriate AI model
        role_info = session_data.get("role_info") if session_data else None
        
        if role_info and getattr(role_info, 'llm_choose', None):
            # Select the specified AI model
            ai = await self.cache.get_ai_by_model_id(role_info.llm_choose)
        else:
            # Use the default AI model
            ai = await self.cache.get_ai()
        
        return ai, memory_manager.get_formatted_history()
    
    async def _generate_answer(self, prompt: str, temperature: float = 0.7, msg: str = "") -> str:
        """generate responses

Args:
Prompt: prompt word
Temperature: generating temperature
Msg: user messages

Returns:
generated answer"""
        try:
            # Acquire AI models and conversation history
            ai, messages = await self.get_ai(msg=msg, prompt=prompt)
            
            # generate responses
            response = await ai.chat_completion(
                messages=messages, 
                temperature=temperature,
                application_scenario=self.llm_application
            )
            
            return response.content
        except Exception as e:
            logger.error(f"an error occurred while generating the response: {e}")
            import traceback
            traceback.print_exc()
            return f"an error occurred while generating the response: {str(e)}"
    
    async def clear_session(self, session_id: str) -> Dict[str, Any]:
        """Clear session history

Args:
session_id: Session ID

Returns:
operation result"""
        # Clear session history
        success = await self.session_manager.clear_session_data(session_id)
        
        if success:
            return {
                "session_id": session_id,
                "message": "Session history cleared"
            }
        else:
            return {
                "session_id": session_id,
                "message": "Failed to clear session history"
            }
    
    async def delete_session(self, session_id: str) -> Dict[str, Any]:
        """Delete session

Args:
session_id: Session ID

Returns:
operation result"""
        # Delete session
        success = await self.session_manager.delete_session(session_id)
        
        if success:
            return {
                "session_id": session_id,
                "message": "Session deleted"
            }
        else:
            return {
                "session_id": session_id,
                "message": "Delete session failed"
            }
    
    async def close(self):
        """Close all resources"""
        pass
    
    async def middleware_clear(self, message: str) -> str:
        """Understand the user's true intentions

Args:
Message: User Message

Returns:
user intent analysis"""
        logger.warning("middleware_clear need subclass implementation")
        return "Not yet implemented" 