"""
边缘查询模板集合
使用Jinja2模板引擎管理所有边缘相关的Cypher查询
"""

from jinja2 import Template

# ================ 基础边缘模板 ================

# 边缘删除模板
EDGE_DELETE = Template("""
MATCH (n)-[e:MENTIONS|RELATES_TO|HAS_MEMBER {uuid: $uuid}]->(m)
DELETE e
""")

# ================ 实体边缘模板 ================

# 实体边缘保存模板
ENTITY_EDGE_SAVE = Template("""
MATCH (source:Entity {uuid: $edge_data.source_uuid})
MATCH (target:Entity {uuid: $edge_data.target_uuid})
MERGE (source)-[e:RELATES_TO {uuid: $edge_data.uuid}]->(target)
SET e = $edge_data
WITH e CALL db.create.setRelationshipVectorProperty(e, "fact_embedding", $edge_data.fact_embedding)
RETURN e.uuid AS uuid
""")

# 实体边缘获取UUID模板
ENTITY_EDGE_GET_BY_UUID = Template("""
MATCH (n:Entity)-[e:RELATES_TO {uuid: $uuid}]->(m:Entity)
RETURN
    e.uuid AS uuid,
    startNode(e).uuid AS source_node_uuid,
    endNode(e).uuid AS target_node_uuid,
    e.created_at AS created_at,
    e.name AS name,
    e.group_id AS group_id,
    e.fact AS fact,
    e.episodes AS episodes,
    e.expired_at AS expired_at,
    e.valid_at AS valid_at,
    e.invalid_at AS invalid_at,
    properties(e) AS attributes
""")

# 实体边缘批量获取UUIDs模板
ENTITY_EDGE_GET_BY_UUIDS = Template("""
MATCH (n:Entity)-[e:RELATES_TO]->(m:Entity)
WHERE e.uuid IN $uuids
RETURN
    e.uuid AS uuid,
    startNode(e).uuid AS source_node_uuid,
    endNode(e).uuid AS target_node_uuid,
    e.created_at AS created_at,
    e.name AS name,
    e.group_id AS group_id,
    e.fact AS fact,
    e.episodes AS episodes,
    e.expired_at AS expired_at,
    e.valid_at AS valid_at,
    e.invalid_at AS invalid_at,
    properties(e) AS attributes
""")

# 实体边缘按组ID获取模板
ENTITY_EDGE_GET_BY_GROUP_IDS = Template("""
MATCH (n:Entity)-[e:RELATES_TO]->(m:Entity)
WHERE e.group_id IN $group_ids
{% if uuid_cursor %}AND e.uuid < $uuid{% endif %}
RETURN
    e.uuid AS uuid,
    startNode(e).uuid AS source_node_uuid,
    endNode(e).uuid AS target_node_uuid,
    e.created_at AS created_at,
    e.name AS name,
    e.group_id AS group_id,
    e.fact AS fact,
    e.episodes AS episodes,
    e.expired_at AS expired_at,
    e.valid_at AS valid_at,
    e.invalid_at AS invalid_at,
    properties(e) AS attributes
ORDER BY e.uuid DESC
{% if limit %}LIMIT $limit{% endif %}
""")

# 实体边缘按节点UUID获取模板
ENTITY_EDGE_GET_BY_NODE_UUID = Template("""
MATCH (n:Entity {uuid: $node_uuid})-[e:RELATES_TO]-(m:Entity)
RETURN
    e.uuid AS uuid,
    startNode(e).uuid AS source_node_uuid,
    endNode(e).uuid AS target_node_uuid,
    e.created_at AS created_at,
    e.name AS name,
    e.group_id AS group_id,
    e.fact AS fact,
    e.episodes AS episodes,
    e.expired_at AS expired_at,
    e.valid_at AS valid_at,
    e.invalid_at AS invalid_at,
    properties(e) AS attributes
""")

# 实体边缘加载事实嵌入模板
ENTITY_EDGE_LOAD_FACT_EMBEDDING = Template("""
MATCH (n:Entity)-[e:RELATES_TO {uuid: $uuid}]->(m:Entity)
RETURN e.fact_embedding AS fact_embedding
""")

