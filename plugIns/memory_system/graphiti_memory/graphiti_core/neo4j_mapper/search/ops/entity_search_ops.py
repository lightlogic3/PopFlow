"""
实体搜索操作函数
提供与Neo4j数据库中实体(节点和边)搜索相关的操作
"""

import asyncio
from time import time
from typing import Optional

from neo4j import AsyncDriver

from knowledge_api.utils.log_config import get_logger
from knowledge_manage.rerank_model import BaseRankingModel
from plugIns.memory_system.graphiti_memory.graphiti_core.errors import SearchRerankerError
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.models.graphiti_types import GraphitiClients
from plugIns.memory_system.graphiti_memory.graphiti_core.utils.utils import semaphore_gather

from .reranking_ops import apply_cross_encoder_reordering, apply_mmr_reordering, apply_rrf_reordering
from ..utils import node_fulltext_search, node_similarity_search, node_bfs_search, rrf, get_embeddings_for_nodes, \
    maximal_marginal_relevance, edge_fulltext_search, edge_similarity_search, edge_bfs_search
from ..utils.rerankers import episode_mentions_reranker, node_distance_reranker
from plugIns.memory_system.graphiti_memory.graphiti_core.config import DEFAULT_SEARCH_LIMIT, MAX_SEARCH_DEPTH
from ...edges import EntityEdge
from ...models import NodeSearchConfig
from ...models.search_models import SearchFilters, NodeSearchMethod, NodeReranker, SearchResults
from ...nodes import EntityNode

logger = get_logger()


async def node_search(
    driver: AsyncDriver,
    cross_encoder: BaseRankingModel,
    query: str,
    query_vector: list[float],
    group_ids: list[str] | None,
    config: NodeSearchConfig | None,
    search_filter: SearchFilters,
    center_node_uuid: str | None = None,
    bfs_origin_node_uuids: list[str] | None = None,
    limit=DEFAULT_SEARCH_LIMIT,
    reranker_min_score: float = 0,
) -> list[EntityNode]:
    """
    搜索与查询相关的节点
    
    参数:
    ----
    driver : AsyncDriver
        Neo4j数据库驱动
    cross_encoder : BaseRankingModel
        跨编码器模型，用于重排序
    query : str
        搜索查询文本
    query_vector : list[float]
        查询向量
    group_ids : list[str] | None
        要搜索的群组ID列表
    config : NodeSearchConfig | None
        节点搜索配置
    search_filter : SearchFilters
        搜索过滤条件
    center_node_uuid : str | None, optional
        中心节点UUID，用于节点距离重排序
    bfs_origin_node_uuids : list[str] | None, optional
        广度优先搜索的起始节点UUID列表
    limit : int, optional
        结果数量限制
    reranker_min_score : float, optional
        重排序最小分数阈值
        
    返回:
    ----
    list[EntityNode]
        匹配的实体节点列表
    """
    if config is None:
        return []

    search_results: list[list[EntityNode]] = list(
        await semaphore_gather(
            *[
                node_fulltext_search(driver, query, search_filter, group_ids, 2 * limit),
                node_similarity_search(
                    driver, query_vector, search_filter, group_ids, 2 * limit, config.sim_min_score
                ),
                node_bfs_search(
                    driver, bfs_origin_node_uuids, search_filter, config.bfs_max_depth, 2 * limit
                ),
            ]
        )
    )

    if NodeSearchMethod.bfs in config.search_methods and bfs_origin_node_uuids is None:
        origin_node_uuids = [node.uuid for result in search_results for node in result]
        search_results.append(
            await node_bfs_search(
                driver, origin_node_uuids, search_filter, config.bfs_max_depth, 2 * limit
            )
        )

    search_result_uuids = [[node.uuid for node in result] for result in search_results]
    node_uuid_map = {node.uuid: node for result in search_results for node in result}

    reranked_uuids: list[str] = []
    if config.reranker == NodeReranker.rrf:
        reranked_uuids = rrf(search_result_uuids, min_score=reranker_min_score)
    elif config.reranker == NodeReranker.mmr:
        search_result_uuids_and_vectors = await get_embeddings_for_nodes(
            driver, list(node_uuid_map.values())
        )

        reranked_uuids = maximal_marginal_relevance(
            query_vector,
            search_result_uuids_and_vectors,
            config.mmr_lambda,
            reranker_min_score,
        )
    elif config.reranker == NodeReranker.cross_encoder:
        name_to_uuid_map = {node.name: node.uuid for node in list(node_uuid_map.values())}

        reranked_node_names = await cross_encoder.async_rank(query, list(name_to_uuid_map.keys()))
        reranked_uuids = [
            name_to_uuid_map[name]
            for name, score in reranked_node_names
            if score >= reranker_min_score
        ]
    elif config.reranker == NodeReranker.episode_mentions:
        reranked_uuids = await episode_mentions_reranker(
            driver, search_result_uuids, min_score=reranker_min_score
        )
    elif config.reranker == NodeReranker.node_distance:
        if center_node_uuid is None:
            raise SearchRerankerError('No center node provided for Node Distance reranker')
        reranked_uuids = await node_distance_reranker(
            driver,
            rrf(search_result_uuids, min_score=reranker_min_score),
            center_node_uuid,
            min_score=reranker_min_score,
        )

    reranked_nodes = [node_uuid_map[uuid] for uuid in reranked_uuids]

    return reranked_nodes[:limit]


