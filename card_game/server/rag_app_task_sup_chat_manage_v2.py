"""Card Game Chat Support Mission - Based on Redis Cached Edition
Chat and challenge-related functions for handling card games"""
import json
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime

from sqlmodel import Session

from knowledge_api.back_task.role_task_sub import RoleTaskSub
from knowledge_api.chat.base_chat import BaseChat
from knowledge_api.framework.ai_collect.function_call.tool_registry import ToolRegistry
from knowledge_api.framework.database.database import get_db_session, get_thread_local_session
from knowledge_api.mapper.role_subtasks import RoleSubtaskCRUD
from knowledge_api.mapper.role_subtasks.crud import UserSubtaskRelationCRUD
from knowledge_api.mapper.role_tasks.base import RoleTask
from knowledge_api.mapper.role_tasks.crud import RoleTaskCRUD
from knowledge_api.model.llm_model import ChatSubTaskInput, SubTask, TaskSessions
from knowledge_api.framework.memory.enhanced_chat_memory_manager import EnhancedChatMemoryManager
from knowledge_api.model.llm_token_model import LLMTokenResponse
from knowledge_api.utils.constant import LLMApplication
from knowledge_api.utils import generate_id
from knowledge_api.mapper.role_subtasks.base import UserSubtaskRelationCreate
from knowledge_api.utils.log_config import get_logger
from knowledge_api.mapper.task_game_sessions.base import TaskGameSessionUpdate, TaskGameSession
from knowledge_api.mapper.task_game_sessions.crud import TaskGameSessionCRUD
from knowledge_api.mapper.task_game_messages.base import TaskGameMessageCreate, TaskGameMessageUpdate
from knowledge_api.mapper.task_game_messages.crud import TaskGameMessageCRUD
from knowledge_api.framework.redis.cache_manager import CacheManager
from pydantic import BaseModel, Field

# Tool Registration
tools = ToolRegistry()
logger = get_logger()


@tools.register_decorator(description="Decide whether to approach the goal based on the conversation progress score (storage)")
def score_change(scoreChange: int, reason: str, isAchieved: int) -> Dict[str, Any]:
    """conversation scoring tool

Args:
scoreChange: score change
Reason: Reason for change
isAchieved: Whether the goal was achieved (1: Yes, 0: No)

Returns:
Rating result information"""
    return {
        "name": "score_change",
        "scoreChange": scoreChange,
        "reason": reason,
        "isAchieved": isAchieved == 1
    }
    # return {
    #     "name": "score_change",
    #     "scoreChange": scoreChange,
    #     "reason": reason,
    #     "isAchieved": True
    # }


async def update_state(db: Session, session_crud: TaskGameSessionCRUD, session_id: str, session_update):
    data = await session_crud.update(session_id, session_update)
    user_subtask_db = UserSubtaskRelationCRUD(db)
    await user_subtask_db.update_by_user_id_skip(
        user_id=data.user_id,
        subtask_id=data.subtask_id,
        status=data.status
    )


