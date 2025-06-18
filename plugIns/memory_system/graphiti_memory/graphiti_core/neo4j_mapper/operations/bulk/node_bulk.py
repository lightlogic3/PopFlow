"""
节点批量处理模块
提供用于批量处理节点的函数，包括历史剧情检索、节点去重等操作
"""

from math import ceil, sqrt
import numpy as np

from neo4j import AsyncDriver
from numpy import dot
from typing import Dict, List, Tuple

from knowledge_api.utils.log_config import get_logger
from plugIns.memory_system.graphiti_memory.graphiti_core.config import EPISODE_WINDOW_LEN
from plugIns.memory_system.graphiti_memory.graphiti_core.llm_client import LLMClient
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.models.search_models import SearchFilters
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes import EpisodicNode, EntityNode
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations import retrieve_episodes, dedupe_extracted_nodes, dedupe_node_list
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.bulk.helpers import CHUNK_SIZE, \
    compress_uuid_map
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.search.utils import get_relevant_nodes
from plugIns.memory_system.graphiti_memory.graphiti_core.utils.utils import semaphore_gather

logger = get_logger()


async def retrieve_previous_episodes_bulk(
    driver: AsyncDriver, episodes: list[EpisodicNode]
) -> list[tuple[EpisodicNode, list[EpisodicNode]]]:
    """批量检索每个剧情节点的历史剧情
    
    参数:
        driver: Neo4j异步驱动
        episodes: 剧情节点列表
        
    返回:
        剧情节点与其对应历史剧情节点的元组列表
    """
    logger.debug(f"开始批量检索 {len(episodes)} 个剧情节点的历史剧情")
    
    # 并行检索每个剧情的历史剧情
    previous_episodes_list = await semaphore_gather(
        *[
            retrieve_episodes(
                driver, episode.valid_at, last_n=EPISODE_WINDOW_LEN, group_ids=[episode.group_id]
            )
            for episode in episodes
        ]
    )
    
    # 将每个剧情节点与其历史剧情组成元组
    episode_tuples: list[tuple[EpisodicNode, list[EpisodicNode]]] = [
        (episode, previous_episodes_list[i]) for i, episode in enumerate(episodes)
    ]
    
    logger.info(f"完成批量检索历史剧情，平均每个剧情有 {sum(len(prev) for prev in previous_episodes_list) / len(episodes) if episodes else 0:.2f} 个历史剧情")
    return episode_tuples


async def dedupe_nodes_bulk(
    driver: AsyncDriver,
    llm_client: LLMClient,
    extracted_nodes: list[EntityNode],
) -> tuple[list[EntityNode], dict[str, str]]:
    """批量去重提取的节点
    
    参数:
        driver: Neo4j异步驱动
        llm_client: LLM客户端
        extracted_nodes: 提取的实体节点列表
        
    返回:
        去重后的节点列表和UUID映射字典
    """
    logger.debug(f"开始批量去重 {len(extracted_nodes)} 个节点")
    
    # 首先通过名称匹配压缩节点
    nodes, uuid_map = node_name_match(extracted_nodes)
    logger.debug(f"基于名称匹配后剩余 {len(nodes)} 个节点，UUID映射数 {len(uuid_map)}")

    # 使用LLM进一步压缩节点
    compressed_nodes, compressed_map = await compress_nodes(llm_client, nodes, uuid_map)
    logger.debug(f"使用LLM压缩后剩余 {len(compressed_nodes)} 个节点，UUID映射数 {len(compressed_map)}")

    # 将节点分成多个块处理
    node_chunks = [compressed_nodes[i : i + CHUNK_SIZE] for i in range(0, len(compressed_nodes), CHUNK_SIZE)]
    logger.debug(f"将节点分为 {len(node_chunks)} 个块进行处理")

    # 获取每个块相关的现有节点
    existing_nodes_chunks: list[list[EntityNode]] = list(
        await semaphore_gather(
            *[get_relevant_nodes(driver, node_chunk, SearchFilters()) for node_chunk in node_chunks]
        )
    )
    
    # 统计找到的现有节点数量
    total_existing_nodes = sum(len(nodes) for nodes in existing_nodes_chunks)
    logger.debug(f"找到 {total_existing_nodes} 个现有相关节点")

    # 为每个块执行去重
    results: list[tuple[list[EntityNode], dict[str, str]]] = list(
        await semaphore_gather(
            *[
                dedupe_extracted_nodes(llm_client, node_chunk, existing_nodes_chunks[i])
                for i, node_chunk in enumerate(node_chunks)
            ]
        )
    )

    # 合并结果
    final_nodes: list[EntityNode] = []
    for result in results:
        final_nodes.extend(result[0])
        partial_uuid_map = result[1]
        compressed_map.update(partial_uuid_map)
    
    logger.info(f"完成批量去重，最终剩余 {len(final_nodes)} 个节点, UUID映射 {len(compressed_map)} 个")
    return final_nodes, compressed_map


def node_name_match(nodes: list[EntityNode]) -> tuple[list[EntityNode], dict[str, str]]:
    """通过节点名称进行初步匹配和压缩
    
    参数:
        nodes: 实体节点列表
        
    返回:
        压缩后的节点列表和UUID映射字典
    """
    logger.debug(f"开始通过名称匹配压缩 {len(nodes)} 个节点")
    
    uuid_map: dict[str, str] = {}
    name_map: dict[str, EntityNode] = {}
    
    # 基于名称匹配节点
    for node in nodes:
        if node.name in name_map:
            # 发现相同名称的节点，记录UUID映射
            uuid_map[node.uuid] = name_map[node.name].uuid
            logger.debug(f"通过名称匹配发现重复节点: '{node.name}' (UUID: {node.uuid} -> {name_map[node.name].uuid})")
            continue

        # 记录新节点
        name_map[node.name] = node
    
    unique_nodes = [node for node in name_map.values()]
    logger.debug(f"名称匹配完成，从 {len(nodes)} 个节点压缩到 {len(unique_nodes)} 个，映射 {len(uuid_map)} 个UUID")
    return unique_nodes, uuid_map


