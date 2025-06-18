"""
重排序操作函数
提供各种用于搜索结果重排序的操作函数
"""

import logging
from time import time
from typing import Any, Dict, List, Tuple, Union
import numpy as np
from collections import defaultdict

from neo4j import AsyncDriver

from knowledge_api.utils.log_config import get_logger
from knowledge_manage.embeddings.base import EmbeddingEngine
from knowledge_manage.rerank_model import BaseRankingModel
from plugIns.memory_system.graphiti_memory.graphiti_core.config import DEFAULT_DATABASE
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.search.search_template import (
    NODE_DISTANCE_RERANKER,
    EPISODE_MENTIONS_RERANKER,
    GET_EMBEDDINGS_FOR_NODES,
    GET_EMBEDDINGS_FOR_COMMUNITIES,
    GET_EMBEDDINGS_FOR_EDGES
)
from plugIns.memory_system.graphiti_memory.graphiti_core.utils.utils import normalize_l2

logger = get_logger()


async def apply_rrf_reordering(edges: list[Any], rank_const: int = 1, min_score: float = 0) -> list[Any]:
    """
    实现RRF (Reciprocal Rank Fusion)重排序算法
    
    参数:
    ----
    edges : list[Any]
        要重排序的边列表
    rank_const : int, optional
        RRF常数，用于调整排序权重
    min_score : float, optional
        最小分数阈值，低于此值的结果会被过滤
        
    返回:
    ----
    list[Any]
        重排序后的边列表
    """
    logger.info(f"应用RRF重排序，边数量：{len(edges)}")
    
    # 按不同来源分组
    edges_by_source = {}
    for edge in edges:
        source = "unknown"
        if hasattr(edge, 'attributes') and isinstance(edge.attributes, dict):
            source = edge.attributes.get('search_method', 'unknown')
        
        if source not in edges_by_source:
            edges_by_source[source] = []
        edges_by_source[source].append(edge)
    
    # 每个来源内部排序
    for source, source_edges in edges_by_source.items():
        if source == "similarity":
            # 相似度搜索结果按分数降序排列
            source_edges.sort(
                key=lambda e: e.attributes.get('similarity_score', 0) if hasattr(e, 'attributes') else 0, 
                reverse=True
            )
        elif source == "bfs":
            # BFS搜索结果按距离升序排列
            source_edges.sort(
                key=lambda e: e.attributes.get('distance', float('inf')) if hasattr(e, 'attributes') else float('inf')
            )
    
    # 计算RRF分数
    rrf_scores = {}
    for source, source_edges in edges_by_source.items():
        for i, edge in enumerate(source_edges):
            if edge.uuid not in rrf_scores:
                rrf_scores[edge.uuid] = 0
            rrf_scores[edge.uuid] += 1.0 / (i + rank_const)
    
    # 按RRF分数重排序
    scored_edges = [(edge, rrf_scores.get(edge.uuid, 0)) for edge in edges]
    scored_edges.sort(key=lambda x: x[1], reverse=True)
    
    # 过滤低分结果并返回
    result = [edge for edge, score in scored_edges if score >= min_score]
    logger.info(f"RRF重排序完成，保留边数量：{len(result)}")
    return result


