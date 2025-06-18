"""
社区管理相关操作
"""

from collections import defaultdict

from neo4j import AsyncDriver

from knowledge_api.utils.log_config import get_logger
from knowledge_manage.embeddings.base import EmbeddingEngine
from plugIns.memory_system.graphiti_memory.graphiti_core.config import DEFAULT_DATABASE
from plugIns.memory_system.graphiti_memory.graphiti_core.llm_client import LLMClient
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.edges import CommunityEdge
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes import EntityNode, CommunityNode, \
    get_community_node_from_record
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.edge import build_community_edges
from plugIns.memory_system.graphiti_memory.graphiti_core.utils.datetime_utils import utc_now

from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.template.community_templates import \
    REMOVE_COMMUNITIES, GET_ENTITY_COMMUNITY_TEMPLATE, GET_RELATED_COMMUNITIES_TEMPLATE
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.community.community_summarization import \
    summarize_pair, generate_summary_description

logger = get_logger()


async def remove_communities(driver: AsyncDriver):
    """移除所有社区节点
    
    参数:
        driver: Neo4j异步驱动
    """
    logger.debug("开始移除所有社区节点")
    await driver.execute_query(
        REMOVE_COMMUNITIES,
        database_=DEFAULT_DATABASE,
    )
    logger.debug("所有社区节点已移除")


async def determine_entity_community(
    driver: AsyncDriver, entity: EntityNode
) -> tuple[CommunityNode | None, bool]:
    """确定实体所属的社区
    
    参数:
        driver: Neo4j异步驱动
        entity: 实体节点
        
    返回:
        社区节点和是否为新关系的元组
    """
    logger.debug(f"为实体 {entity.uuid} 确定社区")
    
    # 步骤1: 检查节点是否已经属于某个社区
    logger.debug("检查节点是否已经属于某个社区")
    # 使用Jinja2模板渲染查询语句
    query = GET_ENTITY_COMMUNITY_TEMPLATE.render(entity_uuid=entity.uuid)
    records, _, _ = await driver.execute_query(
        query,
        database_=DEFAULT_DATABASE,
    )

    # 如果已经有社区关系，返回已存在的社区
    if len(records) > 0:
        logger.debug(f"实体 {entity.uuid} - 已存在社区关系")
        return get_community_node_from_record(records[0]), False

    # 步骤2: 如果节点没有社区，寻找与实体相关的其他实体所属的社区
    logger.debug("寻找与实体相关的其他实体所属的社区")
    # 使用Jinja2模板渲染查询语句
    query = GET_RELATED_COMMUNITIES_TEMPLATE.render(entity_uuid=entity.uuid)
    records, _, _ = await driver.execute_query(
        query,
        database_=DEFAULT_DATABASE,
    )

    # 转换记录为社区节点对象
    communities: list[CommunityNode] = [
        get_community_node_from_record(record) for record in records
    ]
    logger.debug(f"找到 {len(communities)} 个相关社区")

    # 步骤3: 统计每个相关社区的出现次数
    community_map: dict[str, int] = defaultdict(int)
    for community in communities:
        community_map[community.uuid] += 1

    # 步骤4: 找到出现次数最多的社区
    community_uuid = None
    max_count = 0
    for uuid, count in community_map.items():
        if count > max_count:
            community_uuid = uuid
            max_count = count

    # 如果没有找到任何相关社区，返回None
    if max_count == 0:
        logger.debug("没有找到合适的社区")
        return None, False

    # 步骤5: 返回出现次数最多的社区
    for community in communities:
        if community.uuid == community_uuid:
            logger.debug(f"确定社区 {community.uuid} 作为实体的新社区")
            return community, True

    # 如果执行到这里，说明出现了意外情况
    logger.warning(f"意外情况：找到了社区UUID {community_uuid}，但无法在社区列表中找到对应社区对象")
    return None, False


async def update_community(
    driver: AsyncDriver, llm_client: LLMClient, embedder: EmbeddingEngine, entity: EntityNode
):
    """更新社区
    
    根据实体更新社区信息，如果实体是社区的新成员，则将其添加到社区；
    无论是否为新成员，都会基于实体摘要更新社区摘要和名称
    
    参数:
        driver: Neo4j异步驱动
        llm_client: LLM客户端
        embedder: 嵌入引擎
        entity: 实体节点
    """
    logger.debug(f"开始更新实体 {entity.uuid} 的社区")
    
    # 步骤1: 确定实体所属的社区
    community, is_new = await determine_entity_community(driver, entity)

    # 如果没有找到合适的社区，直接返回
    if community is None:
        logger.debug("没有找到合适的社区，跳过更新")
        return

    # 步骤2: 合并实体摘要和社区摘要，生成新的社区摘要
    logger.debug("合并实体摘要和社区摘要")
    new_summary = await summarize_pair(llm_client, (entity.summary, community.summary))
    
    # 步骤3: 为更新后的社区摘要生成新的描述性名称
    logger.debug("为更新后的社区生成新名称")
    new_name = await generate_summary_description(llm_client, new_summary)

    # 步骤4: 更新社区信息
    logger.debug(f"更新社区信息: 名称 '{community.name}' -> '{new_name}'")
    community.summary = new_summary
    community.name = new_name

    # 步骤5: 如果实体是社区的新成员，创建社区边并保存
    if is_new:
        logger.debug("创建新的社区边")
        community_edge = (build_community_edges([entity], community, utc_now()))[0]
        await community_edge.save(driver)
        logger.debug(f"社区边已保存: {entity.uuid} -> {community.uuid}")

    # 步骤6: 生成社区名称的嵌入向量，用于后续的相似度搜索
    logger.debug("生成社区名称嵌入")
    await community.generate_name_embedding(embedder)

    # 步骤7: 保存更新后的社区
    logger.debug(f"保存更新后的社区 {community.uuid}")
    await community.save(driver) 