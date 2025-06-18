"""
数据库批量操作模块
提供用于批量处理数据库操作的函数
"""

from typing import Any

from neo4j import AsyncDriver, AsyncManagedTransaction

from knowledge_api.utils.log_config import get_logger
from knowledge_manage.embeddings.base import EmbeddingEngine
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.models.graphiti_types import GraphitiClients
from plugIns.memory_system.graphiti_memory.graphiti_core.config import DEFAULT_DATABASE
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.edges import EpisodicEdge, EntityEdge
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes import EpisodicNode, EntityNode
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations import extract_nodes, extract_edges
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.edge import build_episodic_edges
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.template import \
    EPISODIC_NODE_SAVE_BULK, ENTITY_NODE_SAVE_BULK, EPISODIC_EDGE_SAVE_BULK, ENTITY_EDGE_SAVE_BULK
from plugIns.memory_system.graphiti_memory.graphiti_core.utils.utils import semaphore_gather

logger = get_logger()


async def add_nodes_and_edges_bulk(
    driver: AsyncDriver,
    episodic_nodes: list[EpisodicNode],
    episodic_edges: list[EpisodicEdge],
    entity_nodes: list[EntityNode],
    entity_edges: list[EntityEdge],
    embedder: EmbeddingEngine,
):
    """批量添加节点和边到数据库
    
    参数:
        driver: Neo4j异步驱动
        episodic_nodes: 剧情节点列表
        episodic_edges: 剧情边列表
        entity_nodes: 实体节点列表
        entity_edges: 实体边列表
        embedder: 嵌入引擎
    """
    logger.debug(f"开始批量添加节点和边到数据库: {len(episodic_nodes)} 个剧情节点, {len(episodic_edges)} 条剧情边, "
               f"{len(entity_nodes)} 个实体节点, {len(entity_edges)} 条实体边")
    
    async with driver.session(database=DEFAULT_DATABASE) as session:
        await session.execute_write(
            add_nodes_and_edges_bulk_tx,
            episodic_nodes,
            episodic_edges,
            entity_nodes,
            entity_edges,
            embedder,
        )
    logger.info("批量添加节点和边完成")


async def add_nodes_and_edges_bulk_tx(
    tx: AsyncManagedTransaction,
    episodic_nodes: list[EpisodicNode],
    episodic_edges: list[EpisodicEdge],
    entity_nodes: list[EntityNode],
    entity_edges: list[EntityEdge],
    embedder: EmbeddingEngine,
):
    """事务中批量添加节点和边

    参数:
        tx: Neo4j异步事务
        episodic_nodes: 剧情节点列表
        episodic_edges: 剧情边列表
        entity_nodes: 实体节点列表
        entity_edges: 实体边列表
        embedder: 嵌入引擎
    """
    logger.debug("开始事务内批量添加节点和边")
    
    # 处理剧情节点
    episodes = [dict(episode) for episode in episodic_nodes]
    for episode in episodes:
        episode['source'] = str(episode['source'].value)
    logger.debug(f"处理 {len(episodes)} 个剧情节点")
    
    # 处理实体节点
    nodes: list[dict[str, Any]] = []
    for node in entity_nodes:
        # 确保节点有名称嵌入
        if node.name_embedding is None:
            await node.generate_name_embedding(embedder)
            
        entity_data: dict[str, Any] = {
            'uuid': node.uuid,
            'name': node.name,
            'name_embedding': node.name_embedding,
            'group_id': node.group_id,
            'summary': node.summary,
            'created_at': node.created_at,
        }

        # 添加其他属性
        entity_data.update(node.attributes or {})
        entity_data['labels'] = list(set(node.labels + ['Entity']))
        nodes.append(entity_data)
    
    logger.debug(f"处理 {len(nodes)} 个实体节点")
    
    # 处理实体边
    edges: list[dict[str, Any]] = []
    for edge in entity_edges:
        # 确保边有嵌入
        if edge.fact_embedding is None:
            await edge.generate_embedding(embedder)
            
        edge_data: dict[str, Any] = {
            'uuid': edge.uuid,
            'source_node_uuid': edge.source_node_uuid,
            'target_node_uuid': edge.target_node_uuid,
            'name': edge.name,
            'fact': edge.fact,
            'fact_embedding': edge.fact_embedding,
            'group_id': edge.group_id,
            'episodes': edge.episodes,
            'created_at': edge.created_at,
            'expired_at': edge.expired_at,
            'valid_at': edge.valid_at,
            'invalid_at': edge.invalid_at,
        }

        # 添加其他属性
        edge_data.update(edge.attributes or {})
        edges.append(edge_data)
    
    logger.debug(f"处理 {len(edges)} 条实体边")
    
    # 执行批量保存
    logger.debug("执行剧情节点批量保存")
    await tx.run(EPISODIC_NODE_SAVE_BULK, episodes=episodes)
    
    logger.debug("执行实体节点批量保存") 
    await tx.run(ENTITY_NODE_SAVE_BULK, nodes=nodes)
    
    logger.debug("执行剧情边批量保存")
    await tx.run(
        EPISODIC_EDGE_SAVE_BULK, episodic_edges=[edge.model_dump() for edge in episodic_edges]
    )
    
    logger.debug("执行实体边批量保存")
    await tx.run(ENTITY_EDGE_SAVE_BULK, entity_edges=edges)
    
    logger.debug("事务内批量添加节点和边完成")


