"""Redis Cache Service Module
Provides basic functionality for Redis cache operations"""
import json
import pickle
from typing import Dict, List, Optional, TypeVar, Generic, Type, Callable
import asyncio
from datetime import datetime, date
from decimal import Decimal
import functools

from redis.asyncio import Redis
from redis.exceptions import RedisError
from pydantic import BaseModel

from knowledge_api.framework.redis.config import get_redis_config
from knowledge_api.framework.redis.connection import get_async_redis
from knowledge_api.utils.log_config import get_logger

logger = get_logger()
T = TypeVar('T')

# Custom JSON encoder to handle special types
class CustomJSONEncoder(json.JSONEncoder):
    """Handling special types of JSON encoders"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        try:
            if isinstance(obj, BaseModel):
                return obj.model_dump()
        except:
            pass
        return super().default(obj)

class RedisCache(Generic[T]):
    """Redis cache base class
Provide a general cache operation method

Generic parameters:
T: Cached data type"""

    def __init__(
        self,
        prefix: str,
        model_class: Optional[Type[T]] = None,
        default_ttl: Optional[int] = None
    ):
        """Initialize Redis cache

Args:
Prefix: cache key prefix
model_class: Model class for serialization/deserialization
default_ttl: Default expiration time (seconds), None means never expires"""
        self.prefix = prefix
        self.config = get_redis_config()
        self.model_class = model_class
        self.default_ttl = default_ttl or self.config.DEFAULT_TIMEOUT
        self.redis: Redis = None  # delayed initialization

    def _get_key(self, key: str) -> str:
        """Get the full cache key

Args:
Key: original key name

Returns:
Str: full prefixed key name"""
        return f"{self.prefix}:{key}"

    @functools.wraps(asyncio.iscoroutinefunction)
    async def get(self, key: str) -> Optional[T]:
        """Get cached value

Args:
Key: cache key

Returns:
Optional [T]: Cached value, returns None if none exists"""
        try:
            # Make sure there is a Redis connection.
            if not self.redis:
                self.redis = await get_async_redis()

            full_key = self._get_key(key)
            data = await self.redis.get(full_key)

            if data is None:
                return None

            return self._deserialize(data)
        except RedisError as e:
            logger.error(f"Redis获取缓存出错 (key={key}): {e}")
            return None

    @functools.wraps(asyncio.iscoroutinefunction)
    async def set(
        self,
        key: str,
        value: T,
        ttl: Optional[int] = None
    ) -> bool:
        """Set cache value

Args:
Key: cache key
Value: Cached value
TTL: expiration time (seconds), None means the default expiration time is used

Returns:
Bool: whether the operation was successful"""
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                # Make sure there is a Redis connection.
                if not self.redis:
                    self.redis = await get_async_redis()

                full_key = self._get_key(key)
                serialized = self._serialize(value)

                if ttl is not None:
                    await self.redis.setex(full_key, ttl, serialized)
                else:
                    await self.redis.set(full_key, serialized)

                return True
            except RedisError as e:
                retry_count += 1
                if "Too many connections" in str(e) and retry_count < max_retries:
                    # Too many connections, wait a while and try again.
                    wait_time = 0.1 * (2 ** retry_count)  # exponential backoff
                    logger.warning(f"The number of Redis connections is too large and waiting {wait_time:.2f}s after retrying ({retry_count}/{max_retries}): {key}")
                    await asyncio.sleep(wait_time)
                    # Release the current connection and obtain a new one
                    self.redis = None
                    continue
                else:
                    logger.error(f"there is an error in setting the redis cache (key={key}): {e}")
                    return False
            except Exception as e:
                logger.error(f"an error occurred during the redis caching process (key={key}): {e}")
                return False

    @functools.wraps(asyncio.iscoroutinefunction)
    async def delete(self, key: str) -> bool:
        """Delete cache

Args:
Key: cache key

Returns:
Bool: whether the operation was successful"""
        try:
            # Make sure there is a Redis connection.
            if not self.redis:
                self.redis = await get_async_redis()

            full_key = self._get_key(key)
            await self.redis.delete(full_key)
            return True
        except RedisError as e:
            logger.error(f"an error occurred in redis deleting the cache (key={key}): {e}")
            return False

    @functools.wraps(asyncio.iscoroutinefunction)
    async def exists(self, key: str) -> bool:
        """Check if the cache exists

