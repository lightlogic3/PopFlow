"""
边搜索工具函数
提供各种边搜索方法的实现
"""

from typing import Dict, List

from neo4j import AsyncDriver

from knowledge_api.utils.log_config import get_logger
from plugIns.memory_system.graphiti_memory.graphiti_core.config import RUNTIME_QUERY, DEFAULT_DATABASE
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.edges import get_entity_edge_from_record, \
    EntityEdge
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.models.search_models import SearchFilters
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.search.filters import \
    edge_search_filter_query_constructor
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.search.utils.query_utils import fulltext_query
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.search.search_template import (
    EDGE_FULLTEXT_SEARCH,
    EDGE_SIMILARITY_SEARCH,
    EDGE_BFS_SEARCH,
    GET_RELEVANT_EDGES,
    GET_EDGE_INVALIDATION_CANDIDATES
)

logger = get_logger()

RELEVANT_SCHEMA_LIMIT = 10
DEFAULT_MIN_SCORE = 0.6


async def edge_fulltext_search(
    driver: AsyncDriver,
    query: str,
    search_filter: SearchFilters,
    group_ids: List[str] | None = None,
    limit=RELEVANT_SCHEMA_LIMIT,
) -> List[EntityEdge]:
    """
    使用全文搜索查询实体边
    
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
    List[EntityEdge]
        匹配的实体边列表
    """
    # 对事实进行全文搜索
    fuzzy_query = fulltext_query(query, group_ids)
    if fuzzy_query == '':
        return []

    filter_query, filter_params = edge_search_filter_query_constructor(search_filter)

    # 调试日志 - 打印查询和参数
    logger.info(f"全文搜索查询: fuzzy_query={fuzzy_query}, group_ids={group_ids}, limit={limit}")

    # 渲染Cypher查询模板
    cypher_query = EDGE_FULLTEXT_SEARCH.render(filter_query=filter_query)
    
    # 创建参数字典，确保包含所有必需参数
    params = {
        "query": fuzzy_query,
        "group_ids": group_ids,
        "limit": limit,
        **filter_params
    }
    
    # 调试日志 - 打印生成的Cypher查询
    logger.info(f"全文搜索Cypher查询: {cypher_query}")
    logger.info(f"查询参数: {params}")

    # 执行查询，直接传递参数而不是Query对象
    records, _, _ = await driver.execute_query(
        cypher_query,
        params,
        database_=DEFAULT_DATABASE,
        routing_='r',
    )

    edges = [get_entity_edge_from_record(record) for record in records]
    logger.info(f"全文搜索结果数量: {len(edges)}")

    return edges


async def edge_similarity_search(
    driver: AsyncDriver,
    search_vector: List[float],
    source_node_uuid: str | None,
    target_node_uuid: str | None,
    search_filter: SearchFilters,
    group_ids: List[str] | None = None,
    limit: int = RELEVANT_SCHEMA_LIMIT,
    min_score: float = DEFAULT_MIN_SCORE,
) -> List[EntityEdge]:
    """
    使用向量相似度搜索实体边
    
    参数:
    ----
    driver : AsyncDriver
        Neo4j数据库驱动
    search_vector : List[float]
        搜索向量
    source_node_uuid : str | None
        源节点UUID，如果指定则限制搜索范围
    target_node_uuid : str | None
        目标节点UUID，如果指定则限制搜索范围
    search_filter : SearchFilters
        搜索过滤条件
    group_ids : List[str] | None, optional
        要过滤的组ID列表
    limit : int, optional
        返回结果数量限制
    min_score : float, optional
        最小相似度分数阈值
    
    返回:
    ----
    List[EntityEdge]
        匹配的实体边列表
    """
    # 调试日志 - 打印搜索参数
    logger.info(f"相似度搜索: search_vector长度={len(search_vector)}, min_score={min_score}, limit={limit}")
    if group_ids:
        logger.info(f"按群组过滤: {group_ids}")
    if source_node_uuid or target_node_uuid:
        logger.info(f"按节点过滤: source={source_node_uuid}, target={target_node_uuid}")
    
    # 对嵌入式事实进行向量相似度搜索
    filter_query, filter_params = edge_search_filter_query_constructor(search_filter)
    
    # 构建过滤条件
    group_filter = None
    if group_ids is not None:
        group_filter = "r.group_id IN $group_ids"
        
    # 添加源节点和目标节点过滤条件
    node_filter = None
    if source_node_uuid is not None or target_node_uuid is not None:
        node_conditions = []
        if source_node_uuid is not None:
            node_conditions.append("n.uuid IN $node_uuids")
        if target_node_uuid is not None:
            node_conditions.append("m.uuid IN $node_uuids")
        node_filter = f"({' OR '.join(node_conditions)})"
    
    # 渲染Cypher查询模板
    cypher_query = EDGE_SIMILARITY_SEARCH.render(
        runtime_query=RUNTIME_QUERY,
        group_filter=group_filter,
        node_filter=node_filter,
        filter_query=filter_query.lstrip("AND ") if filter_query else None
    )
    
    # 创建参数字典
    params = {
        "search_vector": search_vector,
        "min_score": min_score,
        "limit": limit,
        **filter_params
    }
    
    if group_ids is not None:
        params["group_ids"] = group_ids
    
    if source_node_uuid is not None or target_node_uuid is not None:
        node_uuids = []
        if source_node_uuid:
            node_uuids.append(source_node_uuid)
        if target_node_uuid:
            node_uuids.append(target_node_uuid)
        params["node_uuids"] = node_uuids
    
    # 调试日志 - 打印生成的Cypher查询
    logger.info(f"相似度搜索Cypher查询: {cypher_query}")
    logger.info(f"查询参数: {params}")
    
    # 执行查询
    records, _, _ = await driver.execute_query(
        cypher_query,
        params,
        database_=DEFAULT_DATABASE,
        routing_='r',
    )

    # 处理结果
    edges = [get_entity_edge_from_record(record) for record in records]
    
    # 添加查询分数到属性中
    for i, record in enumerate(records):
        if i < len(edges) and hasattr(edges[i], 'attributes'):
            if isinstance(edges[i].attributes, dict) and 'score' in record:
                edges[i].attributes['similarity_score'] = record['score']
    
    logger.info(f"相似度搜索结果数量: {len(edges)}")

    return edges


