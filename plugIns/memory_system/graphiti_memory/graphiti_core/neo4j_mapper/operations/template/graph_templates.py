"""
图数据操作相关的查询模板，包括索引和数据检索
"""

import jinja2
from typing_extensions import LiteralString

# 索引操作模板
SHOW_INDEXES_TEMPLATE: LiteralString = """
SHOW INDEXES YIELD name
"""

DROP_INDEX_TEMPLATE: LiteralString = """DROP INDEX $name"""

# 创建常规索引的模板
CREATE_ENTITY_UUID_INDEX_TEMPLATE: LiteralString = 'CREATE INDEX entity_uuid IF NOT EXISTS FOR (n:Entity) ON (n.uuid)'
CREATE_EPISODE_UUID_INDEX_TEMPLATE: LiteralString = 'CREATE INDEX episode_uuid IF NOT EXISTS FOR (n:Episodic) ON (n.uuid)'
CREATE_COMMUNITY_UUID_INDEX_TEMPLATE: LiteralString = 'CREATE INDEX community_uuid IF NOT EXISTS FOR (n:Community) ON (n.uuid)'
CREATE_RELATION_UUID_INDEX_TEMPLATE: LiteralString = 'CREATE INDEX relation_uuid IF NOT EXISTS FOR ()-[e:RELATES_TO]-() ON (e.uuid)'
CREATE_MENTION_UUID_INDEX_TEMPLATE: LiteralString = 'CREATE INDEX mention_uuid IF NOT EXISTS FOR ()-[e:MENTIONS]-() ON (e.uuid)'
CREATE_HAS_MEMBER_UUID_INDEX_TEMPLATE: LiteralString = 'CREATE INDEX has_member_uuid IF NOT EXISTS FOR ()-[e:HAS_MEMBER]-() ON (e.uuid)'
CREATE_ENTITY_GROUP_ID_INDEX_TEMPLATE: LiteralString = 'CREATE INDEX entity_group_id IF NOT EXISTS FOR (n:Entity) ON (n.group_id)'
CREATE_EPISODE_GROUP_ID_INDEX_TEMPLATE: LiteralString = 'CREATE INDEX episode_group_id IF NOT EXISTS FOR (n:Episodic) ON (n.group_id)'
CREATE_RELATION_GROUP_ID_INDEX_TEMPLATE: LiteralString = 'CREATE INDEX relation_group_id IF NOT EXISTS FOR ()-[e:RELATES_TO]-() ON (e.group_id)'
CREATE_MENTION_GROUP_ID_INDEX_TEMPLATE: LiteralString = 'CREATE INDEX mention_group_id IF NOT EXISTS FOR ()-[e:MENTIONS]-() ON (e.group_id)'
CREATE_NAME_ENTITY_INDEX_TEMPLATE: LiteralString = 'CREATE INDEX name_entity_index IF NOT EXISTS FOR (n:Entity) ON (n.name)'
CREATE_CREATED_AT_ENTITY_INDEX_TEMPLATE: LiteralString = 'CREATE INDEX created_at_entity_index IF NOT EXISTS FOR (n:Entity) ON (n.created_at)'
CREATE_CREATED_AT_EPISODIC_INDEX_TEMPLATE: LiteralString = 'CREATE INDEX created_at_episodic_index IF NOT EXISTS FOR (n:Episodic) ON (n.created_at)'
CREATE_VALID_AT_EPISODIC_INDEX_TEMPLATE: LiteralString = 'CREATE INDEX valid_at_episodic_index IF NOT EXISTS FOR (n:Episodic) ON (n.valid_at)'
CREATE_NAME_EDGE_INDEX_TEMPLATE: LiteralString = 'CREATE INDEX name_edge_index IF NOT EXISTS FOR ()-[e:RELATES_TO]-() ON (e.name)'
CREATE_CREATED_AT_EDGE_INDEX_TEMPLATE: LiteralString = 'CREATE INDEX created_at_edge_index IF NOT EXISTS FOR ()-[e:RELATES_TO]-() ON (e.created_at)'
CREATE_EXPIRED_AT_EDGE_INDEX_TEMPLATE: LiteralString = 'CREATE INDEX expired_at_edge_index IF NOT EXISTS FOR ()-[e:RELATES_TO]-() ON (e.expired_at)'
CREATE_VALID_AT_EDGE_INDEX_TEMPLATE: LiteralString = 'CREATE INDEX valid_at_edge_index IF NOT EXISTS FOR ()-[e:RELATES_TO]-() ON (e.valid_at)'
CREATE_INVALID_AT_EDGE_INDEX_TEMPLATE: LiteralString = 'CREATE INDEX invalid_at_edge_index IF NOT EXISTS FOR ()-[e:RELATES_TO]-() ON (e.invalid_at)'

# 创建全文索引的模板
CREATE_EPISODE_CONTENT_FULLTEXT_INDEX_TEMPLATE: LiteralString = """CREATE FULLTEXT INDEX episode_content IF NOT EXISTS 
FOR (e:Episodic) ON EACH [e.content, e.source, e.source_description, e.group_id]"""

CREATE_NODE_NAME_SUMMARY_FULLTEXT_INDEX_TEMPLATE: LiteralString = """CREATE FULLTEXT INDEX node_name_and_summary IF NOT EXISTS 
FOR (n:Entity) ON EACH [n.name, n.summary, n.group_id]"""

CREATE_COMMUNITY_NAME_FULLTEXT_INDEX_TEMPLATE: LiteralString = """CREATE FULLTEXT INDEX community_name IF NOT EXISTS 
FOR (n:Community) ON EACH [n.name, n.group_id]"""

CREATE_EDGE_NAME_FACT_FULLTEXT_INDEX_TEMPLATE: LiteralString = """CREATE FULLTEXT INDEX edge_name_and_fact IF NOT EXISTS 
FOR ()-[e:RELATES_TO]-() ON EACH [e.name, e.fact, e.group_id]"""

# 数据操作模板
CLEAR_DATA_BY_GROUP_TEMPLATE: jinja2.Template = jinja2.Template("""
MATCH (n) 
WHERE n.group_id = $group_id
DETACH DELETE n
""")

CLEAR_ALL_DATA_TEMPLATE: LiteralString = """
MATCH (n) 
DETACH DELETE n
"""

RETRIEVE_EPISODES_TEMPLATE: jinja2.Template = jinja2.Template("""
MATCH (n:Episodic) 
WHERE {{ conditions }}
RETURN n 
ORDER BY n.valid_at DESC 
SKIP $offset LIMIT $limit
""")

# 按时间范围检索剧情节点的模板
RETRIEVE_EPISODES_BY_REFERENCE_TIME_TEMPLATE: jinja2.Template = jinja2.Template("""
MATCH (e:Episodic) WHERE e.valid_at <= $reference_time
{% if group_ids %}
AND e.group_id IN $group_ids
{% endif %}
{% if source %}
AND e.source = $source
{% endif %}
RETURN e.content AS content,
       e.created_at AS created_at,
       e.valid_at AS valid_at,
       e.uuid AS uuid,
       e.group_id AS group_id,
       e.name AS name,
       e.source_description AS source_description,
       e.source AS source
ORDER BY e.valid_at DESC
LIMIT $num_episodes
""") 