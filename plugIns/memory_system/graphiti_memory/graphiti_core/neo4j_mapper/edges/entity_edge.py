"""
实体边缘模块
提供EntityEdge类及其相关方法和工具函数
"""

import logging
from datetime import datetime
from time import time
from typing import Any, Dict, List, Optional

from neo4j import AsyncDriver
from pydantic import Field

from knowledge_manage.embeddings.base import EmbeddingEngine
from plugIns.memory_system.graphiti_memory.graphiti_core.errors import EdgeNotFoundError, GroupsEdgesNotFoundError
from plugIns.memory_system.graphiti_memory.graphiti_core.config import DEFAULT_DATABASE
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.edges.base_edge import Edge
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.edges.templates import (
    ENTITY_EDGE_SAVE,
    ENTITY_EDGE_GET_BY_UUID,
    ENTITY_EDGE_GET_BY_UUIDS,
    ENTITY_EDGE_GET_BY_GROUP_IDS,
    ENTITY_EDGE_GET_BY_NODE_UUID,
    ENTITY_EDGE_LOAD_FACT_EMBEDDING,
)
from plugIns.memory_system.graphiti_memory.graphiti_core.utils.utils import parse_db_date

logger = logging.getLogger(__name__)

class EntityEdge(Edge):
    """
    实体边缘类
    表示两个实体节点之间的关系
    """
    name: str = Field(description='name of the edge, relation name')
    fact: str = Field(description='fact representing the edge and nodes that it connects')
    fact_embedding: Optional[List[float]] = Field(default=None, description='embedding of the fact')
    episodes: List[str] = Field(
        default=[],
        description='list of episode ids that reference these entity edges',
    )
    expired_at: Optional[datetime] = Field(
        default=None, description='datetime of when the node was invalidated'
    )
    valid_at: Optional[datetime] = Field(
        default=None, description='datetime of when the fact became true'
    )
    invalid_at: Optional[datetime] = Field(
        default=None, description='datetime of when the fact stopped being true'
    )
    attributes: Dict[str, Any] = Field(
        default={}, description='Additional attributes of the edge. Dependent on edge name'
    )

    async def generate_embedding(self, embedder: EmbeddingEngine) -> List[float]:
        """
        生成边缘事实的嵌入向量
        
        Args:
            embedder: 嵌入引擎
            
        Returns:
            生成的嵌入向量
        """
        start = time()

        text = self.fact.replace('\n', ' ')
        self.fact_embedding = await embedder.async_embed_query(text)

        end = time()
        logger.debug(f'embedded {text} in {end - start} ms')

        return self.fact_embedding

    async def load_fact_embedding(self, driver: AsyncDriver) -> List[float]:
        """
        从数据库加载边缘事实的嵌入向量
        
        Args:
            driver: Neo4j异步驱动
            
        Returns:
            加载的嵌入向量
            
        Raises:
            EdgeNotFoundError: 如果边缘不存在
        """
        logger.debug(f'Loading fact embedding for edge: {self.uuid}')
        
        # 渲染Cypher查询
        query = ENTITY_EDGE_LOAD_FACT_EMBEDDING.render()
        
        # 准备参数
        params = {"uuid": self.uuid}
        
        # 执行查询
        records, _, _ = await driver.execute_query(
            query, 
            parameters=params, 
            database_=DEFAULT_DATABASE, 
            routing_='r'
        )

        if len(records) == 0:
            logger.error(f'Edge not found: {self.uuid}')
            raise EdgeNotFoundError(self.uuid)

        self.fact_embedding = records[0]['fact_embedding']
        logger.debug(f'Loaded fact embedding for edge: {self.uuid}')
        return self.fact_embedding

    async def save(self, driver: AsyncDriver) -> Any:
        """
        保存实体边缘到数据库
        
        Args:
            driver: Neo4j异步驱动
            
        Returns:
            保存操作的结果
        """
        logger.debug(f'Saving entity edge: {self.uuid}')
        
        # 准备边缘数据
        edge_data: Dict[str, Any] = {
            'source_uuid': self.source_node_uuid,
            'target_uuid': self.target_node_uuid,
            'uuid': self.uuid,
            'name': self.name,
            'group_id': self.group_id,
            'fact': self.fact,
            'fact_embedding': self.fact_embedding,
            'episodes': self.episodes,
            'created_at': self.created_at,
            'expired_at': self.expired_at,
            'valid_at': self.valid_at,
            'invalid_at': self.invalid_at,
        }

        # 添加额外属性
        edge_data.update(self.attributes or {})
        
        # 渲染Cypher查询
        query = ENTITY_EDGE_SAVE.render()
        
        # 准备参数
        params = {"edge_data": edge_data}
        
        # 执行查询
        try:
            result = await driver.execute_query(
                query,
                parameters=params,
                database_=DEFAULT_DATABASE,
            )
            logger.debug(f'Saved entity edge to neo4j: {self.uuid}')
            return result
        except Exception as e:
            logger.error(f'Error saving entity edge: {str(e)}')
            raise e

    @classmethod
    async def get_by_uuid(cls, driver: AsyncDriver, uuid: str) -> 'EntityEdge':
        """
        根据UUID获取实体边缘
        
        Args:
            driver: Neo4j异步驱动
            uuid: 边缘的UUID
            
        Returns:
            找到的边缘对象
            
        Raises:
            EdgeNotFoundError: 如果边缘不存在
        """
        logger.debug(f'Getting entity edge by UUID: {uuid}')
        
        # 渲染Cypher查询
        query = ENTITY_EDGE_GET_BY_UUID.render()
        
        # 准备参数
        params = {"uuid": uuid}
        
        # 执行查询
        try:
            records, _, _ = await driver.execute_query(
                query,
                parameters=params,
                database_=DEFAULT_DATABASE,
                routing_='r',
            )

            if len(records) == 0:
                logger.error(f'Entity edge not found: {uuid}')
                raise EdgeNotFoundError(uuid)
                
            edge = get_entity_edge_from_record(records[0])
            logger.debug(f'Found entity edge: {edge.uuid}')
            return edge
        except EdgeNotFoundError:
            raise
        except Exception as e:
            logger.error(f'Error getting entity edge by UUID: {str(e)}')
            raise e

    @classmethod
    async def get_by_uuids(cls, driver: AsyncDriver, uuids: List[str]) -> List['EntityEdge']:
        """
        根据UUID列表批量获取实体边缘
        
        Args:
            driver: Neo4j异步驱动
            uuids: 边缘UUID列表
            
        Returns:
            找到的边缘对象列表
        """
        if not uuids:
            logger.debug('Empty UUID list provided, returning empty list')
            return []
            
        logger.debug(f'Getting entity edges by UUIDs. Count: {len(uuids)}')
        
        # 渲染Cypher查询
        query = ENTITY_EDGE_GET_BY_UUIDS.render()
        
        # 准备参数
        params = {"uuids": uuids}
        
        # 执行查询
        try:
            records, _, _ = await driver.execute_query(
                query,
                parameters=params,
                database_=DEFAULT_DATABASE,
                routing_='r',
            )

            edges = [get_entity_edge_from_record(record) for record in records]
            logger.debug(f'Found {len(edges)} entity edges')
            return edges
        except Exception as e:
            logger.error(f'Error getting entity edges by UUIDs: {str(e)}')
            raise e

    @classmethod
    async def get_by_group_ids(
        cls,
        driver: AsyncDriver,
        group_ids: List[str],
        limit: Optional[int] = None,
        uuid_cursor: Optional[str] = None,
    ) -> List['EntityEdge']:
        """
        根据组ID获取实体边缘
        
        Args:
            driver: Neo4j异步驱动
            group_ids: 组ID列表
            limit: 返回结果的最大数量
            uuid_cursor: 分页游标，获取UUID小于该值的边缘
            
        Returns:
            找到的边缘对象列表
            
        Raises:
            GroupsEdgesNotFoundError: 如果没有找到任何边缘
        """
        if not group_ids:
            logger.debug('Empty group_ids list provided, returning empty list')
            return []
            
        logger.debug(
            f'Getting entity edges by group_ids. Count: {len(group_ids)}, ' 
            f'limit: {limit}, uuid_cursor: {uuid_cursor}'
        )
        
        # 渲染Cypher查询
        query = ENTITY_EDGE_GET_BY_GROUP_IDS.render(
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
                parameters=params,
                database_=DEFAULT_DATABASE,
                routing_='r',
            )

            edges = [get_entity_edge_from_record(record) for record in records]
            
            if not edges:
                logger.error(f'No entity edges found for group_ids: {group_ids}')
                raise GroupsEdgesNotFoundError(group_ids)
                
            logger.debug(f'Found {len(edges)} entity edges')
            return edges
        except GroupsEdgesNotFoundError:
            raise
        except Exception as e:
            logger.error(f'Error getting entity edges by group_ids: {str(e)}')
            raise e

    @classmethod
    async def get_by_node_uuid(cls, driver: AsyncDriver, node_uuid: str) -> List['EntityEdge']:
        """
        获取与指定节点相关的所有实体边缘
        
        Args:
            driver: Neo4j异步驱动
            node_uuid: 节点UUID
            
        Returns:
            与该节点相关的边缘对象列表
        """
        logger.debug(f'Getting entity edges by node UUID: {node_uuid}')
        
        # 渲染Cypher查询
        query = ENTITY_EDGE_GET_BY_NODE_UUID.render()
        
        # 准备参数
        params = {"node_uuid": node_uuid}
        
        # 执行查询
        try:
            records, _, _ = await driver.execute_query(
                query,
                parameters=params,
                database_=DEFAULT_DATABASE,
                routing_='r',
            )

            edges = [get_entity_edge_from_record(record) for record in records]
            logger.debug(f'Found {len(edges)} entity edges for node: {node_uuid}')
            return edges
        except Exception as e:
            logger.error(f'Error getting entity edges by node UUID: {str(e)}')
            raise e


