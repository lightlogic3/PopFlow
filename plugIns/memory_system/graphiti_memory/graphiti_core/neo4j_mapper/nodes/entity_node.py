"""
实体节点模块
提供EntityNode类及其相关方法和工具函数
"""

import logging
from datetime import datetime
from time import time
from typing import Any, Dict, List, Optional

from neo4j import AsyncDriver
from pydantic import Field

from knowledge_manage.embeddings.base import EmbeddingEngine
from plugIns.memory_system.graphiti_memory.graphiti_core.errors import NodeNotFoundError
from plugIns.memory_system.graphiti_memory.graphiti_core.config import DEFAULT_DATABASE
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes.base_node import Node
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes.templates import (
    ENTITY_NODE_SAVE,
    ENTITY_NODE_GET_BY_UUID,
    ENTITY_NODE_GET_BY_UUIDS,
    ENTITY_NODE_GET_BY_GROUP_IDS,
    ENTITY_NODE_LOAD_EMBEDDING,
)

logger = logging.getLogger(__name__)

class EntityNode(Node):
    """
    实体节点类
    表示图中的实体对象
    """
    name_embedding: Optional[List[float]] = Field(default=None, description='名称的嵌入向量')
    summary: str = Field(description='周围边缘的区域摘要', default_factory=str)
    attributes: Dict[str, Any] = Field(
        default={}, description='节点的额外属性，取决于节点标签'
    )

    async def generate_name_embedding(self, embedder: EmbeddingEngine) -> List[float]:
        """
        生成节点名称的嵌入向量
        
        Args:
            embedder: 嵌入引擎
            
        Returns:
            生成的嵌入向量
        """
        start = time()
        text = self.name.replace('\n', ' ')
        self.name_embedding = await embedder.async_embed_query(text)
        end = time()
        logger.debug(f'嵌入 {text} 耗时 {end - start} 毫秒')

        return self.name_embedding

    async def load_name_embedding(self, driver: AsyncDriver) -> List[float]:
        """
        从数据库加载节点名称的嵌入向量
        
        Args:
            driver: Neo4j异步驱动
            
        Returns:
            加载的嵌入向量
            
        Raises:
            NodeNotFoundError: 如果节点不存在
        """
        logger.debug(f'加载节点名称嵌入: {self.uuid}')
        
        # 渲染Cypher查询
        query = ENTITY_NODE_LOAD_EMBEDDING.render()
        
        # 准备参数
        params = {"uuid": self.uuid}
        
        # 执行查询
        records, _, _ = await driver.execute_query(
            query, 
            params, 
            database_=DEFAULT_DATABASE, 
            routing_='r'
        )

        if len(records) == 0:
            logger.error(f'未找到节点: {self.uuid}')
            raise NodeNotFoundError(self.uuid)

        self.name_embedding = records[0]['name_embedding']
        logger.debug(f'已加载节点名称嵌入: {self.uuid}')
        return self.name_embedding

    async def save(self, driver: AsyncDriver) -> Any:
        """
        保存实体节点到数据库
        
        Args:
            driver: Neo4j异步驱动
            
        Returns:
            保存操作的结果
        """
        logger.debug(f'保存实体节点: {self.uuid}')
        
        # 准备实体数据
        entity_data: Dict[str, Any] = {
            'uuid': self.uuid,
            'name': self.name,
            'name_embedding': self.name_embedding,
            'group_id': self.group_id,
            'summary': self.summary,
            'created_at': self.created_at,
        }

        # 添加额外属性
        entity_data.update(self.attributes or {})
        
        # 渲染Cypher查询
        query = ENTITY_NODE_SAVE.render()
        
        # 准备参数
        params = {
            "labels": self.labels + ['Entity'],
            "entity_data": entity_data
        }
        
        # 执行查询
        try:
            result = await driver.execute_query(
                query,
                params,
                database_=DEFAULT_DATABASE,
            )
            logger.debug(f'已保存实体节点到neo4j: {self.uuid}')
            return result
        except Exception as e:
            logger.error(f'保存实体节点时出错: {str(e)}')
            raise e

    @classmethod
    async def get_by_uuid(cls, driver: AsyncDriver, uuid: str) -> 'EntityNode':
        """
        根据UUID获取实体节点
        
        Args:
            driver: Neo4j异步驱动
            uuid: 节点的UUID
            
        Returns:
            找到的节点对象
            
        Raises:
            NodeNotFoundError: 如果节点不存在
        """
        logger.debug(f'根据UUID获取实体节点: {uuid}')
        
        # 渲染Cypher查询
        query = ENTITY_NODE_GET_BY_UUID.render()
        
        # 准备参数
        params = {"uuid": uuid}
        
        # 执行查询
        try:
            records, _, _ = await driver.execute_query(
                query,
                params,
                database_=DEFAULT_DATABASE,
                routing_='r',
            )

            if len(records) == 0:
                logger.error(f'未找到实体节点: {uuid}')
                raise NodeNotFoundError(uuid)
                
            nodes = [get_entity_node_from_record(record) for record in records]
            logger.debug(f'已找到实体节点: {nodes[0].uuid}')
            return nodes[0]
        except NodeNotFoundError:
            raise
        except Exception as e:
            logger.error(f'获取实体节点时出错: {str(e)}')
            raise e

    @classmethod
    async def get_by_uuids(cls, driver: AsyncDriver, uuids: List[str]) -> List['EntityNode']:
        """
        根据UUID列表批量获取实体节点
        
        Args:
            driver: Neo4j异步驱动
            uuids: 节点UUID列表
            
        Returns:
            找到的节点对象列表
        """
        if not uuids:
            logger.debug('提供了空的UUID列表，返回空列表')
            return []
            
        logger.debug(f'根据UUID列表获取实体节点。数量: {len(uuids)}')
        
        # 渲染Cypher查询
        query = ENTITY_NODE_GET_BY_UUIDS.render()
        
        # 准备参数
        params = {"uuids": uuids}
        
        # 执行查询
        try:
            records, _, _ = await driver.execute_query(
                query,
                params,
                database_=DEFAULT_DATABASE,
                routing_='r',
            )

            nodes = [get_entity_node_from_record(record) for record in records]
            logger.debug(f'已找到 {len(nodes)} 个实体节点')
            return nodes
        except Exception as e:
            logger.error(f'批量获取实体节点时出错: {str(e)}')
            raise e

    @classmethod
    async def get_by_group_ids(
        cls,
        driver: AsyncDriver,
        group_ids: List[str],
        limit: Optional[int] = None,
        uuid_cursor: Optional[str] = None,
    ) -> List['EntityNode']:
        """
        根据组ID获取实体节点
        
        Args:
            driver: Neo4j异步驱动
            group_ids: 组ID列表
            limit: 返回结果的最大数量
            uuid_cursor: 分页游标，获取UUID小于该值的节点
            
        Returns:
            找到的节点对象列表
        """
        if not group_ids:
            logger.debug('提供了空的group_ids列表，返回空列表')
            return []
            
        logger.debug(
            f'根据组ID获取实体节点。数量: {len(group_ids)}, ' 
            f'limit: {limit}, uuid_cursor: {uuid_cursor}'
        )
        
        # 渲染Cypher查询
        query = ENTITY_NODE_GET_BY_GROUP_IDS.render(
            limit=limit is not None,
            uuid_cursor=uuid_cursor is not None
        )
        
        # 准备参数
        params = {
            "group_ids": group_ids,
        }
        if limit is not None:
            params["limit"] = limit
        if uuid_cursor is not None:
            params["uuid"] = uuid_cursor
        
        # 执行查询
        try:
            records, _, _ = await driver.execute_query(
                query,
                params,
                database_=DEFAULT_DATABASE,
                routing_='r',
            )

            nodes = [get_entity_node_from_record(record) for record in records]
            logger.debug(f'已找到 {len(nodes)} 个实体节点')
            return nodes
        except Exception as e:
            logger.error(f'根据组ID获取实体节点时出错: {str(e)}')
            raise e


