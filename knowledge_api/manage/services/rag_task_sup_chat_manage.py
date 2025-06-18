import json
from typing import Dict, Any, Optional

from jinja2 import Environment

from knowledge_api.back_task.role_task_sub import RoleTaskSub
from knowledge_api.chat.base_chat import BaseChat
from knowledge_api.framework.ai_collect.function_call.tool_registry import ToolRegistry
from knowledge_api.framework.database.database import get_db_session
from knowledge_api.framework.redis.cache_manager import CacheManager
from knowledge_api.mapper.role_subtasks import RoleSubtaskCRUD
from knowledge_api.mapper.role_subtasks.crud import UserSubtaskRelationCRUD
from knowledge_api.mapper.role_subtasks.base import UserSubtaskRelationCreate
from knowledge_api.mapper.role_tasks.base import RoleTask
from knowledge_api.mapper.role_tasks.crud import RoleTaskCRUD
from knowledge_api.model.llm_model import ChatSubTaskInput, SubTask, TaskSessions
from knowledge_api.framework.memory.enhanced_chat_memory_manager import EnhancedChatMemoryManager
from knowledge_api.utils.constant import LLMApplication
from knowledge_api.utils import generate_id
from knowledge_api.utils.log_config import get_logger

tools = ToolRegistry()

logger = get_logger()


@tools.register_decorator(description="Decide whether to approach the goal based on the conversation progress score (storage)")
def score_change(scoreChange: int, reason: str, isAchieved: int) -> Dict[str, Any]:
    return {
        "name": "score_change",
        "scoreChange": scoreChange,
        "reason": reason,
        "isAchieved": isAchieved == 1
    }


class RAGChatSupTaskManage(BaseChat):
    """RAG Auxiliary Task Chat Service"""

    def __init__(self):
        """Initialize RAG Auxiliary Task Chat Service"""
        super().__init__(chat_type="subtask")

    async def init_task(self, input_data):
        """Initialize task session"""
        # Make sure the service is initialized
        await self.ensure_initialized()

        # Generate session ID
        session_id = f"{input_data.user_id}-{input_data.subtask_id}"
        
        # Acquire or create a session
        session_data = await self.init_session(session_id)
        
        # Return task session information
        return {
            "session_id": session_id,
            "message_count": session_data.get("message_count", 0),
            "last_activity": session_data.get("last_activity", "")
        }

    async def chat(self, input_data: ChatSubTaskInput) -> Dict[str, Any]:
        """chat function

Args:
input_data: subtask input data

Returns:
chat response"""
        # Make sure the service is initialized
        await self.ensure_initialized()
            
        # Get session data
        session_data = await self.get_current_session(input_data.session_id)
        if not session_data or "task_info" not in session_data:
            return {
                "message": "The session does not exist or the task information is missing",
                "assistant_message": "",
                "tool_results": "{}"
            }
            
        sub = session_data["task_info"]
        
        sub_task = SubTask(
            taskDescription=sub.description,
            taskPersonality=sub.task_personality,
            taskGoal=sub.task_goal,
            task_goal_judge=sub.task_goal_judge,
            targetScore=sub.target_score,
            scoreRange=sub.score_range,
        )
        
        try:
            # Create prompt word
            sources, contexts, prompt = await self.create_template(
                query=input_data.message,
                top_k=input_data.top_k,
                session_id=input_data.session_id,
                prompt_type=sub.task_type,
                extended=sub_task.model_dump(exclude_none=True)
            )

            # Get AI response
            ai, messages = await self.get_ai(msg=input_data.message, prompt=prompt, session_id=input_data.session_id)
            response = await ai.chat_completion(
                messages=messages, 
                temperature=input_data.temperature,
                application_scenario=self.llm_application
            )
            
            # Update session history
            await self.update_chat(response=response, msg=input_data.message, session_id=input_data.session_id)
            
            # Configure scoring tools
            tools.get_tool("score_change") \
                .set_parameter_description("scoreChange",
                                           f"分数变化，正数表示加分，负数表示减分，范围{sub.score_range}，0表示不变") \
                .set_parameter_description("reason", "The reason for adding or subtracting points") \
                .set_parameter_description("isAchieved",
                                           f"是否已经实际达成了最终目标{sub.task_goal}，1达成，0未达成")
            
            # Get session history
            session_data = await self.get_current_session(input_data.session_id)
            memory_manager = session_data.get("memory_manager")
            if not memory_manager:
                return {
                    "message": response.content,
                    "assistant_message": "",
                    "tool_results": "{}"
                }
                
            history = memory_manager.get_formatted_history()
            
            # Create a scoring memory manager
            memory = EnhancedChatMemoryManager(
                k=4,
                system_message=await get_system_content(sub_task, history),
                memory_type='buffer_window',
            )
            memory.add_function_call_example("score_change", {
                "scoreChange": 1,
                "reason": "It doesn't really answer user questions.",
                "isAchieved": 0,
            })

            # Prepare for scoring tips
            end_history = "\n".join(
                [item.get("role") + "：" + item.get("content") for item in history[-2:] if item.get("role") != "system"])
            memory.add_user_message(f"帮我根据用户和NPC的交流记录对最后一一轮对话进行评判：{end_history}")
            
            # Execute function call
            tool_results, assistant_message,usage = await ai.function_call(
                memory.get_formatted_history(), tools=tools, application_scenario=LLMApplication.BACKEND_CHAT_TASK
            )
            
            return {
                "message": response.content,
                "assistant_message": assistant_message,
                "tool_results": json.dumps(tool_results, ensure_ascii=False),
            }
        finally:
            # Make sure to close the thread local session after processing the request
            from knowledge_api.framework.database.database import close_thread_session
            close_thread_session()

    async def save_session(self, session_id: str):
        """Save session to database

Args:
session_id: Session ID"""
        logger.info(f"子任务聊天：{session_id} 保存会话数据")


async def get_system_content(request: SubTask, messages: list):
    history = "\n".join(
        [item.get("role") + "：" + item.get("content") for item in messages if item.get("role") != "system"])
    judge_score = await CacheManager().get_nearest_prompt("ROLE_SINGLE_PLAYER")
    # Building a cue word engine
    env = Environment(variable_start_string='{', variable_end_string='}')
    template = env.from_string(judge_score.prompt_text)
    return template.render(
        history=history,
        request=request,
    )
