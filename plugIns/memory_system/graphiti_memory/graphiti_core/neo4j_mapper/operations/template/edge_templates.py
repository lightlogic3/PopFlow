"""
边操作相关的数据库查询模板
"""
from typing_extensions import LiteralString
from jinja2 import Template

# 获取实体的相关边
GET_ENTITY_RELATED_EDGES_TEMPLATE = Template("""
MATCH (n:Entity {uuid: "{{ entity_uuid }}"})-[r:RELATES_TO]->(m:Entity)
WHERE m.group_id = "{{ group_id }}"
RETURN
    r.uuid AS uuid,
    r.name AS name,
    r.fact AS fact,
    r.valid_at AS valid_at,
    r.invalid_at AS invalid_at,
    n.name AS source_name,
    m.name AS target_name,
    n.uuid AS source_uuid,
    m.uuid AS target_uuid
ORDER BY r.created_at DESC
LIMIT {{ limit }}
""")

# 查找两个实体之间的边
GET_ENTITIES_CONNECTING_EDGES_TEMPLATE = Template("""
MATCH (n:Entity {uuid: "{{ source_uuid }}"})-[r:RELATES_TO]->(m:Entity {uuid: "{{ target_uuid }}"})
WHERE r.group_id = "{{ group_id }}"
RETURN
    r.uuid AS uuid,
    r.name AS name,
    r.fact AS fact,
    r.valid_at AS valid_at,
    r.invalid_at AS invalid_at,
    n.name AS source_name,
    m.name AS target_name
ORDER BY r.created_at DESC
""")

# 查找可能无效的边
GET_POTENTIALLY_INVALID_EDGES_TEMPLATE = Template("""
MATCH (n:Entity)-[r:RELATES_TO]->(m:Entity)
WHERE r.group_id = "{{ group_id }}" 
  AND r.invalid_at IS NULL
  AND r.created_at < datetime("{{ before_date }}")
  AND (r.embedding_similarity WITH {{ embedding }} > {{ similarity_threshold }})
RETURN
    r.uuid AS uuid,
    r.name AS name,
    r.fact AS fact,
    r.valid_at AS valid_at,
    r.invalid_at AS invalid_at,
    n.name AS source_name,
    m.name AS target_name,
    n.uuid AS source_uuid,
    m.uuid AS target_uuid
LIMIT {{ limit }}
""")

# 更新边的属性
UPDATE_EDGE_ATTRIBUTES_TEMPLATE = Template("""
MATCH ()-[r:RELATES_TO {uuid: "{{ edge_uuid }}"}]->()
SET r.name = "{{ name }}",
    r.fact = "{{ fact }}",
    r.attributes = {{ attributes }},
    r.valid_at = {{ valid_at }},
    r.invalid_at = {{ invalid_at }},
    r.expired_at = {{ expired_at }}
RETURN r
""")

# 添加剧情到边
ADD_EPISODE_TO_EDGE_TEMPLATE = Template("""
MATCH ()-[r:RELATES_TO {uuid: "{{ edge_uuid }}"}]->()
SET r.episodes = r.episodes + ["{{ episode_uuid }}"]
RETURN r
""")

EPISODIC_EDGE_SAVE_BULK:LiteralString = """
    UNWIND $episodic_edges AS edge
    MATCH (episode:Episodic {uuid: edge.source_node_uuid}) 
    MATCH (node:Entity {uuid: edge.target_node_uuid}) 
    MERGE (episode)-[r:MENTIONS {uuid: edge.uuid}]->(node)
    SET r = {uuid: edge.uuid, group_id: edge.group_id, created_at: edge.created_at}
    RETURN r.uuid AS uuid
"""

ENTITY_EDGE_SAVE_BULK:LiteralString = """
    UNWIND $entity_edges AS edge
    MATCH (source:Entity {uuid: edge.source_node_uuid}) 
    MATCH (target:Entity {uuid: edge.target_node_uuid}) 
    MERGE (source)-[r:RELATES_TO {uuid: edge.uuid}]->(target)
    SET r = edge
    WITH r, edge CALL db.create.setRelationshipVectorProperty(r, "fact_embedding", edge.fact_embedding)
    RETURN edge.uuid AS uuid
"""