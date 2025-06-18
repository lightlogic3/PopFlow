"""
社区操作模块
"""

from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.community.community_cluster import (
    get_community_clusters,
    label_propagation,
)

from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.community.community_summarization import (
    summarize_pair,
    generate_summary_description,
)

from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.community.community_builder import (
    build_community,
    build_communities,
)

from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.community.community_management import (
    remove_communities,
    determine_entity_community,
    update_community,
)

__all__ = [
    # 社区集群操作
    'get_community_clusters',
    'label_propagation',
    
    # 社区摘要操作
    'summarize_pair',
    'generate_summary_description',
    
    # 社区构建操作
    'build_community',
    'build_communities',
    
    # 社区管理操作
    'remove_communities',
    'determine_entity_community',
    'update_community',
]