async def compress_nodes(
    llm_client: LLMClient, nodes: list[EntityNode], uuid_map: dict[str, str]
) -> tuple[list[EntityNode], dict[str, str]]:
    """使用LLM压缩节点并去除重复
    
    参数:
        llm_client: LLM客户端
        nodes: 实体节点列表
        uuid_map: UUID映射字典
        
    返回:
        压缩后的节点列表和更新的UUID映射字典
    """
    # 处理边界情况
    if len(nodes) == 0:
        logger.debug("节点列表为空，不需要压缩")
        return nodes, uuid_map
        
    logger.debug(f"开始使用LLM压缩 {len(nodes)} 个节点")

    # 确定块大小 - 我们希望n个块，每个块大小n，使n^2 = 节点数
    # 最小块大小为CHUNK_SIZE，以优化LLM处理时间
    chunk_size = max(int(sqrt(len(nodes))), CHUNK_SIZE)
    logger.debug(f"设定压缩块大小为 {chunk_size}")

    # 计算节点间的相似度分数
    logger.debug("计算节点之间的嵌入相似度")
    similarity_scores: list[tuple[int, int, float]] = []
    for i, n in enumerate(nodes):
        for j, m in enumerate(nodes[:i]):
            # 计算余弦相似度
            if n.name_embedding is not None and m.name_embedding is not None:
                similarity = dot(n.name_embedding, m.name_embedding)
                similarity_scores.append((i, j, similarity))
    
    # 按相似度排序（最相似的在最后）
    similarity_scores.sort(key=lambda score_tuple: score_tuple[2])
    logger.debug(f"计算了 {len(similarity_scores)} 对节点相似度")

    # 根据块大小初始化节点块
    node_chunks: list[list[EntityNode]] = [[] for _ in range(ceil(len(nodes) / chunk_size))]
    logger.debug(f"创建 {len(node_chunks)} 个节点块")

    # 将相似节点分配到相同块中
    assigned_nodes = 0
    while similarity_scores and assigned_nodes < len(nodes):
        # 获取最相似的节点对
        i, j, _ = similarity_scores.pop()
        n, m = nodes[i], nodes[j]
        
        # 确保最短的块有优先权
        node_chunks.sort(reverse=True, key=lambda chunk: len(chunk))

        # 检查节点是否已经在某个块中
        n_chunk = max([i if n in chunk else -1 for i, chunk in enumerate(node_chunks)])
        m_chunk = max([i if m in chunk else -1 for i, chunk in enumerate(node_chunks)])

        # 处理不同情况
        if n_chunk > -1 and m_chunk > -1:
            # 两个节点都已在块中
            continue
        elif n_chunk > -1 and len(node_chunks[n_chunk]) < chunk_size:
            # n已在块中，将m添加到同一块
            node_chunks[n_chunk].append(m)
            assigned_nodes += 1
        elif m_chunk > -1 and len(node_chunks[m_chunk]) < chunk_size:
            # m已在块中，将n添加到同一块
            node_chunks[m_chunk].append(n)
            assigned_nodes += 1
        else:
            # 两个节点都没有块或者块已满，添加到最短的块
            to_add = []
            if n_chunk == -1:
                to_add.append(n)
                assigned_nodes += 1
            if m_chunk == -1:
                to_add.append(m)
                assigned_nodes += 1
            if to_add:
                node_chunks[-1].extend(to_add)
    
    # 确保所有节点都被分配
    for node in nodes:
        if not any(node in chunk for chunk in node_chunks):
            # 找出最短的块
            shortest_chunk = min(node_chunks, key=len)
            shortest_chunk.append(node)
            assigned_nodes += 1
    
    logger.debug(f"分配了 {assigned_nodes} 个节点到 {len(node_chunks)} 个块中")

    # 使用LLM为每个块去重
    results = await semaphore_gather(
        *[dedupe_node_list(llm_client, chunk) for chunk in node_chunks if chunk]
    )
    logger.debug(f"完成 {len(results)} 个块的LLM去重")

    # 合并结果
    extended_map = dict(uuid_map)
    compressed_nodes: list[EntityNode] = []
    for node_chunk, uuid_map_chunk in results:
        compressed_nodes += node_chunk
        extended_map.update(uuid_map_chunk)
    
    logger.debug(f"合并块结果后得到 {len(compressed_nodes)} 个节点和 {len(extended_map)} 个映射")

    # 检查是否已经去除所有重复
    if len(compressed_nodes) == len(nodes):
        logger.debug("未发现更多重复，压缩完成")
        compressed_uuid_map = compress_uuid_map(extended_map)
        logger.debug(f"完成UUID映射压缩，从 {len(extended_map)} 个映射到 {len(compressed_uuid_map)} 个")
        return compressed_nodes, compressed_uuid_map

    # 如果还有重复，递归压缩
    logger.debug(f"仍存在重复，从 {len(nodes)} 个节点压缩到 {len(compressed_nodes)} 个，继续递归压缩")
    return await compress_nodes(llm_client, compressed_nodes, extended_map) 