Args:
Key: cache key

Returns:
Bool: Does the cache exist?"""
        try:
            # Make sure there is a Redis connection.
            if not self.redis:
                self.redis = await get_async_redis()

            full_key = self._get_key(key)
            return await self.redis.exists(full_key) > 0
        except RedisError as e:
            logger.error(f"Redis checks whether there is an error in the cache (key={key}): {e}")
            return False

    @functools.wraps(asyncio.iscoroutinefunction)
    async def clear_prefix(self, sub_prefix: str = "") -> int:
        """Clears all caches for the specified prefix

Args:
sub_prefix: subprefix, clear the cache under all prefixes when empty

Returns:
Int: number of keys deleted"""
        try:
            # Make sure there is a Redis connection.
            if not self.redis:
                self.redis = await get_async_redis()

            pattern = f"{self._get_key(sub_prefix)}*" if sub_prefix else f"{self.prefix}*"

            # Use the scan iterator to find all matching keys
            cursor = b"0"
            deleted_count = 0

            while cursor:
                cursor, keys = await self.redis.scan(cursor=cursor, match=pattern, count=100)
                if keys:
                    deleted_count += await self.redis.delete(*keys)

                if cursor == b"0":
                    break

            return deleted_count
        except RedisError as e:
            logger.error(f"redis cleared prefix cache error (prefix={self.prefix}, sub_prefix={sub_prefix}): {e}")
            return 0

    @functools.wraps(asyncio.iscoroutinefunction)
    async def get_all(self, sub_prefix: str = "") -> Dict[str, T]:
        """Get all cache items matching the prefix

Args:
sub_prefix: subprefix, get cache under all prefixes when empty

Returns:
Dict [str, T]: key-value dictionary"""
        try:
            # Make sure there is a Redis connection.
            if not self.redis:
                self.redis = await get_async_redis()

            pattern = f"{self._get_key(sub_prefix)}*" if sub_prefix else f"{self.prefix}*"

            # Use the scan iterator to find all matching keys
            cursor = b"0"
            result = {}

            while cursor:
                cursor, keys = await self.redis.scan(cursor=cursor, match=pattern, count=100)

                if keys:
                    # Get the values of all keys
                    values = await self.redis.mget(keys)

                    # processing result
                    for key, value in zip(keys, values):
                        if value is not None:
                            # Remove the prefix and return the original key
                            original_key = key.decode('utf-8').replace(f"{self.prefix}:", "", 1)
                            result[original_key] = self._deserialize(value)

                if cursor == b"0":
                    break

            return result
        except RedisError as e:
            logger.error(f"redis fetched all caches with error (prefix={self.prefix}, sub_prefix={sub_prefix}): {e}")
            return {}

    @functools.wraps(asyncio.iscoroutinefunction)
    async def set_many(self, items: Dict[str, T], ttl: Optional[int] = None) -> int:
        """Batch setup cache

Args:
Items: key-value dictionary
TTL: expiration time (seconds), None means the default expiration time is used

Returns:
Int: Number of keys successfully set"""
        if not items:
            return 0

        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                # Make sure there is a Redis connection.
                if not self.redis:
                    self.redis = await get_async_redis()

                pipeline = self.redis.pipeline()

                # Add all settings operations to the pipeline
                for key, value in items.items():
                    full_key = self._get_key(key)
                    serialized = self._serialize(value)

                    expire_time = ttl if ttl is not None else self.default_ttl
                    if expire_time is not None:
                        pipeline.setex(full_key, expire_time, serialized)
                    else:
                        pipeline.set(full_key, serialized)

                # execution pipeline
                results = await pipeline.execute()
                return sum(1 for result in results if result)
            except RedisError as e:
                retry_count += 1
                if "Too many connections" in str(e) and retry_count < max_retries:
                    # Too many connections, wait a while and try again.
                    wait_time = 0.1 * (2 ** retry_count)  # exponential backoff
                    logger.warning(f"Redis批量设置连接数过多，等待 {wait_time:.2f}s 后重试 ({retry_count}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    # Release the current connection and obtain a new one
                    self.redis = None
                    continue
                else:
                    logger.error(f"Redis批量设置缓存出错: {e}")
                    return 0
            except Exception as e:
                logger.error(f"Redis批量设置缓存过程中出错: {e}")
                return 0

    @functools.wraps(asyncio.iscoroutinefunction)
    async def delete_many(self, keys: List[str]) -> int:
        """batch delete cache

