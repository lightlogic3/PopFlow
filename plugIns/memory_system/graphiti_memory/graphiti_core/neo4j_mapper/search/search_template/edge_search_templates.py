"""
Neo4j查询模板集合
使用Jinja2模板引擎管理所有Cypher查询
"""

from jinja2 import Template

# 边全文搜索模板
EDGE_FULLTEXT_SEARCH = Template("""
CALL db.index.fulltext.queryRelationships("edge_name_and_fact", $query, {limit: $limit}) 
YIELD relationship AS rel, score
MATCH (n:Entity)-[r:RELATES_TO]->(m:Entity)
WHERE r = rel AND r.group_id IN $group_ids
{% if filter_query %}{{ filter_query }}{% endif %}
RETURN 
    r.uuid AS uuid,
    r.group_id AS group_id,
    n.uuid AS source_node_uuid,
    m.uuid AS target_node_uuid,
    r.created_at AS created_at,
    r.name AS name,
    r.fact AS fact,
    r.episodes AS episodes,
    r.expired_at AS expired_at,
    r.valid_at AS valid_at,
    r.invalid_at AS invalid_at,
    properties(r) AS attributes,
    score
ORDER BY score DESC
LIMIT $limit
""")

# 边相似度搜索模板
EDGE_SIMILARITY_SEARCH = Template("""
{{ runtime_query }}
MATCH (n:Entity)-[r:RELATES_TO]->(m:Entity)
{% if group_filter %}WHERE {{ group_filter }}{% endif %}
{% if node_filter %}{% if group_filter %}AND {% else %}WHERE {% endif %}{{ node_filter }}{% endif %}
{% if filter_query %}{% if group_filter or node_filter %}AND {% else %}WHERE {% endif %}{{ filter_query }}{% endif %}
WITH r, n, m, vector.similarity.cosine(r.fact_embedding, $search_vector) AS score
WHERE score > $min_score
RETURN 
    r.uuid AS uuid,
    r.group_id AS group_id,
    n.uuid AS source_node_uuid,
    m.uuid AS target_node_uuid,
    r.created_at AS created_at,
    r.name AS name,
    r.fact AS fact,
    r.episodes AS episodes,
    r.expired_at AS expired_at,
    r.valid_at AS valid_at,
    r.invalid_at AS invalid_at,
    properties(r) AS attributes,
    score
ORDER BY score DESC
LIMIT $limit
""")

# 边BFS搜索模板
EDGE_BFS_SEARCH = Template("""
UNWIND $bfs_origin_node_uuids AS origin_uuid
MATCH path = (origin:Entity|Episodic {uuid: origin_uuid})-[:RELATES_TO|MENTIONS]->{1,{{ max_depth }}}(n:Entity)
UNWIND relationships(path) AS rel
MATCH (source)-[r:RELATES_TO]->(target)
WHERE r.uuid = rel.uuid
{% if filter_query %}{{ filter_query }}{% endif %}
WITH DISTINCT r, source, target, length(path)-1 as distance
RETURN 
    r.uuid AS uuid,
    r.group_id AS group_id,
    source.uuid AS source_node_uuid,
    target.uuid AS target_node_uuid,
    r.created_at AS created_at,
    r.name AS name,
    r.fact AS fact,
    r.episodes AS episodes,
    r.expired_at AS expired_at,
    r.valid_at AS valid_at,
    r.invalid_at AS invalid_at,
    properties(r) AS attributes,
    distance
ORDER BY distance ASC
LIMIT $limit
""")

# 获取相关边模板
GET_RELEVANT_EDGES = Template("""
{{ runtime_query }}
UNWIND $edges AS edge
MATCH (n:Entity {uuid: edge.source_node_uuid})-[e:RELATES_TO {group_id: edge.group_id}]-(m:Entity {uuid: edge.target_node_uuid})
{% if filter_query %}{{ filter_query }}{% endif %}
WITH e, edge, n, m, vector.similarity.cosine(e.fact_embedding, edge.fact_embedding) AS score
WHERE score > $min_score
WITH edge, e, n, m, score
ORDER BY score DESC
RETURN 
    edge.uuid AS search_edge_uuid,
    collect({
        uuid: e.uuid, 
        source_node_uuid: n.uuid, 
        target_node_uuid: m.uuid, 
        created_at: e.created_at, 
        name: e.name, 
        group_id: e.group_id, 
        fact: e.fact, 
        fact_embedding: e.fact_embedding, 
        episodes: e.episodes, 
        expired_at: e.expired_at, 
        valid_at: e.valid_at, 
        invalid_at: e.invalid_at, 
        attributes: properties(e),
        similarity_score: score
    })[..$limit] AS matches
""")

# 获取边失效候选模板
GET_EDGE_INVALIDATION_CANDIDATES = Template("""
{{ runtime_query }}
UNWIND $edges AS edge
MATCH (n:Entity)-[e:RELATES_TO {group_id: edge.group_id}]->(m:Entity)
WHERE n.uuid IN [edge.source_node_uuid, edge.target_node_uuid] OR m.uuid IN [edge.target_node_uuid, edge.source_node_uuid]
{% if filter_query %}{{ filter_query }}{% endif %}
WITH edge, e, n, m, vector.similarity.cosine(e.fact_embedding, edge.fact_embedding) AS score
WHERE score > $min_score
WITH edge, e, n, m, score
ORDER BY score DESC
RETURN 
    edge.uuid AS search_edge_uuid,
    collect({
        uuid: e.uuid, 
        source_node_uuid: n.uuid, 
        target_node_uuid: m.uuid, 
        created_at: e.created_at, 
        name: e.name, 
        group_id: e.group_id, 
        fact: e.fact, 
        fact_embedding: e.fact_embedding, 
        episodes: e.episodes, 
        expired_at: e.expired_at, 
        valid_at: e.valid_at, 
        invalid_at: e.invalid_at, 
        attributes: properties(e),
        similarity_score: score
    })[..$limit] AS matches
""")

# 节点全文搜索模板
NODE_FULLTEXT_SEARCH = Template("""
CALL db.index.fulltext.queryNodes("node_name_and_summary", $query, {limit: $limit}) 
YIELD node AS n, score
WHERE n:Entity
{% if filter_query %}{{ filter_query }}{% endif %}
{% if group_ids %}AND n.group_id IN $group_ids{% endif %}
{{ entity_node_return }}
ORDER BY score DESC
""")

# 节点相似度搜索模板
NODE_SIMILARITY_SEARCH = Template("""
{{ runtime_query }}
MATCH (n:Entity)
{% if group_ids %}WHERE n.group_id IN $group_ids{% endif %}
{% if filter_query %}{% if group_ids %}AND {% else %}WHERE {% endif %}{{ filter_query }}{% endif %}
WITH n, vector.similarity.cosine(n.name_embedding, $search_vector) AS score
WHERE score > $min_score
{{ entity_node_return }}
ORDER BY score DESC
LIMIT $limit
""") 