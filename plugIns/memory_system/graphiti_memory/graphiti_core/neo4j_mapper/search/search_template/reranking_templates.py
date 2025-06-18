"""
Neo4j重排序查询模板集合
使用Jinja2模板引擎管理所有重排序相关的Cypher查询
"""

from jinja2 import Template

# 节点距离重排序模板
NODE_DISTANCE_RERANKER = Template("""
UNWIND $node_uuids AS node_uuid
MATCH p = SHORTEST 1 (center:Entity {uuid: $center_uuid})-[:RELATES_TO]-+(n:Entity {uuid: node_uuid})
RETURN length(p) AS score, node_uuid AS uuid
""")

# 情节提及重排序模板
EPISODE_MENTIONS_RERANKER = Template("""
UNWIND $node_uuids AS node_uuid 
MATCH (episode:Episodic)-[r:MENTIONS]->(n:Entity {uuid: node_uuid})
RETURN count(*) AS score, n.uuid AS uuid
""")

# 获取节点嵌入模板
GET_EMBEDDINGS_FOR_NODES = Template("""
MATCH (n:Entity)
WHERE n.uuid IN $node_uuids
RETURN DISTINCT
  n.uuid AS uuid,
  n.name_embedding AS name_embedding
""")

# 获取社区嵌入模板
GET_EMBEDDINGS_FOR_COMMUNITIES = Template("""
MATCH (c:Community)
WHERE c.uuid IN $community_uuids
RETURN DISTINCT
  c.uuid AS uuid,
  c.name_embedding AS name_embedding
""")

# 获取边嵌入模板
GET_EMBEDDINGS_FOR_EDGES = Template("""
MATCH (n:Entity)-[e:RELATES_TO]-(m:Entity)
WHERE e.uuid IN $edge_uuids
RETURN DISTINCT
  e.uuid AS uuid,
  e.fact_embedding AS fact_embedding
""") 