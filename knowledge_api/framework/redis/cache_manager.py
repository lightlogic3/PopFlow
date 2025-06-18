"""Redis-based cache manager
Provide a unified cache service interface to manage various cache objects"""
from typing import Dict, Any, Optional, List

from knowledge_api.framework.ai_collect import BaseLLM
from knowledge_api.framework.redis.cache_system.character_prompt_cache import CharacterPromptCache
from knowledge_api.framework.redis.cache_system.llm_provider_cache import LLMProviderCache
from knowledge_api.framework.redis.cache_system.model_config_cache import ModelConfigCache
from knowledge_api.framework.redis.cache_system.role_cache import RoleCache
from knowledge_api.framework.redis.cache_system.system_config_cache import SystemConfigCache
from knowledge_api.framework.redis.config import get_redis_config
from knowledge_api.framework.redis.connection import get_redis_connection_manager
from knowledge_api.utils.log_config import get_logger

from knowledge_api.mapper.character_prompt_config.base import CharacterPromptConfig
from knowledge_api.mapper.character_prompt_config.crud import CharacterPromptConfigCRUD
from knowledge_api.mapper.llm_provider_config.base import LLMProviderConfig
from knowledge_api.mapper.llm_provider_config.crud import LLMProviderConfigCRUD
from knowledge_api.mapper.llm_model_config.base import LLMModelConfig
from knowledge_api.mapper.llm_model_config.crud import LLMModelConfigCRUD
from knowledge_api.mapper.system_config.crud import SystemConfigCRUD
from knowledge_api.mapper.roles.base import Role
from knowledge_api.mapper.roles.crud import RoleCRUD

logger = get_logger()

