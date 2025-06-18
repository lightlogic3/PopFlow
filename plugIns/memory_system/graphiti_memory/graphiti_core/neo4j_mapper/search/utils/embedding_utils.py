"""
嵌入向量相关工具函数
提供获取节点、社区和边的嵌入向量的方法
"""

from typing import Dict, List, Tuple, Any, Coroutine

from neo4j import AsyncDriver
from numpy import ndarray, dtype
from typing_extensions import LiteralString

from knowledge_api.utils.log_config import get_logger
from plugIns.memory_system.graphiti_memory.graphiti_core.config import DEFAULT_DATABASE
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.edges import EntityEdge
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes import CommunityNode, EntityNode
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.search.search_template import (
    GET_EMBEDDINGS_FOR_NODES,
    GET_EMBEDDINGS_FOR_COMMUNITIES,
    GET_EMBEDDINGS_FOR_EDGES
)
from plugIns.memory_system.graphiti_memory.graphiti_core.utils.utils import normalize_l2

logger = get_logger()


async def get_embeddings_for_nodes(
    driver: AsyncDriver, nodes: List[EntityNode]
) -> Dict[str, List[float]]:
    """
    获取实体节点的嵌入向量
    
    参数:
    ----
    driver : AsyncDriver
        Neo4j数据库驱动
    nodes : List[EntityNode]
        要获取嵌入向量的节点列表
    
    返回:
    ----
    Dict[str, List[float]]
        节点UUID到嵌入向量的映射字典
    """
    if not nodes:
        return {}
    
    node_uuids = [node.uuid for node in nodes]
    logger.info(f"获取节点嵌入向量，节点数量：{len(node_uuids)}")
    
    # 渲染Cypher查询模板
    cypher_query = GET_EMBEDDINGS_FOR_NODES.render()
    
    # 执行查询
    results, _, _ = await driver.execute_query(
        cypher_query,
        {"node_uuids": node_uuids},
        database_=DEFAULT_DATABASE,
        routing_='r'
    )

    embeddings_dict: Dict[str, List[float]] = {}
    for result in results:
        uuid: str = result.get('uuid')
        embedding: List[float] = result.get('name_embedding')
        if uuid is not None and embedding is not None:
            embeddings_dict[uuid] = embedding

    logger.info(f"获取到{len(embeddings_dict)}个节点的嵌入向量")
    return embeddings_dict


async def get_embeddings_for_communities(
    driver: AsyncDriver, communities: List[CommunityNode]
) -> Dict[str, List[float]]:
    """
    获取社区节点的嵌入向量
    
    参数:
    ----
    driver : AsyncDriver
        Neo4j数据库驱动
    communities : List[CommunityNode]
        要获取嵌入向量的社区列表
    
    返回:
    ----
    Dict[str, List[float]]
        社区UUID到嵌入向量的映射字典
    """
    if not communities:
        return {}
    
    community_uuids = [community.uuid for community in communities]
    logger.info(f"获取社区嵌入向量，社区数量：{len(community_uuids)}")
    
    # 渲染Cypher查询模板
    cypher_query = GET_EMBEDDINGS_FOR_COMMUNITIES.render()
    
    # 执行查询
    results, _, _ = await driver.execute_query(
        cypher_query,
        {"community_uuids": community_uuids},
        database_=DEFAULT_DATABASE,
        routing_='r',
    )

    embeddings_dict: Dict[str, List[float]] = {}
    for result in results:
        uuid: str = result.get('uuid')
        embedding: List[float] = result.get('name_embedding')
        if uuid is not None and embedding is not None:
            embeddings_dict[uuid] = embedding

    logger.info(f"获取到{len(embeddings_dict)}个社区的嵌入向量")
    return embeddings_dict


async def get_embeddings_for_edges(
    driver: AsyncDriver, edges: List[EntityEdge]
) -> Dict[str, List[float]]:
    """
    获取实体边的嵌入向量
    
    参数:
    ----
    driver : AsyncDriver
        Neo4j数据库驱动
    edges : List[EntityEdge]
        要获取嵌入向量的边列表
    
    返回:
    ----
    Dict[str, List[float]]
        边UUID到嵌入向量的映射字典
    """
    if not edges:
        return {}
    
    edge_uuids = [edge.uuid for edge in edges]
    logger.info(f"获取边嵌入向量，边数量：{len(edge_uuids)}")
    
    # 渲染Cypher查询模板
    cypher_query = GET_EMBEDDINGS_FOR_EDGES.render()
    
    # 执行查询
    results, _, _ = await driver.execute_query(
        cypher_query,
        {"edge_uuids": edge_uuids},
        database_=DEFAULT_DATABASE,
        routing_='r',
    )

    embeddings_dict: Dict[str, List[float]] = {}
    for result in results:
        uuid: str = result.get('uuid')
        embedding: List[float] = result.get('fact_embedding')
        if uuid is not None and embedding is not None:
            embeddings_dict[uuid] = embedding

    logger.info(f"获取到{len(embeddings_dict)}个边的嵌入向量")
    return embeddings_dict


async def get_nodes_with_embeddings(
    driver: AsyncDriver, nodes: List[EntityNode]
) -> list[tuple[str, ndarray[tuple[int, ...], dtype[Any]]]]:
    """
    获取带有嵌入向量的节点列表
    
    参数:
    ----
    driver : AsyncDriver
        Neo4j数据库驱动
    nodes : List[EntityNode]
        要获取嵌入向量的节点列表
    
    返回:
    ----
    List[Tuple[str, List[float]]]
        (节点UUID, 嵌入向量)的元组列表
    """
    embeddings_dict = await get_embeddings_for_nodes(driver, nodes)
    return [(uuid, normalize_l2(vec)) for uuid, vec in embeddings_dict.items()]


async def get_communities_with_embeddings(
    driver: AsyncDriver, communities: List[CommunityNode]
) -> List[Tuple[str, List[float]]]:
    """
    获取带有嵌入向量的社区列表
    
    参数:
    ----
    driver : AsyncDriver
        Neo4j数据库驱动
    communities : List[CommunityNode]
        要获取嵌入向量的社区列表
    
    返回:
    ----
    List[Tuple[str, List[float]]]
        (社区UUID, 嵌入向量)的元组列表
    """
    embeddings_dict = await get_embeddings_for_communities(driver, communities)
    return [(uuid, normalize_l2(vec)) for uuid, vec in embeddings_dict.items()]


async def get_edges_with_embeddings(
    driver: AsyncDriver, edges: List[EntityEdge]
) -> List[Tuple[str, List[float]]]:
    """
    获取带有嵌入向量的边列表
    
    参数:
    ----
    driver : AsyncDriver
        Neo4j数据库驱动
    edges : List[EntityEdge]
        要获取嵌入向量的边列表
    
    返回:
    ----
    List[Tuple[str, List[float]]]
        (边UUID, 嵌入向量)的元组列表
    """
    embeddings_dict = await get_embeddings_for_edges(driver, edges)
    return [(uuid, normalize_l2(vec)) for uuid, vec in embeddings_dict.items()] 