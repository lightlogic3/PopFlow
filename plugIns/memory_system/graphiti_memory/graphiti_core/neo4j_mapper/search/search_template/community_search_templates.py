"""
Neo4j社区节点搜索查询模板集合
使用Jinja2模板引擎管理所有社区节点相关的Cypher查询
"""

from jinja2 import Template

# 社区全文搜索模板
COMMUNITY_FULLTEXT_SEARCH = Template("""
CALL db.index.fulltext.queryNodes("community_name", $query, {limit: $limit}) 
YIELD node AS comm, score
{% if group_ids %}WHERE comm.group_id IN $group_ids{% endif %}
{% if filter_query %}{% if group_ids %}AND {% else %}WHERE {% endif %}{{ filter_query }}{% endif %}
RETURN
    comm.uuid AS uuid,
    comm.group_id AS group_id, 
    comm.name AS name, 
    comm.created_at AS created_at, 
    comm.summary AS summary,
    comm.name_embedding AS name_embedding,
    score
ORDER BY score DESC
LIMIT $limit
""")

# 社区相似度搜索模板
COMMUNITY_SIMILARITY_SEARCH = Template("""
{{ runtime_query }}
MATCH (comm:Community)
{% if group_ids %}WHERE comm.group_id IN $group_ids{% endif %}
{% if filter_query %}{% if group_ids %}AND {% else %}WHERE {% endif %}{{ filter_query }}{% endif %}
WITH comm, vector.similarity.cosine(comm.name_embedding, $search_vector) AS score
WHERE score > $min_score
RETURN
    comm.uuid AS uuid,
    comm.group_id AS group_id,
    comm.name AS name, 
    comm.created_at AS created_at, 
    comm.summary AS summary,
    comm.name_embedding AS name_embedding,
    score
ORDER BY score DESC
LIMIT $limit
""")

# 获取社区成员模板
GET_COMMUNITY_MEMBERS = Template("""
MATCH (c:Community {uuid: $community_uuid})-[:HAS_MEMBER]->(n:Entity)
RETURN DISTINCT
    n.uuid As uuid, 
    n.name AS name,
    n.group_id AS group_id,
    n.created_at AS created_at, 
    n.summary AS summary,
    labels(n) AS labels,
    properties(n) AS attributes
LIMIT $limit
""")

# 获取节点所属社区模板
GET_COMMUNITIES_BY_NODE = Template("""
MATCH (c:Community)-[:HAS_MEMBER]->(n:Entity {uuid: $node_uuid})
RETURN DISTINCT
    c.uuid AS uuid,
    c.group_id AS group_id,
    c.name AS name, 
    c.created_at AS created_at, 
    c.summary AS summary,
    c.name_embedding AS name_embedding
LIMIT $limit
""") 