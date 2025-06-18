"""
情节搜索工具函数
提供各种情节搜索方法的实现
"""

from typing import Dict, List

from neo4j import AsyncDriver

from knowledge_api.utils.log_config import get_logger
from plugIns.memory_system.graphiti_memory.graphiti_core.config import DEFAULT_DATABASE
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes import EpisodicNode, \
    get_episodic_node_from_record
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.search.utils.query_utils import fulltext_query
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.search.search_template import (
    EPISODE_FULLTEXT_SEARCH,
    GET_EPISODES_BY_ENTITY,
    GET_EPISODES_BY_MENTIONS
)

logger = get_logger()

RELEVANT_SCHEMA_LIMIT = 10
DEFAULT_MIN_SCORE = 0.6


async def episode_fulltext_search(
    driver: AsyncDriver,
    query: str,
    search_filter,
    group_ids: List[str] | None = None,
    limit=RELEVANT_SCHEMA_LIMIT,
) -> List[EpisodicNode]:
    """
    使用全文搜索查询情节节点
    
    参数:
    ----
    driver : AsyncDriver
        Neo4j数据库驱动
    query : str
        搜索查询字符串
    search_filter : SearchFilters
        搜索过滤条件
    group_ids : List[str] | None, optional
        要过滤的组ID列表
    limit : int, optional
        返回结果数量限制
    
    返回:
    ----
    List[EpisodicNode]
        匹配的情节节点列表
    """
    # BM25搜索获取顶级情节
    fuzzy_query = fulltext_query(query, group_ids)
    if fuzzy_query == '':
        return []

    # 调试日志 - 打印查询和参数
    logger.info(f"情节全文搜索查询: fuzzy_query={fuzzy_query}, group_ids={group_ids}, limit={limit}")

    # 渲染Cypher查询模板
    cypher_query = EPISODE_FULLTEXT_SEARCH.render(
        group_ids=group_ids is not None,
        filter_query=None
    )
    
    # 创建参数字典，确保包含所有必需参数
    params = {
        "query": fuzzy_query,
        "limit": limit
    }
    
    if group_ids is not None:
        params["group_ids"] = group_ids
    
    # 调试日志 - 打印生成的Cypher查询
    logger.info(f"情节全文搜索Cypher查询: {cypher_query}")
    logger.info(f"查询参数: {params}")

    # 执行查询
    records, _, _ = await driver.execute_query(
        cypher_query,
        params,
        database_=DEFAULT_DATABASE,
        routing_='r',
    )

    episodes = [get_episodic_node_from_record(record) for record in records]
    logger.info(f"情节全文搜索结果数量: {len(episodes)}")

    return episodes


async def get_episodes_by_entity(
    driver: AsyncDriver,
    entity_node_uuid: str,
    limit: int = RELEVANT_SCHEMA_LIMIT
) -> List[EpisodicNode]:
    """
    获取与实体节点相关的情节
    
    参数:
    ----
    driver : AsyncDriver
        Neo4j数据库驱动
    entity_node_uuid : str
        实体节点UUID
    limit : int, optional
        返回结果数量限制
    
    返回:
    ----
    List[EpisodicNode]
        与实体节点相关的情节列表
    """
    # 调试日志
    logger.info(f"获取与实体相关的情节: entity_node_uuid={entity_node_uuid}, limit={limit}")
    
    # 渲染Cypher查询模板
    cypher_query = GET_EPISODES_BY_ENTITY.render()
    
    # 创建参数字典
    params = {
        "entity_node_uuid": entity_node_uuid,
        "limit": limit
    }
    
    # 调试日志 - 打印生成的Cypher查询
    logger.info(f"获取与实体相关的情节查询: {cypher_query}")
    
    # 执行查询
    records, _, _ = await driver.execute_query(
        cypher_query,
        params,
        database_=DEFAULT_DATABASE,
        routing_='r',
    )
    
    episodes = [get_episodic_node_from_record(record) for record in records]
    logger.info(f"获取与实体相关的情节结果数量: {len(episodes)}")
    
    return episodes


async def get_episodes_by_mentions(
    driver: AsyncDriver,
    edge_uuids: List[str],
    limit: int = RELEVANT_SCHEMA_LIMIT
) -> List[EpisodicNode]:
    """
    获取由边提及的情节
    
    参数:
    ----
    driver : AsyncDriver
        Neo4j数据库驱动
    edge_uuids : List[str]
        边UUID列表
    limit : int, optional
        返回结果数量限制
    
    返回:
    ----
    List[EpisodicNode]
        由边提及的情节列表
    """
    if not edge_uuids:
        return []
        
    # 调试日志
    logger.info(f"获取由边提及的情节: edge_uuids数量={len(edge_uuids)}, limit={limit}")
    
    # 渲染Cypher查询模板
    cypher_query = GET_EPISODES_BY_MENTIONS.render()
    
    # 创建参数字典
    params = {
        "edge_uuids": edge_uuids,
        "limit": limit
    }
    
    # 调试日志 - 打印生成的Cypher查询
    logger.info(f"获取由边提及的情节查询: {cypher_query}")
    
    # 执行查询
    records, _, _ = await driver.execute_query(
        cypher_query,
        params,
        database_=DEFAULT_DATABASE,
        routing_='r',
    )
    
    episodes = [get_episodic_node_from_record(record) for record in records]
    logger.info(f"获取由边提及的情节结果数量: {len(episodes)}")
    
    return episodes 