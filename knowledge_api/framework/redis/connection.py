"""Redis Connection Management Module
Tool classes that provide Redis connection management"""
import asyncio
from typing import Dict, Optional
import time

from redis.asyncio import Redis, ConnectionPool
from redis.exceptions import RedisError
from contextlib import asynccontextmanager

from knowledge_api.framework.redis.config import get_redis_config
from knowledge_api.utils.log_config import get_logger

logger = get_logger()

class RedisConnectionManager:
    """Redis Connection Manager"""
    
    def __init__(self):
        """Initialize the connection manager"""
        self.config = None  # Do not get configuration at initialization
        self.pool: Optional[ConnectionPool] = None
        self.clients: Dict[int, Redis] = {}
        self.last_health_check = 0
        self.health_check_interval = 30  # Check connection health every 30 seconds
        
    def get_connection_pool(self) -> ConnectionPool:
        """Get connection pool

Returns:
ConnectionPool: Redis connection pool"""
        # Reload the configuration each time the connection pool is acquired to ensure the latest environment variables are used
        self.config = get_redis_config()
        
        # If the configuration changes, you need to recreate the connection pool
        if self.pool is not None:
            pool_info = f"{self.config.HOST}:{self.config.PORT}/db{self.config.DB}"
            if hasattr(self, '_pool_info') and self._pool_info != pool_info:
                logger.info(f"Redis配置已变更，重新创建连接池: {pool_info}")
                self.close_all_connections()  # Close all connections
                self.pool = None  # Clear the old connection pool
            
        if self.pool is None:
            # Get connection parameters
            connection_params = self.config.get_connection_params()
            
            # Adjust connection pool parameters
            pool_kwargs = {
                "host": connection_params.pop("host"),
                "port": connection_params.pop("port"),
                "db": connection_params.pop("db", 0),
                "max_connections": connection_params.pop("max_connections", 10),  # Use the value in the configuration
                "decode_responses": False,  # The byte string is reserved and decoded by the cache layer
                "socket_timeout": connection_params.pop("socket_timeout", 5),  # Use the value in the configuration
                "socket_connect_timeout": 5,  # Set connection establishment timeout
                "retry_on_timeout": True,  # retry after timeout
                "health_check_interval": 15  # Check connection health more frequently
            }
            
            # Add authentication parameters
            if "username" in connection_params:
                pool_kwargs["username"] = connection_params.pop("username")
                
            if "password" in connection_params:
                pool_kwargs["password"] = connection_params.pop("password")
            
            # Create a connection pool
            self.pool = ConnectionPool(**pool_kwargs)
            self._pool_info = f"{self.config.HOST}:{self.config.PORT}/db{self.config.DB}"
            logger.info(f"Redis连接池已创建: {self._pool_info}, 最大连接数: {pool_kwargs['max_connections']}")
            
        return self.pool
        
    def create_client(self) -> Redis:
        """Creating a Redis client side

Returns:
Redis: Redis client side"""
        # Get connection pool
        pool = self.get_connection_pool()
        
        # Create client side
        client = Redis(connection_pool=pool)
        
        # Record client side information
        client_id = id(client)
        self.clients[client_id] = client
        
        # If there are more than 5 connections, log a warning
        if len(self.clients) > 5:
            logger.warning(f"当前活跃Redis连接数: {len(self.clients)}, 请注意资源使用")
        
        return client
        
    async def get_client(self) -> Redis:
        """Get the Redis client side

Returns:
Redis: Redis client side"""
        # Clean up before acquiring the new client side, closing unwanted connections
        if len(self.clients) >= 8:  # If the number of connections is close to the maximum, actively conduct a health check
            await self.health_check()
            
        # Reuse existing client side (if available)
        for client_id, client in list(self.clients.items()):
            try:
                # Test if the connection is available
                await client.ping()
                return client  # Return to the first available client side
            except RedisError:
                # Connection unavailable, remove from list
                self.clients.pop(client_id, None)
                try:
                    await client.close()
                except:
                    pass
        
        # If no client side is available, create a new client side
        client = self.create_client()
        
        # Check client side connections
        try:
            # Execute the PING command to test the connection
            await client.ping()
        except RedisError as e:
            logger.error(f"Redis连接测试失败: {e}")
            raise
        
        # Perform regular health checkups
        current_time = time.time()
        if current_time - self.last_health_check > self.health_check_interval:
            asyncio.create_task(self.health_check())  # Perform health checks asynchronously without blocking the current request
            self.last_health_check = current_time
            
        return client
        
    async def health_check(self):
        """Check the health of all client side connections and close unavailable connections"""
        logger.debug(f"执行Redis连接健康检查，当前连接数: {len(self.clients)}")
        closed_count = 0
        
        for client_id, client in list(self.clients.items()):
            try:
                # Try ping to test if the connection is available.
                await asyncio.wait_for(client.ping(), timeout=2.0)
            except (RedisError, asyncio.TimeoutError):
                # Connection unavailable, remove from list
                client = self.clients.pop(client_id, None)
                if client:
                    try:
                        await client.close()
                        closed_count += 1
                    except Exception as e:
                        logger.error(f"关闭Redis连接时出错 (id: {client_id}): {e}")
        
        if closed_count > 0:
            logger.info(f"Redis健康检查已关闭 {closed_count} 个不可用连接，剩余 {len(self.clients)} 个连接")
        
    def close_all_connections(self):
        """Close all Redis connections"""
        # Close all client sides
        for client_id, client in list(self.clients.items()):
            try:
                # Run with an event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If the event loop is already running, create a task
                    asyncio.create_task(client.close())
                else:
                    # Otherwise run synchronously
                    loop.run_until_complete(client.close())
                    
                # Delete from the dictionary
                self.clients.pop(client_id, None)
            except Exception as e:
                logger.error(f"关闭Redis连接时出错 (id: {client_id}): {e}")
        
        # Empty the connection pool
        if self.pool:
            self.pool.disconnect()
            self.pool = None
            
        logger.info("All Redis connections have been closed")


# Connection Manager Singleton
_connection_manager = None

def get_redis_connection_manager() -> RedisConnectionManager:
    """Get Redis Connection Manager

Returns:
RedisConnectionManager: Redis Connection Manager"""
    global _connection_manager
    
    if _connection_manager is None:
        _connection_manager = RedisConnectionManager()
        
    return _connection_manager


async def get_async_redis() -> Redis:
    """Get asynchronous Redis client side

Returns:
Redis: Asynchronous Redis client side"""
    # Get Connection Manager
    manager = get_redis_connection_manager()
    
    # Get the Redis client side
    return await manager.get_client()


@asynccontextmanager
async def get_redis_connection():
    """Redis Connection Context Manager
Use the async with statement to get a Redis connection, automatically close when exiting

Yields:
Redis: Redis client side"""
    # Get Connection Manager
    manager = get_redis_connection_manager()
    
    # Get the Redis client side
    client = await manager.get_client()
    
    try:
        yield client
    finally:
        # The client side is not closed here, it is managed by the connection pool
        pass 