class RAGAppChatSupTask(BaseChat):
    """RAG Card Game Chat Service - Redis Cached Edition

Note: This class inherits from BaseChat, but some methods have been overridden to suit the specific needs of card games.
get_session_data Get session data using Redis cache
update_chat - inherit the parent class method and add the current round trace
update_chat_children - Complete handling of message updates and points changes
create_template - Custom prompt word template generation
5. chat - provides full game chat functionality, including scoring and status tracking

Methods implemented by other base classes (such as get_ai) are used directly and are not implemented repeatedly"""
    
    # Define application scenarios
    llm_application = LLMApplication.BACKEND_CHAT_TASK  # Dedicated to background chat tasks

    def __init__(self, **kwargs):
        """Initialize the RAG card game chat service"""
        super().__init__(chat_type="card_game")  # Use card_game as Redis key prefix
        # Cache manager for more flexible cache operations
        self.cache_manager = CacheManager()

    async def save_session(self, session_id: str):
        """Create a new session and save the session information to the task_game_sessions table

Args:
session_id: Session ID"""
        if not session_id:
            logger.warning("Failed to save session, missing session ID")
            return
            
        # Get session data
        session_data = await self.get_session_data(session_id)

        user_id = session_data.get("user_id")
        task_id = session_data.get("task_id")
        task_info = session_data.get("task_info")
        target_score = session_data.get("target_score", 100)

        if not session_id or not user_id:
            logger.warning(f"保存会话失败，缺少必要信息: session_id={session_id}, user_id={user_id}")
            return

        with get_db_session() as db:
            session_crud = TaskGameSessionCRUD(db)

            # Check if the session already exists
            existing_session = await session_crud.get_by_id(session_id)
            if existing_session:
                logger.info(f"会话已存在: {session_id}")
                return

            # Create a new session
            new_session = TaskGameSession(
                id=session_id,
                user_id=user_id,
                subtask_id=session_data.get("sup_task_id"),
                task_id=task_id,
                status=0,  # in progress
                current_score=0,
                current_round=1,
                max_rounds=task_info.get("max_rounds") if task_info else 5,  # Default maximum 5 rounds
                target_score=target_score,
                last_message_time=datetime.now(),
                create_time=datetime.now(),
                update_time=datetime.now(),
            )
            # Add and submit directly
            db.add(new_session)
            db.commit()
            logger.info(f"成功创建会话: {session_id}") 

    async def search_db_session(self, session_id: str) -> Optional[EnhancedChatMemoryManager]:
        """Restore session information from database

Args:
session_id: Session ID

Returns:
Restored Memory Manager or None"""
        if not session_id:
            return None
            
        logger.info(f"从数据库恢复会话: {session_id}")
        
        # Create a memory manager
        memory_manager = EnhancedChatMemoryManager(
            k=20,
            system_message="",
            memory_type='buffer_window',
        )
        
        with get_db_session() as db:
            # Query session information
            session_crud = TaskGameSessionCRUD(db)
            game_session = await session_crud.get_by_id(session_id)

            if not game_session:
                logger.warning(f"未找到会话: {session_id}")
                return None

            # query session message
            message_crud = TaskGameMessageCRUD(db)
            messages = await message_crud.get_by_session_id(session_id)

            # Initialize session data
            session_data = {
                "session_id": session_id,
                "user_id": game_session.user_id,
                "sup_task_id": game_session.subtask_id,
                "task_id": game_session.task_id,
                "current_round": game_session.current_round,
                "current_score": game_session.current_score,
                "target_score": game_session.target_score
            }
            
            # Check if the session has been completed
            if game_session.status != 0:
                session_data["session_completed"] = True
                session_data["completion_reason"] = game_session.summary or "The session has ended"
            else:
                session_data["session_completed"] = False

            # Obtain task information if necessary
            if game_session.task_id:
                with get_db_session() as task_db:
                    role_task_db = RoleTaskCRUD(task_db)
                    task_info = await role_task_db.get_by_id(game_session.task_id)
                    if task_info:
                        session_data["task_info"] = RoleTask.model_validate(task_info.model_dump()).model_dump(mode="json")

            # Restore message history to memory manager
            for msg in messages:
                if msg.role == "user":
                    memory_manager.add_user_message(msg.content)
                elif msg.role == "assistant":
                    memory_manager.add_ai_message(msg.content)
            
            # Save recovered session data to Redis
            # Check if a session already exists, and if so, update rather than overwrite it
            existing_data = await self.get_session_data(session_id)
            await self.session_manager.create_session(
                session_id,
                memory_manager=memory_manager,
                additional_data={**session_data,**existing_data}
            )

            logger.info(f"成功恢复会话: {session_id}, 当前轮次: {game_session.current_round}, 当前分数: {game_session.current_score}")

        return memory_manager

    async def init_task(self, input_data: ChatSubTaskInput) -> Optional[TaskSessions]:
        """Initialize the task and return the user's uncompleted subtasks

Args:
input_data: Subtask input data, including user ID

Returns:
subtask session information"""
        is_new_task = True  # Default as new task
        history = []  # Default empty history
        
        with get_db_session() as session:
            user_subtask_db = UserSubtaskRelationCRUD(session)
            sub_task_db = RoleSubtaskCRUD(session)
            role_task_db = RoleTaskCRUD(session)
            
            # Check if session data exists
            if input_data.session_id:
                existing_session = await self.get_session_data(input_data.session_id)
                if existing_session:
                    # If the session already exists, it is not a new task
                    is_new_task = False
                    # Try to get history
                    memory_manager = existing_session.get("memory_manager")
                    if memory_manager:
                        history = memory_manager.get_formatted_history()

            # If a subtask ID is specified, get the subtask directly
            if hasattr(input_data, 'task_sup_id') and input_data.task_sup_id:
                sub_task = await sub_task_db.get_by_id(input_data.task_sup_id)
                if not sub_task:
                    logger.warning("The specified subtask was not found")
                    return None

                # Check if the user has completed the subtask
                if hasattr(input_data, 'user_id') and input_data.user_id:
                    user_relation = await user_subtask_db.get_by_user_subtask(
                        user_id=input_data.user_id,
                        subtask_id=input_data.task_sup_id
                    )

                    # If the user has completed the subtask, return None.
                    if user_relation and user_relation.status == 1:
                        logger.info(f"用户 {input_data.user_id} 已完成子任务 {input_data.task_sup_id}")
                        return None
            else:
                # First check if the user has any outstanding tasks
                if hasattr(input_data, 'user_id') and input_data.user_id:
                    # Get the first subtask that the user is in progress (unfinished state)
                    in_progress_task = await user_subtask_db.get_first_in_progress_subtask(
                        user_id=input_data.user_id,
                        task_id=input_data.task_id if hasattr(input_data, 'task_id') and input_data.task_id else None
                    )

                    # If you find an unfinished task, use it directly
                    if in_progress_task:
                        sub_task = in_progress_task
                        is_new_task = False  # This is an ongoing mission, not a new one
                    else:
                        # If no unfinished tasks are found, get a random unfinished task
                        sub_task = await user_subtask_db.get_random_unfinished_subtask(
                            user_id=input_data.user_id,
                            task_id=input_data.task_id if hasattr(input_data, 'task_id') and input_data.task_id else None
                        )
                else:
                    # If there is no user ID, get a random subtask
                    if hasattr(input_data, 'task_id') and input_data.task_id:
                        sub_tasks = await sub_task_db.get_by_task_id(task_id=input_data.task_id, limit=1)
                        sub_task = sub_tasks[0] if sub_tasks else None
                    else:
                        sub_tasks = await sub_task_db.get_all(limit=1)
                        sub_task = sub_tasks[0] if sub_tasks else None

                if not sub_task:
                    # Enter the AI creation question process
                    for i in range(3):
                        sub_task = await RoleTaskSub(session).create_random_task()
                        if sub_task:
                            break
                        logger.info(f"正在重试{i}次")

                if not sub_task:
                    logger.warning("No available subtasks were found")
                    return None

            # Get complete information on the main task
            main_task_db = await role_task_db.get_by_id(sub_task.task_id)
            if not main_task_db:
                logger.warning("Main task not found")
                return None

            # Important change: Create a copy first and disconnect from the database session
            main_task_data = main_task_db.model_dump()
            main_task = RoleTask.model_validate(main_task_data)

            # Synchronize main task personas (in memory only)
            main_task.task_personality = sub_task.task_personality
            main_task.task_goal = sub_task.task_goal
            main_task.task_goal_judge = sub_task.task_goal_judge
            main_task.hide_designs = sub_task.hide_designs
            main_task.task_level = sub_task.task_level
            main_task.description = sub_task.task_description
            main_task.prologues = sub_task.prologues

            # Make sure that the memory object is not associated with the database
            session.expunge_all()

            input_data.role_id = main_task.role_id
            
            # Make sure the session ID exists
            if not input_data.session_id:
                input_data.session_id = f'{input_data.user_id}-{sub_task.id}'
            existing_data = await self.get_session_data(input_data.session_id)
            # Store session data to Redis
            await self.session_manager.create_session(
                input_data.session_id,
                additional_data={
                    **existing_data,
                    "session_id": input_data.session_id,
                    "user_id": input_data.user_id,
                    "sup_task_id": sub_task.id,
                    "task_id": main_task.id,
                    "target_score": main_task.target_score,
                    "is_win": False,
                    "is_failed": False,
                    "task_info": main_task.model_dump(mode="json"),  # Convert to a fully JSON-serializable dictionary
                    "is_new_task": is_new_task  # Save as a flag for new tasks
                }
            )

            await self.init_chat(input_data)
            # 重新获取更新后的会话数据
            memory_manager = existing_data.get("memory_manager") if existing_data else None
            if memory_manager:
                history = memory_manager.get_formatted_history()

            # Build task session returns
            task_session = TaskSessions(
                task=main_task,
                session_id=input_data.session_id,
                sup_task_id=sub_task.id,
                is_new_task=is_new_task,  # Set whether to flag for new task
                history=history  # Set up a conversation history
            )
            
            # Join task association - fix: check subtask relationship for specific user instead of global
            user_relation = await user_subtask_db.get_by_subtask(
                subtask_id=sub_task.id
            )
            if not user_relation:
                await user_subtask_db.create(obj_in=UserSubtaskRelationCreate(
                    user_id=input_data.user_id,
                    subtask_id=sub_task.id,
                    task_id=sub_task.task_id,
                    status=0,
                    score=0
                ))
            return task_session 

    async def update_chat(self, response: LLMTokenResponse, msg: str, session_id=None):
        """Update chat history (inherit from parent class, add current round)

Args:
Response: AI response object
Msg: user messages
session_id: Session ID

Returns:
Current round"""
        # Get current round - get from Redis session cache
        session_data = await self.get_session_data(session_id)
        current_round = session_data.get("current_round", 1)

        # First call the parent class method to update the message history in Redis
        await super().update_chat(response, msg, session_id)
        
        return current_round

    async def update_chat_children(self, response: LLMTokenResponse, msg: str, tool_results, session_id=None):
        """Update chat history, save user messages and AI replies, handle score changes

Args:
Response: AI response object
Msg: user messages
tool_results: Tool Call Results
session_id: Session ID"""
        # If no session_id is provided, try to get it from response
        if not session_id and hasattr(response, 'session_id'):
            session_id = response.session_id

        # If there is still no session_id, try to get an available one from the session manager
        if not session_id:
            # Find the first available session ID as a fallback option only
            sessions = await self.session_manager.list_sessions()
            if sessions:
                session_id = sessions[0]
                logger.warning(f"找不到会话ID，使用第一个可用的会话ID: {session_id}")
            else:
                logger.error("Update chat failed: Could not determine session ID")
                return

        # The current round returned using the update_chat method
        current_round = await self.update_chat(response, msg, session_id)

        # Get session data
        session_data = await self.get_session_data(session_id)
        task = session_data.get("task_info")
        user_id = session_data.get("user_id")

        if not user_id:
            logger.warning(f"更新聊天失败，缺少用户ID，会话ID: {session_id}")
            return

        with get_db_session() as db:
            message_crud = TaskGameMessageCRUD(db)
            session_crud = TaskGameSessionCRUD(db)

            # Save user messages
            user_message = TaskGameMessageCreate(
                session_id=session_id,
                role="user",
                user_id=user_id,
                content=msg,
                round=current_round,
                role_id=task.get("role_id") if task else None,
                score_change=0
            )
            await message_crud.create(obj_in=user_message)

            # Processing AI replies
            ai_message = TaskGameMessageCreate(
                session_id=session_id,
                role="assistant",
                role_id=task.get("role_id") if task else None,
                user_id=user_id,
                content=response.content,
                round=current_round,
                score_change=0,  # It starts at 0 and will be updated later.
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                model_id=response.model
            )
            ai_msg = await message_crud.create(obj_in=ai_message)

            # Processing tool call result
            score_change = 0
            reason = ""
            is_achieved = False

            # Result of parsing tool call
            if tool_results and isinstance(tool_results, list):
                for result in tool_results:
                    if isinstance(result, dict):
                        # Handling possible different formats
                        if "content" in result and isinstance(result["content"], dict):
                            # New format, content in the content field
                            content = result["content"]
                            if content.get("name") == "score_change":
                                score_change = content.get("scoreChange", 0)
                                reason = content.get("reason", "")
                                is_achieved = content.get("isAchieved", False)
                        elif "name" in result and result.get("name") == "score_change":
                            # Old format, content directly in the dictionary
                            score_change = result.get("scoreChange", 0)
                            reason = result.get("reason", "")
                            is_achieved = result.get("isAchieved", False)

            # Update the score change information of the AI message
            if score_change != 0 or reason:
                await message_crud.update(
                    ai_msg.id,
                    TaskGameMessageUpdate(
                        score_change=score_change,
                        score_reason=reason
                    )
                )

            # Update the total score and status of the session
            game_session = await session_crud.get_by_id(session_id)
            if game_session:
                # Make sure to use the latest values in the database for accumulation
                new_score = game_session.current_score + score_change
                # Increase round count
                new_round = game_session.current_round + 1

                # Check if the goal is achieved
                new_status = game_session.status
                session_completed = False
                completion_reason = None

                # Mission objective achieved
                if is_achieved:
                    new_status = 1  # Completed.
                    session_completed = True
                    completion_reason = "Goal achieved"
                    # Update session data Redis cache
                    await self.session_manager.update_session(session_id, {"is_win": True})
                # Scores on target.
                elif new_score >= game_session.target_score:
                    new_status = 1  # Completed.
                    session_completed = True
                    completion_reason = f"达到目标分数: {new_score} >= {game_session.target_score}"
                    # Update session data Redis cache
                    await self.session_manager.update_session(session_id, {"is_win": True})
                # The round reaches the upper limit
                elif new_round > game_session.max_rounds:
                    new_status = 2  # Interrupted (round cap reached)
                    session_completed = True
                    completion_reason = f"达到最大轮次: {new_round} > {game_session.max_rounds}"
                    # Update session data Redis cache
                    await self.session_manager.update_session(session_id, {"is_failed": True})

                # Update session state
                session_update = TaskGameSessionUpdate(
                    current_score=new_score,
                    current_round=new_round,
                    status=new_status,
                    last_message_time=datetime.now()
                )

                # If the session completes, add summary information
                if session_completed and completion_reason:
                    session_update.summary = completion_reason
                    # Update the user subtask relationship table simultaneously
                    if session_data.get("sup_task_id"):
                        try:
                            # Update user subtask relationships
                            await update_state(db, session_crud,session_id, session_update)
                        except Exception as e:
                            logger.error(f"更新用户子任务关系失败: {e}")

                await update_state(db, session_crud, session_id, session_update)
                # Update session data in Redis cache
                await self.session_manager.update_session(
                    session_id,
                    {
                        "current_score": new_score,
                        "current_round": new_round,
                        "session_completed": session_completed,
                        "completion_reason": completion_reason
                    }
                )

            # Record any additional tool calls, if any
            if isinstance(tool_results, list):
                for result in tool_results:
                    func_message = TaskGameMessageCreate(
                        session_id=session_id,
                        role="function",
                        user_id=user_id,
                        content=json.dumps(result, ensure_ascii=False),
                        round=current_round,
                        role_id=task.get("role_id") if task else None
                    )
                    await message_crud.create(obj_in=func_message)

            logger.info(f"已保存会话消息, session_id={session_id}, round={current_round}, score_change={score_change}")

    async def check_session_status(self, session_id=None):
        """Check the conversation status and decide if you can continue chatting

Args:
session_id: Session ID

Returns:
(can_continue, reason) Can continue chatting and why"""
        # If no session_id is provided, try to get one available
        if not session_id:
            sessions = await self.session_manager.list_sessions()
            if sessions:
                session_id = sessions[0]
            else:
                return False, "Session ID is lost"

        # Get session data in Redis cache
        session_data = await self.get_session_data(session_id)

        # Check session state in memory
        if session_data.get("session_completed", False):
            return False, session_data.get("completion_reason", "Session completed")

        # Check the session state in the database
        with get_db_session() as db:
            session_crud = TaskGameSessionCRUD(db)
            game_session = await session_crud.get_by_id(session_id)

            if not game_session:
                return False, "Session does not exist"
                
            # Create a session update object
            session_update = TaskGameSessionUpdate(
                current_score=game_session.current_score,
                current_round=game_session.current_round,
                status=game_session.status,
                last_message_time=datetime.now()
            )
            
            # Check session state
            if game_session.status != 0:
                if game_session.status == 1:
                    # Update Redis cache
                    await self.session_manager.update_session(session_id, {"is_failed": True})
                    return False, "Session completed"
                elif game_session.status == 2:
                    # Update Redis cache
                    await self.session_manager.update_session(session_id, {"is_failed": True})
                    return False, "Session interrupted"
                elif game_session.status == 3:
                    # Update Redis cache
                    await self.session_manager.update_session(session_id, {"is_failed": True})
                    return False, "Session timed out"
                else:
                    # Update Redis cache
                    await self.session_manager.update_session(session_id, {"is_failed": True})
                    return False, f"会话状态异常: {game_session.status}"

            # Check round limit
            if game_session.current_round > game_session.max_rounds:
                session_update.status = 2  # interrupted

                # Update Redis cache
                await self.session_manager.update_session(session_id, {"is_failed": True})
                # Update user subtask relationships
                await update_state(db,session_crud,session_id,session_update)
                return False, f"已达到最大轮次: {game_session.current_round} > {game_session.max_rounds}"

            # Check target score
            if game_session.current_score >= game_session.target_score:
                # Update Redis cache
                await self.session_manager.update_session(session_id, {"is_win": True})

                # Update user subtask relationships
                await update_state(db,session_crud, session_id, session_update)
                
                return False, f"已达到目标分数: {game_session.current_score} >= {game_session.target_score}"

            # Update session state in Redis cache
            await self.session_manager.update_session(
                session_id,
                {
                    "current_round": game_session.current_round,
                    "current_score": game_session.current_score
                }
            )

            return True, "Session can continue"

    async def chat(self, input_data: ChatSubTaskInput) -> Dict[str, Any]:
        """Chat function (streaming)

Args:
input_data: Chat Input Data

Returns:
response result"""
        try:
            # Make sure the session ID exists
            if not input_data.session_id:
                logger.error("Chat failed: session ID is missing, please call/chat/start interface first")
                return {
                    "message": "Please start the challenge before the conversation",
                    "assistant_message": "Session not initialized",
                    "tool_results": json.dumps([{"name": "error", "reason": "The session is not initialized, please call the/chat/start interface first"}], ensure_ascii=False),
                }

            # Check if a session exists
            session_data = await self.session_manager.get_session(input_data.session_id)
            if not session_data:
                logger.error(f"聊天失败：会话不存在，session_id={input_data.session_id}")
                return {
                    "message": "The session does not exist, please restart the challenge",
                    "assistant_message": "Session does not exist",
                    "tool_results": json.dumps([{"name": "error", "reason": "The session does not exist, please restart the challenge"}], ensure_ascii=False),
                }

            # Check session state
            can_continue, reason = await self.check_session_status(input_data.session_id)
            if not can_continue:
                logger.warning(f"会话无法继续: {reason}, session_id={input_data.session_id}")
                return {
                    "message": f"很抱歉，当前会话已结束。原因: {reason}",
                    "assistant_message": "The session has ended",
                    "tool_results": json.dumps([{"name": "session_ended", "reason": reason}], ensure_ascii=False),
                }

            # Get session data
            session_data = await self.get_session_data(input_data.session_id)
            sub = session_data.get("task_info")
            if not sub:
                logger.error(f"会话数据不完整，缺少任务信息, session_id={input_data.session_id}")
                return {
                    "message": "The session data is abnormal, please restart the challenge",
                    "assistant_message": "Failed to get task",
                    "tool_results": json.dumps([{"name": "error", "reason": "The session data is incomplete, please restart the challenge"}], ensure_ascii=False),
                }

            sub=RoleTask.model_validate(sub)
            sub_task: SubTask = SubTask(
                taskDescription=sub.description,
                taskPersonality=sub.task_personality,
                taskGoal=sub.task_goal,
                task_goal_judge=sub.task_goal_judge,
                targetScore=sub.target_score,
                scoreRange=sub.score_range,
            )

            # Create prompt word
            sources, contexts, prompt = await self.create_template(
                input_data.message,
                input_data.top_k,
                input_data.session_id,
                prompt_type=sub.task_type,
                extended=sub_task.model_dump(exclude_none=True)
            )

            ai, messages = await self.get_ai(msg=input_data.message, prompt=prompt, session_id=input_data.session_id)
            response = await ai.chat_completion(messages=messages, temperature=input_data.temperature,
                                               application_scenario=self.llm_application)

            tools.get_tool("score_change") \
                .set_parameter_description("scoreChange",
                                           f"分数变化，正数表示加分，负数表示减分，范围{sub.score_range}，0表示不变") \
                .set_parameter_description("reason", "The reason for adding or subtracting points") \
                .set_parameter_description("isAchieved",
                                           f"是否已经实际达成了最终目标{sub.task_goal}，1达成，0未达成")

            memory_manager = await self.get_memory_manager(input_data.session_id)
            if memory_manager:
                history = memory_manager.get_formatted_history()
                memory = EnhancedChatMemoryManager(
                    k=4,
                    system_message=get_system_content(sub_task, history),
                    memory_type='buffer_window',
                )
                memory.add_function_call_example("score_change", {
                    "scoreChange": 1,
                    "reason": "It doesn't really answer user questions.",
                    "isAchieved": 0,
                })

                end_history = "\n".join(
                    [item.get("role") + "：" + item.get("content") for item in history[-2:] if
                     item.get("role") != "system"])
                memory.add_user_message(f"帮我根据用户和NPC的交流记录对最后一轮对话进行评判：{end_history}")
                tool_results, assistant_message,call= await ai.function_call(
                    memory.get_formatted_history(), tools=tools, application_scenario=LLMApplication.BACKEND_CHAT_TASK
                )

                # Use the optimized update_chat_children method
                await self.update_chat_children(response, input_data.message, tool_results, input_data.session_id)

                # Check the session state again and clear the cache if complete
                session_data = await self.get_session_data(input_data.session_id)
                if session_data.get("session_completed", False):
                    await self.clear_session_cache(input_data.session_id)

                return {
                    "message": response.content,
                    "assistant_message": assistant_message,
                    "tool_results": json.dumps(tool_results, ensure_ascii=False),
                    "history": [item for item in history[-2:] if item.get("role") != "system"],
                    "is_win": session_data.get("is_win", False),
                    "is_failed": session_data.get("is_failed", False),
                    "current_round": session_data.get("current_round", 1),
                }
            else:
                logger.error(f"获取memory_manager失败, session_id={input_data.session_id}")
                return {
                    "message": response.content,
                    "assistant_message": "",
                    "tool_results": "[]",
                    "history": [],
                    "is_win": False,
                    "is_failed": False,
                    "current_round": 1,
                }
        finally:
            # Make sure to close the thread local session after processing the request
            from knowledge_api.framework.database.database import close_thread_session
            close_thread_session()

    async def _retrieve_context(self, query: str, ai_message: str, top_k: int = 3, session_id=None) -> Dict[str, Any]:
        """No need to retrieve a vector database"""
        return {"contexts": [], "sources": []}

    async def get_role_prompt(self, session_id):
        """Initialization, character opening"""
        session_data = await self.get_session_data(session_id)
        memory_manager = session_data.get("memory_manager")
        if not memory_manager:
            return False, None
            
        sub = session_data.get("task_info")
        if hasattr(sub, "prologues") and sub.prologues:
            # Add prompt word
            memory_manager.add_user_message(sub.prologues.split(",")[0])
        return {}

    async def get_prologue(self, message: str, session_id):
        return False, None

    # Methods already implemented get_ai base class do not need to be repeated here

    async def get_memory_manager(self, session_id: str) -> EnhancedChatMemoryManager:
        """Get or create a memory manager from the Redis cache

Args:
session_id: Session ID

Returns:
Memory Manager"""
        if not session_id:
            logger.warning("Failed to get memory manager, session ID is missing")
            # Create a new default memory manager
            return EnhancedChatMemoryManager(k=20, memory_type='buffer_window')
        
        # Get session data from Redis cache
        session_data = await self.get_session_data(session_id)
        
        # Check if there is a memory manager
        memory_manager = session_data.get("memory_manager")
        
        if memory_manager:
            logger.debug(f"从Redis缓存恢复内存管理器, session_id={session_id}")
            return memory_manager
        
        # Attempt to resume a session from the database
        db_memory_manager = await self.search_db_session(session_id)
        if db_memory_manager:
            logger.info(f"从数据库恢复内存管理器, session_id={session_id}")
            return db_memory_manager
        
        # Create a new memory manager
        logger.info(f"创建新的内存管理器, session_id={session_id}")
        new_memory_manager = EnhancedChatMemoryManager(
            k=20,
            system_message="",
            memory_type='buffer_window',
        )
        
        # Update to Redis cache
        await self.session_manager.update_session(
            session_id,
            {"memory_manager": new_memory_manager}
        )
        
        return new_memory_manager

    async def clear_session_cache(self, session_id: str = None):
        """Clean session cache

Args:
session_id: Session ID, if None, clean up all sessions"""
        if session_id:
            # Clean up a specific session
            await self.session_manager.delete_session(session_id)
            logger.info(f"已清理会话缓存: {session_id}")
        else:
            # Clean up all sessions
            sessions = await self.session_manager.list_sessions()
            for sess_id in sessions:
                await self.session_manager.delete_session(sess_id)
            logger.info(f"已清理全部会话缓存，共{len(sessions)}个")


