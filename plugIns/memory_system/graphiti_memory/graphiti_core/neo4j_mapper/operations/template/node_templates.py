"""
节点操作相关的数据库查询模板
"""
from typing_extensions import LiteralString
from jinja2 import Template

# 获取实体的相关节点
GET_ENTITY_RELATED_NODES_TEMPLATE = Template("""
MATCH (n:Entity {uuid: "{{ entity_uuid }}"})-[r:RELATES_TO]-(m:Entity)
WHERE m.group_id = "{{ group_id }}"
RETURN
    m.uuid AS uuid,
    m.name AS name,
    m.summary AS summary,
    count(r) AS relation_count
ORDER BY relation_count DESC
LIMIT {{ limit }}
""")

# 查询实体节点的属性信息
GET_ENTITY_ATTRIBUTES_TEMPLATE = Template("""
MATCH (n:Entity {uuid: "{{ entity_uuid }}"})
RETURN
    n.uuid AS uuid,
    n.name AS name, 
    n.summary AS summary,
    n.attributes AS attributes,
    labels(n) AS labels
""")

# 更新实体节点属性
UPDATE_ENTITY_ATTRIBUTES_TEMPLATE = Template("""
MATCH (n:Entity {uuid: "{{ entity_uuid }}"})
SET n.summary = "{{ summary }}",
    n.attributes = {{ attributes }}
RETURN n
""")

# 查询可能重复的实体节点
FIND_DUPLICATE_ENTITIES_TEMPLATE = Template("""
MATCH (n:Entity)
WHERE n.group_id = "{{ group_id }}" AND n.name =~ "(?i).*{{ name_pattern }}.*"
RETURN
    n.uuid AS uuid,
    n.name AS name,
    n.summary AS summary,
    n.attributes AS attributes,
    labels(n) AS labels
LIMIT {{ limit }}
""")


EPISODIC_NODE_SAVE_BULK:LiteralString = """
    UNWIND $episodes AS episode
    MERGE (n:Episodic {uuid: episode.uuid})
    SET n = {uuid: episode.uuid, name: episode.name, group_id: episode.group_id, source_description: episode.source_description, 
        source: episode.source, content: episode.content, 
    entity_edges: episode.entity_edges, created_at: episode.created_at, valid_at: episode.valid_at}
    RETURN n.uuid AS uuid
"""

ENTITY_NODE_SAVE_BULK:LiteralString = """
    UNWIND $nodes AS node
    MERGE (n:Entity {uuid: node.uuid})
    SET n:$(node.labels)
    SET n = node
    WITH n, node CALL db.create.setNodeVectorProperty(n, "name_embedding", node.name_embedding)
    RETURN n.uuid AS uuid
"""
