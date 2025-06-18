"""
情节搜索操作函数
提供与Neo4j数据库中情节节点搜索相关的操作
"""

import logging
from typing import List

from neo4j import AsyncDriver

from knowledge_api.utils.log_config import get_logger
from knowledge_manage.rerank_model import BaseRankingModel
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.models.search_models import SearchFilters, \
    DEFAULT_SEARCH_LIMIT, EpisodeReranker, EpisodeSearchConfig
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes import EpisodicNode
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.search.utils import episode_fulltext_search, rrf
from plugIns.memory_system.graphiti_memory.graphiti_core.utils.utils import semaphore_gather

logger = get_logger()


async def episode_search(
    driver: AsyncDriver,
    cross_encoder: BaseRankingModel,
    query: str,
    _query_vector: list[float],
    group_ids: list[str] | None,
    config: EpisodeSearchConfig | None,
    search_filter: SearchFilters,
    limit=DEFAULT_SEARCH_LIMIT,
    reranker_min_score: float = 0,
) -> list[EpisodicNode]:
    """
    搜索与查询相关的情节节点
    
    参数:
    ----
    driver : AsyncDriver
        Neo4j数据库驱动
    cross_encoder : BaseRankingModel
        跨编码器模型，用于重排序
    query : str
        搜索查询文本
    _query_vector : list[float]
        查询向量（在此函数中未使用，但为了保持接口一致）
    group_ids : list[str] | None
        要搜索的群组ID列表
    config : EpisodeSearchConfig | None
        情节搜索配置
    search_filter : SearchFilters
        搜索过滤条件
    limit : int, optional
        结果数量限制
    reranker_min_score : float, optional
        重排序最小分数阈值
        
    返回:
    ----
    list[EpisodicNode]
        匹配的情节节点列表
    """
    if config is None:
        return []

    search_results: list[list[EpisodicNode]] = list(
        await semaphore_gather(
            *[
                episode_fulltext_search(driver, query, search_filter, group_ids, 2 * limit),
            ]
        )
    )

    search_result_uuids = [[episode.uuid for episode in result] for result in search_results]
    episode_uuid_map = {episode.uuid: episode for result in search_results for episode in result}

    reranked_uuids: list[str] = []
    if config.reranker == EpisodeReranker.rrf:
        reranked_uuids = rrf(search_result_uuids, min_score=reranker_min_score)

    elif config.reranker == EpisodeReranker.cross_encoder:
        # use rrf as a preliminary reranker
        rrf_result_uuids = rrf(search_result_uuids, min_score=reranker_min_score)
        rrf_results = [episode_uuid_map[uuid] for uuid in rrf_result_uuids][:limit]

        content_to_uuid_map = {episode.content: episode.uuid for episode in rrf_results}

        reranked_contents = await cross_encoder.async_rank(query, list(content_to_uuid_map.keys()))
        reranked_uuids = [
            content_to_uuid_map[content]
            for content, score in reranked_contents
            if score >= reranker_min_score
        ]

    reranked_episodes = [episode_uuid_map[uuid] for uuid in reranked_uuids]

    return reranked_episodes[:limit] 