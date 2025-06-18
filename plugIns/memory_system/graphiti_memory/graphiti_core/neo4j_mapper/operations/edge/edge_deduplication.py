"""
边去重相关操作
"""

from time import time

from knowledge_api.utils.log_config import get_logger
from plugIns.memory_system.graphiti_memory.graphiti_core.config import ModelSize
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.models.graphiti_types import GraphitiClients
from plugIns.memory_system.graphiti_memory.graphiti_core.llm_client import LLMClient
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.edges import EntityEdge, create_entity_edge_embeddings
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.models.search_models import SearchFilters
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes import EntityNode, EpisodicNode
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.search.utils import get_relevant_edges, \
    get_edge_invalidation_candidates
from plugIns.memory_system.graphiti_memory.graphiti_core.prompts import prompt_library
from plugIns.memory_system.graphiti_memory.graphiti_core.prompts.dedupe_edges import EdgeDuplicate, UniqueFacts
from plugIns.memory_system.graphiti_memory.graphiti_core.utils.datetime_utils import utc_now
from pydantic import BaseModel

from plugIns.memory_system.graphiti_memory.graphiti_core.utils.utils import semaphore_gather

logger = get_logger()


async def dedupe_extracted_edges(
    llm_client: LLMClient,
    extracted_edges: list[EntityEdge],
    existing_edges: list[EntityEdge],
) -> list[EntityEdge]:
    """去重提取的边
    
    参数:
        llm_client: LLM客户端
        extracted_edges: 提取的边列表
        existing_edges: 现有边列表
        
    返回:
        去重后的边列表
    """
    # 创建边映射
    edge_map: dict[str, EntityEdge] = {}
    for edge in existing_edges:
        edge_map[edge.uuid] = edge

    # 为LLM准备上下文
    context = {
        'extracted_edges': [
            {'uuid': edge.uuid, 'name': edge.name, 'fact': edge.fact} for edge in extracted_edges
        ],
        'existing_edges': [
            {'uuid': edge.uuid, 'name': edge.name, 'fact': edge.fact} for edge in existing_edges
        ],
    }

    logger.debug(f"调用LLM去重边，提取边数: {len(extracted_edges)}, 现有边数: {len(existing_edges)}")
    llm_response = await llm_client.generate_response(prompt_library.dedupe_edges.edge(context))
    duplicate_data = llm_response.get('duplicates', [])
    logger.debug(f'提取的唯一边数: {len(duplicate_data)}')

    duplicate_uuid_map: dict[str, str] = {}
    for duplicate in duplicate_data:
        uuid_value = duplicate['duplicate_of']
        duplicate_uuid_map[duplicate['uuid']] = uuid_value

    # 获取完整的边数据
    edges: list[EntityEdge] = []
    for edge in extracted_edges:
        if edge.uuid in duplicate_uuid_map:
            existing_uuid = duplicate_uuid_map[edge.uuid]
            existing_edge = edge_map[existing_uuid]
            # 将当前剧情添加到剧情列表
            existing_edge.episodes += edge.episodes
            logger.debug(f"边 {edge.uuid} 是现有边 {existing_uuid} 的副本")
            edges.append(existing_edge)
        else:
            logger.debug(f"边 {edge.uuid} 是新边")
            edges.append(edge)

    return edges


