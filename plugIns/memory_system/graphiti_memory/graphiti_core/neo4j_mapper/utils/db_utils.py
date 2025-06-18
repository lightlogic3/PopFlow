"""
数据库工具函数
提供与数据库操作相关的辅助函数
"""

from typing import Dict, Any, Union, Optional, List

from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.edges import EntityEdge, EpisodicEdge, \
    CommunityEdge


def create_edge_from_record(record: Dict[str, Any], edge_type: str) -> Union[EntityEdge, EpisodicEdge, CommunityEdge]:
    """
    根据边类型从数据库记录创建边对象
    
    Args:
        record: 数据库记录
        edge_type: 边类型，可以是'entity'、'episodic'或'community'
        
    Returns:
        创建的边对象
        
    Raises:
        ValueError: 如果提供了无效的边类型
    """
    if edge_type.lower() == 'entity':
        attributes = record['attributes'].copy() if record.get('attributes') else {}
        
        edge = EntityEdge(
            uuid=record['uuid'],
            source_node_uuid=record['source_node_uuid'],
            target_node_uuid=record['target_node_uuid'],
            fact=record.get('fact', ''),
            name=record.get('name', ''),
            group_id=record['group_id'],
            episodes=record.get('episodes', []),
            created_at=record['created_at'].to_native() if hasattr(record['created_at'], 'to_native') else record['created_at'],
            expired_at=record['expired_at'].to_native() if record.get('expired_at') and hasattr(record['expired_at'], 'to_native') else record.get('expired_at'),
            valid_at=record['valid_at'].to_native() if record.get('valid_at') and hasattr(record['valid_at'], 'to_native') else record.get('valid_at'),
            invalid_at=record['invalid_at'].to_native() if record.get('invalid_at') and hasattr(record['invalid_at'], 'to_native') else record.get('invalid_at'),
            attributes=attributes
        )
        
        # 清理属性中的重复字段
        if edge.attributes:
            edge.attributes.pop('uuid', None)
            edge.attributes.pop('source_node_uuid', None)
            edge.attributes.pop('target_node_uuid', None)
            edge.attributes.pop('fact', None)
            edge.attributes.pop('name', None)
            edge.attributes.pop('group_id', None)
            edge.attributes.pop('episodes', None)
            edge.attributes.pop('created_at', None)
            edge.attributes.pop('expired_at', None)
            edge.attributes.pop('valid_at', None)
            edge.attributes.pop('invalid_at', None)
            
        return edge
        
    elif edge_type.lower() == 'episodic':
        return EpisodicEdge(
            uuid=record['uuid'],
            group_id=record['group_id'],
            source_node_uuid=record['source_node_uuid'],
            target_node_uuid=record['target_node_uuid'],
            created_at=record['created_at'].to_native() if hasattr(record['created_at'], 'to_native') else record['created_at'],
        )
        
    elif edge_type.lower() == 'community':
        return CommunityEdge(
            uuid=record['uuid'],
            group_id=record['group_id'],
            source_node_uuid=record['source_node_uuid'],
            target_node_uuid=record['target_node_uuid'],
            created_at=record['created_at'].to_native() if hasattr(record['created_at'], 'to_native') else record['created_at'],
            relationship_type=record.get('relationship_type', ''),
            weight=record.get('weight', 1.0)
        )
        
    else:
        raise ValueError(f"无效的边类型: {edge_type}") 