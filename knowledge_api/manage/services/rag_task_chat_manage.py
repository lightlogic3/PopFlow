import json
from typing import Dict, Any, Optional, Tuple

from knowledge_api.chat.base_chat import BaseChat
from knowledge_api.framework.ai_collect.function_call.tool_registry import ToolRegistry
from knowledge_api.framework.redis.cache_manager import CacheManager
from knowledge_api.model.llm_model import ChatTaskInput
from knowledge_api.framework.memory.enhanced_chat_memory_manager import EnhancedChatMemoryManager
from knowledge_api.utils.constant import LLMApplication
from knowledge_api.utils.log_config import get_logger
from jinja2 import Environment

logger = get_logger()

tools = ToolRegistry()


@tools.register_decorator(description="Decide whether to approach the goal based on the conversation progress score (storage)")
def score_change(scoreChange: int, reason: str, isAchieved: int) -> Dict[str, Any]:
    return {
        "name": "score_change",
        "scoreChange": scoreChange,
        "reason": reason,
        "isAchieved": isAchieved == 1
    }


class RAGChatTaskManage(BaseChat):
    """RAG task chat service"""

    def __init__(self):
        """Initialize RAG task chat service"""
        super().__init__(chat_type="task")

    async def chat(self, input_data: ChatTaskInput) -> Dict[str, Any]:
        """Processing task chat requests

Args:
input_data: Chat Input Data

Returns:
chat response"""
        # Make sure the service and context manager are initialized
        await self.ensure_initialized()

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
            # Check if there is a include_sources property, if not it defaults to False
            if getattr(input_data, 'include_sources', False):
                result["sources"] = sources
                result["contexts"] = contexts

                # Get session record
                session_data = await self.get_current_session(input_data.session_id)
                memory_manager = session_data.get("memory_manager")
                if memory_manager:
                    result["prompt"] = memory_manager.get_chat_history()

        # Processing Text To Speech
        if role_data.get("timbre"):
            from knowledge_api.utils.string_tool import remove_parentheses_content
            from runtime import ExecutionTimer
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

    async def save_session(self, session_id: str):
        """Save session to database

Args:
session_id: Session ID"""
        logger.info(f"任务聊天：{session_id} 保存会话数据")


async def get_system_content(request: ChatTaskInput, messages: list):
    history = "\n".join(
        [item.get("role") + "：" + item.get("content") for item in messages if item.get("role") != "system"])

    # Get Redis Cache Manager
    judge_score = await CacheManager().get_nearest_prompt("ROLE_SINGLE_PLAYER")
    # Building a cue word engine
    env = Environment(variable_start_string='{', variable_end_string='}')
    template = env.from_string(judge_score.prompt_text)
    return template.render(
        history=history,
        request=request,
    )