async def resolve_extracted_edges(
    clients: GraphitiClients,
    extracted_edges: list[EntityEdge],
    episode: EpisodicNode,
    entities: list[EntityNode],
    edge_types: dict[str, BaseModel],
    edge_type_map: dict[tuple[str, str], list[str]],
) -> tuple[list[EntityEdge], list[EntityEdge]]:
    """解析提取的边，确定重复和冲突
    
    参数:
        clients: Graphiti客户端集合
        extracted_edges: 提取的边列表
        episode: 剧情节点
        entities: 实体节点列表
        edge_types: 边类型字典
        edge_type_map: 边类型映射
        
    返回:
        解析后的边列表和失效边列表
    """
    driver = clients.driver
    llm_client = clients.llm_client
    embedder = clients.embedder

    # 为提取的边生成嵌入向量
    await create_entity_edge_embeddings(embedder, extracted_edges)

    # 并行获取相关边和失效候选边
    logger.debug(f"搜索相关边和失效候选边，边数: {len(extracted_edges)}")
    search_results: tuple[list[list[EntityEdge]], list[list[EntityEdge]]] = await semaphore_gather(
        get_relevant_edges(driver, extracted_edges, SearchFilters()),
        get_edge_invalidation_candidates(driver, extracted_edges, SearchFilters(), 0.2),
    )

    related_edges_lists, edge_invalidation_candidates = search_results

    logger.debug(
        f'相关边列表: {len(related_edges_lists)} 组，总计 {sum(len(edges_lst) for edges_lst in related_edges_lists)} 条'
    )

    # 构建实体哈希表
    uuid_entity_map: dict[str, EntityNode] = {entity.uuid: entity for entity in entities}

    # 确定哪些边缘类型与每个边缘相关
    edge_types_lst: list[dict[str, BaseModel]] = []
    for extracted_edge in extracted_edges:
        source_node_labels = uuid_entity_map[extracted_edge.source_node_uuid].labels
        target_node_labels = uuid_entity_map[extracted_edge.target_node_uuid].labels
        label_tuples = [
            (source_label, target_label)
            for source_label in source_node_labels
            for target_label in target_node_labels
        ]

        extracted_edge_types = {}
        for label_tuple in label_tuples:
            type_names = edge_type_map.get(label_tuple, [])
            for type_name in type_names:
                type_model = edge_types.get(type_name)
                if type_model is None:
                    continue

                extracted_edge_types[type_name] = type_model

        edge_types_lst.append(extracted_edge_types)

    # 并行解析每条边
    logger.debug(f"开始解析 {len(extracted_edges)} 条边")
    results: list[tuple[EntityEdge, list[EntityEdge]]] = list(
        await semaphore_gather(
            *[
                resolve_extracted_edge(
                    llm_client,
                    extracted_edge,
                    related_edges,
                    existing_edges,
                    episode,
                    extracted_edge_types,
                )
                for extracted_edge, related_edges, existing_edges, extracted_edge_types in zip(
                    extracted_edges,
                    related_edges_lists,
                    edge_invalidation_candidates,
                    edge_types_lst,
                    strict=True,
                )
            ]
        )
    )

    resolved_edges: list[EntityEdge] = []
    invalidated_edges: list[EntityEdge] = []
    for result in results:
        resolved_edge = result[0]
        invalidated_edge_chunk = result[1]

        resolved_edges.append(resolved_edge)
        invalidated_edges.extend(invalidated_edge_chunk)

    logger.debug(f'解析后的边: {len(resolved_edges)} 条，失效边: {len(invalidated_edges)} 条')

    # 为解析后的边和失效边生成嵌入向量
    await semaphore_gather(
        create_entity_edge_embeddings(embedder, resolved_edges),
        create_entity_edge_embeddings(embedder, invalidated_edges),
    )

    return resolved_edges, invalidated_edges


def resolve_edge_contradictions(
    resolved_edge: EntityEdge, invalidation_candidates: list[EntityEdge]
) -> list[EntityEdge]:
    """解析边的矛盾
    
    参数:
        resolved_edge: 解析后的边
        invalidation_candidates: 失效候选边列表
        
    返回:
        失效边列表
    """
    if len(invalidation_candidates) == 0:
        return []

    # 确定哪些矛盾边需要过期
    invalidated_edges: list[EntityEdge] = []
    for edge in invalidation_candidates:
        # (在新边生效之前边无效）或 （新边在边生效之前无效)
        if (
            edge.invalid_at is not None
            and resolved_edge.valid_at is not None
            and edge.invalid_at <= resolved_edge.valid_at
        ) or (
            edge.valid_at is not None
            and resolved_edge.invalid_at is not None
            and resolved_edge.invalid_at <= edge.valid_at
        ):
            continue
        # 新边使边无效
        elif (
            edge.valid_at is not None
            and resolved_edge.valid_at is not None
            and edge.valid_at < resolved_edge.valid_at
        ):
            edge.invalid_at = resolved_edge.valid_at
            edge.expired_at = edge.expired_at if edge.expired_at is not None else utc_now()
            invalidated_edges.append(edge)
            logger.debug(f"边 {edge.uuid} 被 {resolved_edge.uuid} 无效化")

    return invalidated_edges


