"""
社区搜索工具函数
提供各种社区搜索方法的实现
"""

from typing import Dict, List

from neo4j import AsyncDriver

from knowledge_api.utils.log_config import get_logger
from plugIns.memory_system.graphiti_memory.graphiti_core.config import DEFAULT_DATABASE, RUNTIME_QUERY
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes import CommunityNode, \
    get_community_node_from_record
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.search.utils.query_utils import fulltext_query
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.search.search_template import (
    COMMUNITY_FULLTEXT_SEARCH,
    COMMUNITY_SIMILARITY_SEARCH,
    GET_COMMUNITY_MEMBERS,
    GET_COMMUNITIES_BY_NODE
)

logger = get_logger()

RELEVANT_SCHEMA_LIMIT = 10
DEFAULT_MIN_SCORE = 0.6


async def community_fulltext_search(
    driver: AsyncDriver,
    query: str,
    group_ids: List[str] | None = None,
    limit=RELEVANT_SCHEMA_LIMIT,
) -> List[CommunityNode]:
    """
    使用全文搜索查询社区节点
    
    参数:
    ----
    driver : AsyncDriver
        Neo4j数据库驱动
    query : str
        搜索查询字符串
    group_ids : List[str] | None, optional
        要过滤的组ID列表
    limit : int, optional
        返回结果数量限制
    
    返回:
    ----
    List[CommunityNode]
        匹配的社区节点列表
    """
    # BM25搜索获取顶级社区
    fuzzy_query = fulltext_query(query, group_ids)
    if fuzzy_query == '':
        return []

    # 调试日志 - 打印查询和参数
    logger.info(f"社区全文搜索查询: fuzzy_query={fuzzy_query}, group_ids={group_ids}, limit={limit}")

    # 渲染Cypher查询模板
    cypher_query = COMMUNITY_FULLTEXT_SEARCH.render(
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
    logger.info(f"社区全文搜索Cypher查询: {cypher_query}")
    logger.info(f"查询参数: {params}")

    # 执行查询
    records, _, _ = await driver.execute_query(
        cypher_query,
        params,
        database_=DEFAULT_DATABASE,
        routing_='r',
    )

    communities = [get_community_node_from_record(record) for record in records]
    logger.info(f"社区全文搜索结果数量: {len(communities)}")

    return communities


async def community_similarity_search(
    driver: AsyncDriver,
    search_vector: List[float],
    group_ids: List[str] | None = None,
    limit=RELEVANT_SCHEMA_LIMIT,
    min_score=DEFAULT_MIN_SCORE,
) -> List[CommunityNode]:
    """
    使用向量相似度搜索社区节点
    
    参数:
    ----
    driver : AsyncDriver
        Neo4j数据库驱动
    search_vector : List[float]
        搜索向量
    group_ids : List[str] | None, optional
        要过滤的组ID列表
    limit : int, optional
        返回结果数量限制
    min_score : float, optional
        最小相似度分数阈值
    
    返回:
    ----
    List[CommunityNode]
        匹配的社区节点列表
    """
    # 调试日志 - 打印搜索参数
    logger.info(f"社区相似度搜索: search_vector长度={len(search_vector)}, min_score={min_score}, limit={limit}")
    if group_ids:
        logger.info(f"按群组过滤: {group_ids}")
    
    # 渲染Cypher查询模板
    cypher_query = COMMUNITY_SIMILARITY_SEARCH.render(
        runtime_query=RUNTIME_QUERY,
        group_ids=group_ids is not None,
        filter_query=None
    )
    
    # 创建参数字典
    params = {
        "search_vector": search_vector,
        "min_score": min_score,
        "limit": limit
    }
    
    if group_ids is not None:
        params["group_ids"] = group_ids
    
    # 调试日志 - 打印生成的Cypher查询
    logger.info(f"社区相似度搜索Cypher查询: {cypher_query}")
    logger.info(f"查询参数: {params}")
    
    # 执行查询
    records, _, _ = await driver.execute_query(
        cypher_query,
        params,
        database_=DEFAULT_DATABASE,
        routing_='r',
    )

    # 处理结果
    communities = [get_community_node_from_record(record) for record in records]
    
    # 添加查询分数到属性中
    for i, record in enumerate(records):
        if i < len(communities) and hasattr(communities[i], 'attributes'):
            if isinstance(communities[i].attributes, dict) and 'score' in record:
                communities[i].attributes['similarity_score'] = record['score']
    
    logger.info(f"社区相似度搜索结果数量: {len(communities)}")

    return communities


async def get_community_members(
    driver: AsyncDriver,
    community_uuid: str,
    limit: int = RELEVANT_SCHEMA_LIMIT
) -> List[Dict[str, any]]:
    """
    获取社区成员节点
    
    参数:
    ----
    driver : AsyncDriver
        Neo4j数据库驱动
    community_uuid : str
        社区节点UUID
    limit : int, optional
        返回结果数量限制
    
    返回:
    ----
    List[Dict[str, any]]
        社区成员节点列表
    """
    # 调试日志
    logger.info(f"获取社区成员: community_uuid={community_uuid}, limit={limit}")
    
    # 渲染Cypher查询模板
    cypher_query = GET_COMMUNITY_MEMBERS.render()
    
    # 创建参数字典
    params = {
        "community_uuid": community_uuid,
        "limit": limit
    }
    
    # 调试日志 - 打印生成的Cypher查询
    logger.info(f"获取社区成员查询: {cypher_query}")
    
    # 执行查询
    records, _, _ = await driver.execute_query(
        cypher_query,
        params,
        database_=DEFAULT_DATABASE,
        routing_='r',
    )
    
    # 返回原始记录结果
    return [dict(record) for record in records]


async def get_communities_by_node(
    driver: AsyncDriver,
    node_uuid: str,
    limit: int = RELEVANT_SCHEMA_LIMIT
) -> List[CommunityNode]:
    """
    获取节点所属的社区
    
    参数:
    ----
    driver : AsyncDriver
        Neo4j数据库驱动
    node_uuid : str
        节点UUID
    limit : int, optional
        返回结果数量限制
    
    返回:
    ----
    List[CommunityNode]
        社区节点列表
    """
    # 调试日志
    logger.info(f"获取节点所属社区: node_uuid={node_uuid}, limit={limit}")
    
    # 渲染Cypher查询模板
    cypher_query = GET_COMMUNITIES_BY_NODE.render()
    
    # 创建参数字典
    params = {
        "node_uuid": node_uuid,
        "limit": limit
    }
    
    # 调试日志 - 打印生成的Cypher查询
    logger.info(f"获取节点所属社区查询: {cypher_query}")
    
    # 执行查询
    records, _, _ = await driver.execute_query(
        cypher_query,
        params,
        database_=DEFAULT_DATABASE,
        routing_='r',
    )
    
    communities = [get_community_node_from_record(record) for record in records]
    logger.info(f"获取节点所属社区结果数量: {len(communities)}")
    
    return communities 