"""
社区构建相关操作
"""

import asyncio

from neo4j import AsyncDriver

from knowledge_api.utils.log_config import get_logger
from plugIns.memory_system.graphiti_memory.graphiti_core.llm_client import LLMClient
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.edges import CommunityEdge
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes import EntityNode, CommunityNode
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.edge import build_community_edges
from plugIns.memory_system.graphiti_memory.graphiti_core.utils.datetime_utils import utc_now

from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.community.community_cluster import get_community_clusters
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.community.community_summarization import summarize_pair, generate_summary_description
from plugIns.memory_system.graphiti_memory.graphiti_core.utils.utils import semaphore_gather

# 设置社区构建的最大并发数
MAX_COMMUNITY_BUILD_CONCURRENCY = 10

logger = get_logger()


async def build_community(
    llm_client: LLMClient, community_cluster: list[EntityNode]
) -> tuple[CommunityNode, list[CommunityEdge]]:
    """构建一个社区
    
    参数:
        llm_client: LLM客户端
        community_cluster: 社区集群中的实体节点列表
        
    返回:
        社区节点和社区边的元组
    """
    logger.debug(f"开始构建社区，集群包含 {len(community_cluster)} 个节点")
    
    # 从每个实体节点获取摘要
    summaries = [entity.summary for entity in community_cluster]
    length = len(summaries)
    
    # 递归地合并摘要，直到只剩一个摘要
    # 实现方式为二分法，每次取两个摘要合并为一个，直到最后只剩一个摘要
    logger.debug(f"开始合并摘要，初始摘要数: {length}")
    while length > 1:
        logger.debug(f"当前摘要数: {length}")
        
        # 处理奇数个摘要的情况
        odd_one_out: str | None = None
        if length % 2 == 1:
            odd_one_out = summaries.pop()
            length -= 1
            logger.debug(f"有奇数个摘要，移除最后一个留待后续处理")
        
        # 并行处理摘要配对合并
        logger.debug(f"开始并行合并 {length//2} 对摘要")
        
        # 计算摘要中点，将摘要分为左右两部分
        mid = int(length / 2)
        left_summaries = summaries[:mid]
        right_summaries = summaries[mid:]
        
        # 并行执行摘要合并
        new_summaries: list[str] = list(
            await semaphore_gather(
                *[
                    summarize_pair(llm_client, (str(left_summary), str(right_summary)))
                    for left_summary, right_summary in zip(left_summaries, right_summaries, strict=False)
                ]
            )
        )
        logger.debug(f"合并后得到 {len(new_summaries)} 个新摘要")
        
        # 如果有剩余的奇数摘要，添加回列表
        if odd_one_out is not None:
            new_summaries.append(odd_one_out)
            logger.debug("将之前移除的奇数摘要添加回列表")
            
        summaries = new_summaries
        length = len(summaries)
        logger.debug(f"合并后摘要数: {length}")

    # 取最终合并后的唯一摘要
    summary = summaries[0]
    logger.debug(f"最终摘要生成完成，长度: {len(summary)}")
    
    # 为社区生成名称描述
    logger.debug("为社区生成名称描述")
    name = await generate_summary_description(llm_client, summary)
    
    # 创建社区节点
    now = utc_now()
    logger.debug(f"创建社区节点，名称: {name}")
    community_node = CommunityNode(
        name=name,
        group_id=community_cluster[0].group_id,
        labels=['Community'],
        created_at=now,
        summary=summary,
    )
    
    # 构建社区边 - 连接社区和实体节点的关系
    logger.debug("构建社区边")
    community_edges = build_community_edges(community_cluster, community_node, now)
    logger.debug(f"为 {len(community_cluster)} 个实体创建了 {len(community_edges)} 条社区边")

    # 将调试信息打印到日志
    logger.debug(f"社区构建完成: {community_node.name}, {len(community_edges)} 条边")
    
    return community_node, community_edges


async def build_communities(
    driver: AsyncDriver, llm_client: LLMClient, group_ids: list[str] | None
) -> tuple[list[CommunityNode], list[CommunityEdge]]:
    """构建多个社区
    
    参数:
        driver: Neo4j异步驱动
        llm_client: LLM客户端
        group_ids: 组ID列表，如果为None则获取所有组
        
    返回:
        社区节点列表和社区边列表的元组
    """
    logger.debug(f"开始构建社区，组ID: {group_ids}")
    
    # 首先获取社区集群
    community_clusters = await get_community_clusters(driver, group_ids)
    logger.debug(f"获取到 {len(community_clusters)} 个社区集群")

    # 创建并发限制信号量
    semaphore = asyncio.Semaphore(MAX_COMMUNITY_BUILD_CONCURRENCY)
    logger.debug(f"设置并发限制: {MAX_COMMUNITY_BUILD_CONCURRENCY}")

    # 创建并发限制的社区构建函数
    async def limited_build_community(cluster):
        logger.debug(f"开始处理包含 {len(cluster)} 个节点的集群")
        async with semaphore:
            return await build_community(llm_client, cluster)

    # 并行构建所有社区
    logger.debug("开始并行构建社区")
    communities: list[tuple[CommunityNode, list[CommunityEdge]]] = list(
        await semaphore_gather(
            *[limited_build_community(cluster) for cluster in community_clusters]
        )
    )
    logger.debug(f"成功构建 {len(communities)} 个社区")

    # 整理返回结果
    community_nodes: list[CommunityNode] = []
    community_edges: list[CommunityEdge] = []
    
    # 将所有社区的节点和边收集到列表中
    for community in communities:
        community_nodes.append(community[0])
        community_edges.extend(community[1])
    
    logger.debug(f"总共构建了 {len(community_nodes)} 个社区节点和 {len(community_edges)} 条社区边")
    return community_nodes, community_edges 