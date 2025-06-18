"""
社区节点模块
提供CommunityNode类及其相关方法和工具函数
"""

import logging
from time import time
from typing import Any, Dict, List, Optional

from neo4j import AsyncDriver
from pydantic import Field

from knowledge_manage.embeddings.base import EmbeddingEngine
from plugIns.memory_system.graphiti_memory.graphiti_core.errors import NodeNotFoundError
from plugIns.memory_system.graphiti_memory.graphiti_core.config import DEFAULT_DATABASE
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes.base_node import Node
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes.templates import (
    COMMUNITY_NODE_SAVE,
    COMMUNITY_NODE_GET_BY_UUID,
    COMMUNITY_NODE_GET_BY_UUIDS,
    COMMUNITY_NODE_GET_BY_GROUP_IDS,
    COMMUNITY_NODE_LOAD_EMBEDDING,
)

logger = logging.getLogger(__name__)

class CommunityNode(Node):
    """
    社区节点类
    表示包含多个成员节点的社区或分组
    """
    name_embedding: Optional[List[float]] = Field(default=None, description='名称的嵌入向量')
    summary: str = Field(description='成员节点的区域摘要', default_factory=str)

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
        logger.debug(f'加载社区节点名称嵌入: {self.uuid}')
        
        # 渲染Cypher查询
        query = COMMUNITY_NODE_LOAD_EMBEDDING.render()
        
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
        logger.debug(f'已加载社区节点名称嵌入: {self.uuid}')
        return self.name_embedding

    async def save(self, driver: AsyncDriver) -> Any:
        """
        保存社区节点到数据库
        
        Args:
            driver: Neo4j异步驱动
            
        Returns:
            保存操作的结果
        """
        logger.debug(f'保存社区节点: {self.uuid}')
        
        # 渲染Cypher查询
        query = COMMUNITY_NODE_SAVE.render()
        
        # 准备参数
        params = {
            "uuid": self.uuid,
            "name": self.name,
            "group_id": self.group_id,
            "summary": self.summary,
            "name_embedding": self.name_embedding,
            "created_at": self.created_at,
        }
        
        # 执行查询
        try:
            result = await driver.execute_query(
                query,
                params,
                database_=DEFAULT_DATABASE,
            )
            logger.debug(f'已保存社区节点到neo4j: {self.uuid}')
            return result
        except Exception as e:
            logger.error(f'保存社区节点时出错: {str(e)}')
            raise e

    @classmethod
    async def get_by_uuid(cls, driver: AsyncDriver, uuid: str) -> 'CommunityNode':
        """
        根据UUID获取社区节点
        
        Args:
            driver: Neo4j异步驱动
            uuid: 节点的UUID
            
        Returns:
            找到的节点对象
            
        Raises:
            NodeNotFoundError: 如果节点不存在
        """
        logger.debug(f'根据UUID获取社区节点: {uuid}')
        
        # 渲染Cypher查询
        query = COMMUNITY_NODE_GET_BY_UUID.render()
        
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
                logger.error(f'未找到社区节点: {uuid}')
                raise NodeNotFoundError(uuid)
                
            nodes = [get_community_node_from_record(record) for record in records]
            logger.debug(f'已找到社区节点: {nodes[0].uuid}')
            return nodes[0]
        except NodeNotFoundError:
            raise
        except Exception as e:
            logger.error(f'获取社区节点时出错: {str(e)}')
            raise e

    @classmethod
    async def get_by_uuids(cls, driver: AsyncDriver, uuids: List[str]) -> List['CommunityNode']:
        """
        根据UUID列表批量获取社区节点
        
        Args:
            driver: Neo4j异步驱动
            uuids: 节点UUID列表
            
        Returns:
            找到的节点对象列表
        """
        if not uuids:
            logger.debug('提供了空的UUID列表，返回空列表')
            return []
            
        logger.debug(f'根据UUID列表获取社区节点。数量: {len(uuids)}')
        
        # 渲染Cypher查询
        query = COMMUNITY_NODE_GET_BY_UUIDS.render()
        
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

            communities = [get_community_node_from_record(record) for record in records]
            logger.debug(f'已找到 {len(communities)} 个社区节点')
            return communities
        except Exception as e:
            logger.error(f'批量获取社区节点时出错: {str(e)}')
            raise e

    @classmethod
    async def get_by_group_ids(
        cls,
        driver: AsyncDriver,
        group_ids: List[str],
        limit: Optional[int] = None,
        uuid_cursor: Optional[str] = None,
    ) -> List['CommunityNode']:
        """
        根据组ID获取社区节点
        
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
            f'根据组ID获取社区节点。数量: {len(group_ids)}, ' 
            f'limit: {limit}, uuid_cursor: {uuid_cursor}'
        )
        
        # 渲染Cypher查询
        query = COMMUNITY_NODE_GET_BY_GROUP_IDS.render(
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

            communities = [get_community_node_from_record(record) for record in records]
            logger.debug(f'已找到 {len(communities)} 个社区节点')
            return communities
        except Exception as e:
            logger.error(f'根据组ID获取社区节点时出错: {str(e)}')
            raise e


def get_community_node_from_record(record: Dict[str, Any]) -> CommunityNode:
    """
    从数据库记录创建社区节点对象
    
    Args:
        record: 数据库记录
        
    Returns:
        创建的社区节点对象
    """
    # 创建社区节点对象
    return CommunityNode(
        uuid=record['uuid'],
        name=record['name'],
        group_id=record['group_id'],
        name_embedding=record['name_embedding'],
        created_at=record['created_at'].to_native() if hasattr(record['created_at'], 'to_native') else record['created_at'],
        summary=record['summary'],
    ) 