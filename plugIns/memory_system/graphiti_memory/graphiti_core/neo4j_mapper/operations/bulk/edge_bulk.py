"""
边批量处理模块
提供用于批量处理边的函数
"""

from collections import defaultdict
from typing import TypeVar

from neo4j import AsyncDriver

from knowledge_api.utils.log_config import get_logger
from plugIns.memory_system.graphiti_memory.graphiti_core.llm_client import LLMClient
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.edges import Edge, EntityEdge
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.models.search_models import SearchFilters
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes import EpisodicNode
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.bulk.helpers import CHUNK_SIZE
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.edge import dedupe_edge_list, dedupe_extracted_edges
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.temporal_operations import extract_edge_dates
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.search.utils import get_relevant_edges
from plugIns.memory_system.graphiti_memory.graphiti_core.utils.datetime_utils import utc_now
from plugIns.memory_system.graphiti_memory.graphiti_core.utils.utils import semaphore_gather

logger = get_logger()

E = TypeVar('E', bound=Edge)


def resolve_edge_pointers(edges: list[E], uuid_map: dict[str, str]) -> list[E]:
    """解析边的指针，替换边的源节点和目标节点UUID
    
    参数:
        edges: 边列表
        uuid_map: UUID映射字典
        
    返回:
        更新后的边列表
    """
    logger.debug(f"开始解析 {len(edges)} 条边的指针")
    updated_count = 0
    
    for edge in edges:
        source_uuid = edge.source_node_uuid
        target_uuid = edge.target_node_uuid
        new_source = uuid_map.get(source_uuid, source_uuid)
        new_target = uuid_map.get(target_uuid, target_uuid)
        
        if source_uuid != new_source or target_uuid != new_target:
            updated_count += 1
            
        edge.source_node_uuid = new_source
        edge.target_node_uuid = new_target
    
    logger.debug(f"完成边指针解析，更新了 {updated_count} 条边")
    return edges


async def dedupe_edges_bulk(
    driver: AsyncDriver, llm_client: LLMClient, extracted_edges: list[EntityEdge]
) -> list[EntityEdge]:
    """批量去重提取的边
    
    参数:
        driver: Neo4j异步驱动
        llm_client: LLM客户端
        extracted_edges: 提取的边列表
        
    返回:
        去重后的边列表
    """
    logger.debug(f"开始批量去重 {len(extracted_edges)} 条边")
    
    # 首先压缩边
    compressed_edges = await compress_edges(llm_client, extracted_edges)
    logger.debug(f"压缩后的边数: {len(compressed_edges)}")

    # 将边分成小块以并行处理
    edge_chunks = [
        compressed_edges[i : i + CHUNK_SIZE] for i in range(0, len(compressed_edges), CHUNK_SIZE)
    ]
    logger.debug(f"将边分为 {len(edge_chunks)} 个块进行处理")

    # 并行获取每个块的相关现有边
    relevant_edges_chunks = list(
        await semaphore_gather(
            *[get_relevant_edges(driver, edge_chunk, SearchFilters()) for edge_chunk in edge_chunks]
        )
    )
    
    # 并行去重每个块
    resolved_edge_chunks = list(
        await semaphore_gather(
            *[
                dedupe_extracted_edges(llm_client, edge_chunk, relevant_edges_chunks[i])
                for i, edge_chunk in enumerate(edge_chunks)
            ]
        )
    )

    # 合并结果
    edges = [edge for edge_chunk in resolved_edge_chunks for edge in edge_chunk]
    logger.info(f"批量去重完成，最终边数: {len(edges)}")
    return edges