async def apply_cross_encoder_reordering(
    reranker: BaseRankingModel, 
    query: str, 
    edges: list[Any], 
    min_score: float = 0,
    min_results: int = 3  # 保证至少返回的结果数
) -> list[Any]:
    """
    使用交叉编码器重排序边列表
    
    参数:
    ----
    reranker : BaseRankingModel
        交叉编码器重排序模型
    query : str
        查询字符串
    edges : list[Any]
        要重排序的边列表
    min_score : float, optional
        最小分数阈值，低于此值的结果会被过滤
    min_results : int, optional
        至少返回的结果数量，即使分数低于阈值
        
    返回:
    ----
    list[Any]
        重排序后的边列表
    """
    logger.info(f"应用交叉编码器重排序，边数量：{len(edges)}")
    
    # 提取边的描述文本
    edge_texts = []
    edge_by_text = {}
    
    for edge in edges:
        if hasattr(edge, 'description') and edge.description:
            text = edge.description
            edge_texts.append(text)
            edge_by_text[text] = edge
    
    if not edge_texts:
        logger.warning("没有找到边的描述文本，无法应用交叉编码器重排序")
        return edges[:min(len(edges), min_results)]  # 返回前min_results个结果
    
    # 使用交叉编码器进行重排序
    start_time = time()
    ranked_texts = await reranker.async_rank(query, edge_texts)
    logger.info(f"交叉编码器重排序耗时：{time() - start_time:.2f}秒")
    
    # 为每个边添加分数
    scored_edges = []
    for (text, score), edge in zip(ranked_texts, edges):
        # 将分数添加到边的属性中
        if hasattr(edge, 'attributes') and isinstance(edge.attributes, dict):
            edge.attributes['cross_encoder_score'] = float(score)
        scored_edges.append((edge, score))
    
    # 按得分降序排序
    scored_edges.sort(key=lambda x: x[1], reverse=True)
    
    # 构建结果列表 - 先按照阈值过滤
    results = [edge for edge, score in scored_edges if score >= min_score]
    
    # 如果过滤后结果太少，保留至少min_results个最佳结果
    if len(results) < min_results and scored_edges:
        logger.info(f"过滤后结果数量({len(results)})少于最小要求({min_results})，保留顶部结果")
        # 取前min_results个结果，不考虑分数
        top_results = [edge for edge, _ in scored_edges[:min_results]]
        
        # 合并已有的高分结果和额外的顶部结果
        final_results = list(set(results + top_results))
        # 重新按分数排序
        final_results.sort(
            key=lambda e: e.attributes.get('cross_encoder_score', 0) if hasattr(e, 'attributes') else 0, 
            reverse=True
        )
        results = final_results
    
    logger.info(f"交叉编码器重排序完成，保留边数量：{len(results)}")
    return results


