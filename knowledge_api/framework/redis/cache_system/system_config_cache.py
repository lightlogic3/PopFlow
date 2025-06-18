"""System Configuration Cache Service
Handling cache operations for system configuration"""
import asyncio
from typing import Any, Optional

from knowledge_api.framework.redis.cache import RedisCache
from knowledge_api.framework.redis.config import get_redis_config
from knowledge_api.mapper.system_config.crud import SystemConfigCRUD
from knowledge_api.framework.database.database import get_db_session
from knowledge_api.utils.log_config import get_logger

logger = get_logger()

class SystemConfigCache:
    """System Configuration Cache Service
Manage cache operations for system configuration"""
    _instance = None

    def __new__(cls):
        """singleton pattern"""
        if cls._instance is None:
            cls._instance = super(SystemConfigCache, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize cache"""
        self.redis_config = get_redis_config()
        self.enabled = True
        
        # Initialize Redis cache
        self.cache = RedisCache(
            prefix=f"{self.redis_config.KEY_PREFIX}{self.redis_config.SYSTEM_CONFIG_PREFIX}"
        )

    def set_enabled(self, enabled: bool):
        """Set cache switch"""
        self.enabled = enabled
    
    async def load_all(self, crud: Optional[SystemConfigCRUD] = None):
        """Load all system configurations to cache

Args:
Crud: Optional SystemConfigCRUD instance, created automatically if not provided"""
        if not self.enabled:
            return
        
        temp_session = None
        try:
            # Get all system configurations
            configs = await crud.get_all_as_dict()
            
            # Empty old cache
            await self.cache.clear_prefix()
            
            # Batch Setup Configuration
            await self.cache.set("all_configs", configs)
            
            # Set each configuration individually for easy individual updates
            tasks = []
            for key, value in configs.items():
                tasks.append(self.cache.set(key, value))
                
            await asyncio.gather(*tasks)
            logger.info(f"已加载 {len(configs)} 个系统配置到Redis缓存")
            
        except Exception as e:
            logger.error(f"加载系统配置缓存出错: {e}")
        finally:
            # Close a temporary session
            if temp_session:
                temp_session.close()

    async def get_value(self, key: str, default_value: Any = None) -> Any:
        """Get the system configuration value and load it from the database if not in the cache

Args:
Key: configuration key
default_value: Default

Returns:
Any: Configuration value, returns the default value if it does not exist"""
        if not self.enabled:
            return default_value
            
        try:
            # Get it directly from Redis
            value = await self.cache.get(key)
            if value is not None:
                return value
                
            # If not, try to get it from all_configs
            all_configs = await self.cache.get("all_configs")
            if all_configs and key in all_configs:
                return all_configs.get(key)
                
            # If not in the cache, load from the database
            with get_db_session() as session:
                crud = SystemConfigCRUD(session)
                config = await crud.get_by_key(config_key=key)
                
                if config:
                    # Cache to Redis
                    value = config.config_value
                    await self.cache.set(key, value)
                    
                    # Update all_configs cache
                    if all_configs:
                        all_configs[key] = value
                        await self.cache.set("all_configs", all_configs)
                        
                    logger.info(f"已从数据库加载并缓存系统配置: {key}")
                    return value
                    
            return default_value
                
        except Exception as e:
            logger.error(f"获取系统配置出错 (key={key}): {e}")
            return default_value

    def get_value_sync(self, key: str, default_value: Any = None) -> Any:
        """Obtain system configuration values synchronously (for internal use only)

Attention: This method should only be used when asynchronous methods are not available

Args:
Key: configuration key
default_value: Default

Returns:
Any: Configuration value, returns the default value if it does not exist"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Asynchronous methods cannot be called synchronously in a running loop
                # Return default value 
                logger.warning(f"在运行中的事件循环中同步获取配置 {key}，返回默认值")
                return default_value
            else:
                # If the loop is not running, it can be called synchronously
                return loop.run_until_complete(self.get_value(key, default_value))
        except RuntimeError:
            # Create a new one when there is no event loop
            new_loop = asyncio.new_event_loop()
            try:
                return new_loop.run_until_complete(self.get_value(key, default_value))
            finally:
                new_loop.close()
        except Exception as e:
            logger.error(f"同步获取系统配置出错 (key={key}): {e}")
            return default_value

    async def update(self, key: str, value: Any, crud: Optional[SystemConfigCRUD] = None) -> bool:
        """Update system configuration values

Args:
Key: configuration key
Value: configuration value
Crud: Optional SystemConfigCRUD instance, created automatically if not provided

Returns:
Bool: whether the operation was successful"""
        if not self.enabled:
            return False
            
        temp_session = None
        try:
            # If no crud instance is passed in, create a temporary one
            if crud is None:
                temp_session = next(get_db_session())
                crud = SystemConfigCRUD(temp_session)
            
            # First verify that the configuration exists in the database
            db_config = await crud.get_by_key(config_key=key)
            if not db_config:
                logger.warning(f"要更新的系统配置在数据库中不存在: {key}")
                return False
            
            # Update individual configurations
            await self.cache.set(key, value)
            
            # Update all_configs cache
            all_configs = await self.cache.get("all_configs")
            if all_configs:
                all_configs[key] = value
                await self.cache.set("all_configs", all_configs)
                
            logger.info(f"已更新系统配置: {key}")
            return True
            
        except Exception as e:
            logger.error(f"更新系统配置缓存出错 (key={key}): {e}")
            return False
        finally:
            # Close a temporary session
            if temp_session:
                temp_session.close()

    async def delete(self, key: str, crud: Optional[SystemConfigCRUD] = None) -> bool:
        """Delete system configuration

Args:
Key: configuration key
Crud: Optional SystemConfigCRUD instance, created automatically if not provided

Returns:
Bool: whether the operation was successful"""
        if not self.enabled:
            return False
            
        try:
            # Verify that the configuration has been deleted from the database
            if crud:
                db_config = await crud.get_by_key(config_key=key)
                if db_config:
                    logger.warning(f"要删除的系统配置在数据库中仍然存在: {key}")
            
            # Delete a separate configuration
            await self.cache.delete(key)
            
            # Update all_configs cache
            all_configs = await self.cache.get("all_configs")
            if all_configs and key in all_configs:
                del all_configs[key]
                await self.cache.set("all_configs", all_configs)
                
            logger.info(f"已删除系统配置: {key}")
            return True
            
        except Exception as e:
            logger.error(f"删除系统配置缓存出错 (key={key}): {e}")
            return False 