"""
图数据库索引和约束相关操作
"""

from neo4j import AsyncDriver

from knowledge_api.utils.log_config import get_logger
from plugIns.memory_system.graphiti_memory.graphiti_core.config import DEFAULT_DATABASE
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.template.graph_templates import (
    SHOW_INDEXES_TEMPLATE,
    DROP_INDEX_TEMPLATE,
    CREATE_ENTITY_UUID_INDEX_TEMPLATE,
    CREATE_EPISODE_UUID_INDEX_TEMPLATE,
    CREATE_COMMUNITY_UUID_INDEX_TEMPLATE,
    CREATE_RELATION_UUID_INDEX_TEMPLATE,
    CREATE_MENTION_UUID_INDEX_TEMPLATE,
    CREATE_HAS_MEMBER_UUID_INDEX_TEMPLATE,
    CREATE_ENTITY_GROUP_ID_INDEX_TEMPLATE,
    CREATE_EPISODE_GROUP_ID_INDEX_TEMPLATE,
    CREATE_RELATION_GROUP_ID_INDEX_TEMPLATE,
    CREATE_MENTION_GROUP_ID_INDEX_TEMPLATE,
    CREATE_NAME_ENTITY_INDEX_TEMPLATE,
    CREATE_CREATED_AT_ENTITY_INDEX_TEMPLATE,
    CREATE_CREATED_AT_EPISODIC_INDEX_TEMPLATE,
    CREATE_VALID_AT_EPISODIC_INDEX_TEMPLATE,
    CREATE_NAME_EDGE_INDEX_TEMPLATE,
    CREATE_CREATED_AT_EDGE_INDEX_TEMPLATE,
    CREATE_EXPIRED_AT_EDGE_INDEX_TEMPLATE,
    CREATE_VALID_AT_EDGE_INDEX_TEMPLATE,
    CREATE_INVALID_AT_EDGE_INDEX_TEMPLATE,
    CREATE_EPISODE_CONTENT_FULLTEXT_INDEX_TEMPLATE,
    CREATE_NODE_NAME_SUMMARY_FULLTEXT_INDEX_TEMPLATE,
    CREATE_COMMUNITY_NAME_FULLTEXT_INDEX_TEMPLATE,
    CREATE_EDGE_NAME_FACT_FULLTEXT_INDEX_TEMPLATE,
)
from plugIns.memory_system.graphiti_memory.graphiti_core.utils.utils import semaphore_gather

logger = get_logger()


async def build_indices_and_constraints(driver: AsyncDriver, delete_existing: bool = False):
    """构建数据库索引和约束
    
    参数:
        driver: Neo4j驱动
        delete_existing: 是否删除已存在的索引
    """
    if delete_existing:
        logger.info("删除现有的所有索引")
        records, _, _ = await driver.execute_query(
            SHOW_INDEXES_TEMPLATE,
            database_=DEFAULT_DATABASE,
        )
        index_names = [record['name'] for record in records]
        await semaphore_gather(
            *[
                driver.execute_query(
                    DROP_INDEX_TEMPLATE,
                    name=name,
                    database_=DEFAULT_DATABASE,
                )
                for name in index_names
            ]
        )

    logger.debug("开始构建数据库索引")
    
    # 定义常规索引
    range_indices = [
        CREATE_ENTITY_UUID_INDEX_TEMPLATE,
        CREATE_EPISODE_UUID_INDEX_TEMPLATE,
        CREATE_COMMUNITY_UUID_INDEX_TEMPLATE,
        CREATE_RELATION_UUID_INDEX_TEMPLATE,
        CREATE_MENTION_UUID_INDEX_TEMPLATE,
        CREATE_HAS_MEMBER_UUID_INDEX_TEMPLATE,
        CREATE_ENTITY_GROUP_ID_INDEX_TEMPLATE,
        CREATE_EPISODE_GROUP_ID_INDEX_TEMPLATE,
        CREATE_RELATION_GROUP_ID_INDEX_TEMPLATE,
        CREATE_MENTION_GROUP_ID_INDEX_TEMPLATE,
        CREATE_NAME_ENTITY_INDEX_TEMPLATE,
        CREATE_CREATED_AT_ENTITY_INDEX_TEMPLATE,
        CREATE_CREATED_AT_EPISODIC_INDEX_TEMPLATE,
        CREATE_VALID_AT_EPISODIC_INDEX_TEMPLATE,
        CREATE_NAME_EDGE_INDEX_TEMPLATE,
        CREATE_CREATED_AT_EDGE_INDEX_TEMPLATE,
        CREATE_EXPIRED_AT_EDGE_INDEX_TEMPLATE,
        CREATE_VALID_AT_EDGE_INDEX_TEMPLATE,
        CREATE_INVALID_AT_EDGE_INDEX_TEMPLATE,
    ]

    # 定义全文索引
    fulltext_indices = [
        CREATE_EPISODE_CONTENT_FULLTEXT_INDEX_TEMPLATE,
        CREATE_NODE_NAME_SUMMARY_FULLTEXT_INDEX_TEMPLATE,
        CREATE_COMMUNITY_NAME_FULLTEXT_INDEX_TEMPLATE,
        CREATE_EDGE_NAME_FACT_FULLTEXT_INDEX_TEMPLATE,
    ]

    index_queries = range_indices + fulltext_indices

    # 并行执行所有索引创建查询
    logger.debug(f"执行 {len(index_queries)} 条索引创建查询")
    await semaphore_gather(
        *[
            driver.execute_query(
                query,
                database_=DEFAULT_DATABASE,
            )
            for query in index_queries
        ]
    )
    logger.info("索引和约束构建完成") 