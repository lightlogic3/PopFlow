"""LLM model configuration cache service
Handling cache operations for the LLM model"""
import asyncio
from typing import Dict, List, Optional

from knowledge_api.framework.redis.cache import RedisCache
from knowledge_api.framework.redis.config import get_redis_config
from knowledge_api.mapper.llm_model_config.base import LLMModelConfig
from knowledge_api.mapper.llm_model_config.crud import LLMModelConfigCRUD
from knowledge_api.framework.database.database import get_db_session
from knowledge_api.utils.log_config import get_logger

logger = get_logger()

class ModelConfigCache:
    """LLM model configuration cache service
Cache operations for managing model configurations"""
    _instance = None

    def __new__(cls):
        """singleton pattern"""
        if cls._instance is None:
            cls._instance = super(ModelConfigCache, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize cache"""
        self.redis_config = get_redis_config()
        self.enabled = True
        
        # Initialize Redis cache
        self.cache = RedisCache(
            prefix=f"{self.redis_config.KEY_PREFIX}llm_model",
            model_class=LLMModelConfig
        )

    def set_enabled(self, enabled: bool):
        """Set cache switch"""
        self.enabled = enabled
    
    async def load_all(self, crud: Optional[LLMModelConfigCRUD] = None):
        """Load all model configurations to cache

Args:
Crud: Optional LLMModelConfigCRUD instance, automatically created if not provided"""
        if not self.enabled:
            return
        
        use_provided_crud = crud is not None
        
        try:
            # If no crud instance is passed in, create a temporary one
            if not use_provided_crud:
                with get_db_session() as session:
                    crud = LLMModelConfigCRUD(session)
                    
                    # Get all enabled models
                    models = await crud.get_active_models()
                    
                    # Transforming models to cache-safe objects
                    models = [LLMModelConfig.model_validate(model.model_dump()) for model in models]
                    
                    # Reset cache
                    await self.cache.clear_prefix()
                    
                    # Create a map by model_id
                    models_by_id = {model.model_id: model for model in models}
                    
                    # Group by provider_id
                    models_by_provider = {}
                    for model in models:
                        provider_id = model.provider_id
                        if provider_id not in models_by_provider:
                            models_by_provider[provider_id] = []
                        models_by_provider[provider_id].append(model)
                    
                    # Create cache task
                    tasks = []
                    
                    # Cache mappings for all models
                    tasks.append(self.cache.set("all_models", models_by_id))
                    
                    # Model of cache grouping by provider
                    for provider_id, provider_models in models_by_provider.items():
                        tasks.append(self.cache.set(f"provider:{provider_id}", provider_models))
                    
                    # Cache each model individually
                    for model_id, model in models_by_id.items():
                        tasks.append(self.cache.set(f"model:{model_id}", model))
                        
                    # Perform all caching tasks
                    await asyncio.gather(*tasks)
                    logger.info(f"已加载 {len(models)} 个LLM模型配置到Redis缓存")
            else:
                # Using the provided crud instance
                # Get all enabled models
                models = await crud.get_active_models()
                
                # Transforming models to cache-safe objects
                models = [LLMModelConfig.model_validate(model.model_dump()) for model in models]
                
                # Reset cache
                await self.cache.clear_prefix()
                
                # Create a map by model_id
                models_by_id = {model.model_id: model for model in models}
                
                # Group by provider_id
                models_by_provider = {}
                for model in models:
                    provider_id = model.provider_id
                    if provider_id not in models_by_provider:
                        models_by_provider[provider_id] = []
                    models_by_provider[provider_id].append(model)
                
                # Create cache task
                tasks = []
                
                # Cache mappings for all models
                tasks.append(self.cache.set("all_models", models_by_id))
                
                # Model of cache grouping by provider
                for provider_id, provider_models in models_by_provider.items():
                    tasks.append(self.cache.set(f"provider:{provider_id}", provider_models))
                
                # Cache each model individually
                for model_id, model in models_by_id.items():
                    tasks.append(self.cache.set(f"model:{model_id}", model))
                    
                # Perform all caching tasks
                await asyncio.gather(*tasks)
                logger.info(f"已加载 {len(models)} 个LLM模型配置到Redis缓存")
            
        except Exception as e:
            logger.error(f"加载LLM模型缓存出错: {e}")
            import traceback
            traceback.print_exc()

    async def get_model(self, model_id: str) -> Optional[LLMModelConfig]:
        """Get the model configuration and load from the database if not in the cache

Args:
model_id: Model ID

Returns:
Optional [LLMModelConfig]: Model configuration, return None if not present"""
        if not self.enabled:
            return None
            
        try:
            # Get it directly from Redis
            model = await self.cache.get(f"model:{model_id}")
            if model:
                return model
                
            # If not in separate cache, try fetching from all_models
            all_models = await self.cache.get("all_models")
            if all_models and model_id in all_models:
                return all_models[model_id]

            tem_model=None
            # If not in the cache, load from the database
            with get_db_session() as session:
                # Create a CRUD instance
                crud = LLMModelConfigCRUD(session)
                
                # Note: There is no way to directly query through model_id in the database, because model_id need to provider_id joint query
                # Get all models and then filter
                all_db_models = await crud.get_all()
                for model in all_db_models:
                    if model.model_id == model_id:
                        # Clone the model object outside the session
                        tem_model = LLMModelConfig.model_validate(model.model_dump())
                        # Cache to Redis
                        await self.cache.set(f"model:{model_id}", tem_model)
                        logger.info(f"已从数据库加载并缓存LLM模型: {model_id}")
                        break
                
            return tem_model
                
        except Exception as e:
            logger.error(f"获取LLM模型配置出错: {e}")
            return None

    async def get_provider_models(self, provider_id: int) -> List[LLMModelConfig]:
        """Obtain all model configurations from the vendor

Args:
provider_id: Supplier ID

Returns:
List [LLMModelConfig]: Model configuration list"""
        if not self.enabled:
            return []
            
        try:
            # Get it from Redis
            models = await self.cache.get(f"provider:{provider_id}")
            if models:
                return models
                
            # If not in the cache, load from the database
            with get_db_session() as session:
                crud = LLMModelConfigCRUD(session)
                db_models = await crud.get_by_provider_id(provider_id=provider_id)
                
                if db_models:
                    # Clone the model object outside the session
                    models = [LLMModelConfig.model_validate(model.model_dump()) for model in db_models]
                    
                    # Cache to Redis
                    await self.cache.set(f"provider:{provider_id}", models)
                    logger.info(f"已从数据库加载并缓存供应商 {provider_id} 的所有模型")
                    
                    # Updating the cache of a single model simultaneously
                    for model in models:
                        await self.cache.set(f"model:{model.model_id}", model)
                    
                    return models
                
                return []
                
        except Exception as e:
            logger.error(f"获取供应商模型配置出错: {e}")
            return []

    async def get_all_models(self) -> Dict[str, LLMModelConfig]:
        """Get all model configurations

Returns:
Dict [str, LLMModelConfig]: Model configuration dictionary with model_id keys"""
        if not self.enabled:
            return {}
            
        try:
            # Get all model mappings from Redis
            models = await self.cache.get("all_models")
            if models:
                return models
                
            # If not in the cache, load from the database
            with get_db_session() as session:
                crud = LLMModelConfigCRUD(session)
                db_models_list = await crud.get_active_models()
                
                if db_models_list:
                    # Clone the model object outside the session
                    models_list = [LLMModelConfig.model_validate(model.model_dump()) for model in db_models_list]
                    
                    # Convert to dictionary
                    models_dict = {model.model_id: model for model in models_list}
                    
                    # Cache to Redis
                    await self.cache.set("all_models", models_dict)
                    logger.info(f"已从数据库加载并缓存所有模型配置")
                    
                    # Simultaneously group caching by provider
                    models_by_provider = {}
                    for model in models_list:
                        provider_id = model.provider_id
                        if provider_id not in models_by_provider:
                            models_by_provider[provider_id] = []
                        models_by_provider[provider_id].append(model)
                    
                    for provider_id, provider_models in models_by_provider.items():
                        await self.cache.set(f"provider:{provider_id}", provider_models)
                    
                    # Cache a single model
                    for model in models_list:
                        await self.cache.set(f"model:{model.model_id}", model)
                    
                    return models_dict
                
                return {}
                
        except Exception as e:
            logger.error(f"获取所有模型配置出错: {e}")
            return {}

    async def update(self, model: LLMModelConfig, crud: Optional[LLMModelConfigCRUD] = None) -> bool:
        """Update model configuration

Args:
Model: model configuration
Crud: Optional LLMModelConfigCRUD instance

Returns:
Bool: whether the operation was successful"""
        if not self.enabled:
            return False
            
        use_provided_crud = crud is not None
            
        try:
            model_id = model.model_id
            provider_id = model.provider_id
            
            # If no crud instance is passed in, create a temporary one
            if not use_provided_crud:
                with get_db_session() as session:
                    crud = LLMModelConfigCRUD(session)
                    
                    # First verify whether the model exists in the database
                    db_model = await crud.get_by_provider_and_model(provider_id=provider_id, model_id=model_id)
                    if not db_model:
                        logger.warning(f"要更新的LLM模型在数据库中不存在: {model_id}")
                        return False
            else:
                # Using the provided crud instance
                # First verify whether the model exists in the database
                db_model = await crud.get_by_provider_and_model(provider_id=provider_id, model_id=model_id)
                if not db_model:
                    logger.warning(f"要更新的LLM模型在数据库中不存在: {model_id}")
                    return False
            
            # update model cache
            await self.cache.set(f"model:{model_id}", model)
            
            # Update all_models cache
            all_models = await self.cache.get("all_models")
            if all_models:
                all_models[model_id] = model
                await self.cache.set("all_models", all_models)
            
            # Update provider model list cache
            provider_models = await self.cache.get(f"provider:{provider_id}")
            if provider_models:
                # Find and update models in the list
                updated = False
                for i, m in enumerate(provider_models):
                    if m.model_id == model_id:
                        provider_models[i] = model
                        updated = True
                        break
                
                # If not found, add
                if not updated:
                    provider_models.append(model)
                
                await self.cache.set(f"provider:{provider_id}", provider_models)
                    
            logger.info(f"已更新LLM模型配置: {model_id}")
            return True
            
        except Exception as e:
            logger.error(f"更新LLM模型缓存出错 (model_id={model.model_id}): {e}")
            return False

    async def delete(self, model_id: str, provider_id: Optional[int] = None, crud: Optional[LLMModelConfigCRUD] = None) -> bool:
        """Delete model configuration

Args:
model_id: Model ID
provider_id: Optional Supplier ID, provided to optimize deletion
Crud: Optional LLMModelConfigCRUD instance

Returns:
Bool: whether the operation was successful"""
        if not self.enabled:
            return False
            
        try:
            # If no provider_id is provided, you need to obtain the model information first
            if provider_id is None:
                model = await self.get_model(model_id)
                if model:
                    provider_id = model.provider_id
                else:
                    # If the model does not exist, provide a temporary crud to retrieve the database data
                    with get_db_session() as session:
                        temp_crud = LLMModelConfigCRUD(session)
                        all_models = await temp_crud.get_all()
                        for m in all_models:
                            if m.model_id == model_id:
                                provider_id = m.provider_id
                                break
            
            # Delete model cache
            await self.cache.delete(f"model:{model_id}")
            
            # Update all_models cache
            all_models = await self.cache.get("all_models")
            if all_models and model_id in all_models:
                del all_models[model_id]
                await self.cache.set("all_models", all_models)
            
            # If you know provider_id, update the provider model list cache
            if provider_id:
                provider_models = await self.cache.get(f"provider:{provider_id}")
                if provider_models:
                    # Filter out models to be deleted
                    provider_models = [m for m in provider_models if m.model_id != model_id]
                    await self.cache.set(f"provider:{provider_id}", provider_models)
                    
            logger.info(f"已删除LLM模型配置: {model_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除LLM模型缓存出错 (model_id={model_id}): {e}")
            return False 