async def edge_bfs_search(
    driver: AsyncDriver,
    bfs_origin_node_uuids: List[str] | None,
    bfs_max_depth: int,
    search_filter: SearchFilters,
    limit: int,
) -> List[EntityEdge]:
    """
    使用广度优先搜索查询实体边
    
    参数:
    ----
    driver : AsyncDriver
        Neo4j数据库驱动
    bfs_origin_node_uuids : List[str] | None
        BFS起始节点UUID列表
    bfs_max_depth : int
        最大搜索深度
    search_filter : SearchFilters
        搜索过滤条件
    limit : int
        返回结果数量限制
    
    返回:
    ----
    List[EntityEdge]
        匹配的实体边列表
    """
    # 对嵌入式事实进行向量相似度搜索
    if bfs_origin_node_uuids is None:
        return []
    
    # 调试日志 - 打印BFS搜索参数
    logger.info(f"BFS搜索: 起始节点数量={len(bfs_origin_node_uuids)}, 最大深度={bfs_max_depth}, 限制={limit}")

    filter_query, filter_params = edge_search_filter_query_constructor(search_filter)
    
    # 渲染Cypher查询模板
    cypher_query = EDGE_BFS_SEARCH.render(
        max_depth=bfs_max_depth,
        filter_query=filter_query
    )
    
    # 创建参数字典
    params = {
        "bfs_origin_node_uuids": bfs_origin_node_uuids,
        "limit": limit,
        **filter_params
    }
    
    # 调试日志 - 打印生成的Cypher查询
    logger.info(f"BFS搜索Cypher查询: {cypher_query}")
    logger.info(f"查询参数: {params}")

    # 执行查询
    records, _, _ = await driver.execute_query(
        cypher_query,
        params,
        database_=DEFAULT_DATABASE,
        routing_='r',
    )

    edges = [get_entity_edge_from_record(record) for record in records]
    
    # 将距离信息添加到边的属性中
    for i, record in enumerate(records):
        if i < len(edges) and hasattr(edges[i], 'attributes') and 'distance' in record:
            if isinstance(edges[i].attributes, dict):
                edges[i].attributes['distance'] = record['distance']
                edges[i].attributes['search_method'] = 'bfs'

    logger.info(f"BFS搜索结果数量: {len(edges)}")

    return edges