# ================ 情节边缘模板 ================

# 情节边缘保存模板
EPISODIC_EDGE_SAVE = Template("""
MATCH (episode:Episodic {uuid: $episode_uuid})
MATCH (entity:Entity {uuid: $entity_uuid})
MERGE (episode)-[e:MENTIONS {uuid: $uuid}]->(entity)
SET e.group_id = $group_id,
    e.created_at = $created_at
RETURN e.uuid AS uuid
""")

# 情节边缘获取UUID模板
EPISODIC_EDGE_GET_BY_UUID = Template("""
MATCH (n:Episodic)-[e:MENTIONS {uuid: $uuid}]->(m:Entity)
RETURN
    e.uuid As uuid,
    e.group_id AS group_id,
    n.uuid AS source_node_uuid,
    m.uuid AS target_node_uuid,
    e.created_at AS created_at
""")

# 情节边缘批量获取UUIDs模板
EPISODIC_EDGE_GET_BY_UUIDS = Template("""
MATCH (n:Episodic)-[e:MENTIONS]->(m:Entity)
WHERE e.uuid IN $uuids
RETURN
    e.uuid As uuid,
    e.group_id AS group_id,
    n.uuid AS source_node_uuid,
    m.uuid AS target_node_uuid,
    e.created_at AS created_at
""")

# 情节边缘按组ID获取模板
EPISODIC_EDGE_GET_BY_GROUP_IDS = Template("""
MATCH (n:Episodic)-[e:MENTIONS]->(m:Entity)
WHERE e.group_id IN $group_ids
{% if uuid_cursor %}AND e.uuid < $uuid{% endif %}
RETURN
    e.uuid As uuid,
    e.group_id AS group_id,
    n.uuid AS source_node_uuid,
    m.uuid AS target_node_uuid,
    e.created_at AS created_at
ORDER BY e.uuid DESC
{% if limit %}LIMIT $limit{% endif %}
""")

# ================ 社区边缘模板 ================

# 社区边缘保存模板
COMMUNITY_EDGE_SAVE = Template("""
MATCH (community:Community {uuid: $community_uuid})
MATCH (entity {uuid: $entity_uuid})
WHERE entity:Entity OR entity:Community
MERGE (community)-[e:HAS_MEMBER {uuid: $uuid}]->(entity)
SET e.group_id = $group_id,
    e.created_at = $created_at
RETURN e.uuid AS uuid
""")

# 社区边缘获取UUID模板
COMMUNITY_EDGE_GET_BY_UUID = Template("""
MATCH (n:Community)-[e:HAS_MEMBER {uuid: $uuid}]->(m:Entity | Community)
RETURN
    e.uuid As uuid,
    e.group_id AS group_id,
    n.uuid AS source_node_uuid,
    m.uuid AS target_node_uuid,
    e.created_at AS created_at
""")

# 社区边缘批量获取UUIDs模板
COMMUNITY_EDGE_GET_BY_UUIDS = Template("""
MATCH (n:Community)-[e:HAS_MEMBER]->(m:Entity | Community)
WHERE e.uuid IN $uuids
RETURN
    e.uuid As uuid,
    e.group_id AS group_id,
    n.uuid AS source_node_uuid,
    m.uuid AS target_node_uuid,
    e.created_at AS created_at
""")

# 社区边缘按组ID获取模板
COMMUNITY_EDGE_GET_BY_GROUP_IDS = Template("""
MATCH (n:Community)-[e:HAS_MEMBER]->(m:Entity | Community)
WHERE e.group_id IN $group_ids
{% if uuid_cursor %}AND e.uuid < $uuid{% endif %}
RETURN
    e.uuid As uuid,
    e.group_id AS group_id,
    n.uuid AS source_node_uuid,
    m.uuid AS target_node_uuid,
    e.created_at AS created_at
ORDER BY e.uuid DESC
{% if limit %}LIMIT $limit{% endif %}
""") 