Args:
Keys: list of keys

Returns:
Int: number of keys deleted"""
        if not keys:
            return 0

        try:
            # Make sure there is a Redis connection.
            if not self.redis:
                self.redis = await get_async_redis()

            full_keys = [self._get_key(key) for key in keys]
            return await self.redis.delete(*full_keys)
        except RedisError as e:
            logger.error(f"Redis批量删除缓存出错: {e}")
            return 0

    def _serialize(self, value: T) -> bytes:
        """Serialized value

Args:
Value: The value to be serialized

Returns:
Bytes: the serialized byte string"""
        if value is None:
            return b""

        # If the value is a Pydantic model
        if isinstance(value, BaseModel):
            try:
                # Handling special types with custom encoders
                return json.dumps(value.model_dump(), cls=CustomJSONEncoder).encode('utf-8')
            except Exception as e:
                logger.warning(f"Pydantic模型序列化失败: {e}")
                # Try using pickle.
                return pickle.dumps(value)

        # Dictionary types are serialized directly to JSON, without first instantiating as a model
        # This avoids additional model validation overhead and potential exceptions
        if isinstance(value, dict):
            try:
                # Handling cases where the key in the dictionary is not a string
                normalized_dict = self._normalize_dict_keys(value)
                return json.dumps(normalized_dict, cls=CustomJSONEncoder).encode('utf-8')
            except Exception as e:
                logger.warning(f"字典JSON序列化失败: {e}")
                return pickle.dumps(value)

        # Other types attempt JSON serialization
        try:
            # Handling special types with custom encoders
            return json.dumps(value, cls=CustomJSONEncoder).encode('utf-8')
        except (TypeError, ValueError) as e:
            logger.warning(f"JSON序列化失败，使用pickle: {e}")
            # Using pickle as an alternative serialization method
            return pickle.dumps(value)

    def _normalize_dict_keys(self, d: dict) -> dict:
        """Recursively converts all keys in the dictionary to strings

Args:
D: input dictionary

Returns:
Dict: Dictionary where all keys are strings"""
        if not isinstance(d, dict):
            return d

        result = {}
        for k, v in d.items():
            # Convert current key to string
            k_str = str(k)

            # Recursive processing of nested values
            if isinstance(v, dict):
                result[k_str] = self._normalize_dict_keys(v)
            elif isinstance(v, list):
                result[k_str] = [
                    self._normalize_dict_keys(item) if isinstance(item, dict) else item
                    for item in v
                ]
            else:
                result[k_str] = v

        return result

    def _deserialize(self, data: bytes) -> T:
        """deserialize value

Args:
Data: The byte string to be deserialized

Returns:
T: The deserialized value"""
        if not data:
            return None

        # Try JSON deserialization first
        try:
            value = json.loads(data)

            # If there is a model class, try converting it to a model instance
            if self.model_class:
                if issubclass(self.model_class, BaseModel):
                    # Checks if value is a list and contains dictionary elements
                    if isinstance(value, list) and value and isinstance(value[0], dict):
                        # This is a list of models, serializing each dictionary element as a model instance
                        result = []
                        for item in value:
                            if isinstance(item, dict):
                                try:
                                    result.append(self.model_class(**item))
                                except Exception as e:
                                    logger.warning(f"反序列化列表中的模型实例失败: {e}")
                                    result.append(item)
                            else:
                                result.append(item)
                        return result
                    elif isinstance(value, dict) and self._is_model_collection(value):
                        # This is a collection of models in dictionary form, keeping the JSON format unserialized
                        return value
                    elif isinstance(value, dict):
                        # single model instance
                        return self.model_class(**value)
                    else:
                        # Non-dictionary/list type, return directly
                        return value
                else:
                    # Non-Pydantic models, try to instantiate
                    return self.model_class(value)

            return value
        except (json.JSONDecodeError, UnicodeDecodeError, TypeError, ValueError) as e:
            logger.debug(f"JSON反序列化失败，尝试pickle: {e}")
            # Try deserializing with pickle
            try:
                return pickle.loads(data)
            except Exception as e:
                logger.error(f"反序列化失败: {e}")
                return None

    def _is_model_collection(self, value: dict) -> bool:
        """Determine whether the dictionary is a collection of models

