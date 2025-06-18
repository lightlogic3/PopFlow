"""
社区操作相关的数据库查询模板
"""
from typing_extensions import LiteralString
from jinja2 import Template

# 获取所有实体组ID
GET_GROUP_IDS:LiteralString = """
MATCH (n:Entity WHERE n.group_id IS NOT NULL)
RETURN 
    collect(DISTINCT n.group_id) AS group_ids
"""

# 获取指定组ID和UUID的实体与其他实体的关系
GET_ENTITY_RELATIONSHIPS_TEMPLATE = Template("""
MATCH (n:Entity {group_id: "{{ group_id }}", uuid: "{{ uuid }}"})-[r:RELATES_TO]-(m: Entity {group_id: "{{ group_id }}"})
WITH count(r) AS count, m.uuid AS uuid
RETURN
    uuid,
    count
""")

# 删除所有社区
REMOVE_COMMUNITIES:LiteralString = """
MATCH (c:Community)
DETACH DELETE c
"""

# 查找实体所属的社区
GET_ENTITY_COMMUNITY_TEMPLATE = Template("""
MATCH (c:Community)-[:HAS_MEMBER]->(n:Entity {uuid: "{{ entity_uuid }}"})
RETURN
    c.uuid As uuid, 
    c.name AS name,
    c.group_id AS group_id,
    c.created_at AS created_at, 
    c.summary AS summary
""")

# 查找与实体相关的社区
GET_RELATED_COMMUNITIES_TEMPLATE = Template("""
MATCH (c:Community)-[:HAS_MEMBER]->(m:Entity)-[:RELATES_TO]-(n:Entity {uuid: "{{ entity_uuid }}"})
RETURN
    c.uuid As uuid, 
    c.name AS name,
    c.group_id AS group_id,
    c.created_at AS created_at, 
    c.summary AS summary
""") 