"""
社区搜索操作函数
提供与Neo4j数据库中社区节点搜索相关的操作
"""

from neo4j import AsyncDriver

from knowledge_api.utils.log_config import get_logger
from knowledge_manage.rerank_model import BaseRankingModel
from plugIns.memory_system.graphiti_memory.graphiti_core.config import DEFAULT_SEARCH_LIMIT
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.models import CommunitySearchConfig, \
    CommunityReranker
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes import CommunityNode
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.search.utils import community_fulltext_search, \
    community_similarity_search, get_embeddings_for_communities, rrf, maximal_marginal_relevance
from plugIns.memory_system.graphiti_memory.graphiti_core.utils.utils import semaphore_gather

logger = get_logger()


async def community_search(
    driver: AsyncDriver,
    cross_encoder: BaseRankingModel,
    query: str,
    query_vector: list[float],
    group_ids: list[str] | None,
    config: CommunitySearchConfig | None,
    limit=DEFAULT_SEARCH_LIMIT,
    reranker_min_score: float = 0,
) -> list[CommunityNode]:
    """
    搜索与查询相关的社区节点
    
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
    config : CommunitySearchConfig | None
        社区搜索配置
    limit : int, optional
        结果数量限制
    reranker_min_score : float, optional
        重排序最小分数阈值
        
    返回:
    ----
    list[CommunityNode]
        匹配的社区节点列表
    """
    if config is None:
        return []

    search_results: list[list[CommunityNode]] = list(
        await semaphore_gather(
            *[
                community_fulltext_search(driver, query, group_ids, 2 * limit),
                community_similarity_search(
                    driver, query_vector, group_ids, 2 * limit, config.sim_min_score
                ),
            ]
        )
    )

    search_result_uuids = [[community.uuid for community in result] for result in search_results]
    community_uuid_map = {
        community.uuid: community for result in search_results for community in result
    }

    reranked_uuids: list[str] = []
    if config.reranker == CommunityReranker.rrf:
        reranked_uuids = rrf(search_result_uuids, min_score=reranker_min_score)
    elif config.reranker == CommunityReranker.mmr:
        search_result_uuids_and_vectors = await get_embeddings_for_communities(
            driver, list(community_uuid_map.values())
        )

        reranked_uuids = maximal_marginal_relevance(
            query_vector, search_result_uuids_and_vectors, config.mmr_lambda, reranker_min_score
        )
    elif config.reranker == CommunityReranker.cross_encoder:
        name_to_uuid_map = {node.name: node.uuid for result in search_results for node in result}
        reranked_nodes = await cross_encoder.async_rank(query, list(name_to_uuid_map.keys()))
        reranked_uuids = [
            name_to_uuid_map[name] for name, score in reranked_nodes if score >= reranker_min_score
        ]

    reranked_communities = [community_uuid_map[uuid] for uuid in reranked_uuids]

    return reranked_communities[:limit] 