async def apply_mmr_reordering(
    embedder_client: EmbeddingEngine,
    query: str,
    edges: list[Any],
    mmr_lambda: float = 0.5,
    min_score: float = 0,
    driver: AsyncDriver = None
) -> list[Any]:
    """
    使用最大边际相关性(MMR)算法重排序边列表
    
    参数:
    ----
    embedder_client : EmbeddingEngine
        嵌入引擎客户端
    query : str
        查询字符串
    edges : list[Any]
        要重排序的边列表
    mmr_lambda : float, optional
        MMR lambda参数，控制多样性与相关性的平衡
    min_score : float, optional
        最小分数阈值，低于此值的结果会被过滤
    driver : AsyncDriver, optional
        Neo4j驱动，用于获取现有嵌入
        
    返回:
    ----
    list[Any]
        重排序后的边列表
    """
    logger.info(f"应用MMR重排序，边数量：{len(edges)}")
    
    if not edges:
        return []
    
    # 获取查询向量
    query_vector = await embedder_client.embed_query(query)
    query_vector = normalize_l2(query_vector)
    
    # 获取边向量
    edge_vectors = []
    
    if driver:
        # 尝试从数据库获取现有嵌入
        edge_uuids = [edge.uuid for edge in edges if hasattr(edge, 'uuid')]
        
        # 渲染Cypher查询模板
        cypher_query = GET_EMBEDDINGS_FOR_EDGES.render()
        
        # 执行查询
        records, _, _ = await driver.execute_query(
            cypher_query,
            {"edge_uuids": edge_uuids},
            database_=DEFAULT_DATABASE,
            routing_='r',
        )
        
        # 创建UUID到嵌入的映射
        uuid_to_embedding = {}
        for record in records:
            uuid = record['uuid']
            embedding = record['fact_embedding']
            if embedding:
                uuid_to_embedding[uuid] = normalize_l2(embedding)
        
        # 处理每个边的嵌入
        for edge in edges:
            if hasattr(edge, 'uuid') and edge.uuid in uuid_to_embedding:
                edge_vectors.append((edge.uuid, uuid_to_embedding[edge.uuid]))
            else:
                # 如果数据库中没有嵌入，则使用描述生成嵌入
                if hasattr(edge, 'description') and edge.description:
                    vec = await embedder_client.embed_query(edge.description)
                    edge_vectors.append((edge.uuid, normalize_l2(vec)))
    else:
        # 如果没有提供数据库驱动，则直接从描述生成嵌入
        for edge in edges:
            if hasattr(edge, 'description') and edge.description:
                vec = await embedder_client.embed_query(edge.description)
                edge_vectors.append((edge.uuid, normalize_l2(vec)))
    
    if not edge_vectors:
        logger.warning("无法获取边的嵌入向量，无法应用MMR重排序")
        return edges
    
    # 执行MMR算法
    selected_indices = []
    remaining_indices = list(range(len(edge_vectors)))
    
    edge_uuid_to_index = {edge_vectors[i][0]: i for i in range(len(edge_vectors))}
    edge_index_to_uuid = {i: edge_vectors[i][0] for i in range(len(edge_vectors))}
    
    # 计算所有边与查询的相似度
    similarities = []
    for _, vec in edge_vectors:
        sim = np.dot(query_vector, vec)
        similarities.append(sim)
    
    while remaining_indices and len(selected_indices) < len(edge_vectors):
        # 计算MMR分数
        mmr_scores = []
        
        for i in remaining_indices:
            if not selected_indices:
                # 第一个元素，仅考虑相关性
                mmr_scores.append((i, similarities[i]))
            else:
                # 计算与已选择元素的最大相似度
                max_sim = max(
                    np.dot(edge_vectors[i][1], edge_vectors[j][1])
                    for j in selected_indices
                )
                
                # MMR公式：lambda * 相关性 - (1-lambda) * 多样性
                mmr_score = mmr_lambda * similarities[i] - (1 - mmr_lambda) * max_sim
                mmr_scores.append((i, mmr_score))
        
        # 选择MMR分数最高的元素
        selected_i, score = max(mmr_scores, key=lambda x: x[1])
        
        # 如果分数低于阈值，停止选择
        if score < min_score:
            break
            
        selected_indices.append(selected_i)
        remaining_indices.remove(selected_i)
    
    # 按照MMR顺序重排序边
    selected_uuids = [edge_index_to_uuid[i] for i in selected_indices]
    uuid_to_edge = {edge.uuid: edge for edge in edges if hasattr(edge, 'uuid')}
    
    result = [uuid_to_edge[uuid] for uuid in selected_uuids if uuid in uuid_to_edge]
    
    # 为每个边保存其MMR分数
    for i, edge in enumerate(result):
        if hasattr(edge, 'attributes') and isinstance(edge.attributes, dict):
            edge.attributes['mmr_score'] = float(similarities[edge_uuid_to_index[edge.uuid]])
            edge.attributes['mmr_rank'] = i
    
    logger.info(f"MMR重排序完成，保留边数量：{len(result)}")
    return result


async def node_distance_reranker(
    driver: AsyncDriver,
    node_uuids: List[str],
    center_node_uuid: str,
    min_score: float = 0,
) -> List[str]:
    """
    基于图距离的重排序策略
    
    参数:
    ----
    driver : AsyncDriver
        Neo4j驱动实例
    node_uuids : List[str]
        待重排序的节点UUID列表
    center_node_uuid : str
        中心节点UUID，基于到该节点的距离进行排序
    min_score : float, optional
        最小分数阈值
    
    返回:
    ----
    List[str]
        重新排序后的UUID列表
    """
    # 过滤掉中心节点UUID
    filtered_uuids = list(filter(lambda node_uuid: node_uuid != center_node_uuid, node_uuids))
    scores: Dict[str, float] = {center_node_uuid: 0.0}

    # 渲染Cypher查询模板
    cypher_query = NODE_DISTANCE_RERANKER.render()
    
    # 执行查询
    path_results, _, _ = await driver.execute_query(
        cypher_query,
        {"node_uuids": filtered_uuids, "center_uuid": center_node_uuid},
        database_=DEFAULT_DATABASE,
        routing_='r',
    )

    for result in path_results:
        uuid = result['uuid']
        score = result['score']
        scores[uuid] = score

    for uuid in filtered_uuids:
        if uuid not in scores:
            scores[uuid] = float('inf')

    # 按最短距离重排序
    filtered_uuids.sort(key=lambda cur_uuid: scores[cur_uuid])

    # 如果之前被过滤掉的中心节点存在于原始列表中，则将其添加回来
    if center_node_uuid in node_uuids:
        scores[center_node_uuid] = 0.1
        filtered_uuids = [center_node_uuid] + filtered_uuids

    return [uuid for uuid in filtered_uuids if (1 / scores[uuid] if scores[uuid] > 0 else float('inf')) >= min_score]