def get_system_content(request: SubTask, messages: list):
    """Get system prompt content

Args:
Request: subtask request
Messages: chat history

Returns:
System prompt content"""
    history = "\n".join(
        [item.get("role") + "：" + item.get("content") for item in messages if item.get("role") != "system"])
    return f"""You are a scoring system that needs to evaluate whether the user's conversation with NPCs is progressing towards completing the task goal. If there is a judgment standard setting, you need to focus on whether the conversation between the user and NPCs is close to the judgment standard
It is important to note that you cannot rely on the user's one-sided words to determine whether the user is close to the goal, because the user will deceive, and you need to consider the context of the conversation to determine whether the user has actually achieved the goal.
Task Description: {request.taskDescription}
NPC settings: {request.taskPersonality}
Task Goal: {request.taskGoal}
Judgment criteria: {request.task_goal_judge}
NPC and User History Dialogue:
{history}
Please judge whether the user is close to the goal based on the latest conversation content. Points should be added if the user's conversation strategy meets the goal or takes advantage of NPC characteristics (such as fear); points should be deducted if it deviates from the goal or backfires.
Each time you have to call the function score_change to store the score, in order to ensure accuracy, even if 0 points you need to call this function to help me save the value.
Note: The target score is {request.targetScore} for completion, and the value range is {request.scoreRange}"""

