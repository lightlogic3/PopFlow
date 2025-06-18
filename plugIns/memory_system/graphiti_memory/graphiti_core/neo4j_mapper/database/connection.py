"""
Neo4j数据库连接管理
实现单例模式确保连接复用
"""

from typing import Optional
from neo4j import AsyncGraphDatabase, AsyncDriver
from plugIns.memory_system.graphiti_memory.graphiti_core.config import DEFAULT_DATABASE, DEFAULT_CONNECTION_TIMEOUT

class Neo4jConnection:
    """Neo4j数据库连接管理器，实现单例模式确保连接复用"""
    
    _instance: Optional["Neo4jConnection"] = None
    _driver: Optional[AsyncDriver] = None
    
    def __new__(cls, *args, **kwargs):
        """实现单例模式"""
        if cls._instance is None:
            cls._instance = super(Neo4jConnection, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, uri: str = None, user: str = None, password: str = None, database: str = DEFAULT_DATABASE):
        """初始化连接，如果已经初始化则忽略"""
        # 避免重复初始化
        if hasattr(self, 'initialized') and self.initialized:
            return
            
        # 如果提供了连接参数，则直接初始化驱动
        if uri and user and password:
            self._driver = AsyncGraphDatabase.driver(
                uri, 
                auth=(user, password),
                max_connection_lifetime=DEFAULT_CONNECTION_TIMEOUT
            )
        
        self.database = database
        self.initialized = True
    
    @property
    def driver(self) -> AsyncDriver:
        """获取数据库驱动，如果不存在则抛出异常"""
        if self._driver is None:
            raise ValueError("Neo4j driver not initialized. Please call connect() first.")
        return self._driver
    
    @classmethod
    def get_instance(cls) -> "Neo4jConnection":
        """获取连接实例，如果不存在则创建"""
        if cls._instance is None:
            cls._instance = Neo4jConnection()
        return cls._instance
    
    def connect(self, uri: str, user: str, password: str) -> AsyncDriver:
        """连接到Neo4j数据库"""
        # 如果已经有连接则直接返回
        if self._driver is not None:
            return self._driver
            
        self._driver = AsyncGraphDatabase.driver(
            uri, 
            auth=(user, password),
            max_connection_lifetime=DEFAULT_CONNECTION_TIMEOUT
        )
        return self._driver
        
    async def close(self):
        """关闭连接"""
        if self._driver:
            await self._driver.close()
            self._driver = None
            
    def __del__(self):
        """析构时确保连接关闭"""
        import asyncio
        if self._driver:
            try:
                # 尝试在事件循环中关闭连接
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._driver.close())
                else:
                    # 如果没有事件循环运行，则使用同步关闭方法
                    self._driver.close()
            except Exception:
                # 如果无法优雅地关闭，则忽略
                pass 