async def episode_mentions_reranker(
    driver: AsyncDriver, 
    node_uuids: List[List[str]], 
    min_score: float = 0
) -> List[str]:
    """
    基于情节提及次数的重排序策略
    
    参数:
    ----
    driver : AsyncDriver
        Neo4j驱动实例
    node_uuids : List[List[str]]
        待重排序的节点UUID列表
    min_score : float, optional
        最小分数阈值
    
    返回:
    ----
    List[str]
        重新排序后的UUID列表
    """
    # 实现RRF排序，避免循环导入
    scores: Dict[str, float] = defaultdict(float)
    rank_const = 1  # 默认RRF参数
    
    for result in node_uuids:
        for i, uuid in enumerate(result):
            scores[uuid] += 1 / (i + rank_const)

    scored_uuids = [term for term in scores.items()]
    scored_uuids.sort(reverse=True, key=lambda term: term[1])

    sorted_uuids = [term[0] for term in scored_uuids]
    rrf_filtered_uuids = [uuid for uuid in sorted_uuids if scores[uuid] >= min_score]
    
    logger.info(f"应用RRF预排序，原始列表数量：{len(node_uuids)}，合并后数量：{len(sorted_uuids)}，过滤后数量：{len(rrf_filtered_uuids)}")

    # 渲染Cypher查询模板
    cypher_query = EPISODE_MENTIONS_RERANKER.render()
    
    # 创建参数字典
    params = {
        "node_uuids": rrf_filtered_uuids
    }
    
    # 调试日志 - 打印生成的Cypher查询
    logger.info(f"情节提及重排序查询: {cypher_query}")

    # 执行查询
    results, _, _ = await driver.execute_query(
        cypher_query,
        params,
        database_=DEFAULT_DATABASE,
        routing_='r',
    )

    mention_scores: Dict[str, float] = {}
    for result in results:
        mention_scores[result['uuid']] = result['score']

    # 为未查询到的节点设置默认分数0
    for uuid in rrf_filtered_uuids:
        if uuid not in mention_scores:
            mention_scores[uuid] = 0

    # 按提及次数重排序（按降序排列，提及次数越多排名越靠前）
    rrf_filtered_uuids.sort(key=lambda cur_uuid: mention_scores.get(cur_uuid, 0), reverse=True)
    
    result_uuids = [uuid for uuid in rrf_filtered_uuids if mention_scores.get(uuid, 0) >= min_score]
    logger.info(f"情节提及重排序完成: 结果数量={len(result_uuids)}")

    return result_uuids


async def get_embeddings_for_nodes(
    driver: AsyncDriver, 
    nodes: list[Any]
) -> list[tuple[str, list[float]]]:
    """
    获取节点的嵌入向量
    
    参数:
    ----
    driver : AsyncDriver
        Neo4j驱动实例
    nodes : list[Any]
        节点列表
        
    返回:
    ----
    list[tuple[str, list[float]]]
        (节点UUID, 嵌入向量)的元组列表
    """
    if not nodes:
        return []
    
    node_uuids = [node.uuid for node in nodes if hasattr(node, 'uuid')]
    
    # 渲染Cypher查询模板
    cypher_query = GET_EMBEDDINGS_FOR_NODES.render()
    
    # 执行查询
    records, _, _ = await driver.execute_query(
        cypher_query,
        {"node_uuids": node_uuids},
        database_=DEFAULT_DATABASE,
        routing_='r',
    )
    
    result = []
    for record in records:
        uuid = record['uuid']
        embedding = record['name_embedding']
        if embedding:
            result.append((uuid, normalize_l2(embedding)))
    
    return result


