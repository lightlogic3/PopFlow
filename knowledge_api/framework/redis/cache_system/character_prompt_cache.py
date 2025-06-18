"""Role hint caching service
Caching operations for handling role hints"""
import asyncio
from typing import List, Optional

from knowledge_api.framework.redis.cache import RedisCache
from knowledge_api.framework.redis.config import get_redis_config
from knowledge_api.framework.redis.connection import get_async_redis
from knowledge_api.mapper.character_prompt_config.base import CharacterPromptConfig
from knowledge_api.mapper.character_prompt_config.crud import CharacterPromptConfigCRUD
from knowledge_api.framework.database.database import get_db_session
from knowledge_api.utils.log_config import get_logger

logger = get_logger()

class CharacterPromptCache:
    """Role hint caching service
Manage cache operations for role prompt configuration"""
    _instance = None

    def __new__(cls):
        """singleton pattern"""
        if cls._instance is None:
            cls._instance = super(CharacterPromptCache, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize cache"""
        self.redis_config = get_redis_config()
        self.enabled = True

        # Initialize Redis cache
        self.cache = RedisCache(
            prefix=f"{self.redis_config.KEY_PREFIX}{self.redis_config.CHARACTER_PROMPT_PREFIX}",
            model_class=CharacterPromptConfig
        )

    def set_enabled(self, enabled: bool):
        """Set cache switch"""
        self.enabled = enabled

    async def load_all(self, crud: Optional[CharacterPromptConfigCRUD] = None):
        """Load all role prompt word configurations to cache

Args:
Crud: Optional CharacterPromptConfigCRUD instance, created automatically if not provided"""
        if not self.enabled:
            return


        try:
            with get_db_session() as session:
                crud = CharacterPromptConfigCRUD(session)

                # Get all enabled configurations
                configs = await crud.get_all_cache()

                # Create a safe deep copy to avoid object invalidation after the session ends
                configs = [CharacterPromptConfig.model_validate(config.model_dump()) for config in configs]

                # Organize data by role ID and level
                character_prompts = {}

                # Record all levels of each role to create an ordered collection
                role_levels = {}

                for config in configs:
                    role_id = config.role_id
                    level = config.level

                    # Initialize the role's data structure
                    if role_id not in character_prompts:
                        character_prompts[role_id] = {}
                        role_levels[role_id] = []

                    # To avoid problems with floating-point numbers as keys, use the string key
                    level_key = f"level_{level}"

                    # Store configurations and record levels
                    character_prompts[role_id][level_key] = config
                    role_levels[role_id].append(level)

                # Empty old cache
                await self.cache.clear_prefix()

                # Get a Redis client side
                redis = await get_async_redis()

                # Batch by role to avoid creating too many connections at once
                for role_id, levels_dict in character_prompts.items():
                    # Create a task list
                    tasks = []

                    # 1. Store all configurations for this role
                    tasks.append(self.cache.set(f"role:{role_id}", levels_dict))

                    # 2. Store each level configuration separately (up to 10 levels per role)
                    for level_key, config in levels_dict.items():
                        level = float(level_key.replace("level_", ""))
                        tasks.append(self.cache.set(f"role:{role_id}:level:{level}", config))

                    # 3. Create an ordered collection
                    sorted_set_key = f"{self.cache.prefix}:role:{role_id}:levels"

                    # Delete the old ordered collection first
                    await redis.delete(sorted_set_key)

                    # Create a new ordered collection
                    if role_levels[role_id]:
                        mapping = {str(level): float(level) for level in role_levels[role_id]}
                        # Instead of using tasks, execute them directly to avoid keeping too many connections
                        await redis.zadd(sorted_set_key, mapping=mapping)

                    # Each role performs a cache operation
                    try:
                        await asyncio.gather(*tasks)
                    except Exception as e:
                        logger.error(f"缓存角色 {role_id} 提示词出错: {e}")

                    # Sleep briefly to avoid too many requests
                    await asyncio.sleep(0.05)

                logger.info(f"已加载 {len(character_prompts)} 个角色的提示词配置到Redis缓存")

        except Exception as e:
            logger.error(f"加载角色提示词缓存出错: {e}")
            import traceback
            traceback.print_exc()

    async def get_nearest_prompt(self, role_id: str, current_level: float=9999.0, crud: Optional[CharacterPromptConfigCRUD] = None) -> Optional[CharacterPromptConfig]:
        """Get the most recent prompt word configuration

Use Redis' ordered set (ZSET) to efficiently find the maximum level less than or equal to a given level
If you can't find it in Redis, it will try to load it from the database and cache it automatically

Args:
role_id: Role ID
current_level: Current level
Crud: Optional CharacterPromptConfigCRUD instance, created automatically if not provided

Returns:
Optional [CharacterPromptConfig]: Recent prompt word configuration, returns None when none exists"""
        if not self.enabled:
            return None

        try:
            # Get Redis connections directly for ordered collection operations
            redis = await get_async_redis()

            # Keys for building ordered collections
            sorted_set_key = f"{self.cache.prefix}:role:{role_id}:levels"

            # Use the ZREVRANGEBYSCORE command to find the maximum level less than or equal to the current level
            levels = await redis.zrevrangebyscore(
                sorted_set_key,        # key
                current_level,         # Maximum score (inclusive)
                float('-inf'),         # minimum fraction
                start=0,               # Offset
                num=1                  # Limit returns one result (maximum)
            )

            # If a matching level is found
            if levels:
                # Get the level found. Note: The bytecode returned needs to be decoded and converted to a floating-point number.
                target_level = float(levels[0].decode('utf-8')) if isinstance(levels[0], bytes) else float(levels[0])

                # Get the configuration of this level directly
                config = await self.cache.get(f"role:{role_id}:level:{target_level}")
                if config:
                    return config

            # If the cache is not found or the level found does not have a corresponding configuration, try to get all configurations
            all_levels = await self.cache.get(f"role:{role_id}")
            if all_levels:
                # Filter out configurations less than or equal to the current level
                valid_levels = {}
                for level_key, config in all_levels.items():
                    # Extract rank values
                    level = float(level_key.replace("level_", ""))
                    if level <= current_level:
                        valid_levels[level] = config

                if valid_levels:
                    # Return to the highest level of configuration
                    max_level = max(valid_levels.keys())
                    return valid_levels[max_level]

            # If nothing is found in Redis, load it from the database
            try:
                # Create temporary database sessions and CRUD instances
                with get_db_session() as session:
                    crud_tem = CharacterPromptConfigCRUD(session)

                    # Load all configurations for this role from the database
                    db_configs = await crud_tem.get_by_role_id(role_id=role_id)

                    if db_configs:
                        # Create deep copy
                        configs = [CharacterPromptConfig.model_validate(config.model_dump()) for config in db_configs]

                        # Cache all configurations for this role
                        await self._cache_role_prompts(role_id, configs)

                        # Find a matching configuration
                        return await self._find_nearest_config(configs, current_level)

            except Exception as e:
                logger.error(f"从数据库加载角色提示词出错 (role_id={role_id}): {e}")

            # All attempts have failed
            return None

        except Exception as e:
            logger.error(f"获取最近提示词出错 (role_id={role_id}, level={current_level}): {e}")
            try:
                # If no crud instance is passed in, create a temporary one
                with get_db_session() as session:
                    crud = CharacterPromptConfigCRUD(session)

                    # Load all configurations for this role from the database
                    db_configs = await crud.get_by_role_id(role_id=role_id)
                    if db_configs:
                        # Create deep copy
                        configs = [CharacterPromptConfig.model_validate(config.model_dump()) for config in db_configs]
                        # Try to find the latest configuration
                        return await self._find_nearest_config(configs, current_level)
            except Exception as e2:
                logger.error(f"从数据库获取提示词失败 (role_id={role_id}): {e2}")

            return None

    async def _find_nearest_config(self, configs: List[CharacterPromptConfig], current_level: float) -> Optional[CharacterPromptConfig]:
        """Find the configuration closest to, but not higher than, the current level from the configuration list

Args:
Config: configuration list
current_level: Current level

Returns:
Optional [CharacterPromptConfig]: Recent configuration, returns None if none exists"""
        valid_configs = [config for config in configs if config.level <= current_level]
        if not valid_configs:
            return None

        # Sort by rank in descending order, returning the first one
        return sorted(valid_configs, key=lambda x: x.level, reverse=True)[0]

    async def _cache_role_prompts(self, role_id: str, configs: List[CharacterPromptConfig]) -> None:
        """Cache all prompt word configurations for a role

Args:
role_id: Role ID
Config: configuration list"""
        if not configs:
            logger.warning(f"尝试缓存空配置列表给角色 {role_id}")
            return

        try:
            # Organize data by rank
            levels_dict = {}
            levels = []

            for config in configs:
                level = config.level
                levels.append(level)

                # To avoid problems with floating-point numbers as keys, use the string key
                level_key = f"level_{level}"
                levels_dict[level_key] = config

            # Create a task list
            tasks = []

            # 1. Store all configurations for this role
            tasks.append(self.cache.set(f"role:{role_id}", levels_dict))

            # 2. Store each level configuration separately
            for level_key, config in levels_dict.items():
                level = float(level_key.replace("level_", ""))
                tasks.append(self.cache.set(f"role:{role_id}:level:{level}", config))

            # 3. Create an ordered collection
            redis = await get_async_redis()
            sorted_set_key = f"{self.cache.prefix}:role:{role_id}:levels"

            # Delete the old ordered collection first
            await redis.delete(sorted_set_key)

            # Create a new ordered collection
            if levels:
                # Execute the ZADD command directly here without adding to the task list
                mapping = {str(level): float(level) for level in levels}
                await redis.zadd(sorted_set_key, mapping=mapping)

            # Perform storage operations
            await asyncio.gather(*tasks)
            logger.info(f"已为角色 {role_id} 缓存 {len(configs)} 个等级的提示词配置")

        except Exception as e:
            logger.error(f"缓存角色提示词出错 (role_id={role_id}): {e}")
            # Add retry logic
            if "Too many connections" in str(e):
                logger.warning(f"连接数过多，将在1秒后重试缓存角色 {role_id}")
                await asyncio.sleep(1)
                try:
                    # Simplified retry, caching only role dictionaries and ordered collections
                    await self.cache.set(f"role:{role_id}", levels_dict)

                    # Retrieve Redis connection
                    redis = await get_async_redis()
                    sorted_set_key = f"{self.cache.prefix}:role:{role_id}:levels"

                    if levels:
                        mapping = {str(level): float(level) for level in levels}
                        await redis.zadd(sorted_set_key, mapping=mapping)

                    logger.info(f"重试成功：已为角色 {role_id} 缓存提示词配置")
                except Exception as e2:
                    logger.error(f"重试缓存角色提示词仍然失败 (role_id={role_id}): {e2}")

    async def update(self, config: CharacterPromptConfig, crud: Optional[CharacterPromptConfigCRUD] = None) -> bool:
        """Update character prompt word cache

Note: This method is not responsible for updating the database, only the Redis cache
Ensure cached content is consistent with get_nearest_prompt fetch mechanism

Args:
Config: Configuration to update
Crud: Optional CharacterPromptConfigCRUD instance to get additional configuration

Returns:
Bool: whether the operation was successful"""
        if not self.enabled:
            return False
        try:
            role_id = config.role_id
            level = config.level
            with get_db_session() as session:
                crud = CharacterPromptConfigCRUD(session)

                # Update cache using _cache_role_prompts method uniformly
                # 1. Get all existing configurations for the role first
                db_configs = await crud.get_by_role_id(role_id=role_id)

                # Create deep copy
                configs = [CharacterPromptConfig.model_validate(c.model_dump()) for c in db_configs] if db_configs else []

                # 2. If there is no configuration, only the currently provided configuration is cached
                if not configs:
                    configs = [config]
                else:
                    # 3. Replace or add the current configuration
                    updated = False
                    for i, cfg in enumerate(configs):
                        if cfg.level == level:
                            configs[i] = config
                            updated = True
                            break

                    # 4. If no configuration of the same level is found, add it to the configuration list
                    if not updated:
                        configs.append(config)

                # 5. Use _cache_role_prompts method to update cache uniformly
                await self._cache_role_prompts(role_id, configs)
            logger.info(f"已更新角色 {role_id} 的等级 {level} 提示词缓存")
            return True

        except Exception as e:
            logger.error(f"更新角色提示词缓存出错 (role_id={config.role_id}, level={config.level}): {e}")
            return False

    async def delete(self, role_id: str, level: float, crud: Optional[CharacterPromptConfigCRUD] = None) -> bool:
        """Delete single role prompt word configuration

Args:
role_id: Role ID
Level: Level
Crud: Optional CharacterPromptConfigCRUD instance, created automatically if not provided

Returns:
Bool: whether the operation was successful"""
        if not self.enabled:
            return False

        try:
            # Verify that the configuration has been deleted from the database
            if crud:
                db_config = await crud.get_by_role_and_level(role_id=role_id, level=level)
                if db_config:
                    logger.warning(f"要删除的配置在数据库中仍然存在 (role_id={role_id}, level={level})")

            # Get all configurations for the role
            all_levels = await self.cache.get(f"role:{role_id}")

            if all_levels and isinstance(all_levels, dict):
                # Delete a specific level of configuration
                level_key = f"level_{level}"
                if level_key in all_levels:
                    del all_levels[level_key]

                    # If there are other configurations, update the total cache
                    if all_levels:
                        await self.cache.set(f"role:{role_id}", all_levels)
                    else:
                        # If nothing else is configured, delete the entire role cache
                        await self.cache.delete(f"role:{role_id}")
            else:
                logger.warning(f"角色 {role_id} 的缓存数据类型错误或不存在，直接删除单独的等级缓存")

            # Delete separate level cache
            await self.cache.delete(f"role:{role_id}:level:{level}")

            # Delete from an ordered collection
            redis = await get_async_redis()
            sorted_set_key = f"{self.cache.prefix}:role:{role_id}:levels"
            await redis.zrem(sorted_set_key, str(level))

            # If the ordered set is empty, delete it
            if await redis.zcard(sorted_set_key) == 0:
                await redis.delete(sorted_set_key)

            logger.info(f"已删除角色 {role_id} 的等级 {level} 提示词配置")
            return True

        except Exception as e:
            logger.error(f"删除角色提示词缓存出错 (role_id={role_id}, level={level}): {e}")
            return False 