"""
节点去重相关操作
"""

from time import time

from knowledge_api.utils.log_config import get_logger
from plugIns.memory_system.graphiti_memory.graphiti_core.config import ModelSize
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.models.graphiti_types import GraphitiClients
from plugIns.memory_system.graphiti_memory.graphiti_core.llm_client import LLMClient
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.models.search_models import SearchFilters
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes import EntityNode, EpisodicNode
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.search.ops import search
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.search.recipes import NODE_HYBRID_SEARCH_RRF
from plugIns.memory_system.graphiti_memory.graphiti_core.prompts import prompt_library
from plugIns.memory_system.graphiti_memory.graphiti_core.prompts.dedupe_nodes import NodeDuplicate, NodeResolutions
from pydantic import BaseModel

from plugIns.memory_system.graphiti_memory.graphiti_core.utils.utils import semaphore_gather

logger = get_logger()


async def dedupe_extracted_nodes(
    llm_client: LLMClient,
    extracted_nodes: list[EntityNode],
    existing_nodes: list[EntityNode],
) -> tuple[list[EntityNode], dict[str, str]]:
    """使用LLM去重提取的节点
    
    参数:
        llm_client: LLM客户端
        extracted_nodes: 提取的节点列表
        existing_nodes: 现有节点列表
        
    返回:
        去重后的节点列表和UUID映射字典
    """
    start = time()
    logger.debug(f"开始去重，提取节点数: {len(extracted_nodes)}, 现有节点数: {len(existing_nodes)}")

    # 构建现有节点映射
    node_map: dict[str, EntityNode] = {}
    for node in existing_nodes:
        node_map[node.uuid] = node

    # 为LLM准备上下文
    existing_nodes_context = []
    for node in existing_nodes:
        if hasattr(node,'summary') and node.summary:
            existing_nodes_context.append({'uuid': node.uuid, 'name': node.name, 'summary': node.summary})

    extracted_nodes_context = [
        {'uuid': node.uuid, 'name': node.name, 'summary': node.summary} for node in extracted_nodes
    ]

    context = {
        'existing_nodes': existing_nodes_context,
        'extracted_nodes': extracted_nodes_context,
    }

    # 调用LLM进行去重
    logger.debug("调用LLM进行节点去重")
    llm_response = await llm_client.generate_response(prompt_library.dedupe_nodes.node(context))
    
    # 处理去重结果
    duplicate_data = llm_response.get('duplicates', [])
    end = time()
    logger.debug(f'去重结果: {duplicate_data}，耗时: {(end - start) * 1000} ms')
    
    # 构建UUID映射
    uuid_map: dict[str, str] = {}
    for duplicate in duplicate_data:
        uuid_value = duplicate['duplicate_of']
        uuid_map[duplicate['uuid']] = uuid_value
    
    # 生成最终节点列表
    nodes: list[EntityNode] = []
    for node in extracted_nodes:
        if node.uuid in uuid_map:
            existing_uuid = uuid_map[node.uuid]
            existing_node = node_map[existing_uuid]
            nodes.append(existing_node)
            logger.debug(f"节点 {node.name} ({node.uuid}) 是现有节点 {existing_node.name} ({existing_uuid}) 的副本")
        else:
            nodes.append(node)
            logger.debug(f"节点 {node.name} ({node.uuid}) 是新节点")

    logger.info(f"去重完成，最终节点数: {len(nodes)}")
    return nodes, uuid_map