Args:
Value: The dictionary to check

Returns:
Bool: Whether it is a collection of models"""
        if not isinstance(value, dict) or len(value) == 0:
            return False

        # Check several values to see if they are all dictionaries and contain model fields
        sample_count = min(3, len(value))
        dict_values = 0

        for k, v in list(value.items())[:sample_count]:
            if isinstance(v, dict):
                dict_values += 1
                # Check if common model fields are included
                if any(field in v for field in ['id', 'created_at', 'updated_at']):
                    continue
                else:
                    return False
            else:
                return False

        # If most of the values are dictionaries, consider this a collection of models
        return dict_values >= sample_count * 0.8


def redis_cache(
    prefix: str,
    key_builder: Callable[..., str],
    ttl: Optional[int] = None,
    model_class: Optional[Type[T]] = None
):
    """Redis cache decorator
Add Redis caching functionality to a function or method

Args:
Prefix: cache key prefix
key_builder: Functions to build cache keys
TTL: cache expiration time (seconds)
model_class: Model class for serialization/deserialization

Returns:
Decorated function"""
    def decorator(func):
        # Create cache instance
        cache = RedisCache(prefix=prefix, model_class=model_class, default_ttl=ttl)
        
        # Check if the function is a coroutine function
        is_async = asyncio.iscoroutinefunction(func)
        
        if is_async:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                # build cache key
                cache_key = key_builder(*args, **kwargs)
                
                # Try to get from cache
                cached_value = await cache.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # Execute the original function
                result = await func(*args, **kwargs)
                
                # cache
                if result is not None:
                    await cache.set(cache_key, result, ttl)
                
                return result
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                # build cache key
                cache_key = key_builder(*args, **kwargs)
                
                # Create a new event loop to perform asynchronous operations
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If the current loop is running, create a new loop
                        new_loop = asyncio.new_event_loop()
                        cached_value = new_loop.run_until_complete(cache.get(cache_key))
                        new_loop.close()
                    else:
                        cached_value = loop.run_until_complete(cache.get(cache_key))
                except RuntimeError:
                    # Create a new event loop
                    new_loop = asyncio.new_event_loop()
                    cached_value = new_loop.run_until_complete(cache.get(cache_key))
                    new_loop.close()
                
                if cached_value is not None:
                    return cached_value
                
                # Execute the original function
                result = func(*args, **kwargs)
                
                # cache
                if result is not None:
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # If the current loop is running, create a new loop
                            new_loop = asyncio.new_event_loop()
                            new_loop.run_until_complete(cache.set(cache_key, result, ttl))
                            new_loop.close()
                        else:
                            loop.run_until_complete(cache.set(cache_key, result, ttl))
                    except RuntimeError:
                        # Create a new event loop
                        new_loop = asyncio.new_event_loop()
                        new_loop.run_until_complete(cache.set(cache_key, result, ttl))
                        new_loop.close()
                
                return result
            return sync_wrapper
            
    return decorator


def clear_cache_decorator(prefix: str, key_pattern: Optional[str] = None):
    """Clear cache decorator
Clears the cache of the specified prefix after function execution

Args:
Prefix: cache key prefix
key_pattern: key mode, None means clear cache under all prefixes

Returns:
Decorated function"""
    def decorator(func):
        # Create cache instance
        cache = RedisCache(prefix=prefix)
        
        # Check if the function is a coroutine function
        is_async = asyncio.iscoroutinefunction(func)
        
        if is_async:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                # Execute the original function
                result = await func(*args, **kwargs)
                
                # Clear cache
                await cache.clear_prefix(key_pattern or "")
                
                return result
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                # Execute the original function
                result = func(*args, **kwargs)
                
                # Create a new event loop to perform asynchronous operations
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If the current loop is running, create a new loop
                        new_loop = asyncio.new_event_loop()
                        new_loop.run_until_complete(cache.clear_prefix(key_pattern or ""))
                        new_loop.close()
                    else:
                        loop.run_until_complete(cache.clear_prefix(key_pattern or ""))
                except RuntimeError:
                    # Create a new event loop
                    new_loop = asyncio.new_event_loop()
                    new_loop.run_until_complete(cache.clear_prefix(key_pattern or ""))
                    new_loop.close()
                
                return result
            return sync_wrapper
            
    return decorator 