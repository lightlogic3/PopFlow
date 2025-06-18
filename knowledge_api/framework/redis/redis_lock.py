"""Redis distributed lock implementation
Provides Redis-based distributed lock functionality for concurrency control in multi-process, multi-threaded environments"""
import time
import uuid
import asyncio
from redis.asyncio import Redis
from redis.exceptions import RedisError

from knowledge_api.framework.redis.connection import get_async_redis
from knowledge_api.utils.log_config import get_logger

logger = get_logger()

class RedisLock:
    """Redis distributed lock

Redis-based distributed lock implementation can be used in multi-process, multi-threaded, and distributed environments

Example:
"Python
#Using a Context Manager
Async with RedisLock ("user: 123: lock") as lock_acquired:
If lock_acquired:
#Acquired lock successfully
Pass
Else:
Failed to acquire lock
Pass

#Or manually acquire and release
Lock = RedisLock ("user: 123: lock")
If await lock.acquire ():
Try:
#Acquired lock successfully
Pass
Finally:
Awaiting lock.release ()
"..."""
    
    def __init__(
        self, 
        lock_name: str, 
        expire: int = 30, 
        retry_interval: float = 0.1,
        max_retries: int = 3,
        prefix: str = "redis_lock:"
    ):
        """Initialize Redis lock

Args:
lock_name: Lock Name
Expire: lock expiration time (seconds) to prevent deadlock
retry_interval: Retry interval (seconds)
max_retries: Maximum number of retries
Prefix: key prefix"""
        self.lock_name = f"{prefix}{lock_name}"
        self.expire = expire
        self.retry_interval = retry_interval
        self.max_retries = max_retries
        self._redis = None  # delayed initialization
        self._lock_value = None  # The unique identifier of the storage lock
        
    async def __aenter__(self):
        """asynchronous context manager entry

Returns:
Bool: whether to acquire the lock"""
        return await self.acquire()
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Asynchronous Context Manager Exit
Release lock"""
        if self._lock_value:
            await self.release()
        
    async def acquire(self) -> bool:
        """Acquire lock

Returns:
Bool: whether to get successful"""
        # Make sure Redis is connected
        if not self._redis:
            self._redis = await get_async_redis()
            
        # Generate a unique lock value for safe release
        self._lock_value = f"{uuid.uuid4().hex}:{time.time()}"
        
        retry_count = 0
        while retry_count < self.max_retries:
            # Attempt to set the lock, NX means only set if the key does not exist
            # EX sets the expiration time to prevent deadlock
            acquired = await self._redis.set(
                self.lock_name, 
                self._lock_value,
                nx=True,
                ex=self.expire
            )
            
            if acquired:
                logger.debug(f"获取锁成功: {self.lock_name}")
                return True
                
            # Failed to get, waiting to try again
            retry_count += 1
            if retry_count < self.max_retries:
                await asyncio.sleep(self.retry_interval)
        
        # Lock not acquired after multiple retries
        logger.warning(f"获取锁失败，已达到最大重试次数: {self.lock_name}")
        self._lock_value = None
        return False
        
    async def release(self) -> bool:
        """Release lock

Returns:
Bool: whether the release was successful"""
        # If the lock has not been acquired, return directly
        if not self._lock_value:
            logger.debug(f"没有锁需要释放: {self.lock_name}")
            return True
            
        # If there is no Redis connection, try to get it.
        if not self._redis:
            try:
                self._redis = await get_async_redis()
            except Exception as e:
                logger.error(f"获取Redis连接失败，无法释放锁: {e}")
                self._lock_value = None  # Clear lock values to prevent repeated attempts
                return False
            
        try:
            # Using a Lua script, ensure that only your own locks are removed
            # Prevent deleting locks created by other client sides
            script = """
            if redis.call('get', KEYS[1]) == ARGV[1] then
                return redis.call('del', KEYS[1])
            else
                return 0
            end
            """
            
            # Compatible with different versions of Redis libraries
            result = 0
            try:
                # Try method 1: pass the position parameter directly after the script
                result = await self._redis.eval(script, 1, self.lock_name, self._lock_value)
            except TypeError:
                try:
                    # Try method 2: directly pass in the list as a positional parameter
                    result = await self._redis.eval(script, [self.lock_name], [self._lock_value])
                except TypeError:
                    try:
                        # Method 3: Use named parameters
                        result = await self._redis.eval(
                            script,
                            keys=[self.lock_name],
                            args=[self._lock_value]
                        )
                    except Exception as eval_error:
                        # Try the last option: delete the key directly (unsafe but as a last resort).
                        logger.warning(f"使用Lua脚本释放锁失败，尝试直接删除键: {eval_error}")
                        try:
                            # First check if the values match
                            current_value = await self._redis.get(self.lock_name)
                            if current_value == self._lock_value:
                                result = await self._redis.delete(self.lock_name)
                            else:
                                logger.warning(f"锁值不匹配，不进行删除: 期望={self._lock_value}, 实际={current_value}")
                        except Exception as direct_error:
                            logger.error(f"直接删除键失败: {direct_error}")
            
            if result:
                logger.debug(f"释放锁成功: {self.lock_name}")
            else:
                logger.warning(f"释放锁失败，锁不存在或已被其他客户端修改: {self.lock_name}")
                
            self._lock_value = None
            return bool(result)
        except Exception as e:
            logger.error(f"释放锁出错: {e}")
            self._lock_value = None  # Clear lock values to prevent repeated attempts
            return False
            
    async def extend(self, additional_time: int) -> bool:
        """Extend the expiration time of the lock

Args:
additional_time: Extra expiration time (seconds)

Returns:
Bool: Whether the extension is successful"""
        if not self._lock_value or not self._redis:
            return False
            
        try:
            # Use Lua scripts to ensure that only your own locks are extended
            script = """
            if redis.call('get', KEYS[1]) == ARGV[1] then
                return redis.call('expire', KEYS[1], ARGV[2])
            else
                return 0
            end
            """
            
            # Compatible with different versions of Redis libraries
            try:
                # Try method 1: pass the position parameter directly after the script
                result = await self._redis.eval(script, 1, self.lock_name, self._lock_value, additional_time)
            except TypeError:
                try:
                    # Try method 2: directly pass in the list as a positional parameter
                    result = await self._redis.eval(script, [self.lock_name], [self._lock_value, additional_time])
                except TypeError:
                    # Method 3: Use named parameters
                    result = await self._redis.eval(
                        script,
                        keys=[self.lock_name],
                        args=[self._lock_value, additional_time]
                    )
            
            if result:
                logger.debug(f"延长锁成功: {self.lock_name}")
            else:
                logger.warning(f"延长锁失败，锁不存在或已被其他客户端修改: {self.lock_name}")
                
            return bool(result)
        except Exception as e:
            logger.error(f"延长锁出错: {e}")
            return False 