async def resolve_extracted_nodes(
    clients: GraphitiClients,
    extracted_nodes: list[EntityNode],
    episode: EpisodicNode | None = None,
    previous_episodes: list[EpisodicNode] | None = None,
    entity_types: dict[str, BaseModel] | None = None,
) -> tuple[list[EntityNode], dict[str, str]]:
    """解析提取的节点，搜索可能的重复节点并解决冲突
    
    参数:
        clients: Graphiti客户端集合
        extracted_nodes: 提取的节点列表
        episode: 当前剧情节点
        previous_episodes: 之前的剧情节点列表
        entity_types: 实体类型字典
        
    返回:
        解析后的节点列表和UUID映射字典
    """
    logger.debug(f"开始解析提取的节点，节点数: {len(extracted_nodes)}")
    llm_client = clients.llm_client

    # 为每个提取的节点搜索可能的重复节点
    logger.debug("搜索每个提取节点的可能重复项")
    search_results = await semaphore_gather(
        *[
            search(
                clients=clients,
                query=node.name,
                group_ids=[node.group_id],
                search_filter=SearchFilters(),
                config=NODE_HYBRID_SEARCH_RRF,
            )
            for node in extracted_nodes
        ]
    )

    # 从搜索结果中获取现有节点列表
    existing_nodes_lists: list[list[EntityNode]] = [result.nodes for result in search_results]
    logger.debug(f"搜索到的现有节点数: {sum(len(nodes) for nodes in existing_nodes_lists)}")

    # 获取实体类型字典
    entity_types_dict: dict[str, BaseModel] = entity_types if entity_types is not None else {}

    # 为LLM准备上下文
    extracted_nodes_context = [
        {
            'id': i,
            'name': node.name,
            'entity_type': node.labels,
            'entity_type_description': entity_types_dict.get(
                next((item for item in node.labels if item != 'Entity'), '')
            ).__doc__
            or 'Default Entity Type',
            'duplication_candidates': [
                {
                    **{
                        'idx': j,
                        'name': candidate.name,
                        'entity_types': candidate.labels,
                    },
                    **candidate.attributes,
                }
                for j, candidate in enumerate(existing_nodes_lists[i])
            ],
        }
        for i, node in enumerate(extracted_nodes)
    ]

    context = {
        'extracted_nodes': extracted_nodes_context,
        'episode_content': episode.content if episode is not None else '',
        'previous_episodes': [ep.content for ep in previous_episodes]
        if previous_episodes is not None
        else [],
    }
    
    # 调用LLM解析节点
    logger.debug("调用LLM解析节点")
    llm_response = await llm_client.generate_response(
        prompt_library.dedupe_nodes.nodes(context),
        response_model=NodeResolutions,
    )

    node_resolutions: list = llm_response.get('entity_resolutions', [])
    logger.debug(f"获取节点解析结果: {len(node_resolutions)} 条")

    # 处理解析结果
    resolved_nodes: list[EntityNode] = []
    uuid_map: dict[str, str] = {}
    
    for resolution in node_resolutions:
        resolution_id = resolution.get('id', -1)
        duplicate_idx = resolution.get('duplicate_idx', -1)
        
        # 检查解析结果是否有效
        if resolution_id < 0 or resolution_id >= len(extracted_nodes):
            logger.warning(f"无效的解析ID: {resolution_id}，跳过此解析")
            continue
            
        extracted_node = extracted_nodes[resolution_id]
        
        # 确定解析后的节点
        if 0 <= duplicate_idx < len(existing_nodes_lists[resolution_id]):
            # 使用现有节点
            resolved_node = existing_nodes_lists[resolution_id][duplicate_idx]
            logger.debug(f"节点 {extracted_node.name} 解析为现有节点 {resolved_node.name}")
        else:
            # 使用提取的节点
            resolved_node = extracted_node
            logger.debug(f"节点 {extracted_node.name} 保留为新节点")

        # 更新节点名称（如果解析提供了新名称）
        if 'name' in resolution and resolution.get('name'):
            resolved_node.name = resolution.get('name')
            logger.debug(f"更新节点名称为: {resolved_node.name}")

        # 添加到结果列表并映射UUID
        resolved_nodes.append(resolved_node)
        uuid_map[extracted_node.uuid] = resolved_node.uuid

    logger.info(f"解析完成，最终节点数: {len(resolved_nodes)}")
    return resolved_nodes, uuid_map