async def get_embeddings_for_communities(
    driver: AsyncDriver, 
    communities: list[Any]
) -> list[tuple[str, list[float]]]:
    """
    获取社区节点的嵌入向量
    
    参数:
    ----
    driver : AsyncDriver
        Neo4j驱动实例
    communities : list[Any]
        社区节点列表
        
    返回:
    ----
    list[tuple[str, list[float]]]
        (社区UUID, 嵌入向量)的元组列表
    """
    if not communities:
        return []
    
    community_uuids = [community.uuid for community in communities if hasattr(community, 'uuid')]
    
    # 渲染Cypher查询模板
    cypher_query = GET_EMBEDDINGS_FOR_COMMUNITIES.render()
    
    # 执行查询
    records, _, _ = await driver.execute_query(
        cypher_query,
        {"community_uuids": community_uuids},
        database_=DEFAULT_DATABASE,
        routing_='r',
    )
    
    result = []
    for record in records:
        uuid = record['uuid']
        embedding = record['name_embedding']
        if embedding:
            result.append((uuid, normalize_l2(embedding)))
    
    return result


def maximal_marginal_relevance(
    query_vector: list[float],
    candidates_with_vectors: list[tuple[str, list[float]]],
    lambda_param: float = 0.5,
    min_score: float = 0
) -> list[str]:
    """
    最大边际相关性算法实现
    
    参数:
    ----
    query_vector : list[float]
        查询向量
    candidates_with_vectors : list[tuple[str, list[float]]]
        候选项及其向量的元组列表
    lambda_param : float, optional
        控制多样性与相关性的平衡参数
    min_score : float, optional
        最小分数阈值
        
    返回:
    ----
    list[str]
        按MMR排序的UUID列表
    """
    if not candidates_with_vectors:
        return []
    
    # 计算与查询的相似度
    query_similarities = {}
    for uuid, vector in candidates_with_vectors:
        query_similarities[uuid] = np.dot(query_vector, vector)
    
    # 预先计算候选项之间的相似度
    candidate_similarities = {}
    for i, (uuid_i, vector_i) in enumerate(candidates_with_vectors):
        for j, (uuid_j, vector_j) in enumerate(candidates_with_vectors):
            if i != j:
                sim = np.dot(vector_i, vector_j)
                candidate_similarities[(uuid_i, uuid_j)] = sim
    
    # 初始化
    selected = []
    candidates = [uuid for uuid, _ in candidates_with_vectors]
    
    # 贪婪选择
    while candidates and len(selected) < len(candidates_with_vectors):
        # 计算MMR分数
        mmr_scores = {}
        
        for uuid in candidates:
            if not selected:
                # 第一个元素，仅考虑相关性
                mmr_scores[uuid] = query_similarities[uuid]
            else:
                # 计算与已选择元素的最大相似度
                max_sim = max(
                    candidate_similarities.get((uuid, sel), 0)
                    for sel in selected
                )
                
                # MMR公式：lambda * 相关性 - (1-lambda) * 多样性
                mmr_scores[uuid] = lambda_param * query_similarities[uuid] - (1 - lambda_param) * max_sim
        
        # 选择MMR分数最高的元素
        selected_uuid = max(candidates, key=lambda uuid: mmr_scores[uuid])
        score = mmr_scores[selected_uuid]
        
        # 如果分数低于阈值，停止选择
        if score < min_score:
            break
            
        selected.append(selected_uuid)
        candidates.remove(selected_uuid)
    
    return selected 