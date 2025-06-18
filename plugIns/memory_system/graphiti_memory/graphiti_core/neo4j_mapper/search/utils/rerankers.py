"""
重排序工具函数
提供各种重排序策略的实现

注意：此文件保留了一些基础功能，其他高级重排序功能已迁移到search/ops/reranking_ops.py
"""

from collections import defaultdict
from time import time
from typing import Dict, List, Tuple

import numpy as np
from neo4j import AsyncDriver, Query

from knowledge_api.utils.log_config import get_logger
from plugIns.memory_system.graphiti_memory.graphiti_core.config import DEFAULT_DATABASE
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.search.search_template import \
    NODE_DISTANCE_RERANKER, EPISODE_MENTIONS_RERANKER

DEFAULT_MMR_LAMBDA = 0.5

logger = get_logger()
def rrf(results: List[List[str]], rank_const=1, min_score: float = 0) -> List[str]:
    """
    倒数排名融合算法 (Reciprocal Rank Fusion)
    
    参数:
    ----
    results : List[List[str]]
        待合并的多个排名结果列表
    rank_const : int, optional
        排名常数，用于计算权重，默认为1
    min_score : float, optional
        最小分数阈值，低于该阈值的结果将被过滤，默认为0
    
    返回:
    ----
    List[str]
        重新排序后的UUID列表
    """
    if not results:
        return []
        
    logger.info(f"应用RRF重排序，结果列表数量：{len(results)}")
    
    scores: Dict[str, float] = defaultdict(float)
    for result in results:
        for i, uuid in enumerate(result):
            scores[uuid] += 1 / (i + rank_const)

    scored_uuids = [term for term in scores.items()]
    scored_uuids.sort(reverse=True, key=lambda term: term[1])

    sorted_uuids = [term[0] for term in scored_uuids]
    filtered_uuids = [uuid for uuid in sorted_uuids if scores[uuid] >= min_score]
    
    logger.info(f"RRF重排序完成，排序前数量：{len(sorted_uuids)}，过滤后数量：{len(filtered_uuids)}")
    return filtered_uuids


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
    
    logger.info(f"执行节点距离重排序: 节点数量={len(filtered_uuids)}, 中心节点={center_node_uuid}")

    # 渲染Cypher查询模板
    cypher_query = NODE_DISTANCE_RERANKER.render()
    
    # 创建参数字典
    params = {
        "node_uuids": filtered_uuids,
        "center_uuid": center_node_uuid
    }
    
    # 调试日志 - 打印生成的Cypher查询
    logger.info(f"节点距离重排序查询: {cypher_query}")

    # 执行查询
    path_results, _, _ = await driver.execute_query(
        cypher_query,
        params,
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
    
    result_uuids = [uuid for uuid in filtered_uuids if (1 / scores[uuid]) >= min_score]
    logger.info(f"节点距离重排序完成: 结果数量={len(result_uuids)}")

    return result_uuids


async def episode_mentions_reranker(
    driver: AsyncDriver, node_uuids: List[List[str]], min_score: float = 0
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
    # 使用RRF作为初步排序
    sorted_uuids = rrf(node_uuids)
    scores: Dict[str, float] = {}
    
    logger.info(f"执行情节提及重排序: 节点数量={len(sorted_uuids)}")

    # 渲染Cypher查询模板
    cypher_query = EPISODE_MENTIONS_RERANKER.render()
    
    # 创建参数字典
    params = {
        "node_uuids": sorted_uuids
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

    for result in results:
        scores[result['uuid']] = result['score']

    # 为未查询到的节点设置默认分数0
    for uuid in sorted_uuids:
        if uuid not in scores:
            scores[uuid] = 0

    # 按提及次数重排序（按降序排列，提及次数越多排名越靠前）
    sorted_uuids.sort(key=lambda cur_uuid: scores[cur_uuid], reverse=True)
    
    result_uuids = [uuid for uuid in sorted_uuids if scores[uuid] >= min_score]
    logger.info(f"情节提及重排序完成: 结果数量={len(result_uuids)}")

    return result_uuids


def maximal_marginal_relevance(
    query_vector: List[float],
    candidates_with_vectors: List[Tuple[str, List[float]]],
    mmr_lambda: float = DEFAULT_MMR_LAMBDA,
    min_score: float = 0
) -> List[str]:
    """
    最大边际相关性算法实现
    
    参数:
    ----
    query_vector : List[float]
        查询向量
    candidates_with_vectors : List[Tuple[str, List[float]]]
        候选项及其向量的元组列表 [(uuid, vector), ...]
    mmr_lambda : float, optional
        控制多样性与相关性的平衡参数
    min_score : float, optional
        最小分数阈值
        
    返回:
    ----
    List[str]
        按MMR排序的UUID列表
    """
    if not candidates_with_vectors:
        return []
    
    logger.info(f"应用MMR重排序，候选项数量：{len(candidates_with_vectors)}")
    start_time = time()
    
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
                mmr_scores[uuid] = mmr_lambda * query_similarities[uuid] - (1 - mmr_lambda) * max_sim
        
        # 选择MMR分数最高的元素
        selected_uuid = max(candidates, key=lambda uuid: mmr_scores[uuid])
        score = mmr_scores[selected_uuid]
        
        # 如果分数低于阈值，停止选择
        if score < min_score:
            break
            
        selected.append(selected_uuid)
        candidates.remove(selected_uuid)
    
    logger.info(f"MMR重排序完成，耗时：{time() - start_time:.2f}秒，结果数量：{len(selected)}")
    return selected 