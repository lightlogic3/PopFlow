"""
边构建相关操作
"""
from datetime import datetime

from knowledge_api.utils.log_config import get_logger
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.edges import EpisodicEdge, CommunityEdge
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes import EntityNode, EpisodicNode, CommunityNode

logger = get_logger()


def build_episodic_edges(
    entity_nodes: list[EntityNode],
    episode: EpisodicNode,
    created_at: datetime,
) -> list[EpisodicEdge]:
    """构建剧情边
    
    参数:
        entity_nodes: 实体节点列表
        episode: 剧情节点
        created_at: 创建时间
        
    返回:
        构建的剧情边列表
    """
    episodic_edges: list[EpisodicEdge] = [
        EpisodicEdge(
            source_node_uuid=episode.uuid,
            target_node_uuid=node.uuid,
            created_at=created_at,
            group_id=episode.group_id,
        )
        for node in entity_nodes
    ]

    logger.debug(f'构建了 {len(episodic_edges)} 条剧情边')

    return episodic_edges


def build_community_edges(
    entity_nodes: list[EntityNode],
    community_node: CommunityNode,
    created_at: datetime,
) -> list[CommunityEdge]:
    """构建社区边
    
    参数:
        entity_nodes: 实体节点列表
        community_node: 社区节点
        created_at: 创建时间
        
    返回:
        构建的社区边列表
    """
    edges: list[CommunityEdge] = [
        CommunityEdge(
            source_node_uuid=community_node.uuid,
            target_node_uuid=node.uuid,
            created_at=created_at,
            group_id=community_node.group_id,
        )
        for node in entity_nodes
    ]

    logger.debug(f'构建了 {len(edges)} 条社区边')
    return edges 