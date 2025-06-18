"""
Neo4j节点搜索查询模板集合
使用Jinja2模板引擎管理所有节点相关的Cypher查询
"""

from jinja2 import Template

# 节点全文搜索模板
NODE_FULLTEXT_SEARCH = Template("""
CALL db.index.fulltext.queryNodes("node_name_and_summary", $query, {limit: $limit}) 
YIELD node AS n, score
WHERE n:Entity
{% if filter_query %}{{ filter_query }}{% endif %}
{% if group_ids %}AND n.group_id IN $group_ids{% endif %}
RETURN
    n.uuid As uuid, 
    n.name AS name,
    n.group_id AS group_id,
    n.created_at AS created_at, 
    n.summary AS summary,
    labels(n) AS labels,
    properties(n) AS attributes,
    score
ORDER BY score DESC
LIMIT $limit
""")

# 节点相似度搜索模板
NODE_SIMILARITY_SEARCH = Template("""
{{ runtime_query }}
MATCH (n:Entity)
{% if group_ids %}WHERE n.group_id IN $group_ids{% endif %}
{% if filter_query %}{% if group_ids %}AND {% else %}WHERE {% endif %}{{ filter_query }}{% endif %}
WITH n, vector.similarity.cosine(n.name_embedding, $search_vector) AS score
WHERE score > $min_score
RETURN
    n.uuid As uuid, 
    n.name AS name,
    n.group_id AS group_id,
    n.created_at AS created_at, 
    n.summary AS summary,
    labels(n) AS labels,
    properties(n) AS attributes,
    score
ORDER BY score DESC
LIMIT $limit
""")

# 节点BFS搜索模板
NODE_BFS_SEARCH = Template("""
UNWIND $bfs_origin_node_uuids AS origin_uuid
MATCH path = (origin:Entity|Episodic {uuid: origin_uuid})-[:RELATES_TO|MENTIONS]->{1,{{ max_depth }}}(n:Entity)
WHERE n.group_id = origin.group_id
{% if filter_query %}{{ filter_query }}{% endif %}
RETURN DISTINCT
    n.uuid As uuid, 
    n.name AS name,
    n.group_id AS group_id,
    n.created_at AS created_at, 
    n.summary AS summary,
    labels(n) AS labels,
    properties(n) AS attributes,
    length(path) AS distance
ORDER BY distance ASC
LIMIT $limit
""")

# 获取相关节点模板
GET_RELEVANT_NODES = Template("""
{{ runtime_query }}
UNWIND $nodes AS node
MATCH (n:Entity {group_id: $group_id})
{% if filter_query %}{{ filter_query }}{% endif %}
WITH node, n, vector.similarity.cosine(n.name_embedding, node.name_embedding) AS score
WHERE score > $min_score
WITH node, collect(n)[..$limit] AS top_vector_nodes, collect(n.uuid) AS vector_node_uuids

CALL db.index.fulltext.queryNodes("node_name_and_summary", node.fulltext_query, {limit: $limit}) 
YIELD node AS m
WHERE m.group_id = $group_id
WITH node, top_vector_nodes, vector_node_uuids, collect(m) AS fulltext_nodes

WITH node, 
     top_vector_nodes, 
     [m IN fulltext_nodes WHERE NOT m.uuid IN vector_node_uuids] AS filtered_fulltext_nodes

WITH node, top_vector_nodes + filtered_fulltext_nodes AS combined_nodes

UNWIND combined_nodes AS combined_node
WITH node, collect(DISTINCT combined_node) AS deduped_nodes

RETURN 
  node.uuid AS search_node_uuid,
  [x IN deduped_nodes | {
    uuid: x.uuid, 
    name: x.name,
    name_embedding: x.name_embedding,
    group_id: x.group_id,
    created_at: x.created_at,
    summary: x.summary,
    labels: labels(x),
    attributes: properties(x)
  }] AS matches
""")

# 获取情节中提及的节点模板
GET_MENTIONED_NODES = Template("""
MATCH (episode:Episodic)-[:MENTIONS]->(n:Entity) 
WHERE episode.uuid IN $episode_uuids
RETURN DISTINCT
    n.uuid As uuid, 
    n.group_id AS group_id,
    n.name AS name,
    n.created_at AS created_at, 
    n.summary AS summary,
    labels(n) AS labels,
    properties(n) AS attributes
""") 