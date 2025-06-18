"""
边缘查询模板初始化文件
导出所有边缘相关的Cypher查询模板
"""

from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.edges.templates.edge_templates import (
    # 基础边缘模板
    EDGE_DELETE,
    
    # 实体边缘模板
    ENTITY_EDGE_SAVE,
    ENTITY_EDGE_GET_BY_UUID,
    ENTITY_EDGE_GET_BY_UUIDS,
    ENTITY_EDGE_GET_BY_GROUP_IDS,
    ENTITY_EDGE_GET_BY_NODE_UUID,
    ENTITY_EDGE_LOAD_FACT_EMBEDDING,
    
    # 情节边缘模板
    EPISODIC_EDGE_SAVE,
    EPISODIC_EDGE_GET_BY_UUID,
    EPISODIC_EDGE_GET_BY_UUIDS,
    EPISODIC_EDGE_GET_BY_GROUP_IDS,
    
    # 社区边缘模板
    COMMUNITY_EDGE_SAVE,
    COMMUNITY_EDGE_GET_BY_UUID,
    COMMUNITY_EDGE_GET_BY_UUIDS,
    COMMUNITY_EDGE_GET_BY_GROUP_IDS,
)

__all__ = [
    # 基础边缘模板
    'EDGE_DELETE',
    
    # 实体边缘模板
    'ENTITY_EDGE_SAVE',
    'ENTITY_EDGE_GET_BY_UUID',
    'ENTITY_EDGE_GET_BY_UUIDS',
    'ENTITY_EDGE_GET_BY_GROUP_IDS',
    'ENTITY_EDGE_GET_BY_NODE_UUID',
    'ENTITY_EDGE_LOAD_FACT_EMBEDDING',
    
    # 情节边缘模板
    'EPISODIC_EDGE_SAVE',
    'EPISODIC_EDGE_GET_BY_UUID',
    'EPISODIC_EDGE_GET_BY_UUIDS',
    'EPISODIC_EDGE_GET_BY_GROUP_IDS',
    
    # 社区边缘模板
    'COMMUNITY_EDGE_SAVE',
    'COMMUNITY_EDGE_GET_BY_UUID',
    'COMMUNITY_EDGE_GET_BY_UUIDS',
    'COMMUNITY_EDGE_GET_BY_GROUP_IDS',
] 