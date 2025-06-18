"""
节点基类模块
提供所有节点类型的公共基类和抽象方法
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, List
from uuid import uuid4

from neo4j import AsyncDriver
from pydantic import BaseModel, Field

from plugIns.memory_system.graphiti_memory.graphiti_core.config import DEFAULT_DATABASE
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes.templates import (
    NODE_DELETE,
    NODE_DELETE_BY_GROUP_ID,
)
from plugIns.memory_system.graphiti_memory.graphiti_core.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)

class Node(BaseModel, ABC):
    """
    节点基类
    定义了所有节点类型的通用属性和方法
    """
    uuid: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(description='节点名称')
    group_id: str = Field(description='图分区标识')
    labels: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: utc_now())

    @abstractmethod
    async def save(self, driver: AsyncDriver) -> Any:
        """
        保存节点到数据库
        
        Args:
            driver: Neo4j异步驱动
            
        Returns:
            保存操作的结果
        """
        pass

    async def delete(self, driver: AsyncDriver) -> Any:
        """
        删除节点
        
        Args:
            driver: Neo4j异步驱动
            
        Returns:
            删除操作的结果
        """
        logger.debug(f'删除节点: {self.uuid}')
        
        # 渲染Cypher查询
        query = NODE_DELETE.render()
        
        # 准备参数
        params = {"uuid": self.uuid}
        
        # 执行查询
        result = await driver.execute_query(
            query,
            params,
            database_=DEFAULT_DATABASE,
        )
        
        logger.debug(f'已删除节点: {self.uuid}')
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
    async def delete_by_group_id(cls, driver: AsyncDriver, group_id: str) -> str:
        """
        删除指定组ID的所有节点
        
        Args:
            driver: Neo4j异步驱动
            group_id: 组ID
            
        Returns:
            操作状态
        """
        logger.debug(f'删除组ID为 {group_id} 的所有节点')
        
        # 渲染Cypher查询
        query = NODE_DELETE_BY_GROUP_ID.render()
        
        # 准备参数
        params = {"group_id": group_id}
        
        # 执行查询
        await driver.execute_query(
            query,
            params,
            database_=DEFAULT_DATABASE,
        )
        
        logger.debug(f'已删除组ID为 {group_id} 的所有节点')
        return 'SUCCESS'

    @classmethod
    @abstractmethod
    async def get_by_uuid(cls, driver: AsyncDriver, uuid: str) -> Any:
        """
        根据UUID获取节点
        
        Args:
            driver: Neo4j异步驱动
            uuid: 节点UUID
            
        Returns:
            找到的节点对象
        """
        pass

    @classmethod
    @abstractmethod
    async def get_by_uuids(cls, driver: AsyncDriver, uuids: List[str]) -> List[Any]:
        """
        根据UUID列表批量获取节点
        
        Args:
            driver: Neo4j异步驱动
            uuids: 节点UUID列表
            
        Returns:
            找到的节点对象列表
        """
        pass 