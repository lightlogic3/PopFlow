"""
情节边缘模块
提供EpisodicEdge类及其相关方法和工具函数
"""

import logging
from typing import Any, Dict, List

from neo4j import AsyncDriver

from plugIns.memory_system.graphiti_memory.graphiti_core.errors import EdgeNotFoundError, GroupsEdgesNotFoundError
from plugIns.memory_system.graphiti_memory.graphiti_core.config import DEFAULT_DATABASE
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.edges.base_edge import Edge
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.edges.templates import (
    EPISODIC_EDGE_SAVE,
    EPISODIC_EDGE_GET_BY_UUID,
    EPISODIC_EDGE_GET_BY_UUIDS,
    EPISODIC_EDGE_GET_BY_GROUP_IDS,
)

logger = logging.getLogger(__name__)

class EpisodicEdge(Edge):
    """
    情节边缘类
    表示情节节点和实体节点之间的关系
    """
    
    async def save(self, driver: AsyncDriver) -> Any:
        """
        保存情节边缘到数据库
        
        Args:
            driver: Neo4j异步驱动
            
        Returns:
            保存操作的结果
        """
        logger.debug(f'Saving episodic edge: {self.uuid}')
        
        # 渲染Cypher查询
        query = EPISODIC_EDGE_SAVE.render()
        
        # 准备参数
        params = {
            "episode_uuid": self.source_node_uuid,
            "entity_uuid": self.target_node_uuid,
            "uuid": self.uuid,
            "group_id": self.group_id,
            "created_at": self.created_at,
        }
        
        # 执行查询
        try:
            result = await driver.execute_query(
                query,
                parameters=params,
                database_=DEFAULT_DATABASE,
            )
            logger.debug(f'Saved episodic edge to neo4j: {self.uuid}')
            return result
        except Exception as e:
            logger.error(f'Error saving episodic edge: {str(e)}')
            raise e

    @classmethod
    async def get_by_uuid(cls, driver: AsyncDriver, uuid: str) -> 'EpisodicEdge':
        """
        根据UUID获取情节边缘
        
        Args:
            driver: Neo4j异步驱动
            uuid: 边缘的UUID
            
        Returns:
            找到的边缘对象
            
        Raises:
            EdgeNotFoundError: 如果边缘不存在
        """
        logger.debug(f'Getting episodic edge by UUID: {uuid}')
        
        # 渲染Cypher查询
        query = EPISODIC_EDGE_GET_BY_UUID.render()
        
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
                logger.error(f'Episodic edge not found: {uuid}')
                raise EdgeNotFoundError(uuid)
                
            edge = get_episodic_edge_from_record(records[0])
            logger.debug(f'Found episodic edge: {edge.uuid}')
            return edge
        except EdgeNotFoundError:
            raise
        except Exception as e:
            logger.error(f'Error getting episodic edge by UUID: {str(e)}')
            raise e

    @classmethod
    async def get_by_uuids(cls, driver: AsyncDriver, uuids: List[str]) -> List['EpisodicEdge']:
        """
        根据UUID列表批量获取情节边缘
        
        Args:
            driver: Neo4j异步驱动
            uuids: 边缘UUID列表
            
        Returns:
            找到的边缘对象列表
            
        Raises:
            EdgeNotFoundError: 如果边缘不存在
        """
        if not uuids:
            logger.debug('Empty UUID list provided, returning empty list')
            return []
            
        logger.debug(f'Getting episodic edges by UUIDs. Count: {len(uuids)}')
        
        # 渲染Cypher查询
        query = EPISODIC_EDGE_GET_BY_UUIDS.render()
        
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

            edges = [get_episodic_edge_from_record(record) for record in records]
            
            if not edges:
                logger.error(f'Episodic edges not found: {uuids}')
                raise EdgeNotFoundError(uuids[0])
                
            logger.debug(f'Found {len(edges)} episodic edges')
            return edges
        except EdgeNotFoundError:
            raise
        except Exception as e:
            logger.error(f'Error getting episodic edges by UUIDs: {str(e)}')
            raise e

    @classmethod
    async def get_by_group_ids(
        cls,
        driver: AsyncDriver,
        group_ids: List[str],
        limit: int = None,
        uuid_cursor: str = None,
    ) -> List['EpisodicEdge']:
        """
        根据组ID获取情节边缘
        
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
            f'Getting episodic edges by group_ids. Count: {len(group_ids)}, ' 
            f'limit: {limit}, uuid_cursor: {uuid_cursor}'
        )
        
        # 渲染Cypher查询
        query = EPISODIC_EDGE_GET_BY_GROUP_IDS.render(
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

            edges = [get_episodic_edge_from_record(record) for record in records]
            
            if not edges:
                logger.error(f'No episodic edges found for group_ids: {group_ids}')
                raise GroupsEdgesNotFoundError(group_ids)
                
            logger.debug(f'Found {len(edges)} episodic edges')
            return edges
        except GroupsEdgesNotFoundError:
            raise
        except Exception as e:
            logger.error(f'Error getting episodic edges by group_ids: {str(e)}')
            raise e


def get_episodic_edge_from_record(record: Dict[str, Any]) -> EpisodicEdge:
    """
    从数据库记录创建情节边缘对象
    
    Args:
        record: 数据库记录
        
    Returns:
        创建的情节边缘对象
    """
    # 创建情节边缘对象
    edge = EpisodicEdge(
        uuid=record['uuid'],
        group_id=record['group_id'],
        source_node_uuid=record['source_node_uuid'],
        target_node_uuid=record['target_node_uuid'],
        created_at=record['created_at'].to_native() if hasattr(record['created_at'], 'to_native') else record['created_at'],
    )
    
    return edge 