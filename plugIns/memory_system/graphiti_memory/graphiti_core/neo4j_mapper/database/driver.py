"""
Neo4j数据库操作工具函数
提供异步数据库查询执行功能
"""

from typing import Dict, List, Any, Callable, Awaitable, TypeVar
from neo4j import AsyncDriver, AsyncResult

from plugIns.memory_system.graphiti_memory.graphiti_core.config import DEFAULT_DATABASE

T = TypeVar('T')

async def execute_query(
    driver: AsyncDriver, 
    query: str, 
    params: Dict[str, Any] = None, 
    database: str = DEFAULT_DATABASE
) -> List[Dict[str, Any]]:
    """
    执行只读查询并返回结果
    
    Args:
        driver: Neo4j异步驱动
        query: Cypher查询语句
        params: 查询参数
        database: 数据库名称
        
    Returns:
        查询结果列表
    """
    records, _, _ = await driver.execute_query(
        query,
        parameters=params or {},
        database_=database,
        routing_='r',  # 指定只读路由
    )
    
    # 将记录转换为字典形式
    return [dict(record) for record in records]

async def execute_write(
    driver: AsyncDriver, 
    query: str, 
    params: Dict[str, Any] = None, 
    database: str = DEFAULT_DATABASE
) -> AsyncResult:
    """
    执行写入查询并返回结果
    
    Args:
        driver: Neo4j异步驱动
        query: Cypher写入查询语句
        params: 查询参数
        database: 数据库名称
        
    Returns:
        写入操作结果
    """
    result = await driver.execute_query(
        query,
        parameters=params or {},
        database_=database,
    )
    return result

async def execute_transaction(
    driver: AsyncDriver,
    tx_function: Callable[[AsyncDriver], Awaitable[T]],
    database: str = DEFAULT_DATABASE
) -> T:
    """
    在事务中执行一组操作
    
    Args:
        driver: Neo4j异步驱动
        tx_function: 事务函数，接受事务会话并返回结果
        database: 数据库名称
        
    Returns:
        事务函数返回值
    """
    async with driver.session(database=database) as session:
        result = await session.execute_write(tx_function)
        return result 