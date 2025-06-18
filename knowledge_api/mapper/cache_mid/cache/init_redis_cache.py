"""Redis cache initialization module
Provides the ability to migrate applications from in-memory cache to Redis cache"""
import os
from typing import Dict

from fastapi import FastAPI
from contextlib import asynccontextmanager

from knowledge_api.framework.redis.cache_manager import RedisCacheManager
from knowledge_api.framework.redis.config import get_redis_config
from knowledge_api.framework.redis.connection import get_async_redis
from knowledge_api.mapper.character_prompt_config.crud import CharacterPromptConfigCRUD
from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.llm_model_config import LLMModelConfigCRUD
from knowledge_api.mapper.llm_provider_config.crud import LLMProviderConfigCRUD
from knowledge_api.mapper.roles.crud import RoleCRUD
from knowledge_api.mapper.system_config.crud import SystemConfigCRUD
from knowledge_api.utils import init_snowflake
from knowledge_api.utils.log_config import get_logger
from knowledge_manage.embeddings.huggingface_embeddings import HuggingFaceEmbeddings
from knowledge_manage.rerank_model.ranking_chinese_base_model import TextRankingModel
logger = get_logger()

# global instance
redis_cache_manager = RedisCacheManager()

# The cache configuration can be modified directly in the code
CACHE_CONFIG = {
    "enable_character_prompt_cache": True,
    "enable_system_config_cache": True,
    "enable_llm_provider_cache": True,
    "enable_model_config_cache": True,
    "enable_role_config_cache": True,
}

@asynccontextmanager
async def redis_cache_lifespan(app: FastAPI):
    """Redis Cache Lifecycle Management
Initialize the Redis cache at startup, and close the connection without cleaning the cached data at shutdown

Replace the original in-memory cache lifecycle manager

Args:
App: FastAPI Application Example"""
    logger.info("Initializing Global Snowflake Algorithm ID Generator...")
    machine_id = int(os.environ.get("SNOWFLAKE_MACHINE_ID", "1"))
    # Initialize Snowflake Algorithm ID Generator
    init_snowflake(machine_id=machine_id)

    logger.info("Initializing vector model and Redis cache...")
    # Initialize the vector model
    from knowledge_api.config import EMBEDDING_MODEL_DEVICE
    HuggingFaceEmbeddings.get_instance("./model/models--BAAI--bge-small-zh-v1.5",
                                     EMBEDDING_MODEL_DEVICE)
    logger.info("The vector model was successfully initialized, initializing the Redis cache....")
    
    # Initialize the sorting model
    try:
        logger.info("Initializing text sorting model...")
        TextRankingModel.initialize(r"./model/model_ranking_chinese_tiny")
        logger.info(f"文本排序模型初始化成功，使用模型路径: {TextRankingModel.get_model_id()}")
    except Exception as e:
        logger.error(f"初始化文本排序模型失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Operation at startup
    db = next(get_session())
    try:
        # Initialize individual services and CRUD instances
        character_prompt_crud = CharacterPromptConfigCRUD(db)
        system_config_service = SystemConfigCRUD(db)
        llm_provider_crud = LLMProviderConfigCRUD(db)
        llm_model_config_crud = LLMModelConfigCRUD(db)
        role_crud = RoleCRUD(db)

        # Load Redis cache configuration from configuration file
        redis_config = get_redis_config()
        
        # Check if the Redis connection is available
        await check_redis_connection()

        # Directly use the cache configuration defined in the code
        redis_cache_manager.set_cache_config(CACHE_CONFIG)

        # Load the system configuration first, as other functions may depend on the system configuration
        await redis_cache_manager.load_system_configs(system_config_service)

        # Load other cached data
        if CACHE_CONFIG["enable_character_prompt_cache"]:
            await redis_cache_manager.load_character_prompts(character_prompt_crud)
            
        if CACHE_CONFIG["enable_llm_provider_cache"]:
            await redis_cache_manager.load_llm_providers(llm_provider_crud)
            
        if CACHE_CONFIG["enable_model_config_cache"]:
            await redis_cache_manager.load_model_configs(llm_model_config_crud)

        if CACHE_CONFIG["enable_role_config_cache"]:
            await redis_cache_manager.load_role_configs(role_crud)
        
        # Initialize default model configuration
        default_model_id = await redis_cache_manager.system_config_cache.get_value("DEFAULT_LLM_MODEL")
        if default_model_id:
            # Create an LLM instance
            llm = await redis_cache_manager.get_ai_by_model_id(default_model_id)
            if llm:
                logger.info(f"默认模型 {default_model_id} 链接创建成功")
            else:
                logger.error(f"创建默认模型 {default_model_id} 链接失败")
        else:
            logger.warning("Default LLM model not configured")

        # Record the initialization completion information
        logger.info(f"Redis缓存初始化完成，配置状态: {CACHE_CONFIG}")
        logger.info(f"Redis连接信息: {redis_config.HOST}:{redis_config.PORT} (DB: {redis_config.DB})")
        
    except Exception as e:
        import traceback
        traceback.print_exc()  # Print detailed error information
        logger.error(f"Redis缓存初始化失败: {str(e)}")

    finally:
        db.close()

    yield  # This is where the app runs.

    # Operation on shutdown
    logger.info("Closing Redis connection...")
    
    # In a distributed environment, simply close local connections and LLM instances without clearing cached data
    try:
        # Close Redis connections and LLM instances
        redis_cache_manager.close_connections()
        logger.info("App closed, Redis connection closed")
    except Exception as e:
        logger.error(f"关闭Redis连接时出错: {e}")


async def check_redis_connection():
    """Check if the Redis connection is available

Raises:
RuntimeError: Throws an exception if the connection fails"""
    from redis.exceptions import RedisError

    try:
        # Get the Redis client side
        redis_client = await get_async_redis()
        
        # test connection
        await redis_client.ping()
        
        # Test read and write operations
        test_key = f"{get_redis_config().KEY_PREFIX}connection_test"
        await redis_client.set(test_key, "ok")
        test_value = await redis_client.get(test_key)
        await redis_client.delete(test_key)
        
        if test_value != b"ok":
            raise RuntimeError("Redis connection test failed: inconsistent read and write data")
            
        logger.info("Redis connection test was successful")
    except RedisError as e:
        logger.error(f"Redis连接测试失败: {e}")
        raise RuntimeError(f"无法连接到Redis服务器: {e}")


def get_cache_manager() -> RedisCacheManager:
    """Get the Redis Cache Manager instance

Returns:
RedisCacheManager: Redis Cache Manager"""
    return redis_cache_manager


# Functions to modify cache configuration
def set_cache_config(config: Dict[str, bool]):
    """Modify the cache configuration and apply it to the cache manager

Args:
Config: cache configuration dictionary"""
    global CACHE_CONFIG
    CACHE_CONFIG.update(config)
    redis_cache_manager.set_cache_config(CACHE_CONFIG)
    logger.info(f"已更新缓存配置: {CACHE_CONFIG}")

