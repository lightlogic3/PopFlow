"""
节点搜索工具函数
提供各种节点搜索方法的实现
"""

import logging
from time import time
from typing import Any, Dict, List

from neo4j import AsyncDriver
from typing_extensions import LiteralString

from knowledge_api.utils.log_config import get_logger
from plugIns.memory_system.graphiti_memory.graphiti_core.config import DEFAULT_DATABASE, RUNTIME_QUERY
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.models.search_models import SearchFilters
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes import EntityNode, \
    get_entity_node_from_record
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.search.filters import \
    node_search_filter_query_constructor
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.search.utils.query_utils import fulltext_query
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.search.utils.rerankers import rrf
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.search.search_template import (
    NODE_FULLTEXT_SEARCH,
    NODE_SIMILARITY_SEARCH,
    NODE_BFS_SEARCH,
    GET_RELEVANT_NODES,
    GET_MENTIONED_NODES
)
from plugIns.memory_system.graphiti_memory.graphiti_core.utils.utils import semaphore_gather

logger = get_logger()

RELEVANT_SCHEMA_LIMIT = 10
DEFAULT_MIN_SCORE = 0.6


async def node_fulltext_search(
    driver: AsyncDriver,
    query: str,
    search_filter: SearchFilters,
    group_ids: List[str] | None = None,
    limit=RELEVANT_SCHEMA_LIMIT,
) -> List[EntityNode]:
    """
    使用全文搜索查询实体节点
    
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
    List[EntityNode]
        匹配的实体节点列表
    """
    # BM25搜索获取顶级节点
    fuzzy_query = fulltext_query(query, group_ids)
    if fuzzy_query == '':
        return []

    filter_query, filter_params = node_search_filter_query_constructor(search_filter)

    # 调试日志 - 打印查询和参数
    logger.info(f"节点全文搜索查询: fuzzy_query={fuzzy_query}, group_ids={group_ids}, limit={limit}")

    # 渲染Cypher查询模板
    cypher_query = NODE_FULLTEXT_SEARCH.render(
        filter_query=filter_query,
        group_ids=group_ids is not None,
        entity_node_return=""
    )
    
    # 创建参数字典，确保包含所有必需参数
    params = {
        "query": fuzzy_query,
        "limit": limit,
        **filter_params
    }
    
    if group_ids is not None:
        params["group_ids"] = group_ids
    
    # 调试日志 - 打印生成的Cypher查询
    logger.info(f"节点全文搜索Cypher查询: {cypher_query}")
    logger.info(f"查询参数: {params}")

    # 执行查询
    records, _, _ = await driver.execute_query(
        cypher_query,
        params,
        database_=DEFAULT_DATABASE,
        routing_='r',
    )

    nodes = [get_entity_node_from_record(record) for record in records]
    logger.info(f"节点全文搜索结果数量: {len(nodes)}")

    return nodes


