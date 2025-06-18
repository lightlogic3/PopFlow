"""
节点查询模板集合
使用Jinja2模板引擎管理所有节点相关的Cypher查询
"""

from jinja2 import Template

# ================ 基础节点模板 ================

# 节点删除模板
NODE_DELETE = Template("""
MATCH (n:Entity|Episodic|Community {uuid: $uuid})
DETACH DELETE n
""")

# 按组ID删除节点模板
NODE_DELETE_BY_GROUP_ID = Template("""
MATCH (n:Entity|Episodic|Community {group_id: $group_id})
DETACH DELETE n
""")

# ================ 实体节点模板 ================

# 实体节点保存模板
ENTITY_NODE_SAVE = Template("""
MERGE (n:Entity {uuid: $entity_data.uuid})
SET n:$($labels)
SET n = $entity_data
WITH n CALL db.create.setNodeVectorProperty(n, "name_embedding", $entity_data.name_embedding)
RETURN n.uuid AS uuid
""")

# 实体节点获取UUID模板
ENTITY_NODE_GET_BY_UUID = Template("""
MATCH (n:Entity {uuid: $uuid})
RETURN
    n.uuid AS uuid, 
    n.name AS name,
    n.group_id AS group_id,
    n.created_at AS created_at, 
    n.summary AS summary,
    labels(n) AS labels,
    properties(n) AS attributes
""")

# 实体节点批量获取UUIDs模板
ENTITY_NODE_GET_BY_UUIDS = Template("""
MATCH (n:Entity) 
WHERE n.uuid IN $uuids
RETURN
    n.uuid AS uuid, 
    n.name AS name,
    n.group_id AS group_id,
    n.created_at AS created_at, 
    n.summary AS summary,
    labels(n) AS labels,
    properties(n) AS attributes
""")

# 实体节点按组ID获取模板
ENTITY_NODE_GET_BY_GROUP_IDS = Template("""
MATCH (n:Entity) 
WHERE n.group_id IN $group_ids
{% if uuid_cursor %}AND n.uuid < $uuid{% endif %}
RETURN
    n.uuid AS uuid, 
    n.name AS name,
    n.group_id AS group_id,
    n.created_at AS created_at, 
    n.summary AS summary,
    labels(n) AS labels,
    properties(n) AS attributes
ORDER BY n.uuid DESC
{% if limit %}LIMIT $limit{% endif %}
""")

# 加载实体节点名称嵌入模板
ENTITY_NODE_LOAD_EMBEDDING = Template("""
MATCH (n:Entity {uuid: $uuid})
RETURN n.name_embedding AS name_embedding
""")

# ================ 情节节点模板 ================

# 情节节点保存模板
EPISODIC_NODE_SAVE = Template("""
MERGE (n:Episodic {uuid: $uuid})
SET n = {
    uuid: $uuid, 
    name: $name, 
    group_id: $group_id, 
    source_description: $source_description, 
    source: $source, 
    content: $content, 
    entity_edges: $entity_edges, 
    created_at: $created_at, 
    valid_at: $valid_at
}
RETURN n.uuid AS uuid
""")

# 情节节点获取UUID模板
EPISODIC_NODE_GET_BY_UUID = Template("""
MATCH (e:Episodic {uuid: $uuid})
RETURN 
    e.content AS content,
    e.created_at AS created_at,
    e.valid_at AS valid_at,
    e.uuid AS uuid,
    e.name AS name,
    e.group_id AS group_id,
    e.source_description AS source_description,
    e.source AS source,
    e.entity_edges AS entity_edges
""")

# 情节节点批量获取UUIDs模板
EPISODIC_NODE_GET_BY_UUIDS = Template("""
MATCH (e:Episodic) 
WHERE e.uuid IN $uuids
RETURN DISTINCT
    e.content AS content,
    e.created_at AS created_at,
    e.valid_at AS valid_at,
    e.uuid AS uuid,
    e.name AS name,
    e.group_id AS group_id,
    e.source_description AS source_description,
    e.source AS source,
    e.entity_edges AS entity_edges
""")

# 情节节点按组ID获取模板
EPISODIC_NODE_GET_BY_GROUP_IDS = Template("""
MATCH (e:Episodic) 
WHERE e.group_id IN $group_ids
{% if uuid_cursor %}AND e.uuid < $uuid{% endif %}
RETURN DISTINCT
    e.content AS content,
    e.created_at AS created_at,
    e.valid_at AS valid_at,
    e.uuid AS uuid,
    e.name AS name,
    e.group_id AS group_id,
    e.source_description AS source_description,
    e.source AS source,
    e.entity_edges AS entity_edges
ORDER BY e.uuid DESC
{% if limit %}LIMIT $limit{% endif %}
""")

# 按实体节点UUID获取情节节点模板
EPISODIC_NODE_GET_BY_ENTITY_NODE_UUID = Template("""
MATCH (e:Episodic)-[r:MENTIONS]->(n:Entity {uuid: $entity_node_uuid})
RETURN DISTINCT
    e.content AS content,
    e.created_at AS created_at,
    e.valid_at AS valid_at,
    e.uuid AS uuid,
    e.name AS name,
    e.group_id AS group_id,
    e.source_description AS source_description,
    e.source AS source,
    e.entity_edges AS entity_edges
""")

# ================ 社区节点模板 ================

# 社区节点保存模板
COMMUNITY_NODE_SAVE = Template("""
MERGE (n:Community {uuid: $uuid})
SET n = {
    uuid: $uuid, 
    name: $name, 
    group_id: $group_id, 
    summary: $summary, 
    created_at: $created_at
}
WITH n CALL db.create.setNodeVectorProperty(n, "name_embedding", $name_embedding)
RETURN n.uuid AS uuid
""")

# 社区节点获取UUID模板
COMMUNITY_NODE_GET_BY_UUID = Template("""
MATCH (n:Community {uuid: $uuid})
RETURN
    n.uuid AS uuid, 
    n.name AS name,
    n.group_id AS group_id,
    n.created_at AS created_at, 
    n.summary AS summary,
    n.name_embedding AS name_embedding
""")

# 社区节点批量获取UUIDs模板
COMMUNITY_NODE_GET_BY_UUIDS = Template("""
MATCH (n:Community) 
WHERE n.uuid IN $uuids
RETURN
    n.uuid AS uuid, 
    n.name AS name,
    n.group_id AS group_id,
    n.created_at AS created_at, 
    n.summary AS summary,
    n.name_embedding AS name_embedding
""")

# 社区节点按组ID获取模板
COMMUNITY_NODE_GET_BY_GROUP_IDS = Template("""
MATCH (n:Community) 
WHERE n.group_id IN $group_ids
{% if uuid_cursor %}AND n.uuid < $uuid{% endif %}
RETURN
    n.uuid AS uuid, 
    n.name AS name,
    n.group_id AS group_id,
    n.created_at AS created_at, 
    n.summary AS summary,
    n.name_embedding AS name_embedding
ORDER BY n.uuid DESC
{% if limit %}LIMIT $limit{% endif %}
""")

# 加载社区节点名称嵌入模板
COMMUNITY_NODE_LOAD_EMBEDDING = Template("""
MATCH (c:Community {uuid: $uuid})
RETURN c.name_embedding AS name_embedding
""") 