async def extract_nodes_and_edges_bulk(
    clients: GraphitiClients, episode_tuples: list[tuple[EpisodicNode, list[EpisodicNode]]]
) -> tuple[list[EntityNode], list[EntityEdge], list[EpisodicEdge]]:
    """批量提取节点和边
    
    参数:
        clients: Graphiti客户端集合
        episode_tuples: 剧情节点与历史剧情节点的元组列表
        
    返回:
        提取的实体节点列表、实体边列表和剧情边列表
    """
    logger.debug(f"开始批量提取 {len(episode_tuples)} 对剧情的节点和边")
    
    # 并行提取每个剧情的节点
    extracted_nodes_bulk = await semaphore_gather(
        *[
            extract_nodes(clients, episode, previous_episodes)
            for episode, previous_episodes in episode_tuples
        ]
    )
    logger.debug(f"完成批量提取节点，共 {sum(len(nodes) for nodes in extracted_nodes_bulk)} 个")
    
    # 分离剧情和历史剧情
    episodes = [episode[0] for episode in episode_tuples]
    previous_episodes_list = [episode[1] for episode in episode_tuples]
    
    # 并行提取每个剧情的边
    extracted_edges_bulk = await semaphore_gather(
        *[
            extract_edges(
                clients,
                episode,
                extracted_nodes_bulk[i],
                previous_episodes_list[i],
                episode.group_id,
            )
            for i, episode in enumerate(episodes)
        ]
    )
    logger.debug(f"完成批量提取边，共 {sum(len(edges) for edges in extracted_edges_bulk)} 条")
    
    # 为每个剧情生成剧情边
    logger.debug("开始生成剧情边")
    episodic_edges: list[EpisodicEdge] = []
    for i, episode in enumerate(episodes):
        episodic_edges += build_episodic_edges(extracted_nodes_bulk[i], episode, episode.created_at)
    logger.debug(f"生成剧情边 {len(episodic_edges)} 条")
    
    # 合并所有提取的节点和边
    nodes: list[EntityNode] = []
    for extracted_nodes in extracted_nodes_bulk:
        nodes += extracted_nodes

    edges: list[EntityEdge] = []
    for extracted_edges in extracted_edges_bulk:
        edges += extracted_edges
    
    logger.info(f"批量提取完成: {len(nodes)} 个实体节点, {len(edges)} 条实体边, {len(episodic_edges)} 条剧情边")
    return nodes, edges, episodic_edges 