async def compress_edges(llm_client: LLMClient, edges: list[EntityEdge]) -> list[EntityEdge]:
    """压缩边，去除重复的边
    
    参数:
        llm_client: LLM客户端
        edges: 边列表
        
    返回:
        压缩后的边列表
    """
    if len(edges) == 0:
        return edges
        
    logger.debug(f"开始压缩 {len(edges)} 条边")
    
    # 只去重相同节点对之间的边
    edge_chunks = chunk_edges_by_nodes(edges)
    logger.debug(f"将边按节点对分为 {len(edge_chunks)} 个块")

    # 并行处理每个块
    results = await semaphore_gather(
        *[dedupe_edge_list(llm_client, chunk) for chunk in edge_chunks]
    )

    # 合并结果
    compressed_edges = []
    for edge_chunk in results:
        compressed_edges += edge_chunk

    # 检查是否已移除所有重复项
    logger.debug(f"压缩后的边数: {len(compressed_edges)}，原边数: {len(edges)}")
    if len(compressed_edges) == len(edges):
        return compressed_edges

    # 如果还有重复，递归压缩
    return await compress_edges(llm_client, compressed_edges)


def chunk_edges_by_nodes(edges: list[EntityEdge]) -> list[list[EntityEdge]]:
    """根据边的源节点和目标节点将边分块
    
    参数:
        edges: 边列表
        
    返回:
        边块列表
    """
    # 只去重相同节点对之间的边
    edge_chunk_map: dict[str, list[EntityEdge]] = defaultdict(list)
    loop_edges = 0
    
    for edge in edges:
        # 跳过自循环边
        if edge.source_node_uuid == edge.target_node_uuid:
            loop_edges += 1
            continue

        # 保持节点顺序一致，方向无关
        pointers = [edge.source_node_uuid, edge.target_node_uuid]
        pointers.sort()

        # 将边添加到对应的块中
        edge_chunk_map[pointers[0] + pointers[1]].append(edge)

    if loop_edges > 0:
        logger.debug(f"跳过了 {loop_edges} 条自循环边")
        
    # 将映射转换为块列表
    edge_chunks = [chunk for chunk in edge_chunk_map.values()]
    return edge_chunks


async def extract_edge_dates_bulk(
    llm_client: LLMClient,
    extracted_edges: list[EntityEdge],
    episode_pairs: list[tuple[EpisodicNode, list[EpisodicNode]]],
) -> list[EntityEdge]:
    """批量提取边的日期信息
    
    参数:
        llm_client: LLM客户端
        extracted_edges: 提取的边列表
        episode_pairs: 剧情节点与历史剧情节点的元组列表
        
    返回:
        更新后的边列表
    """
    logger.debug(f"开始批量提取 {len(extracted_edges)} 条边的日期信息")
    
    # 筛选有剧情ID的边
    edges = []
    for edge in extracted_edges:
        if edge.episodes is not None and len(edge.episodes) > 0:
            edges.append(edge)
        else:
            logger.warning(f"边 {edge.uuid} 没有关联的剧情ID，跳过日期提取")
            
    logger.debug(f"有效边数: {len(edges)}，无效边数: {len(extracted_edges) - len(edges)}")

    # 创建剧情UUID映射
    episode_uuid_map = {
        episode.uuid: (episode, previous_episodes) for episode, previous_episodes in episode_pairs
    }
    logger.debug(f"创建剧情UUID映射，大小: {len(episode_uuid_map)}")

    # 并行提取每条边的日期信息
    missing_episodes = 0
    valid_edges = []
    
    for edge in edges:
        if edge.episodes[0] not in episode_uuid_map:
            missing_episodes += 1
            continue
        valid_edges.append(edge)
            
    if missing_episodes > 0:
        logger.warning(f"{missing_episodes} 条边的剧情UUID不在映射中")
    
    logger.debug(f"开始并行提取 {len(valid_edges)} 条边的日期信息")
    results = await semaphore_gather(
        *[
            extract_edge_dates(
                llm_client,
                edge,
                episode_uuid_map[edge.episodes[0]][0],
                episode_uuid_map[edge.episodes[0]][1],
            )
            for edge in valid_edges
        ]
    )

    # 更新边的日期信息
    updated_count = 0
    expired_count = 0
    for i, result in enumerate(results):
        valid_at, invalid_at = result
        edge = valid_edges[i]

        if valid_at or invalid_at:
            updated_count += 1
            
        edge.valid_at = valid_at
        edge.invalid_at = invalid_at
        
        if edge.invalid_at:
            edge.expired_at = utc_now()
            expired_count += 1

    logger.info(f"完成日期提取，更新了 {updated_count} 条边，{expired_count} 条边已过期")
    return edges 