async def edge_search(
    clients: GraphitiClients,
    query: str,
    group_ids: Optional[list[str]] = None,
    origin_node_uuids: Optional[list[str]] = None,
    target_type_names: Optional[list[str]] = None,
    search_filter: Optional[SearchFilters] = None,
    reordering_config: Optional[dict] = None,
    limit: int = 10,
) -> SearchResults:
    """
    搜索图数据库中与查询相关的边，边可以表示实体之间的关系或事实

    参数:
    ----
    clients : GraphitiClients
        客户端集合
    query : str
        搜索查询
    group_ids : Optional[list[str]], optional
        限制搜索的群组ID列表
    origin_node_uuids : Optional[list[str]], optional
        源节点UUID列表，用于限制边的起点
    target_type_names : Optional[list[str]], optional
        目标节点类型名称列表
    search_filter : Optional[SearchFilters], optional
        搜索过滤器
    reordering_config : Optional[dict], optional
        重排序配置
    limit : int, optional
        结果数量限制

    返回:
    ----
    SearchResults
        搜索结果，包含匹配的边
    """
    start_time = time()
    logger.info(f"开始边搜索 - 查询: '{query[:50]}...', 限制: {limit}, 源节点: {len(origin_node_uuids) if origin_node_uuids else 0}个")

    # 增加初始搜索结果限制，以便获取更多候选项进行重排序,为限制的倍数
    search_limit_multiplier = 3
    initial_limit = limit * search_limit_multiplier
    logger.info(f"使用初始搜索限制: {initial_limit} (= {limit} * {search_limit_multiplier})")

    # 设置更严格的最小相似度阈值
    min_score = 0.65  # 增加阈值以确保更高质量的匹配
    
    # 确保search_filter不为None
    if search_filter is None:
        search_filter = SearchFilters()
    
    # 执行搜索
    tasks = []
    
    # 全文搜索
    tasks.append(
        edge_fulltext_search(
            clients.driver,
            query,
            search_filter,
            group_ids=group_ids,
            limit=initial_limit,
        )
    )
    
    # 准备查询向量进行相似度搜索
    query_vector = None
    if clients.embedder:
        try:
            query_vector = await clients.embedder.async_embed_query(query)
        except Exception as e:
            logger.error(f"嵌入查询时出错: {e}")
    
    # 向量相似度搜索
    if query_vector:
        tasks.append(
            edge_similarity_search(
                clients.driver,
                query_vector,
                None,  # 这里不限制源节点，以获取更广泛的结果
                None,  # 这里不限制目标节点，以获取更广泛的结果
                search_filter,
                group_ids=group_ids,
                limit=initial_limit,
                min_score=min_score
            )
        )
    
    # BFS搜索
    bfs_results = []
    if origin_node_uuids:
        tasks.append(
            edge_bfs_search(
                clients.driver,
                origin_node_uuids,
                MAX_SEARCH_DEPTH,
                search_filter,
                initial_limit,
            )
        )
    
    # 同时执行所有搜索任务
    fulltext_results, similarity_results, *bfs_results = await asyncio.gather(*tasks)
    
    # 记录各种搜索结果的数量
    logger.info(f"搜索结果统计 - 全文: {len(fulltext_results)}, 向量相似度: {len(similarity_results)}, BFS: {len(bfs_results[0]) if bfs_results else 0}")
    
    # 如果没有源节点但有匹配的结果，可以提取节点用于BFS搜索
    if not origin_node_uuids and (fulltext_results or similarity_results):
        # 从现有结果中提取唯一的节点UUID
        node_uuids = set()
        for result in fulltext_results + similarity_results:
            if hasattr(result, 'source_node_uuid') and result.source_node_uuid:
                node_uuids.add(result.source_node_uuid)
            if hasattr(result, 'target_node_uuid') and result.target_node_uuid:
                node_uuids.add(result.target_node_uuid)
        
        # 对提取的节点执行BFS搜索
        if node_uuids:
            logger.info(f"从初始结果中提取了{len(node_uuids)}个节点，执行BFS扩展搜索")
            bfs_results_extra = await edge_bfs_search(
                clients.driver,
                list(node_uuids),
                MAX_SEARCH_DEPTH,
                search_filter,
                initial_limit,
            )
            if bfs_results:
                bfs_results[0].extend(bfs_results_extra)
            else:
                bfs_results = [bfs_results_extra]
            logger.info(f"BFS扩展搜索结果: {len(bfs_results_extra)}")
    
    # 聚合所有搜索结果
    all_results = fulltext_results + similarity_results
    if bfs_results:
        all_results.extend(bfs_results[0])

    # 为每个边添加来源元数据，方便后续分析
    for edge in fulltext_results:
        if hasattr(edge, 'attributes') and isinstance(edge.attributes, dict):
            edge.attributes["search_method"] = "fulltext"
    
    for edge in similarity_results:
        if hasattr(edge, 'attributes') and isinstance(edge.attributes, dict):
            edge.attributes["search_method"] = "similarity"
            edge.attributes["similarity_score"] = getattr(edge, "score", 0)
    
    if bfs_results:
        for edge in bfs_results[0]:
            if hasattr(edge, 'attributes') and isinstance(edge.attributes, dict):
                edge.attributes["search_method"] = "bfs"
                edge.attributes["distance"] = getattr(edge, "distance", 1)
    
    # 对结果进行去重，按照UUID聚合相同的边
    edges_by_uuid = {}
    for edge in all_results:
        if edge.uuid not in edges_by_uuid:
            edges_by_uuid[edge.uuid] = edge
        else:
            # 合并来自不同来源的同一个边的信息
            existing_edge = edges_by_uuid[edge.uuid]
            if hasattr(edge, 'attributes') and hasattr(existing_edge, 'attributes'):
                # 如果两个边都来自不同的搜索方法，合并attributes信息
                existing_edge.attributes["multiple_sources"] = True
                # 将edge的attributes复制到existing_edge
                for key, value in edge.attributes.items():
                    if key not in existing_edge.attributes:
                        existing_edge.attributes[key] = value

    # 提取去重后的边列表
    unique_edges = list(edges_by_uuid.values())
    logger.info(f"去重后的边数量: {len(unique_edges)}")
    
    # 根据配置选择重排序方法
    if not reordering_config:
        reordering_config = {}
    
    # 默认使用节点距离作为排序方法
    reordering_method = reordering_config.get("method", "cross_encoder")
    logger.info(f"使用重排序方法: {reordering_method}")
    
    # 根据重排序方法应用适当的排序
    if reordering_method == "distance":
        # 按节点距离排序
        ordered_edges = sorted(
            unique_edges,
            key=lambda edge: edge.attributes.get("distance", float("inf")) if hasattr(edge, "attributes") else float("inf")
        )
    elif reordering_method == "rrf":
        # 实现RRF (Reciprocal Rank Fusion)
        ordered_edges = await apply_rrf_reordering(unique_edges)
    elif reordering_method == "cross_encoder":
        # 使用cross_encoder进行重排序
        ordered_edges = await apply_cross_encoder_reordering(
            clients.cross_encoder, 
            query, 
            unique_edges,
            min_score=min_score,  # 传入最小分数阈值
            min_results=max(3, limit // 2)  # 确保至少返回一些结果
        )
    elif reordering_method == "mmr":
        # 实现MMR (Maximal Marginal Relevance)
        ordered_edges = await apply_mmr_reordering(
            clients.embedder, query, unique_edges
        )
    else:
        # 默认按相似度分数排序
        ordered_edges = sorted(
            unique_edges,
            key=lambda edge: edge.attributes.get("similarity_score", 0) if hasattr(edge, "attributes") else 0,
            reverse=True
        )
    
    # 限制结果数量
    final_results = ordered_edges[:limit]
    
    # 记录执行时间
    end_time = time()
    execution_time = end_time - start_time
    logger.info(f"边搜索完成 - 耗时: {execution_time:.2f}秒, 返回: {len(final_results)}/{len(unique_edges)} 个边")
    
    # 构建并返回搜索结果
    # 修复：处理两个不同EntityEdge类之间的兼容性问题
    try:
        # 将graphiti_core.edges.EntityEdge对象转换为neo4j_mapper.models.edges.EntityEdge对象
        model_edges = []
        for edge in final_results:
            # 提取对象的属性字典
            edge_dict = edge.model_dump()
            
            # 如果目标模型需要不同的字段名，在这里转换
            if 'source_node_uuid' in edge_dict and 'source_uuid' not in edge_dict:
                edge_dict['source_uuid'] = edge_dict['source_node_uuid']
            if 'target_node_uuid' in edge_dict and 'target_uuid' not in edge_dict:
                edge_dict['target_uuid'] = edge_dict['target_node_uuid']
                
            # 创建目标模型实例
            model_edge = EntityEdge(**edge_dict)
            model_edges.append(model_edge)
            
        # 使用转换后的对象
        results = SearchResults(
            edges=model_edges,
            nodes=[],
            episodes=[],
            communities=[]
        )
    except Exception as e:
        logger.warning(f"转换EntityEdge对象失败，尝试使用字典: {str(e)}")
        # 如果转换失败，则使用原始字典
        edge_dicts = [edge.model_dump() for edge in final_results]
        results = SearchResults(
            edges=edge_dicts,
            nodes=[],
            episodes=[],
            communities=[]
        )
    
    return results 