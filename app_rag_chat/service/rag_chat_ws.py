from typing import Dict, Any

from app_rag_chat.model.chat_models import ChatInput
from app_rag_chat.service.rag_chat_base import RAGChatService
from runtime import ExecutionTimer


class RAGChatWebSocket(RAGChatService):
    """RAG chat service"""

    async def chat(self, input_data: ChatInput) -> Dict[str, Any]:
        """
        聊天功能（非流式）

        Args:
        Returns:
            聊天响应
        """
        userInfo = {
            "role_id": input_data.role_id,
            "level": input_data.level,
            "user_level": input_data.user_level,
            "user_id": input_data.user_id,

        }
        session = await self._get_session(userInfo, input_data.session_id)
        session_id = session["id"]
        memory_manager = session["memory_manager"]
        timer = ExecutionTimer("The comprehensive time consumption of various query services:")
        timer.start()
        sources, contexts, prompt, timbre = await self.create_template(
            input_data.message,
            input_data.top_k,
            userInfo=userInfo
        )
        # Acquire or create a session
        timer.stop()

        response = await self._generate_answer(prompt, input_data.temperature, memory_manager,input_data.message)
        timer2 = ExecutionTimer("Update operation, time-consuming situation:")
        timer2.start()
        self.update_chat(session, memory_manager, response=response, msg=input_data.message)
        timer2.stop()
        # Prepare for response
        result = {
            "message": response,
            "session_id": session_id
        }
        # If necessary, include the source
        if input_data.include_sources:
            result["sources"] = sources
            result["contexts"] = contexts
            result["prompt"] = memory_manager.get_chat_history()
        return result
