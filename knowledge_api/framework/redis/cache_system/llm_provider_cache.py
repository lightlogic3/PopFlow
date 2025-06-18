"""LLM Provider Caching Service
Handling caching operations configured by LLM providers"""
import asyncio
from typing import Dict, Optional, Tuple

from knowledge_api.framework.ai_collect import BaseLLM, LLMFactory
from knowledge_api.framework.redis.cache import RedisCache

from knowledge_api.framework.redis.config import get_redis_config
from knowledge_api.mapper.llm_provider_config.base import LLMProviderConfig
from knowledge_api.mapper.llm_provider_config.crud import LLMProviderConfigCRUD
from knowledge_api.mapper.llm_model_config.base import LLMModelConfig
from knowledge_api.framework.database.database import get_db_session
from knowledge_api.utils.log_config import get_logger

logger = get_logger()

class LLMProviderCache:
    """LLM Provider Caching Service
Manage cache operations and LLM instance creation for LLM provider configurations"""
    _instance = None

    def __new__(cls):
        """singleton pattern"""
        if cls._instance is None:
            cls._instance = super(LLMProviderCache, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize cache"""
        self.redis_config = get_redis_config()
        self.enabled = True
        
        # Initialize Redis cache
        self.cache = RedisCache(
            prefix=f"{self.redis_config.KEY_PREFIX}{self.redis_config.LLM_PROVIDER_PREFIX}",
            model_class=LLMProviderConfig
        )
        
        # LLM instance cache (kept local for performance reasons)
        self.default_llm = None
        self.llm_instances: Dict[str, BaseLLM] = {}  # Use model_id as key

    def set_enabled(self, enabled: bool):
        """Set cache switch"""
        self.enabled = enabled

    async def load_all(self, crud: Optional[LLMProviderConfigCRUD] = None):
        """Load all LLM provider configurations into cache

Args:
Crud: Optional LLMProviderConfigCRUD instance, created automatically if not provided"""
        if not self.enabled:
            return

        temp_session = None
        try:
            providers = await crud.get_active_providers()

            # Reset cache
            await self.cache.clear_prefix()

            # Create a provider map
            provider_dict = {provider.provider_name: provider for provider in providers}
            provider_id_dict = {provider.id: provider for provider in providers}

            # Set up caching for all providers
            tasks = []
            tasks.append(self.cache.set("all_providers", provider_dict))
            tasks.append(self.cache.set("providers_by_id", provider_id_dict))

            # Cache each provider individually
            for name, provider in provider_dict.items():
                tasks.append(self.cache.set(name, provider))
                tasks.append(self.cache.set(f"id:{provider.id}", provider))

            await asyncio.gather(*tasks)
            logger.info(f"已加载 {len(provider_dict)} 个LLM提供商配置到Redis缓存")

        except Exception as e:
            logger.error(f"加载LLM提供商缓存出错: {e}")
        finally:
            # Close a temporary session
            if temp_session:
                temp_session.close()

    async def get_provider(self, provider_name: str) -> Optional[LLMProviderConfig]:
        """Get the LLM provider configuration and load from the database if not in the cache

Args:
provider_name: Provider Name

Returns:
Optional [LLMProviderConfig]: Provider configuration, return None if not present"""
        if not self.enabled:
            return None

        try:
            # Get it directly from Redis
            provider = await self.cache.get(provider_name)
            if provider:
                return provider

            # If not in the cache, load from the database
            with get_db_session() as session:
                crud = LLMProviderConfigCRUD(session)
                provider = await crud.get_by_name(provider_name=provider_name)

                if provider:
                    # Cache to Redis
                    await self.cache.set(provider_name, provider)
                    await self.cache.set(f"id:{provider.id}", provider)

                    # Update provider list cache
                    all_providers = await self.cache.get("all_providers")
                    if all_providers:
                        all_providers[provider_name] = provider
                        await self.cache.set("all_providers", all_providers)

                    providers_by_id = await self.cache.get("providers_by_id")
                    if providers_by_id:
                        providers_by_id[provider.id] = provider
                        await self.cache.set("providers_by_id", providers_by_id)

                    logger.info(f"已从数据库加载并缓存LLM提供商: {provider_name}")
                    return provider

            return None

        except Exception as e:
            logger.error(f"获取LLM提供商配置出错: {e}")
            return None

    async def get_provider_by_id(self, provider_id: int) -> Optional[LLMProviderConfig]:
        """Obtain LLM provider configuration by ID

Args:
provider_id: Provider ID

Returns:
Optional [LLMProviderConfig]: Provider configuration, return None if not present"""
        if not self.enabled:
            return None

        try:
            # Get it directly from Redis
            provider = await self.cache.get(f"id:{provider_id}")
            if provider:
                return provider

            # Try to get from providers_by_id
            providers_by_id = await self.cache.get("providers_by_id")
            if providers_by_id and provider_id in providers_by_id:
                return providers_by_id[provider_id]
                
            # If not in the cache, load from the database
            with get_db_session() as session:
                crud = LLMProviderConfigCRUD(session)
                provider = await crud.get(provider_id=provider_id)
                
                if provider:
                    # Cache to Redis
                    await self.cache.set(f"id:{provider_id}", provider)
                    await self.cache.set(provider.provider_name, provider)
                    
                    # Update provider list cache
                    all_providers = await self.cache.get("all_providers")
                    if all_providers:
                        all_providers[provider.provider_name] = provider
                        await self.cache.set("all_providers", all_providers)
                        
                    providers_by_id = await self.cache.get("providers_by_id")
                    if providers_by_id:
                        providers_by_id[provider_id] = provider
                        await self.cache.set("providers_by_id", providers_by_id)
                        
                    logger.info(f"已从数据库加载并缓存LLM提供商(ID: {provider_id})")
                    return provider
                    
            return None
                
        except Exception as e:
            logger.error(f"获取LLM提供商配置出错 (ID: {provider_id}): {e}")
            return None

    async def get_ai(self, system_config_cache=None) -> BaseLLM:
        """Get the default AI instance

Args:
system_config_cache: Optional system configuration cache instance

Returns:
BaseLLM: Default AI instance, return None if creation fails"""
        if self.default_llm is None:
            # If the default instance does not exist, create a new instance
            default_model_id = ""
            
            if system_config_cache:
                default_model_id = await system_config_cache.get_value("DEFAULT_LLM_MODEL", "")
                if isinstance(default_model_id, str):
                    default_model_id = default_model_id.strip()
            
            if default_model_id:
                self.default_llm = await self.get_ai_by_model_id(default_model_id)
                
        return self.default_llm
        
    async def get_ai_by_model_id(self, model_id: str, model_config_cache=None) -> Optional[BaseLLM]:
        """Get the AI instance with the specified model ID

Args:
model_id: Model ID
model_config_cache: Optional model configuration cache instance

Returns:
Optional [BaseLLM]: AI instance, return None if creation fails"""
        # Check if it is already in the memory cache
        if model_id in self.llm_instances:
            logger.debug(f"从本地缓存获取LLM实例: {model_id}")
            return self.llm_instances[model_id]
            
        # Create a new instance
        model_config, provider_config = await self._get_model_and_provider_info(model_id, model_config_cache)
        
        if not model_config or not provider_config:
            logger.error(f"找不到模型ID({model_id})或其对应的提供商配置")
            return None
            
        # Create an LLM instance
        llm = self._create_llm_instance(model_config, provider_config)
        
        # Add to local cache
        if llm:
            self.llm_instances[model_id] = llm
                
        return llm
    
    async def _get_model_and_provider_info(self, model_id: str, model_config_cache=None) -> Tuple[Optional[LLMModelConfig], Optional[LLMProviderConfig]]:
        """Obtain configuration information for the model and corresponding provider

Args:
model_id: Model ID
model_config_cache: Optional model configuration cache instance

Returns:
Tuple [Optional [LLMModelConfig], Optional [LLMProviderConfig]]:
Model configuration and provider configuration, return None if either does not exist"""
        # Get model configuration
        model_config = None
        if model_config_cache:
            model_config = await model_config_cache.get_model(model_id)
        
        if not model_config:
            # If no model_config_cache is provided or the fetch fails, query directly from the database
            from knowledge_api.mapper.llm_model_config.crud import LLMModelConfigCRUD
            with get_db_session() as session:
                crud = LLMModelConfigCRUD(session)
                # Because there is no way to directly query model_id, you can only get all and then filter
                all_models = await crud.get_all()
                for model in all_models:
                    if model.model_id == model_id:
                        model_config = model
                        break
        
        if not model_config:
            logger.error(f"找不到模型配置: {model_id}")
            return None, None
        
        # Get provider configuration
        provider_id = model_config.provider_id
        provider_config = await self.get_provider_by_id(provider_id)
        
        if not provider_config:
            logger.error(f"找不到模型({model_id})对应的提供商配置(ID: {provider_id})")
            return model_config, None
        
        return model_config, provider_config
    
    def _create_llm_instance(self, model_config: LLMModelConfig, provider_config: LLMProviderConfig) -> Optional[BaseLLM]:
        """Create LLM instances based on model and provider configuration

Args:
model_config: Model Configuration
provider_config: Provider Configuration

Returns:
Optional [BaseLLM]: LLM instance, return None if creation fails"""
        # Merge model and provider configuration
        api_key = provider_config.api_key
        api_url = provider_config.api_url
        
        # Get additional parameters from the model configuration
        extra_config = model_config.extra_config or {}
        
        # If the model has its own URL, the model's URL is preferred
        if extra_config.get("api_url"):
            api_url = extra_config.get("api_url")
        
        # Create an LLM instance
        try:
            llm = LLMFactory.create_llm(
                ai_name=provider_config.provider_sign,
                model=model_config.model_id,
                api_key=api_key,
                base_url=api_url,
                **extra_config
            )
            
            if llm:
                logger.info(f"已创建LLM实例: {model_config.model_id} (提供商: {provider_config.provider_name})")
                return llm
            else:
                logger.error(f"创建LLM实例失败: {model_config.model_id}")
                return None
                
        except Exception as e:
            logger.error(f"创建LLM实例时发生错误 ({model_config.model_id}): {e}")
            return None

    async def update(self, provider: LLMProviderConfig, crud: Optional[LLMProviderConfigCRUD] = None) -> bool:
        """Update LLM Provider Configuration

Args:
Provider: Provider configuration
Crud: Optional LLMProviderConfigCRUD instance, created automatically if not provided

Returns:
Bool: whether the operation was successful"""
        if not self.enabled:
            return False
            
        temp_session = None
        try:
            provider_name = provider.provider_name
            provider_id = provider.id
            # First verify that the configuration exists in the database
            db_config = await crud.get_by_name(provider_name=provider_name)
            if not db_config:
                logger.warning(f"要更新的LLM提供商在数据库中不存在: {provider_name}")
                return False
            
            # Update Provider Cache
            await self.cache.set(provider_name, provider)
            await self.cache.set(f"id:{provider_id}", provider)
            
            # Update all_providers cache
            all_providers = await self.cache.get("all_providers")
            if all_providers:
                all_providers[provider_name] = provider
                await self.cache.set("all_providers", all_providers)
            
            providers_by_id = await self.cache.get("providers_by_id")
            if providers_by_id:
                providers_by_id[provider_id] = provider
                await self.cache.set("providers_by_id", providers_by_id)
            from knowledge_api.framework.redis.cache_system.model_config_cache import ModelConfigCache
            # Clean up the cache of all LLM instances using this provider
            # Due to the change in storage structure, we need to obtain all models under the provider through the model configuration cache
            model_cache = ModelConfigCache()
            models = await model_cache.get_provider_models(provider_id)

            # Clean up the corresponding LLM instance
            for model in models:
                model_id = model.model_id
                if model_id in self.llm_instances:
                    llm = self.llm_instances.pop(model_id)
                    if hasattr(llm, 'close'):
                        try:
                            llm.close()
                        except Exception as e:
                            logger.error(f"关闭LLM实例出错 ({model_id}): {e}")

                    # If it is the default instance, also clear
                    if self.default_llm and self.default_llm is llm:
                        self.default_llm = None

            logger.info(f"已更新LLM提供商配置: {provider_name}")
            return True

        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"更新LLM提供商缓存出错 (provider={provider.provider_name}): {e}")
            return False
        finally:
            # Close a temporary session
            if temp_session:
                temp_session.close()

    async def delete(self, provider_name: str, crud: Optional[LLMProviderConfigCRUD] = None) -> bool:
        """Delete LLM Provider Configuration

Args:
provider_name: Provider Name
Crud: Optional LLMProviderConfigCRUD instance, created automatically if not provided

Returns:
Bool: whether the operation was successful"""
        if not self.enabled:
            return False

        try:
            # Get Provider ID
            provider = await self.get_provider(provider_name)
            provider_id = None
            if provider:
                provider_id = provider.id

            # Verify that the configuration has been deleted from the database
            if crud:
                db_config = await crud.get_by_name(provider_name=provider_name)
                if db_config:
                    logger.warning(f"要删除的LLM提供商在数据库中仍然存在: {provider_name}")

            # Delete the separate provider cache
            await self.cache.delete(provider_name)
            if provider_id:
                await self.cache.delete(f"id:{provider_id}")

            # Update all_providers cache
            all_providers = await self.cache.get("all_providers")
            if all_providers and provider_name in all_providers:
                del all_providers[provider_name]
                await self.cache.set("all_providers", all_providers)

            # Update providers_by_id cache
            if provider_id:
                providers_by_id = await self.cache.get("providers_by_id")
                if providers_by_id and provider_id in providers_by_id:
                    del providers_by_id[provider_id]
                    await self.cache.set("providers_by_id", providers_by_id)

            # Clean up the cache of all LLM instances using this provider
            if provider_id:
                from knowledge_api.framework import ModelConfigCache
                model_cache = ModelConfigCache()
                models = await model_cache.get_provider_models(provider_id)
                
                # Clean up the corresponding LLM instance
                for model in models:
                    model_id = model.model_id
                    if model_id in self.llm_instances:
                        llm = self.llm_instances.pop(model_id)
                        if hasattr(llm, 'close'):
                            try:
                                llm.close()
                            except Exception as e:
                                logger.error(f"关闭LLM实例出错 ({model_id}): {e}")
                        
                        # If it is the default instance, also clear
                        if self.default_llm and self.default_llm is llm:
                            self.default_llm = None
                    
            logger.info(f"已删除LLM提供商配置: {provider_name}")
            return True
            
        except Exception as e:
            logger.error(f"删除LLM提供商缓存出错 (provider_name={provider_name}): {e}")
            return False
            
    def close_all_instances(self):
        """Close all LLM instances"""
        # Close the LLM instance
        if self.default_llm:
            try:
                self.default_llm.close()
            except Exception as e:
                logger.error(f"关闭默认LLM实例失败: {e}")
            self.default_llm = None
            
        # Close all cached LLM instances
        for model_id, llm_instance in list(self.llm_instances.items()):
            if llm_instance and hasattr(llm_instance, 'close'):
                try:
                    llm_instance.close()
                    logger.debug(f"已关闭LLM实例: {model_id}")
                except Exception as e:
                    logger.error(f"关闭LLM实例时出错 {model_id}: {e}")
                    
        self.llm_instances.clear() 