"""
边缘模块
提供图数据库中的边缘类型和操作
"""

from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.edges.base_edge import Edge
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.edges.entity_edge import (
    EntityEdge,
    get_entity_edge_from_record,
    create_entity_edge_embeddings,
)
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.edges.episodic_edge import (
    EpisodicEdge,
    get_episodic_edge_from_record,
)
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.edges.community_edge import (
    CommunityEdge,
    get_community_edge_from_record,
)

__all__ = [
    'Edge',
    'EntityEdge',
    'EpisodicEdge',
    'CommunityEdge',
    'get_entity_edge_from_record',
    'get_episodic_edge_from_record',
    'get_community_edge_from_record',
    'create_entity_edge_embeddings',
]
