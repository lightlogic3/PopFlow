from knowledge_api.framework.ai_collect import BaseLLM
from knowledge_api.framework.redis.cache_manager import CacheManager
from knowledge_api.framework.memory.enhanced_chat_memory_manager import EnhancedChatMemoryManager
import time
import uuid
from typing import Optional
from pydantic import BaseModel, Field, root_validator


class GameRole:
    def __init__(self, role_id, model_id, setting="", voice="", role_info=None):
        self.role_id = role_id
        self.model_id = model_id
        self.setting = setting
        self.voice = voice
        self.role_info = role_info


class BaseGameAgent:
    def __init__(self, role: GameRole, system=""):
        self.agent_id = role.role_id
        self.model_id = role.model_id
        self.client: BaseLLM = None
        self.setting = role.setting  # identity settings
        self.voice = role.voice  # sound timbre
        self.memory = EnhancedChatMemoryManager(
            k=20,
            system_message=system,
            memory_type='buffer_window',
        )
        self.system = system
        self.role_info = role.role_info
        self.identity = ""
        self.role:GameRole=role

    async def init_client(self):
        self.client = await CacheManager().get_ai_by_model_id(self.model_id)
        if self.client is None:
            self.client = await CacheManager().get_ai_by_model_id(
                await CacheManager().get_system_config("DEFAULT_LLM_MODEL_TASK"))

    async def chat(self, user_msg="") -> str:
        if user_msg:
            self.memory.add_user_message(user_msg)
        chat_data = await self.client.chat_completion(
            messages=self.memory.get_formatted_history(),
            temperature=0.7,
            application_scenario=f"test"
        )
        if user_msg:
            self.memory.add_ai_message(chat_data.content)
        return chat_data.content


class TurtleSoupGameAgent(BaseGameAgent):
    def __init__(self, role, system, identity="player"):
        super().__init__(role, system)
        self.identity = identity  # Player, setter


# Message Model Definition
class GameMessage(BaseModel):
    """Game message model for validating and standardizing message formats"""
    msgId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str
    content: str
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))
    agentId: Optional[str] = None
    replyTo: Optional[str] = None
    isHint: Optional[bool] = None
    isReveal: Optional[bool] = None
    playerIndex: Optional[int] = None
    role_info: Optional[str] = None

    @root_validator(pre=True)
    def set_defaults(cls, values):
        """Set default values to ensure that necessary fields are present"""
        if "role" not in values:
            values["role"] = "system"
        if "content" not in values and values.get("role") == "system":
            values["content"] = "System message"
        return values

    class Config:
        # Allow additional fields to support future extensions
        extra = "allow"


class GameBaseInfo(BaseModel):
    description: Optional[str] = None  # task description
    setting: Optional[str] = None  # task setting
    reference_case: Optional[str] = None  # Reference case