async def node_similarity_search(
    driver: AsyncDriver,
    search_vector: List[float],
    search_filter: SearchFilters,
    group_ids: List[str] | None = None,
    limit=RELEVANT_SCHEMA_LIMIT,
    min_score: float = DEFAULT_MIN_SCORE,
) -> List[EntityNode]:
    """
    使用向量相似度搜索实体节点
    
    参数:
    ----
    driver : AsyncDriver
        Neo4j数据库驱动
    search_vector : List[float]
        搜索向量
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
    List[EntityNode]
        匹配的实体节点列表
    """
    # 调试日志 - 打印搜索参数
    logger.info(f"节点相似度搜索: search_vector长度={len(search_vector)}, min_score={min_score}, limit={limit}")
    if group_ids:
        logger.info(f"按群组过滤: {group_ids}")
    
    # 对嵌入式节点名称进行向量相似度搜索
    filter_query, filter_params = node_search_filter_query_constructor(search_filter)
    
    # 渲染Cypher查询模板
    cypher_query = NODE_SIMILARITY_SEARCH.render(
        runtime_query=RUNTIME_QUERY,
        group_ids=group_ids is not None,
        filter_query=filter_query.lstrip("AND ") if filter_query else None,
        entity_node_return=""
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
    
    # 调试日志 - 打印生成的Cypher查询
    logger.info(f"节点相似度搜索Cypher查询: {cypher_query}")
    logger.info(f"查询参数: {params}")
    
    # 执行查询
    records, _, _ = await driver.execute_query(
        cypher_query,
        params,
        database_=DEFAULT_DATABASE,
        routing_='r',
    )

    # 处理结果
    nodes = [get_entity_node_from_record(record) for record in records]
    
    # 添加查询分数到属性中
    for i, record in enumerate(records):
        if i < len(nodes) and hasattr(nodes[i], 'attributes'):
            if isinstance(nodes[i].attributes, dict) and 'score' in record:
                nodes[i].attributes['similarity_score'] = record['score']
    
    logger.info(f"节点相似度搜索结果数量: {len(nodes)}")

    return nodes


async def node_bfs_search(
    driver: AsyncDriver,
    bfs_origin_node_uuids: List[str] | None,
    search_filter: SearchFilters,
    bfs_max_depth: int,
    limit: int,
) -> List[EntityNode]:
    """
    使用广度优先搜索查询实体节点
    
    参数:
    ----
    driver : AsyncDriver
        Neo4j数据库驱动
    bfs_origin_node_uuids : List[str] | None
        BFS起始节点UUID列表
    search_filter : SearchFilters
        搜索过滤条件
    bfs_max_depth : int
        最大搜索深度
    limit : int
        返回结果数量限制
    
    返回:
    ----
    List[EntityNode]
        匹配的实体节点列表
    """
    # 对嵌入式节点名称进行向量相似度搜索
    if bfs_origin_node_uuids is None:
        return []
    
    # 调试日志 - 打印BFS搜索参数
    logger.info(f"节点BFS搜索: 起始节点数量={len(bfs_origin_node_uuids)}, 最大深度={bfs_max_depth}, 限制={limit}")

    filter_query, filter_params = node_search_filter_query_constructor(search_filter)
    
    # 渲染Cypher查询模板
    cypher_query = NODE_BFS_SEARCH.render(
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
    logger.info(f"节点BFS搜索Cypher查询: {cypher_query}")
    logger.info(f"查询参数: {params}")

    # 执行查询
    records, _, _ = await driver.execute_query(
        cypher_query,
        params,
        database_=DEFAULT_DATABASE,
        routing_='r',
    )

    nodes = [get_entity_node_from_record(record) for record in records]
    
    # 将距离信息添加到节点的属性中
    for i, record in enumerate(records):
        if i < len(nodes) and hasattr(nodes[i], 'attributes') and 'distance' in record:
            if isinstance(nodes[i].attributes, dict):
                nodes[i].attributes['distance'] = record['distance']
                nodes[i].attributes['search_method'] = 'bfs'

    logger.info(f"节点BFS搜索结果数量: {len(nodes)}")

    return nodes


async def hybrid_node_search(
    queries: List[str],
    embeddings: List[List[float]],
    driver: AsyncDriver,
    search_filter: SearchFilters,
    group_ids: List[str] | None = None,
    limit: int = RELEVANT_SCHEMA_LIMIT,
) -> List[EntityNode]:
    """
    使用混合搜索方法查找实体节点
    
    将全文搜索和向量相似度搜索结果结合起来，使用RRF重排序
    
    参数:
    ----
    queries : List[str]
        文本查询列表
    embeddings : List[List[float]]
        嵌入向量列表
    driver : AsyncDriver
        Neo4j数据库驱动
    search_filter : SearchFilters
        搜索过滤条件
    group_ids : List[str] | None, optional
        要过滤的组ID列表
    limit : int, optional
        返回结果数量限制
    
    返回:
    ----
    List[EntityNode]
        匹配的实体节点列表
    """
    start = time()
    logger.info(f"开始混合节点搜索: 查询数量={len(queries)}, 嵌入向量数量={len(embeddings)}")
    
    # 并行执行全文搜索和向量相似度搜索
    search_tasks = []
    
    # 全文搜索任务
    for q in queries:
        search_tasks.append(node_fulltext_search(driver, q, search_filter, group_ids, 2 * limit))
    
    # 相似度搜索任务
    for e in embeddings:
        search_tasks.append(node_similarity_search(driver, e, search_filter, group_ids, 2 * limit))
    
    # 并行执行所有搜索任务
    results: List[List[EntityNode]] = list(await semaphore_gather(*search_tasks))

    # 收集所有结果和UUID
    node_uuid_map: Dict[str, EntityNode] = {
        node.uuid: node for result in results for node in result
    }
    result_uuids = [[node.uuid for node in result] for result in results]

    # 使用RRF算法重排序
    ranked_uuids = rrf(result_uuids)

    # 按照排序顺序选择节点
    relevant_nodes: List[EntityNode] = [node_uuid_map[uuid] for uuid in ranked_uuids]

    end = time()
    logger.info(f"混合节点搜索完成: 耗时={(end - start) * 1000:.2f}ms, 找到{len(relevant_nodes)}个节点")
    return relevant_nodes


async def get_relevant_nodes(
    driver: AsyncDriver,
    nodes: List[EntityNode],
    search_filter: SearchFilters,
    min_score: float = DEFAULT_MIN_SCORE,
    limit: int = RELEVANT_SCHEMA_LIMIT,
) -> List[List[EntityNode]]:
    """
    获取与给定节点相关的节点
    
    参数:
    ----
    driver : AsyncDriver
        Neo4j数据库驱动
    nodes : List[EntityNode]
        要查找相关节点的节点列表
    search_filter : SearchFilters
        搜索过滤条件
    min_score : float, optional
        最小相似度分数阈值
    limit : int, optional
        每个节点返回的相关节点数量限制
    
    返回:
    ----
    List[List[EntityNode]]
        每个输入节点对应的相关节点列表
    """
    if len(nodes) == 0:
        return []
    
    group_id = nodes[0].group_id
    
    # 调试日志
    logger.info(f"获取相关节点: 输入节点数量={len(nodes)}, min_score={min_score}, limit={limit}")

    filter_query, filter_params = node_search_filter_query_constructor(search_filter)
    
    # 渲染Cypher查询模板
    cypher_query = GET_RELEVANT_NODES.render(
        runtime_query=RUNTIME_QUERY,
        filter_query=filter_query
    )
    
    # 准备节点查询数据
    query_nodes = [
        {
            'uuid': node.uuid,
            'name': node.name,
            'name_embedding': node.name_embedding,
            'fulltext_query': fulltext_query(node.name, [node.group_id]),
        }
        for node in nodes
    ]
    
    # 创建参数字典
    params = {
        "nodes": query_nodes,
        "group_id": group_id,
        "min_score": min_score,
        "limit": limit,
        **filter_params
    }
    
    # 调试日志
    logger.info(f"获取相关节点查询: {cypher_query}")
    logger.info(f"相关节点查询参数: {{ nodes: [{len(params['nodes'])} items], min_score: {min_score}, limit: {limit} }}")

    results, _, _ = await driver.execute_query(
        cypher_query,
        params,
        database_=DEFAULT_DATABASE,
        routing_='r',
    )
    
    relevant_nodes_dict: Dict[str, List[EntityNode]] = {
        result['search_node_uuid']: [
            get_entity_node_from_record(record) for record in result['matches']
        ]
        for result in results
    }

    relevant_nodes = [relevant_nodes_dict.get(node.uuid, []) for node in nodes]
    
    # 调试日志
    total_nodes = sum(len(node_list) for node_list in relevant_nodes)
    logger.info(f"获取相关节点结果: 返回{len(relevant_nodes)}个输入节点的相关节点，共{total_nodes}个节点")

    return relevant_nodes


async def get_mentioned_nodes(
    driver: AsyncDriver, episodes: List["EpisodicNode"]
) -> List[EntityNode]:
    """
    获取情节中提及的实体节点
    
    参数:
    ----
    driver : AsyncDriver
        Neo4j数据库驱动
    episodes : List["EpisodicNode"]
        情节节点列表
    
    返回:
    ----
    List[EntityNode]
        提及的实体节点列表
    """
    if not episodes:
        return []
        
    episode_uuids = [episode.uuid for episode in episodes]
    logger.info(f"获取情节提及的节点: 情节数量={len(episode_uuids)}")
    
    # 渲染Cypher查询模板
    cypher_query = GET_MENTIONED_NODES.render()
    
    # 执行查询
    records, _, _ = await driver.execute_query(
        cypher_query,
        {"episode_uuids": episode_uuids},
        database_=DEFAULT_DATABASE,
        routing_='r',
    )

    nodes = [get_entity_node_from_record(record) for record in records]
    logger.info(f"获取到{len(nodes)}个被提及的节点")

    return nodes 