def get_entity_node_from_record(record: Dict[str, Any]) -> EntityNode:
    """
    从数据库记录创建实体节点对象
    
    Args:
        record: 数据库记录
        
    Returns:
        创建的实体节点对象
    """
    # 创建实体节点
    entity_node = EntityNode(
        uuid=record['uuid'],
        name=record['name'],
        group_id=record['group_id'],
        labels=record['labels'],
        created_at=record['created_at'].to_native() if hasattr(record['created_at'], 'to_native') else record['created_at'],
        summary=record['summary'],
        attributes=record['attributes'],
    )
    
    # 删除重复字段
    entity_node.attributes.pop('uuid', None)
    entity_node.attributes.pop('name', None)
    entity_node.attributes.pop('group_id', None)
    entity_node.attributes.pop('name_embedding', None)
    entity_node.attributes.pop('summary', None)
    entity_node.attributes.pop('created_at', None)
    
    return entity_node


async def create_entity_node_embeddings(embedder: EmbeddingEngine, nodes: List[EntityNode]) -> None:
    """
    批量生成实体节点的名称嵌入向量
    
    Args:
        embedder: 嵌入引擎
        nodes: 实体节点列表
    """
    if not nodes:
        return
        
    logger.debug(f'为 {len(nodes)} 个实体节点生成嵌入向量')
    
    # 批量生成嵌入向量
    name_embeddings = await embedder.async_embed_documents([node.name for node in nodes])
    
    # 将嵌入向量分配给对应的节点
    for node, name_embedding in zip(nodes, name_embeddings, strict=True):
        node.name_embedding = name_embedding
        
    logger.debug(f'已成功为 {len(nodes)} 个实体节点生成嵌入向量') 