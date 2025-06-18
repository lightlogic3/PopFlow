"""
情节节点模块
提供EpisodicNode类及其相关方法和工具函数
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from neo4j import AsyncDriver
from pydantic import Field

from plugIns.memory_system.graphiti_memory.graphiti_core.errors import NodeNotFoundError
from plugIns.memory_system.graphiti_memory.graphiti_core.config import DEFAULT_DATABASE
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes.base_node import Node
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes.episode_type import EpisodeType
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes.templates import (
    EPISODIC_NODE_SAVE,
    EPISODIC_NODE_GET_BY_UUID,
    EPISODIC_NODE_GET_BY_UUIDS,
    EPISODIC_NODE_GET_BY_GROUP_IDS,
    EPISODIC_NODE_GET_BY_ENTITY_NODE_UUID,
)

logger = logging.getLogger(__name__)

class EpisodicNode(Node):
    """
    情节节点类
    表示图中的情节对象，如消息、事件等
    """
    source: EpisodeType = Field(description='来源类型')
    source_description: str = Field(description='数据来源的描述')
    content: str = Field(description='原始情节数据')
    valid_at: datetime = Field(
        description='原始文档创建的日期时间',
    )
    entity_edges: List[str] = Field(
        description='此情节中引用的实体边缘列表',
        default_factory=list,
    )

    async def save(self, driver: AsyncDriver) -> Any:
        """
        保存情节节点到数据库
        
        Args:
            driver: Neo4j异步驱动
            
        Returns:
            保存操作的结果
        """
        logger.debug(f'保存情节节点: {self.uuid}')
        
        # 渲染Cypher查询
        query = EPISODIC_NODE_SAVE.render()
        
        # 准备参数
        params = {
            "uuid": self.uuid,
            "name": self.name,
            "group_id": self.group_id,
            "source_description": self.source_description,
            "content": self.content,
            "entity_edges": self.entity_edges,
            "created_at": self.created_at,
            "valid_at": self.valid_at,
            "source": self.source.value,
        }
        
        # 执行查询
        try:
            result = await driver.execute_query(
                query,
                params,
                database_=DEFAULT_DATABASE,
            )
            logger.debug(f'已保存情节节点到neo4j: {self.uuid}')
            return result
        except Exception as e:
            logger.error(f'保存情节节点时出错: {str(e)}')
            raise e

    @classmethod
    async def get_by_uuid(cls, driver: AsyncDriver, uuid: str) -> 'EpisodicNode':
        """
        根据UUID获取情节节点
        
        Args:
            driver: Neo4j异步驱动
            uuid: 节点的UUID
            
        Returns:
            找到的节点对象
            
        Raises:
            NodeNotFoundError: 如果节点不存在
        """
        logger.debug(f'根据UUID获取情节节点: {uuid}')
        
        # 渲染Cypher查询
        query = EPISODIC_NODE_GET_BY_UUID.render()
        
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
                logger.error(f'未找到情节节点: {uuid}')
                raise NodeNotFoundError(uuid)
                
            episodes = [get_episodic_node_from_record(record) for record in records]
            logger.debug(f'已找到情节节点: {episodes[0].uuid}')
            return episodes[0]
        except NodeNotFoundError:
            raise
        except Exception as e:
            logger.error(f'获取情节节点时出错: {str(e)}')
            raise e

    @classmethod
    async def get_by_uuids(cls, driver: AsyncDriver, uuids: List[str]) -> List['EpisodicNode']:
        """
        根据UUID列表批量获取情节节点
        
        Args:
            driver: Neo4j异步驱动
            uuids: 节点UUID列表
            
        Returns:
            找到的节点对象列表
        """
        if not uuids:
            logger.debug('提供了空的UUID列表，返回空列表')
            return []
            
        logger.debug(f'根据UUID列表获取情节节点。数量: {len(uuids)}')
        
        # 渲染Cypher查询
        query = EPISODIC_NODE_GET_BY_UUIDS.render()
        
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

            episodes = [get_episodic_node_from_record(record) for record in records]
            logger.debug(f'已找到 {len(episodes)} 个情节节点')
            return episodes
        except Exception as e:
            logger.error(f'批量获取情节节点时出错: {str(e)}')
            raise e

    @classmethod
    async def get_by_group_ids(
        cls,
        driver: AsyncDriver,
        group_ids: List[str],
        limit: Optional[int] = None,
        uuid_cursor: Optional[str] = None,
    ) -> List['EpisodicNode']:
        """
        根据组ID获取情节节点
        
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
            f'根据组ID获取情节节点。数量: {len(group_ids)}, ' 
            f'limit: {limit}, uuid_cursor: {uuid_cursor}'
        )
        
        # 渲染Cypher查询
        query = EPISODIC_NODE_GET_BY_GROUP_IDS.render(
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

            episodes = [get_episodic_node_from_record(record) for record in records]
            logger.debug(f'已找到 {len(episodes)} 个情节节点')
            return episodes
        except Exception as e:
            logger.error(f'根据组ID获取情节节点时出错: {str(e)}')
            raise e

    @classmethod
    async def get_by_entity_node_uuid(cls, driver: AsyncDriver, entity_node_uuid: str) -> List['EpisodicNode']:
        """
        获取与指定实体节点相关的所有情节节点
        
        Args:
            driver: Neo4j异步驱动
            entity_node_uuid: 实体节点的UUID
            
        Returns:
            与该实体节点相关的情节节点列表
        """
        logger.debug(f'获取与实体节点相关的情节节点: {entity_node_uuid}')
        
        # 渲染Cypher查询
        query = EPISODIC_NODE_GET_BY_ENTITY_NODE_UUID.render()
        
        # 准备参数
        params = {"entity_node_uuid": entity_node_uuid}
        
        # 执行查询
        try:
            records, _, _ = await driver.execute_query(
                query,
                params,
                database_=DEFAULT_DATABASE,
                routing_='r',
            )

            episodes = [get_episodic_node_from_record(record) for record in records]
            logger.debug(f'找到与实体节点 {entity_node_uuid} 相关的 {len(episodes)} 个情节节点')
            return episodes
        except Exception as e:
            logger.error(f'获取与实体节点相关的情节节点时出错: {str(e)}')
            raise e


def get_episodic_node_from_record(record: Dict[str, Any]) -> EpisodicNode:
    """
    从数据库记录创建情节节点对象
    
    Args:
        record: 数据库记录
        
    Returns:
        创建的情节节点对象
    """
    # 创建情节节点对象
    return EpisodicNode(
        content=record['content'],
        created_at=record['created_at'].to_native().timestamp() if hasattr(record['created_at'], 'to_native') else record['created_at'],
        valid_at=record['valid_at'].to_native() if hasattr(record['valid_at'], 'to_native') else record['valid_at'],
        uuid=record['uuid'],
        group_id=record['group_id'],
        source=EpisodeType.from_str(record['source']),
        name=record['name'],
        source_description=record['source_description'],
        entity_edges=record['entity_edges'],
    ) 