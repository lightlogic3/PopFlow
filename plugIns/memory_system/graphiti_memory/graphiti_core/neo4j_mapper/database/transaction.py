"""
Neo4j事务管理工具
"""

import contextlib
from typing import AsyncGenerator, TypeVar, Callable, Awaitable, Any, Optional
from neo4j import AsyncDriver, AsyncSession, AsyncTransaction

T = TypeVar('T')

@contextlib.asynccontextmanager
async def transaction_context(driver: AsyncDriver, database: str = "neo4j") -> AsyncGenerator[AsyncTransaction, None]:
    """
    创建一个异步事务上下文管理器，用于包装Neo4j事务操作
    
    Args:
        driver: Neo4j异步驱动
        database: 数据库名称
        
    Yields:
        事务对象
    
    Example:
        async with transaction_context(driver) as tx:
            await tx.run("CREATE (n:Node {name: $name})", name="Example")
            await tx.run("CREATE (n:Node {name: $name})", name="Another Example")
    """
    async with driver.session(database=database) as session:
        async with session.begin_transaction() as tx:
            try:
                yield tx
                # 上下文管理器退出时自动提交
            except Exception:
                # 发生异常时自动回滚
                await tx.rollback()
                raise

class TransactionManager:
    """事务管理器，提供事务操作的高级抽象"""
    
    def __init__(self, driver: AsyncDriver, database: str = "neo4j"):
        """
        初始化事务管理器
        
        Args:
            driver: Neo4j异步驱动
            database: 数据库名称
        """
        self.driver = driver
        self.database = database
    
    @contextlib.asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncTransaction, None]:
        """
        创建事务上下文
        
        Yields:
            事务对象
        """
        async with transaction_context(self.driver, self.database) as tx:
            yield tx
    
    async def execute_in_transaction(
        self, 
        func: Callable[[AsyncTransaction], Awaitable[T]]
    ) -> T:
        """
        在事务中执行函数
        
        Args:
            func: 接受事务对象并返回结果的异步函数
            
        Returns:
            函数的执行结果
        """
        async with self.transaction() as tx:
            return await func(tx) 