"""
搜索主操作函数
提供与Neo4j数据库搜索的主要入口点
"""

from time import time
from typing import List

from knowledge_api.utils.log_config import get_logger
from knowledge_manage.embeddings.base import EmbeddingEngine
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.models.graphiti_types import GraphitiClients

from .entity_search_ops import edge_search, node_search
from .episode_search_ops import episode_search
from .community_search_ops import community_search
from ...models import SearchConfig
from ...models.search_models import SearchFilters, SearchResults

logger = get_logger()


async def _get_query_vector(embedder: EmbeddingEngine, query: str) -> List[float]:
    """
    获取查询向量，支持多种方法
    
    参数:
    ----
    embedder : EmbeddingEngine
        嵌入引擎
    query : str
        查询文本
        
    返回:
    ----
    List[float]
        查询向量
    """
    return await embedder.async_embed_query(query)


async def search(
    clients: GraphitiClients,
    query: str,
    group_ids: list[str] | None,
    config: SearchConfig,
    search_filter: SearchFilters,
    center_node_uuid: str | None = None,
    bfs_origin_node_uuids: list[str] | None = None,
    query_vector: list[float] | None = None,
) -> SearchResults:
    """
    执行综合搜索操作，包括节点、边、情节和社区
    
    参数:
    ----
    clients : GraphitiClients
        Neo4j客户端和相关服务的集合
    query : str
        搜索查询文本
    group_ids : list[str] | None
        要搜索的群组ID列表
    config : SearchConfig
        搜索配置
    search_filter : SearchFilters
        搜索过滤条件
    center_node_uuid : str | None, optional
        中心节点UUID，用于节点距离重排序
    bfs_origin_node_uuids : list[str] | None, optional
        广度优先搜索的起始节点UUID列表
    query_vector : list[float] | None, optional
        预计算的查询向量
        
    返回:
    ----
    SearchResults
        搜索结果，包含匹配的节点、边、情节和社区
    """
    start = time()

    driver = clients.driver
    embedder = clients.embedder
    cross_encoder = clients.cross_encoder

    if query.strip() == '':
        return SearchResults(
            edges=[],
            nodes=[],
            episodes=[],
            communities=[],
        )
    # 确保正确获取查询向量
    if query_vector is None:
        query_vector = await _get_query_vector(embedder, query)
        logger.info(f"成功为查询生成向量: '{query[:30]}...'")

    # if group_ids is empty, set it to None
    group_ids = group_ids if group_ids else None
    
    # 单独执行每个搜索函数，以避免处理复杂的返回值结构
    edges_result = await edge_search(
        clients,
        query,
        group_ids=group_ids,
        origin_node_uuids=bfs_origin_node_uuids,
        search_filter=search_filter,
        reordering_config=config.edge_reordering,
        limit=config.edge_limit,
    )
    
    nodes_result = await node_search(
        driver,
        cross_encoder,
        query,
        query_vector,
        group_ids,
        config.node_config,
        search_filter,
        center_node_uuid,
        bfs_origin_node_uuids,
        config.node_limit,
        config.reranker_min_score,
    )
    
    episodes_result = await episode_search(
        driver,
        cross_encoder,
        query,
        query_vector,
        group_ids,
        config.episode_config,
        search_filter,
        config.episode_limit,
        config.reranker_min_score,
    )
    
    communities_result = await community_search(
        driver,
        cross_encoder,
        query,
        query_vector,
        group_ids,
        config.community_config,
        config.community_limit,
        config.reranker_min_score,
    )

    # 从edge_search返回的SearchResults中获取edges
    edges = edges_result.edges
    
    results = SearchResults(
        edges=edges,
        nodes=nodes_result,
        episodes=episodes_result,
        communities=communities_result,
    )

    latency = (time() - start) * 1000

    logger.debug(f'search returned context for query {query} in {latency} ms')

    return results 