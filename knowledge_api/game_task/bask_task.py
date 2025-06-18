from starlette.websockets import WebSocket

from knowledge_api.model.agent.game_agent import GameBaseInfo
from knowledge_api.game_play import GameFactory
from knowledge_api.game_play.game_session_manager import GameSessionManager
from knowledge_api.mapper.chat_session.base import Session
from knowledge_api.mapper.task_character_relations.crud import TaskCharacterRelationCRUD
from knowledge_api.mapper.tasks.crud import TaskCRUD
from knowledge_api.model.task_game_model import TaskGameInput
from knowledge_api.utils.constant import LLMApplication
from knowledge_api.utils.log_config import get_logger

logger = get_logger()


class BaseTask:
    """Basic task classes that support game task management in a distributed environment"""

    def __init__(self, db: Session, taskInput: TaskGameInput, game_type: str):
        self.db = db
        self.taskInput = taskInput
        self.game_type = game_type
        self.task_db = TaskCRUD(db)
        self.character_db = TaskCharacterRelationCRUD(db)
        self.character_list = []
        self.task = None
        self.game = None
        self.session_id = taskInput.session_id if taskInput else None

    async def init_task(self):
        """Initialize tasks, create game instances, and set up relevant data"""
        # First check if task session data exists in Redis
        if self.session_id:
            session_data = await GameSessionManager.load_game_session(self.session_id, self.game_type)
            if session_data:
                logger.info(f"从Redis加载已有任务会话: {self.session_id}")
        
        # Create a game instance
        self.game = await GameFactory.create_game(self.game_type, self.db, self.taskInput)
        
        # Load task information from database
        self.task = await self.task_db.get_by_id(int(self.taskInput.task_id))
        self.character_list = await self.character_db.get_by_task_id(int(self.taskInput.task_id))
        
        # Set the initial data for the game
        await self.game.set_init_data(
            self.character_list,
            GameBaseInfo(
                description=self.task.description,
                setting=self.task.setting,
                reference_case=self.task.reference_case,
            ),
            function_call_scenario=LLMApplication.BACKEND_GAME_TASK
        )
        
        # If it is a new session, save the initial state to Redis.
        if self.session_id and not session_data:
            # Save basic task information to Redis for easy multi-instance access
            initial_data = {
                "game_type": self.game_type,
                "task_id": self.taskInput.task_id,
                "user_info": self.taskInput.user_info,
                "roles": self.taskInput.roles,
                "is_initialized": True
            }
            await GameSessionManager.save_game_session(self.session_id, initial_data, self.game_type)
            logger.info(f"已将任务初始数据保存到Redis: {self.session_id}")

    async def play_game(self, websocket: WebSocket):
        """Start the game and process the WebSocket connection"""
        # Verify that the number of players is within the allowable range
        role_len = len(self.taskInput.roles)
        
        # Check if the number of players limit exists
        if self.task.game_number_min is None or self.task.game_number_max is None:
            await websocket.send_json({
                "error": "Task size limit not configured",
                "status": "error"
            })
            return
            
        # Verify that the number of players is within the allowable range
        if not (self.task.game_number_min <= role_len <= self.task.game_number_max):
            await websocket.send_json({
                "error": "The number of people does not meet the requirements",
                "status": "error"
            })
            return

        # Check if task rule data exists
        if self.task and self.task.rule_data:
            soup = self.task.rule_data.get("soup")
            answer = self.task.rule_data.get("answer")
            if soup is None or answer is None:
                await websocket.send_json({
                    "error": "Incomplete task configuration",
                    "status": "error"
                })
                return
                
            # Start the game
            try:
                # Share game state using Redis cache to support distributed environments
                await self.game.play_game(websocket, {
                    "truth": answer,
                    "surface": soup
                })
            except Exception as e:
                logger.error(f"游戏运行出错: {str(e)}")
                await websocket.send_json({
                    "error": f"游戏运行出错: {str(e)}",
                    "status": "error"
                })
        else:
            await websocket.send_json({
                "error": "Task parameter configuration not performed",
                "status": "error"
            })

    async def cleanup_task(self):
        """Clean up task resources and call them at the end of the task"""
        if self.session_id:
            # Get session data
            session_data = await GameSessionManager.load_game_session(self.session_id, self.game_type)
            if session_data:
                # Mark session ended
                session_data["is_game_over"] = True
                await GameSessionManager.save_game_session(self.session_id, session_data, self.game_type)
                logger.info(f"已标记任务会话结束: {self.session_id}")