def get_entity_edge_from_record(record: Dict[str, Any]) -> EntityEdge:
    """
    从数据库记录创建实体边缘对象
    
    Args:
        record: 数据库记录
        
    Returns:
        创建的实体边缘对象
    """
    # 获取属性
    attributes = dict(record['attributes'])
    
    # 创建实体边缘对象
    edge = EntityEdge(
        uuid=record['uuid'],
        source_node_uuid=record['source_node_uuid'],
        target_node_uuid=record['target_node_uuid'],
        fact=record['fact'],
        name=record['name'],
        group_id=record['group_id'],
        episodes=record['episodes'],
        created_at=record['created_at'].to_native() if hasattr(record['created_at'], 'to_native') else record['created_at'],
        expired_at=parse_db_date(record['expired_at']),
        valid_at=parse_db_date(record['valid_at']),
        invalid_at=parse_db_date(record['invalid_at']),
        attributes=attributes,
    )
    
    # 删除重复字段
    field_names = {
        'uuid', 'source_node_uuid', 'target_node_uuid', 'fact', 'name', 
        'group_id', 'episodes', 'created_at', 'expired_at', 'valid_at', 'invalid_at'
    }
    for field_name in field_names:
        if field_name in edge.attributes:
            del edge.attributes[field_name]
    
    return edge


async def create_entity_edge_embeddings(embedder: EmbeddingEngine, edges: List[EntityEdge]) -> None:
    """
    批量生成实体边缘的嵌入向量
    
    Args:
        embedder: 嵌入引擎
        edges: 实体边缘列表
    """
    if not edges:
        return
        
    logger.debug(f'Generating embeddings for {len(edges)} entity edges')
    
    # 批量生成嵌入向量
    fact_embeddings = await embedder.async_embed_documents([edge.fact for edge in edges])
    
    # 将嵌入向量分配给对应的边缘
    for edge, fact_embedding in zip(edges, fact_embeddings, strict=True):
        edge.fact_embedding = fact_embedding
        
    logger.debug(f'Generated embeddings for {len(edges)} entity edges successfully') 