async def resolve_extracted_edge(
    llm_client: LLMClient,
    extracted_edge: EntityEdge,
    related_edges: list[EntityEdge],
    existing_edges: list[EntityEdge],
    episode: EpisodicNode,
    edge_types: dict[str, BaseModel] | None = None,
) -> tuple[EntityEdge, list[EntityEdge]]:
    """解析单个提取的边
    
    参数:
        llm_client: LLM客户端
        extracted_edge: 提取的边
        related_edges: 相关边列表
        existing_edges: 现有边列表
        episode: 剧情节点
        edge_types: 边类型字典
        
    返回:
        解析后的边和失效边列表
    """
    # 如果没有相关边和现有边，直接返回提取的边
    if len(related_edges) == 0 and len(existing_edges) == 0:
        return extracted_edge, []

    start = time()

    # 为LLM准备上下文
    related_edges_context = [
        {'id': edge.uuid, 'fact': edge.fact} for i, edge in enumerate(related_edges)
    ]

    invalidation_edge_candidates_context = [
        {'id': i, 'fact': existing_edge.fact} for i, existing_edge in enumerate(existing_edges)
    ]

    edge_types_context = (
        [
            {
                'fact_type_id': i,
                'fact_type_name': type_name,
                'fact_type_description': type_model.__doc__,
            }
            for i, (type_name, type_model) in enumerate(edge_types.items())
        ]
        if edge_types is not None
        else []
    )

    context = {
        'existing_edges': related_edges_context,
        'new_edge': extracted_edge.fact,
        'edge_invalidation_candidates': invalidation_edge_candidates_context,
        'edge_types': edge_types_context,
    }

    # 调用LLM解析边
    logger.debug(f"调用LLM解析边 {extracted_edge.name}")
    llm_response = await llm_client.generate_response(
        prompt_library.dedupe_edges.resolve_edge(context),
        response_model=EdgeDuplicate,
        model_size=ModelSize.small,
    )

    duplicate_fact_id: int = llm_response.get('duplicate_fact_id', -1)

    # 确定解析后的边
    resolved_edge = (
        related_edges[duplicate_fact_id]
        if 0 <= duplicate_fact_id < len(related_edges)
        else extracted_edge
    )

    # 如果找到重复，添加剧情ID
    if duplicate_fact_id >= 0 and episode is not None:
        resolved_edge.episodes.append(episode.uuid)
        logger.debug(f"边 {extracted_edge.uuid} 是现有边 {resolved_edge.uuid} 的副本，添加剧情ID")

    # 处理矛盾的边
    contradicted_facts: list[int] = llm_response.get('contradicted_facts', [])
    invalidation_candidates: list[EntityEdge] = [existing_edges[i] for i in contradicted_facts]
    logger.debug(f"发现 {len(contradicted_facts)} 条矛盾边")

    # 处理边类型
    fact_type: str = str(llm_response.get('fact_type'))
    if fact_type.upper() != 'DEFAULT' and edge_types is not None:
        resolved_edge.name = fact_type

        edge_attributes_context = {
            'message': episode.content,
            'reference_time': episode.valid_at,
            'fact': resolved_edge.fact,
        }

        edge_model = edge_types.get(fact_type)

        # 提取边属性
        edge_attributes_response = await llm_client.generate_response(
            prompt_library.extract_edges.extract_attributes(edge_attributes_context),
            response_model=edge_model,  # type: ignore
            model_size=ModelSize.small,
        )

        resolved_edge.attributes = edge_attributes_response
        logger.debug(f"更新边 {resolved_edge.uuid} 类型为 {fact_type}")

    end = time()
    logger.debug(
        f'解析边完成: {extracted_edge.name} 到 {resolved_edge.name}，耗时: {(end - start) * 1000} ms'
    )

    now = utc_now()

    # 检查边是否需要过期
    if resolved_edge.invalid_at and not resolved_edge.expired_at:
        resolved_edge.expired_at = now
        logger.debug(f"边 {resolved_edge.uuid} 已过期")

    # 确定新边是否需要过期
    if resolved_edge.expired_at is None:
        invalidation_candidates.sort(key=lambda c: (c.valid_at is None, c.valid_at))
        for candidate in invalidation_candidates:
            if (
                candidate.valid_at
                and resolved_edge.valid_at
                and candidate.valid_at.tzinfo
                and resolved_edge.valid_at.tzinfo
                and candidate.valid_at > resolved_edge.valid_at
            ):
                # 由于存在更新信息，使新边过期
                resolved_edge.invalid_at = candidate.valid_at
                resolved_edge.expired_at = now
                logger.debug(f"边 {resolved_edge.uuid} 被更新信息使过期")
                break

    # 确定哪些矛盾的边需要过期
    invalidated_edges = resolve_edge_contradictions(resolved_edge, invalidation_candidates)

    return resolved_edge, invalidated_edges


