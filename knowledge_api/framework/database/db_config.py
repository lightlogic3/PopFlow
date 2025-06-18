from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional
import os


class DatabaseSettings(BaseSettings):
    """Database configuration settings"""
    # basic database configuration
    DB_ENGINE: str = "mysql"  # 'MySQL 'or'postgresql'
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306  # MySQL default port, PostgreSQL default is 5432
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "ai_game_chat"
    DB_CHARSET: str = "utf8mb4"
    
    # connection pool configuration
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 1800  # 30 Minutes
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_PRE_PING: bool = True
    
    # debug configuration
    DB_ECHO: bool = False  # Whether to print SQL statements
    DB_ECHO_POOL: bool = False  # Whether to print the connection pool log
    
    # connection timeout configuration
    DB_CONNECT_TIMEOUT: int = 10  # Connection timeout (seconds)
    
    @property
    def DATABASE_URL(self) -> str:
        """Build the connection URL from the configured database engine"""
        if self.DB_ENGINE == "mysql":
            return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        elif self.DB_ENGINE == "postgresql":
            return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        else:
            raise ValueError(f"不支持的数据库引擎: {self.DB_ENGINE}")
    
    @property
    def CONNECT_ARGS(self) -> dict:
        """Get connection parameters"""
        if self.DB_ENGINE == "mysql":
            return {"charset": self.DB_CHARSET, "connect_timeout": self.DB_CONNECT_TIMEOUT}
        return {}
    
    class Config:
        # Read configuration from custom or default environment files
        env_file = os.environ.get('ENV_FILE', '.env')
        env_file_encoding = "utf-8"
        # Allow additional attributes
        extra = "ignore"


@lru_cache()
def get_db_settings() -> DatabaseSettings:
    """Get database settings to optimize performance with LRU cache"""
    return DatabaseSettings()