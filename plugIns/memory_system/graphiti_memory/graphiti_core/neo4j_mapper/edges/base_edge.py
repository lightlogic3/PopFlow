"""
边缘基类模块
提供所有边缘类型的公共基类和抽象方法
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from uuid import uuid4

from neo4j import AsyncDriver
from pydantic import BaseModel, Field

from plugIns.memory_system.graphiti_memory.graphiti_core.config import DEFAULT_DATABASE
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.edges.templates import EDGE_DELETE
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes import Node

logger = logging.getLogger(__name__)

class Edge(BaseModel, ABC):
    """
    边缘基类
    定义了所有边缘类型的通用属性和方法
    """
    uuid: str = Field(default_factory=lambda: str(uuid4()))
    group_id: str = Field(description='partition of the graph')
    source_node_uuid: str
    target_node_uuid: str
    created_at: datetime

    @abstractmethod
    async def save(self, driver: AsyncDriver) -> Any:
        """
        保存边缘到数据库
        
        Args:
            driver: Neo4j异步驱动
            
        Returns:
            保存操作的结果
        """
        pass

    async def delete(self, driver: AsyncDriver) -> Any:
        """
        删除边缘
        
        Args:
            driver: Neo4j异步驱动
            
        Returns:
            删除操作的结果
        """
        logger.debug(f'Deleting Edge: {self.uuid}')
        
        # 渲染Cypher查询
        query = EDGE_DELETE.render()
        
        # 准备参数
        params = {"uuid": self.uuid}
        
        # 执行查询
        result = await driver.execute_query(
            query,
            parameters=params,
            database_=DEFAULT_DATABASE,
        )
        
        logger.debug(f'Deleted Edge: {self.uuid}')
        return result

    def __hash__(self):
        """获取哈希值，用于字典键和集合元素"""
        return hash(self.uuid)

    def __eq__(self, other):
        """
        比较两个对象是否相等
        
        Args:
            other: 要比较的另一个对象
            
        Returns:
            如果UUID相同则返回True，否则返回False
        """
        if isinstance(other, Node):
            return self.uuid == other.uuid
        return False

    @classmethod
    @abstractmethod
    async def get_by_uuid(cls, driver: AsyncDriver, uuid: str) -> Any:
        """
        根据UUID获取边缘
        
        Args:
            driver: Neo4j异步驱动
            uuid: 边缘的UUID
            
        Returns:
            找到的边缘对象
        """
        pass 