class CacheManager:
    """cache manager
Manage various cache objects and provide a unified interface"""
    _instance = None

    def __new__(cls):
        """singleton pattern"""
        if cls._instance is None:
            cls._instance = super(CacheManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize cache"""
        self.redis_config = get_redis_config()
        
        # Obtain various cache instances
        self.character_prompt_cache = CharacterPromptCache()
        self.system_config_cache = SystemConfigCache()
        self.llm_provider_cache = LLMProviderCache()
        self.model_config_cache = ModelConfigCache()
        self.role_config_cache = RoleCache()
        
        # cache configuration
        self.cache_config = {
            "enable_character_prompt_cache": True,
            "enable_system_config_cache": True,
            "enable_llm_provider_cache": True,
            "enable_model_config_cache": True,
            "enable_role_config_cache": True
        }

    def set_cache_config(self, config: Dict[str, bool]):
        """Set cache switch"""
        self.cache_config.update(config)
        
        # Update the status of individual cache components
        self.character_prompt_cache.set_enabled(
            self.cache_config.get("enable_character_prompt_cache", True)
        )
        self.system_config_cache.set_enabled(
            self.cache_config.get("enable_system_config_cache", True)
        )
        self.llm_provider_cache.set_enabled(
            self.cache_config.get("enable_llm_provider_cache", True)
        )
        self.model_config_cache.set_enabled(
            self.cache_config.get("enable_model_config_cache", True)
        )
        self.role_config_cache.set_enabled(
            self.cache_config.get("enable_role_config_cache", True)
        )

    async def load_character_prompts(self, crud: Optional[CharacterPromptConfigCRUD] = None):
        """Load character prompt word configuration to cache

Args:
Crud: Optional CharacterPromptConfigCRUD instance"""
        if not self.cache_config["enable_character_prompt_cache"]:
            return
            
        await self.character_prompt_cache.load_all(crud)

    async def load_system_configs(self, crud: Optional[SystemConfigCRUD] = None):
        """Load system configuration to cache

Args:
Crud: Optional SystemConfigCRUD instance"""
        if not self.cache_config["enable_system_config_cache"]:
            return
            
        await self.system_config_cache.load_all(crud)

    async def load_llm_providers(self, crud: Optional[LLMProviderConfigCRUD] = None):
        """Load LLM provider configuration to cache

Args:
Crud: Optional LLMProviderConfigCRUD instance"""
        if not self.cache_config["enable_llm_provider_cache"]:
            return
            
        await self.llm_provider_cache.load_all(crud)
        
    async def load_model_configs(self, crud: Optional[LLMModelConfigCRUD] = None):
        """Load LLM model configuration to cache

Args:
Crud: Optional LLMModelConfigCRUD instance"""
        if not self.cache_config["enable_model_config_cache"]:
            return
            
        await self.model_config_cache.load_all(crud)
        
    async def load_role_configs(self, crud: Optional[RoleCRUD] = None):
        """Load role configuration to cache

Args:
Crud: Optional instance of RoleCRUD"""
        if not self.cache_config["enable_role_config_cache"]:
            return
            
        await self.role_config_cache.load_all(crud)

    async def get_system_config_value(self, key: str, default_value: Any = None) -> Any:
        """Get system configuration value

Args:
Key: configuration key
default_value: Default

Returns:
Any: Configuration value, returns the default value if it does not exist"""
        if not self.cache_config["enable_system_config_cache"]:
            return default_value
            
        return await self.system_config_cache.get_value(key, default_value)

    async def get_llm_provider(self, provider_name: str) -> Optional[LLMProviderConfig]:
        """Obtain LLM Provider Configuration

Args:
provider_name: Provider Name

Returns:
Optional [LLMProviderConfig]: Provider configuration, return None if not present"""
        if not self.cache_config["enable_llm_provider_cache"]:
            return None
            
        return await self.llm_provider_cache.get_provider(provider_name)
        
    async def get_llm_provider_by_id(self, provider_id: int) -> Optional[LLMProviderConfig]:
        """Obtain LLM provider configuration by ID

Args:
provider_id: Provider ID

Returns:
Optional [LLMProviderConfig]: Provider configuration, return None if not present"""
        if not self.cache_config["enable_llm_provider_cache"]:
            return None
            
        return await self.llm_provider_cache.get_provider_by_id(provider_id)
        
    async def get_model_config(self, model_id: str) -> Optional[LLMModelConfig]:
        """Get model configuration

Args:
model_id: Model ID

Returns:
Optional [LLMModelConfig]: Model configuration, return None if not present"""
        if not self.cache_config["enable_model_config_cache"]:
            return None
            
        return await self.model_config_cache.get_model(model_id)
        
    async def get_provider_models(self, provider_id: int) -> list[LLMModelConfig]:
        """Acquire all models from the provider

Args:
provider_id: Provider ID

Returns:
List [LLMModelConfig]: Model configuration list"""
        if not self.cache_config["enable_model_config_cache"]:
            return []
            
        return await self.model_config_cache.get_provider_models(provider_id)
        
    async def get_all_models(self) -> Dict[str, LLMModelConfig]:
        """Get all model configurations

Args:
model_id: Model ID

Returns:
Dict [str, LLMModelConfig]: Model configuration dictionary with model_id keys"""
        if not self.cache_config["enable_model_config_cache"]:
            return {}
            
        return await self.model_config_cache.get_all_models()
        
    async def get_role(self, role_id: str) -> Optional[Role]:
        """Get role configuration

Args:
role_id: Role ID

Returns:
Optional [Role]: Role configuration, return None if not present"""
        if not self.cache_config["enable_role_config_cache"]:
            return None
            
        return await self.role_config_cache.get_role(role_id)
        
    async def get_role_by_name(self, name: str) -> Optional[Role]:
        """Get role configuration by name

Args:
Name: Role Name

Returns:
Optional [Role]: Role configuration, return None if not present"""
        if not self.cache_config["enable_role_config_cache"]:
            return None
            
        return await self.role_config_cache.get_by_name(name)
        
    async def get_all_roles(self) -> List[Role]:
        """Get all role configurations

Returns:
List [Roles]: Role configuration list"""
        if not self.cache_config["enable_role_config_cache"]:
            return []
            
        return await self.role_config_cache.get_all_roles()

    async def get_ai(self) -> BaseLLM:
        """Get the default AI instance

Returns:
BaseLLM: Default AI instance, return None if creation fails"""
        return await self.llm_provider_cache.get_ai(self.system_config_cache)
        
    async def get_ai_by_model_id(self, model_id: str) -> Optional[BaseLLM]:
        """Obtain AI instances based on model ID

Args:
model_id: Model ID

Returns:
Optional [BaseLLM]: AI instance, return None if creation fails"""
        return await self.llm_provider_cache.get_ai_by_model_id(
            model_id, 
            self.model_config_cache
        )
        
    # Compatible with outdated API
    async def get_ai_by_name(self, provider_name: str) -> Optional[BaseLLM]:
        """Get AI instances by provider name (deprecated, compatibility preserved)

Args:
provider_name: Provider Name

Returns:
Optional [BaseLLM]: AI instance, return None if creation fails"""
        logger.warning(f"get_ai_by_name方法已废弃，请使用get_ai_by_model_id")
        # Get a default model ID
        model_id = provider_name  # Try using provider_name as model_id
        return await self.get_ai_by_model_id(model_id)

    async def get_nearest_prompt(self, role_id: str, current_level: float=9999.0, crud: Optional[CharacterPromptConfigCRUD] = None) -> Optional[CharacterPromptConfig]:
        """Get the most recent prompt word configuration

Args:
role_id: Role ID
current_level: Current level
Crud: Optional CharacterPromptConfigCRUD instance

Returns:
Optional [CharacterPromptConfig]: Recent prompt word configuration, returns None when none exists"""
        if not self.cache_config["enable_character_prompt_cache"]:
            return None
            
        return await self.character_prompt_cache.get_nearest_prompt(role_id, current_level, crud)

    async def update_character_prompt(self, config: CharacterPromptConfig, crud: Optional[CharacterPromptConfigCRUD] = None) -> bool:
        """Update character prompt word configuration

Args:
Config: Configuration to update
Crud: Optional CharacterPromptConfigCRUD instance

Returns:
Bool: whether the operation was successful"""
        if not self.cache_config["enable_character_prompt_cache"]:
            return False
        
        return await self.character_prompt_cache.update(config, crud)

    async def delete_character_prompt(self, role_id: str, level: float, crud: Optional[CharacterPromptConfigCRUD] = None) -> bool:
        """Delete character prompt word configuration

Args:
role_id: Role ID
Level: Level
Crud: Optional CharacterPromptConfigCRUD instance

Returns:
Bool: whether the operation was successful"""
        if not self.cache_config["enable_character_prompt_cache"]:
            return False
        
        return await self.character_prompt_cache.delete(role_id, level, crud)
        
    async def update_model_config(self, model: LLMModelConfig, crud: Optional[LLMModelConfigCRUD] = None) -> bool:
        """Update model configuration

Args:
Model: model configuration
Crud: Optional LLMModelConfigCRUD instance

Returns:
Bool: whether the operation was successful"""
        if not self.cache_config["enable_model_config_cache"]:
            return False
        
        return await self.model_config_cache.update(model, crud)
        
    async def delete_model_config(self, model_id: str, provider_id: Optional[int] = None, crud: Optional[LLMModelConfigCRUD] = None) -> bool:
        """Delete model configuration

Args:
model_id: Model ID
provider_id: Optional Provider ID that can be optimized for deletion
Crud: Optional LLMModelConfigCRUD instance

Returns:
Bool: whether the operation was successful"""
        if not self.cache_config["enable_model_config_cache"]:
            return False
        
        return await self.model_config_cache.delete(model_id, provider_id, crud)
        
    async def update_role(self, role: Role) -> bool:
        """Update role configuration

Args:
Role: role configuration
Crud: Optional instance of RoleCRUD

Returns:
Bool: whether the operation was successful"""
        if not self.cache_config["enable_role_config_cache"]:
            return False
        
        return await self.role_config_cache.update(role)
        
    async def delete_role(self, role_id: str, crud: Optional[RoleCRUD] = None) -> bool:
        """Delete role configuration

Args:
role_id: Role ID
Crud: Optional instance of RoleCRUD

Returns:
Bool: whether the operation was successful"""
        if not self.cache_config["enable_role_config_cache"]:
            return False
        
        return await self.role_config_cache.delete(role_id, crud)

    async def get_system_config(self, key: str, default=None) -> Optional[Any]:
        """Get system configuration from cache (compatible with old API names)"""
        return await self.system_config_cache.get_value(key, default)

    def close_connections(self):
        """Close all connections"""
        # Close the LLM instance
        self.llm_provider_cache.close_all_instances()
        
        # Close Redis connection
        get_redis_connection_manager().close_all_connections()
        logger.info("All Redis connections have been closed")

# Compatible with the original name
RedisCacheManager = CacheManager 