async def resolve_extracted_node(
        llm_client: LLMClient,
        extracted_node: EntityNode,
        existing_nodes: list[EntityNode],
        episode: EpisodicNode | None = None,
        previous_episodes: list[EpisodicNode] | None = None,
        entity_type: BaseModel | None = None,
) -> EntityNode:
    """解析单个提取的节点
    
    参数:
        llm_client: LLM客户端
        extracted_node: 提取的节点
        existing_nodes: 现有节点列表
        episode: 当前剧情节点
        previous_episodes: 之前的剧情节点列表
        entity_type: 实体类型
        
    返回:
        解析后的节点
    """
    start = time()
    logger.debug(f"开始解析单个节点: {extracted_node.name}")
    
    # 如果没有现有节点，直接返回提取的节点
    if len(existing_nodes) == 0:
        logger.debug("没有现有节点用于比较，返回原始节点")
        return extracted_node

    # 准备LLM上下文
    existing_nodes_context = []
    for i, node in enumerate(existing_nodes):
        node_data = {
            'id': i,
            'name': node.name,
            'entity_types': node.labels,
        }
        # 安全获取属性
        if hasattr(node, 'attributes'):
            node_data.update(node.attributes)
        existing_nodes_context.append(node_data)

    # 获取实体类型名称和描述
    entity_type_name = "Entity"
    entity_type_description = "Default Entity Type"
    if entity_type is not None:
        if hasattr(entity_type, '__name__'):
            entity_type_name = entity_type.__name__
        if hasattr(entity_type, '__doc__') and entity_type.__doc__:
            entity_type_description = entity_type.__doc__

    extracted_node_context = {
        'name': extracted_node.name,
        'entity_type': entity_type_name,
    }

    # 准备episode内容
    episode_content = ""
    if episode is not None and hasattr(episode, 'content'):
        episode_content = episode.content

    # 准备previous_episodes内容
    previous_episodes_content = []
    if previous_episodes is not None:
        for ep in previous_episodes:
            if hasattr(ep, 'content'):
                previous_episodes_content.append(ep.content)

    context = {
        'existing_nodes': existing_nodes_context,
        'extracted_node': extracted_node_context,
        'entity_type_description': entity_type_description,
        'episode_content': episode_content,
        'previous_episodes': previous_episodes_content,
    }

    try:
        # 调用LLM解析节点
        logger.debug("调用LLM解析单个节点")
        llm_response = await llm_client.generate_response(
            prompt_library.dedupe_nodes.node(context),
            response_model=NodeDuplicate,
            model_size=ModelSize.small,
        )

        duplicate_id: int = llm_response.get('duplicate_node_id', -1)
        logger.debug(f"LLM返回的重复节点ID: {duplicate_id}")

        # 确定解析后的节点
        if 0 <= duplicate_id < len(existing_nodes):
            node = existing_nodes[duplicate_id]
            logger.debug(f"节点 {extracted_node.name} 解析为现有节点 {node.name}")
        else:
            node = extracted_node
            logger.debug(f"节点 {extracted_node.name} 保留为新节点")

        # 更新节点名称（如果解析提供了新名称）
        if 'name' in llm_response and llm_response.get('name'):
            node.name = llm_response.get('name')
            logger.debug(f"更新节点名称为: {node.name}")

        end = time()
        logger.debug(f'解析节点完成: {extracted_node.name} -> {node.name}, 耗时: {(end - start) * 1000} ms')

        return node
    except Exception as e:
        logger.error(f"解析单个节点时出错: {e}")
        # 出错时返回原始节点
        return extracted_node


async def dedupe_node_list(
        llm_client: LLMClient,
        nodes: list[EntityNode],
) -> tuple[list[EntityNode], dict[str, str]]:
    """去重节点列表
    
    参数:
        llm_client: LLM客户端
        nodes: 节点列表
        
    返回:
        去重后的节点列表和UUID映射字典
    """
    start = time()
    logger.debug(f"开始去重节点列表，节点数: {len(nodes)}")

    # 构建节点映射
    node_map = {}
    for node in nodes:
        node_map[node.uuid] = node

    # 为LLM准备上下文
    nodes_context = []
    for node in nodes:
        node_data = {'uuid': node.uuid, 'name': node.name}
        # 安全获取属性
        if hasattr(node, 'attributes'):
            node_data.update(node.attributes)
        nodes_context.append(node_data)

    context = {
        'nodes': nodes_context,
    }

    try:
        # 调用LLM去重节点列表
        logger.debug("调用LLM去重节点列表")
        llm_response = await llm_client.generate_response(
            prompt_library.dedupe_nodes.node_list(context)
        )

        nodes_data = llm_response.get('nodes', [])
        logger.debug(f"LLM返回节点组数: {len(nodes_data)}")

        end = time()
        logger.debug(f'去重节点列表完成，耗时: {(end - start) * 1000} ms')

        # 处理去重结果
        unique_nodes = []
        uuid_map: dict[str, str] = {}

        for node_data in nodes_data:
            # 确保uuids字段存在且不为空
            if 'uuids' not in node_data or not node_data['uuids']:
                logger.warning("节点数据中缺少uuids字段或为空")
                continue

            # 获取第一个UUID对应的节点实例
            first_uuid = node_data['uuids'][0]
            node_instance: EntityNode | None = node_map.get(first_uuid)

            if node_instance is None:
                logger.warning(f'节点 {first_uuid} 在节点映射中不存在')
                continue

            # 安全更新摘要
            if 'summary' in node_data:
                node_instance.summary = node_data['summary']

            unique_nodes.append(node_instance)
            logger.debug(f"添加去重后节点: {node_instance.name} ({first_uuid})")

            # 建立UUID映射关系
            for uuid in node_data['uuids'][1:]:
                if uuid in node_map:
                    uuid_map[uuid] = first_uuid
                    logger.debug(f"映射UUID: {uuid} -> {first_uuid}")
                else:
                    logger.warning(f'节点 {uuid} 在节点映射中不存在')

        logger.info(f"去重完成，最终节点数: {len(unique_nodes)}")
        return unique_nodes, uuid_map

    except Exception as e:
        logger.error(f"节点列表去重过程中出错: {e}")
        # 出错时返回原始节点列表
        return nodes, {} 