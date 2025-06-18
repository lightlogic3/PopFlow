"""
边操作模块
"""

from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.edge.edge_extraction import (
    extract_edges,
)

from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.edge.edge_deduplication import (
    dedupe_extracted_edges,
    resolve_extracted_edges,
    resolve_extracted_edge,
    resolve_edge_contradictions,
    dedupe_extracted_edge,
    dedupe_edge_list,
)

from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.edge.edge_building import (
    build_episodic_edges,
    build_community_edges,
)

__all__ = [
    # 边提取操作
    'extract_edges',
    
    # 边去重操作
    'dedupe_extracted_edges',
    'resolve_extracted_edges',
    'resolve_extracted_edge',
    'resolve_edge_contradictions',
    'dedupe_extracted_edge',
    'dedupe_edge_list',
    
    # 边构建操作
    'build_episodic_edges',
    'build_community_edges',
] 