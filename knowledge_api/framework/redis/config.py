"""Redis configuration module
Provides Redis connection configuration and management capabilities"""
import os
from typing import Dict, Any, Optional
from functools import lru_cache
from pydantic import BaseModel
from dotenv import load_dotenv

from knowledge_api.utils.log_config import get_logger

logger = get_logger()

# Note: environment variables are now loaded uniformly by app.py at app startup
# No more calling load_dotenv () here

class RedisConfig(BaseModel):
    """Redis configuration class"""
    # Redis connection configuration
    HOST: str = "localhost"
    PORT: int = 6379
    DB: int = 0
    USERNAME: str = ""
    PASSWORD: Optional[str] = None
    
    # connection pool configuration
    MAX_CONNECTIONS: int = 10
    SOCKET_TIMEOUT: int = 5
    
    # cache configuration
    DEFAULT_TIMEOUT: Optional[int] = 86400  # Default cache for 24 hours
    
    # key prefix
    KEY_PREFIX: str = "knowleadge_api:"
    SYSTEM_CONFIG_PREFIX: str = "system_config:"
    CHARACTER_PROMPT_PREFIX: str = "character_prompt:"
    LLM_PROVIDER_PREFIX: str = "llm_provider:"
    MODEL_CONFIG_PREFIX: str = "model_config:"
    
    def get_redis_url(self) -> str:
        """Get the Redis connection URL

Returns:
STR: Redis Connection URL"""
        auth_part = ""
        
        # Add username and password
        if self.USERNAME and self.PASSWORD:
            auth_part = f"{self.USERNAME}:{self.PASSWORD}@"
        elif self.PASSWORD:
            auth_part = f":{self.PASSWORD}@"
        elif self.USERNAME:
            auth_part = f"{self.USERNAME}@"
            
        return f"redis://{auth_part}{self.HOST}:{self.PORT}/{self.DB}"
        
    def get_connection_params(self) -> dict:
        """Get Redis connection parameters

Returns:
DICT: Redis connection parameters"""
        params = {
            "host": self.HOST,
            "port": self.PORT,
            "db": self.DB,
            "max_connections": self.MAX_CONNECTIONS,
            "socket_timeout": self.SOCKET_TIMEOUT,
            "retry_on_timeout": True,
            "health_check_interval": 30
        }
        
        # Add username and password
        if self.USERNAME:
            params["username"] = self.USERNAME
            
        if self.PASSWORD:
            params["password"] = self.PASSWORD
            
        return params

    def get_cache_key(self, key_type: str, key: str) -> str:
        """Generate prefixed cache keys

Args:
key_type: key type prefix
Key: key name

Returns:
Str: full cache key name"""
        if key_type == "character_prompt":
            prefix = self.CHARACTER_PROMPT_PREFIX
        elif key_type == "system_config":
            prefix = self.SYSTEM_CONFIG_PREFIX
        elif key_type == "llm_provider":
            prefix = self.LLM_PROVIDER_PREFIX
        elif key_type == "model_config":
            prefix = self.MODEL_CONFIG_PREFIX
        else:
            prefix = ""
            
        return f"{self.KEY_PREFIX}{prefix}{key}"

# cached singleton pattern
_redis_config = None

def get_redis_config() -> RedisConfig:
    """Get Redis Configuration

Returns:
RedisConfig: Redis configuration"""
    global _redis_config
    
    if _redis_config is None:
        # Check if the gunicorn is in progress
        is_gunicorn = os.environ.get('GUNICORN_WORKER') == 'true'
        
        # Loading configuration from environment variables
        config = {
            "HOST": os.environ.get("REDIS_HOST", "localhost"),
            "PORT": int(os.environ.get("REDIS_PORT", 6379)),
            "DB": int(os.environ.get("REDIS_DB", 0)),
            "USERNAME": os.environ.get("REDIS_USERNAME", ""),
            "PASSWORD": os.environ.get("REDIS_PASSWORD", None),
            "MAX_CONNECTIONS": int(os.environ.get("REDIS_MAX_CONNECTIONS", 10)),
            "SOCKET_TIMEOUT": int(os.environ.get("REDIS_SOCKET_TIMEOUT", 5)),
        }
        
        # Create configuration object
        _redis_config = RedisConfig(**config)
        
        # logging
        host_info = f"{_redis_config.HOST}:{_redis_config.PORT}/db{_redis_config.DB}"
        
        # Reduce log output in the gunicorn worker process
        if not is_gunicorn or os.environ.get('REDIS_CONFIG_LOGGED') != 'true':
            logger.info(f"Redis配置已加载: {host_info}")
            # Mark the output log to avoid duplication
            os.environ['REDIS_CONFIG_LOGGED'] = 'true'
        
    return _redis_config

def reset_redis_config():
    """Reset Redis configuration
Calling this function after environment variables change forces a reload of the configuration"""
    global _redis_config
    
    # Check if it is in the gunicorn process, if so skip the reset
    if os.environ.get('GUNICORN_WORKER') == 'true' and os.environ.get('REDIS_CONFIG_RESET') == 'true':
        return _redis_config
    
    # Tag reset executed
    os.environ['REDIS_CONFIG_RESET'] = 'true'
    
    _redis_config = None
    logger.info("Redis configuration has been reset and will be reloaded on the next visit")
    return get_redis_config() 