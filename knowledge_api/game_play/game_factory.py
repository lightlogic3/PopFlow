from sqlmodel import Session

from knowledge_api.game_play.base_game import BaseGame, GameSessionManager
from knowledge_api.model.task_game_model import TaskGameInput
from . import GAME_REGISTRY  # Import global regedit


class GameFactory:
    """@Description Game Factory class to create or restore game instances based on game type"""

    @classmethod
    async def create_game(cls, game_type: str, db: Session, task_input: TaskGameInput) -> BaseGame:
        """Create and initialize the game instance
@Param {string} game_type - Game Type
@Param {Session} db - database session
@param {TaskGameInput} task_input - Task Input
@Returns {BaseTaskGame} initialized game instance"""
        # Check if the game type is supported
        game_type = game_type.lower()
        if game_type not in GAME_REGISTRY:
            raise ValueError(f"不支持的游戏类型: {game_type}。支持的类型: {list(GAME_REGISTRY.keys())}")

        # Create a game instance and initialize it
        game_class = GAME_REGISTRY[game_type]
        instance = game_class(db, task_input)
        await instance.init_data()
        return instance

    @classmethod
    async def get_or_create_game(cls, game_type: str, db: Session, task_input: TaskGameInput) -> BaseGame:
        """Get or create a game instance, preferentially loading existing sessions from Redis

Args:
game_type: Game Type
DB: database session
task_input: Task Input

Returns:
game example"""
        # First try loading session data from Redis
        if task_input.session_id:
            session_data = await GameSessionManager.load_game_session(task_input.session_id)
            if session_data and session_data.get("game_type") == game_type:
                # Session exists and type matches, create instance and restore state
                instance = await cls.create_game(game_type, db, task_input)
                # Initialization has been done in create_game, including loading data from Redis
                return instance
                
        # Session or type mismatch not found, create new game instance
        return await cls.create_game(game_type, db, task_input)
