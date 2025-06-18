import json
import uuid
from typing import List, Any, Dict, Type, ClassVar, Optional, Set
import asyncio
import time
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

from sqlmodel import Session

from knowledge_api.model.agent.game_agent import GameMessage, BaseGameAgent, GameBaseInfo
from knowledge_api.framework.ai_collect.function_call.tool_manager import ToolManager
from knowledge_api.framework.ai_collect.function_call.tool_registry import ToolRegistry
from knowledge_api.framework.redis.cache_manager import CacheManager
from knowledge_api.game_play.game_session_manager import GameSessionManager
from knowledge_api.mapper.game_character_relations import GameCharacterRelationCRUD
from knowledge_api.mapper.game_play_type.crud import GamePlayTypeCRUD
from knowledge_api.mapper.roles.base import Role
from knowledge_api.mapper.roles.crud import RoleCRUD
from knowledge_api.model.llm_token_model import LLMTokenResponse
from knowledge_api.model.task_game_model import TaskGameInput
from knowledge_api.utils.constant import LLMApplication
from knowledge_api.utils.log_config import get_logger

logger = get_logger()


class BaseGame:
    """game task base class"""
    # Class properties, storing all game type mappings
    _registry: ClassVar[Dict[str, Type['BaseGame']]] = {}

    # Game type identifier (subclasses must override this attribute)
    game_type: ClassVar[str] = None

    def __init__(self, db: Session, taskInput: TaskGameInput):
        """Initialize game

Args:
DB: database session
taskInput: task input data"""
        self.agents: List[BaseGameAgent] = None
        self.character_list = None
        self.task = None
        self.session_id = None
        self.game_info: GameBaseInfo = None
        self.character_infos: List[Role] = None
        self._init_databases(db)
        self._init_task_info(taskInput)
        self.game_config = {}
        self.function_call_scenario = LLMApplication.BACKEND_CHAT_GAME_PLAY
        # A local WebSocket connection map that contains only the connections of the current service instance
        self._local_websockets: Dict[str, Set[WebSocket]] = {}
        # Local message queue for temporary storage of messages to be sent
        self._local_message_queue: Dict[str, List[Dict]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Note: This is no longer active registration, but __init__
        # Keep this method for backward compatibility, but the actual registration is done through __init__
        pass

    def _init_databases(self, db: Session):
        """Initialize the database access object

Args:
DB: database session"""
        self.character_db = GameCharacterRelationCRUD(db)
        self.role_db = RoleCRUD(db)
        self.game_play_db = GamePlayTypeCRUD(db)
        self.agents = []

    def _init_task_info(self, taskInput: TaskGameInput):
        """Initialize task information

Args:
taskInput: task input data"""
        self.taskInput = taskInput
        self.session_id = taskInput.session_id
        
        # Create tool regedit
        self.tools = ToolRegistry()
        self.tool_manager = ToolManager(self.tools)

    def _register_tool(self):
        """The registration tool is initialized and needs to be implemented by subclasses. It is not mandatory here, so it is an empty function. If the subclass is implemented, self.is_register_tool is automatically True."""
        pass

    async def function_call(self, agent: BaseGameAgent, messages, model=None):
        """Execute function call

Args:
Agent: Game Agent
Messages: Message List
Model: model name

Returns:
function call result"""
        try:
            agent = agent.client
            if not agent.is_function_call and len(self.tools.get_all_tools()) == 0:
                logger.error("Unregistered tools or agents do not support Function Call and cannot use Function Call")
                return None
            return await agent.function_call(messages, self.tools, model=model, application_scenario=f"{self.function_call_scenario}-{self.game_type}")
        except Exception as e:
            logger.error(f"函数调用处理失败: {e}")
            return None

    async def init_data(self):
        """Initialize game data

Returns:
BaseGame: current instance, supports chained calls"""
        self.character_list = await self.character_db.get_by_game_id(int(self.taskInput.task_id))
        self.game_info = await self.game_play_db.get_by_game_play_type(self.game_type)
        try:
            game_config = self.game_info.additional_content
            config = {}
            for key, value in game_config.items():
                config[key] = value.get("value")
            self.game_config = config
        except Exception:
            logger.error("Failed to initialize configuration")

        if self.character_list:
            # Filter out directly, no selected ones.
            self.character_list = [item for item in self.character_list if item.role_id in self.taskInput.roles]
            self.character_infos = await self.role_db.get_by_ids(role_ids=self.taskInput.roles)
            # To create agents, you need to use await because subclasses may be implemented as asynchronous methods
            self.agents = await self.create_agents()
            await self.__init_agent_client()

        # Registration tool
        self._register_tool()
        
        # Load session data from Redis (if present)
        await self._load_session_from_redis()
        
        return self

    async def _load_session_from_redis(self):
        """Loading session data from Redis"""
        if not self.session_id:
            return
            
        # Load session data
        session_data = await GameSessionManager.load_game_session(self.session_id, self.game_type)
        if session_data:
            # Session data exists and state can be restored
            logger.info(f"从Redis加载游戏会话: {self.session_id}")
            
            # The properties of the game state can be restored here
            if "soup_surface" in session_data and hasattr(self, "soup_surface"):
                self.soup_surface = session_data["soup_surface"]
            if "soup_truth" in session_data and hasattr(self, "soup_truth"):
                self.soup_truth = session_data["soup_truth"]

    async def set_init_data(self, character_list, game_info: GameBaseInfo = None, function_call_scenario=LLMApplication.BACKEND_CHAT_GAME_PLAY):
        """Set initialization data

Args:
character_list: Character List
game_info: Game Information
function_call_scenario: Function Call Scenario

Returns:
BaseGame: current instance, supports chained calls"""
        self.function_call_scenario = function_call_scenario
        self.character_list = character_list
        self.character_list = [item for item in self.character_list if item.role_id in self.taskInput.roles]
        self.character_infos = await self.role_db.get_by_ids(role_ids=self.taskInput.roles)
        # To create agents, you need to use await because subclasses may be implemented as asynchronous methods
        self.agents = await self.create_agents()
        await self.__init_agent_client()
        
        if game_info:
            if not self.game_info:
                self.game_info = GameBaseInfo()
            self.game_info.description = game_info.description
            self.game_info.setting = game_info.setting
            self.game_info.reference_case = game_info.reference_case
        
        # Loading session data from Redis
        await self._load_session_from_redis()
        
        return self

    async def __init_agent_client(self):
        """Initialize agent client side"""
        for agent in self.agents:
            await agent.init_client()

    async def create_agents(self) -> List[BaseGameAgent]:
        """Create an agent list, subclasses must implement

Returns:
List [BaseGameAgent]: list of agents"""
        raise NotImplementedError("Subclasses must implement create_agents methods")

    async def create_prompt(self, prompt_id: str, info: Dict[str, Any]) -> str:
        """Create prompt word

Args:
prompt_id: Cue Word ID
Info: hint word parameter

Returns:
Str: generated cue word"""
        cache = CacheManager()
        prompt = await cache.get_nearest_prompt(role_id=prompt_id)
        # Process template
        return prompt_pre(prompt.prompt_text, info)

    @property
    def registry(self):
        """Get game type regedit"""
        return self._registry

    async def register_websocket(self, session_id: str, websocket: WebSocket) -> None:
        """Register a WebSocket to connect to a specific session

Args:
session_id: Session ID
WebSocket: WebSocket connection instance"""
        # Generate a unique websocket ID
        websocket_id = str(uuid.uuid4())
        # Add the ID attribute to the WebSocket object
        setattr(websocket, "id", websocket_id)
        
        # Initialize the local websocket collection (if it doesn't exist)
        if session_id not in self._local_websockets:
            self._local_websockets[session_id] = set()
            self._local_message_queue[session_id] = []

        # Add a new websocket connection to local management
        self._local_websockets[session_id].add(websocket)
        
        # Register with Redis
        await GameSessionManager.save_websocket_info(session_id, websocket_id, self.game_type)

        # Load session data from Redis and send chat history
        session_data = await GameSessionManager.load_game_session(session_id, self.game_type)
        if session_data and "game_record" in session_data:
            game_record = session_data["game_record"]
            for message in game_record:
                try:
                    await websocket.send_json(message)
                    await asyncio.sleep(0.05)
                except Exception as e:
                    logger.error(f"发送历史消息出错: {str(e)}")

        # Backlog of messages in the sending queue
        if session_id in self._local_message_queue:
            for message in self._local_message_queue[session_id]:
                try:
                    await websocket.send_json(message)
                    await asyncio.sleep(0.05)
                except Exception as e:
                    logger.error(f"发送队列消息出错: {str(e)}")

            # Clear the sent message queue
            self._local_message_queue[session_id] = []

    async def unregister_websocket(self, session_id: str, websocket: WebSocket) -> None:
        """Unregister WebSocket Connection

Args:
session_id: Session ID
WebSocket: WebSocket connection instance"""
        # Get WebSocket ID
        websocket_id = getattr(websocket, "id", None)
        
        # Remove from local administration
        if session_id in self._local_websockets:
            self._local_websockets[session_id].discard(websocket)

            # If there are no more connections, consider cleaning up resources
            if not self._local_websockets[session_id]:
                del self._local_websockets[session_id]
                # But keep the message queue until the end of the session
        
        # Remove from Redis
        if websocket_id:
            await GameSessionManager.remove_websocket_info(session_id, websocket_id, self.game_type)

    async def send_message(self, message: Dict[str, Any]) -> None:
        """Send a message to all WebSocket connections for the specified session

Args:
Message: The message to be sent"""
        # Validate and standardize messages using Pydantic models
        validated_message = GameMessage(**message).dict()

        # If no session ID is specified, try to get it from the sessionId field of the message
        session_id = self.session_id
        if not session_id and "sessionId" in validated_message:
            session_id = validated_message.get("sessionId")

        # If there is still no session_id, the message cannot be sent
        if not session_id:
            logger.error("Unable to send message: No session ID specified and message does not contain sessionId field")
            return

        # Load current session data
        session_data = await GameSessionManager.load_game_session(session_id, self.game_type)
        if not session_data:
            session_data = {
                "game_type": self.game_type,
                "session_id": session_id,
                "created_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
                "game_record": []
            }
            
        # Update session history
        game_record = session_data.get("game_record", [])
        
        # Avoid adding the same message repeatedly
        if not any(msg.get("msgId") == validated_message.get("msgId") for msg in game_record):
            game_record.append(validated_message)
            session_data["game_record"] = game_record
            session_data["last_activity"] = datetime.now().isoformat()
            
            # Save updated session data
            await GameSessionManager.save_game_session(session_id, session_data, self.game_type)

        # If there is a local WebSocket connection, send a message to all connections
        if session_id in self._local_websockets and self._local_websockets[session_id]:
            disconnected = set()

            for ws in self._local_websockets[session_id]:
                try:
                    await ws.send_json(validated_message)
                except WebSocketDisconnect:
                    disconnected.add(ws)
                except Exception as e:
                    logger.error(f"发送消息出错: {str(e)}")
                    disconnected.add(ws)

            # Remove broken connections
            for ws in disconnected:
                await self.unregister_websocket(session_id, ws)

            # If all connections are lost, store the message in a local queue
            if not self._local_websockets[session_id] and disconnected:
                if session_id not in self._local_message_queue:
                    self._local_message_queue[session_id] = []
                self._local_message_queue[session_id].append(validated_message)
        else:
            # If there is no active WebSocket connection, store messages in a local queue
            if session_id not in self._local_message_queue:
                self._local_message_queue[session_id] = []
            self._local_message_queue[session_id].append(validated_message)

        # Print to the console at the same time (for debugging)
        logger.debug(f"消息[{session_id}]: {json.dumps(validated_message, ensure_ascii=False)}")

    async def initialize_game(self, customize_parameters: Optional[Dict[str, Any]] = None) -> None:
        """Initialize game configuration

Args:
customize_parameters: Custom Parameters"""
        raise NotImplementedError("Subclasses must implement initialize_game methods")

    async def play_round(self, message: Optional[str] = None) -> Dict:
        """Game round

Args:
Message: User Message

Returns:
Dicts: Round Results"""
        raise NotImplementedError("Subclasses must implement play_round methods")

    async def end_game(self):
        """Game Over"""
        raise NotImplementedError("Subclasses must implement end_game methods")

    async def play_game(self,
                        websocket: WebSocket,
                        customize_parameters: Optional[Dict[str, Any]] = None,
                        ) -> None:
        """Start game

Args:
WebSocket: WebSocket connection
customize_parameters: Custom Parameters"""
        # Check if a session exists
        session_data = await GameSessionManager.load_game_session(self.session_id, self.game_type)
        if not session_data or "game_record" not in session_data:
            logger.info(f"创建新游戏会话: {self.session_id}")
            # Initialize game
            await self.initialize_game(customize_parameters)
            logger.info(f"游戏初始化成功: 会话ID={self.session_id}")
        else:
            logger.info(f"恢复已有游戏会话: {self.session_id}")
            is_game_over = session_data.get("is_game_over", False)
            if not is_game_over:
                # Notify the front-end user that they can enter
                await websocket.send_json({
                    "status": "waiting_for_human",
                    "message": "It's your turn to ask questions"
                })
    async def send_message_answer(self, agent=None, answer: str = "", role="system",usage:LLMTokenResponse = None):
        """Send message reply

Args:
Agent: Agent
Answer: the answer
Role: Role
Usage: spent token information"""
        agent_id = ""
        role_info = json.dumps({})
        if agent:
            agent_id = agent.agent_id
            role_info = json.dumps(agent.role_info)
        # Create response message
        answer_msg = {
            "msgId": str(uuid.uuid4()),
            "role": role,
            "agentId": agent_id,
            "content": answer,
            "timestamp": self._get_timestamp(),
            "sessionId": self.session_id,
            "role_info": role_info,
            "usage": {
                "input_tokens": usage.input_tokens if usage else 0,
                "output_tokens": usage.output_tokens if usage else 0,
                "total_tokens": usage.total_tokens if usage else 0,
                "price": usage.price if usage else 0.0
            } if usage else {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "price": 0.0
            }
        }
        await self.send_message(answer_msg)

    def _get_timestamp(self):
        """Get the current timestamp"""
        return int(time.time() * 1000)


def prompt_pre(text, dist_kwargs: dict[str, str]):
    """Replace variables in prompt word templates

Args:
Text: Cue word template
dist_kwargs: Variable Dictionary

Returns:
Replaced cue word"""
    if not text:
        return text
    if not ("{" in text):
        return text
    template = text
    for key, value in dist_kwargs.items():
        template = template.replace("{" + key + "}", str(value))
    return template