async def dedupe_extracted_edge(
    llm_client: LLMClient,
    extracted_edge: EntityEdge,
    related_edges: list[EntityEdge],
    episode: EpisodicNode | None = None,
) -> EntityEdge:
    """去重单个提取的边
    
    参数:
        llm_client: LLM客户端
        extracted_edge: 提取的边
        related_edges: 相关边列表
        episode: 剧情节点
        
    返回:
        去重后的边
    """
    # 如果没有相关边，直接返回提取的边
    if len(related_edges) == 0:
        return extracted_edge

    start = time()

    # 为LLM准备上下文
    related_edges_context = [
        {'id': edge.uuid, 'fact': edge.fact} for i, edge in enumerate(related_edges)
    ]

    extracted_edge_context = {
        'fact': extracted_edge.fact,
    }

    context = {
        'related_edges': related_edges_context,
        'extracted_edges': extracted_edge_context,
    }

    # 调用LLM去重边
    logger.debug(f"调用LLM去重单个边 {extracted_edge.name}")
    llm_response = await llm_client.generate_response(
        prompt_library.dedupe_edges.edge(context),
        response_model=EdgeDuplicate,
        model_size=ModelSize.small,
    )

    duplicate_fact_id: int = llm_response.get('duplicate_fact_id', -1)

    # 确定去重后的边
    edge = (
        related_edges[duplicate_fact_id]
        if 0 <= duplicate_fact_id < len(related_edges)
        else extracted_edge
    )

    # 如果找到重复，添加剧情ID
    if duplicate_fact_id >= 0 and episode is not None:
        edge.episodes.append(episode.uuid)
        logger.debug(f"边 {extracted_edge.uuid} 是现有边 {edge.uuid} 的副本，添加剧情ID")

    end = time()
    logger.debug(
        f'去重边完成: {extracted_edge.name} 到 {edge.name}，耗时: {(end - start) * 1000} ms'
    )

    return edge


async def dedupe_edge_list(
    llm_client: LLMClient,
    edges: list[EntityEdge],
) -> list[EntityEdge]:
    """去重边列表
    
    参数:
        llm_client: LLM客户端
        edges: 边列表
        
    返回:
        去重后的边列表
    """
    start = time()

    # 创建边映射
    edge_map = {}
    for edge in edges:
        edge_map[edge.uuid] = edge

    # 为LLM准备上下文
    context = {'edges': [{'uuid': edge.uuid, 'fact': edge.fact} for edge in edges]}

    # 调用LLM去重边列表
    logger.debug(f"调用LLM去重边列表，边数: {len(edges)}")
    llm_response = await llm_client.generate_response(
        prompt_library.dedupe_edges.edge_list(context), response_model=UniqueFacts
    )
    unique_edges_data = llm_response.get('unique_facts', [])

    end = time()
    logger.debug(f'提取的边重复项: {len(unique_edges_data)} 条，耗时: {(end - start) * 1000} ms')

    # 获取完整的边数据
    unique_edges = []
    for edge_data in unique_edges_data:
        uuid = edge_data['uuid']
        edge = edge_map[uuid]
        edge.fact = edge_data['fact']
        unique_edges.append(edge)

    return unique_edges 