async def get_relevant_edges(
    driver: AsyncDriver,
    edges: List[EntityEdge],
    search_filter: SearchFilters,
    min_score: float = DEFAULT_MIN_SCORE,
    limit: int = RELEVANT_SCHEMA_LIMIT,
) -> List[List[EntityEdge]]:
    """
    获取与给定边相关的边
    
    参数:
    ----
    driver : AsyncDriver
        Neo4j数据库驱动
    edges : List[EntityEdge]
        要查找相关边的边列表
    search_filter : SearchFilters
        搜索过滤条件
    min_score : float, optional
        最小相似度分数阈值
    limit : int, optional
        每个边返回的相关边数量限制
    
    返回:
    ----
    List[List[EntityEdge]]
        每个输入边对应的相关边列表
    """
    if len(edges) == 0:
        return []
    
    # 调试日志
    logger.info(f"获取相关边: 输入边数量={len(edges)}, min_score={min_score}, limit={limit}")

    filter_query, filter_params = edge_search_filter_query_constructor(search_filter)
    
    # 渲染Cypher查询模板
    cypher_query = GET_RELEVANT_EDGES.render(
        runtime_query=RUNTIME_QUERY,
        filter_query=filter_query
    )
    
    # 创建参数字典
    params = {
        "edges": [edge.model_dump() for edge in edges],
        "min_score": min_score,
        "limit": limit,
        **filter_params
    }
    
    # 调试日志
    logger.info(f"获取相关边查询: {cypher_query}")
    logger.info(f"相关边查询参数: {{ edges: [{len(params['edges'])} items], min_score: {min_score}, limit: {limit} }}")

    results, _, _ = await driver.execute_query(
        cypher_query,
        params,
        database_=DEFAULT_DATABASE,
        routing_='r',
    )
    
    relevant_edges_dict: Dict[str, List[EntityEdge]] = {
        result['search_edge_uuid']: [
            get_entity_edge_from_record(record) for record in result['matches']
        ]
        for result in results
    }

    relevant_edges = [relevant_edges_dict.get(edge.uuid, []) for edge in edges]
    
    # 调试日志
    total_edges = sum(len(edge_list) for edge_list in relevant_edges)
    logger.info(f"获取相关边结果: 返回{len(relevant_edges)}个输入边的相关边，共{total_edges}个边")

    return relevant_edges


async def get_edge_invalidation_candidates(
    driver: AsyncDriver,
    edges: List[EntityEdge],
    search_filter: SearchFilters,
    min_score: float = DEFAULT_MIN_SCORE,
    limit: int = RELEVANT_SCHEMA_LIMIT,
) -> List[List[EntityEdge]]:
    """
    获取可能与给定边冲突的边（可能导致该边失效的边）
    
    参数:
    ----
    driver : AsyncDriver
        Neo4j数据库驱动
    edges : List[EntityEdge]
        要查找可能冲突边的边列表
    search_filter : SearchFilters
        搜索过滤条件
    min_score : float, optional
        最小相似度分数阈值
    limit : int, optional
        每个边返回的候选边数量限制
    
    返回:
    ----
    List[List[EntityEdge]]
        每个输入边对应的可能冲突边列表
    """
    if len(edges) == 0:
        return []

    # 调试日志
    logger.info(f"获取边失效候选: 输入边数量={len(edges)}, min_score={min_score}, limit={limit}")

    filter_query, filter_params = edge_search_filter_query_constructor(search_filter)
    
    # 渲染Cypher查询模板
    cypher_query = GET_EDGE_INVALIDATION_CANDIDATES.render(
        runtime_query=RUNTIME_QUERY,
        filter_query=filter_query
    )
    
    # 创建参数字典
    params = {
        "edges": [edge.model_dump() for edge in edges],
        "min_score": min_score,
        "limit": limit,
        **filter_params
    }
    
    # 调试日志
    logger.info(f"获取边失效候选查询: {cypher_query}")
    logger.info(f"边失效候选查询参数: {{ edges: [{len(params['edges'])} items], min_score: {min_score}, limit: {limit} }}")

    results, _, _ = await driver.execute_query(
        cypher_query,
        params,
        database_=DEFAULT_DATABASE,
        routing_='r',
    )
    
    invalidation_edges_dict: Dict[str, List[EntityEdge]] = {
        result['search_edge_uuid']: [
            get_entity_edge_from_record(record) for record in result['matches']
        ]
        for result in results
    }

    invalidation_edges = [invalidation_edges_dict.get(edge.uuid, []) for edge in edges]
    
    # 调试日志
    total_candidates = sum(len(edge_list) for edge_list in invalidation_edges)
    logger.info(f"获取边失效候选结果: 返回{len(invalidation_edges)}个输入边的冲突候选，共{total_candidates}个候选")

    return invalidation_edges 