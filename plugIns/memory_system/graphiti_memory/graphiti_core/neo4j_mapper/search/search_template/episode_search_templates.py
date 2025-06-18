"""
Neo4j情节节点搜索查询模板集合
使用Jinja2模板引擎管理所有情节节点相关的Cypher查询
"""

from jinja2 import Template

# 情节全文搜索模板
EPISODE_FULLTEXT_SEARCH = Template("""
CALL db.index.fulltext.queryNodes("episode_content", $query, {limit: $limit}) 
YIELD node AS episode, score
MATCH (e:Episodic)
WHERE e.uuid = episode.uuid
{% if group_ids %}AND e.group_id IN $group_ids{% endif %}
{% if filter_query %}{{ filter_query }}{% endif %}
RETURN 
    e.content AS content,
    e.created_at AS created_at,
    e.valid_at AS valid_at,
    e.uuid AS uuid,
    e.name AS name,
    e.group_id AS group_id,
    e.source_description AS source_description,
    e.source AS source,
    e.entity_edges AS entity_edges,
    score
ORDER BY score DESC
LIMIT $limit
""")

# 获取与实体节点相关的情节模板
GET_EPISODES_BY_ENTITY = Template("""
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
LIMIT $limit
""")

# 获取由实体边提及的情节模板
GET_EPISODES_BY_MENTIONS = Template("""
UNWIND $edge_uuids AS edge_uuid
MATCH (e:Episodic)
WHERE edge_uuid IN e.entity_edges
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
LIMIT $limit
""") 