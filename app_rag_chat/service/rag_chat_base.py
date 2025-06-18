from datetime import datetime

from knowledge_api.chat.base_chat import BaseChat
from knowledge_api.framework.redis.cache_manager import CacheManager

from knowledge_api.mapper.chat_session.base import SessionCreate
from knowledge_api.framework.memory.enhanced_chat_memory_manager import EnhancedChatMemoryManager


class RAGChatService(BaseChat):
    """RAG chat service"""

    def __init__(self, role, world):
        """Initialize RAG chat service"""
        # Flag initialized only once
        super().__init__(role, world)

    async def save_db(self, session_id: str):
        try:
            if not self.session_db.get_by_id(session_id=session_id):
                self.session_db.create(
                    session=SessionCreate(user_id=self.user_info.get("user_id"),
                                          session_id=session_id,
                                          role_id=self.user_info.get("role_id"),
                                          model_name=await CacheManager().get_system_config("DEFAULT_LLM_MODEL"),
                                          session_status="active",
                                          type_session="user"
                                          )
                )
        except Exception as e:
            print(f"Error saving session data: {e}")
            import traceback
            traceback.print_exc()
            # Make sure to close the thread session
            from knowledge_api.framework.database.database import close_thread_session
            close_thread_session()

    async def save_sessions(self, session_id):
        await self.task_manager.submit(
            self.save_db,
            session_id,  # function object            description="Asynchronous Storage Session Task",
        )

    async def search_db_session(self, session_id):
        """Query whether this session is stored in the database"""
        try:
            session = self.session_db.get_by_id(session_id=session_id)
            if session is not None:
                # query message log table
                msg_list = self.msg_db.get_by_session_id(session_id=session_id)
                memory_manager = EnhancedChatMemoryManager(
                    k=5,
                    system_message="",
                    memory_type='buffer_window',
                )
                for msg in msg_list:
                    if msg.role == "user":
                        memory_manager.add_user_message(msg.content)
                    elif msg.role == "assistant":
                        memory_manager.add_ai_message(msg.content)
                return memory_manager
        except Exception as e:
            print(f"Error querying session data: {e}")
            import traceback
            traceback.print_exc()
            # Reset database state
            from knowledge_api.framework.database.database import reset_database_state
            reset_database_state()
        return None


    async def update_chat(self, response, msg):
        await self.task_manager.submit(
            self._background_update_chat,
            response, msg
        )

    async def _background_update_chat(self,response, msg):
        try:
            memory_manager=self.session["memory_manager"]
            memory_manager.add_user_message(msg)
            response_save = response
            if type(response) is not str:
                response_save = response.get("content")
                # Add complete answers to history
                memory_manager.add_ai_message(response_save)
            else:
                memory_manager.add_ai_message(response)

            # Update session information
            self.session["message_count"] += 2  # User message + system reply            self.session["last_activity"] = datetime.now().isoformat()
            user_info = self.session.get("user_info", {})
            user_msg =self.create_msg(msg, "user")
            self.msg_db.create(conversation=user_msg)

            ai_msg =self.create_msg(response_save, "assistant")
            self.msg_db.create(conversation=ai_msg)
        except Exception as e:
            # Log errors without interrupting the main program
            print(f"Error updating chat history: {str (e) }")
            import traceback
            traceback.print_exc()
