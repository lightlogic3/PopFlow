"""
边提取相关操作
"""

import traceback
from datetime import datetime
from time import time

from pydantic import BaseModel

from knowledge_api.utils.log_config import get_logger
from plugIns.memory_system.graphiti_memory.graphiti_core.config import MAX_REFLEXION_ITERATIONS
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.models.graphiti_types import GraphitiClients
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.edges import EntityEdge
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes import EntityNode, EpisodicNode
from plugIns.memory_system.graphiti_memory.graphiti_core.prompts import prompt_library
from plugIns.memory_system.graphiti_memory.graphiti_core.prompts.extract_edges import ExtractedEdges, MissingFacts
from plugIns.memory_system.graphiti_memory.graphiti_core.utils.datetime_utils import ensure_utc, utc_now

logger = get_logger()


async def extract_edges(
    clients: GraphitiClients,
    episode: EpisodicNode,
    nodes: list[EntityNode],
    previous_episodes: list[EpisodicNode],
    group_id: str = '',
    edge_types: dict[str, BaseModel] | None = None,
    custom_prompt: str = '',
) -> list[EntityEdge]:
    """从剧情节点中提取实体间的边
    
    参数:
        clients: Graphiti客户端集合
        episode: 当前剧情节点
        nodes: 实体节点列表
        previous_episodes: 之前的剧情节点列表
        group_id: 群组ID
        edge_types: 边类型字典
        custom_prompt: 自定义提示词
        
    返回:
        提取的边列表
    """
    start = time()

    extract_edges_max_tokens = 16384
    llm_client = clients.llm_client

    node_uuids_by_name_map = {node.name: node.uuid for node in nodes}

    edge_types_context = (
        [
            {
                'fact_type_name': type_name,
                'fact_type_description': type_model.__doc__,
            }
            for type_name, type_model in edge_types.items()
        ]
        if edge_types is not None
        else []
    )

    # 确保previous_episodes是列表类型
    if previous_episodes is None:
        previous_episodes = []
    
    # 确保有效的previous_episodes
    valid_previous_episodes = []
    for ep in previous_episodes:
        if hasattr(ep, 'content') and ep.content:
            valid_previous_episodes.append(ep.content)
        else:
            # 如果没有content属性或内容为空，创建一个空字符串
            valid_previous_episodes.append("")

    # 准备LLM上下文
    context = {
        'episode_content': episode.content,
        'nodes': [node.name for node in nodes],
        'previous_episodes': valid_previous_episodes,
        'reference_time': episode.valid_at,
        'edge_types': edge_types_context,
        'custom_prompt': custom_prompt,
    }

    try:
        facts_missed = True
        reflexion_iterations = 0
        edges_data = []
        
        while facts_missed and reflexion_iterations <= MAX_REFLEXION_ITERATIONS:
            logger.debug(f"调用LLM提取边，迭代: {reflexion_iterations+1}/{MAX_REFLEXION_ITERATIONS+1}")
            llm_response = await llm_client.generate_response(
                prompt_library.extract_edges.edge(context),
                response_model=ExtractedEdges,
                max_tokens=extract_edges_max_tokens,
            )
            edges_data = llm_response.get('edges', [])
            
            context['extracted_facts'] = [edge_data.get('fact', '') for edge_data in edges_data]
            
            reflexion_iterations += 1
            if reflexion_iterations < MAX_REFLEXION_ITERATIONS:
                reflexion_response = await llm_client.generate_response(
                    prompt_library.extract_edges.reflexion(context),
                    response_model=MissingFacts,
                    max_tokens=extract_edges_max_tokens,
                )
    
                missing_facts = reflexion_response.get('missing_facts', [])
    
                custom_prompt = 'The following facts were missed in a previous extraction: '
                for fact in missing_facts:
                    custom_prompt += f'\n{fact},'
    
                context['custom_prompt'] = custom_prompt
    
                facts_missed = len(missing_facts) != 0
                logger.debug(f"发现遗漏事实数: {len(missing_facts)}")
    
        end = time()
        logger.debug(f'提取新边: {len(edges_data)} 条，耗时: {(end - start) * 1000} ms')
    
        if len(edges_data) == 0:
            return []
    
        # 转换提取的数据为EntityEdge对象
        edges = []
        for edge_data in edges_data:
            # 验证边日期信息
            valid_at = edge_data.get('valid_at', None)
            invalid_at = edge_data.get('invalid_at', None)
            valid_at_datetime = None
            invalid_at_datetime = None
    
            if valid_at:
                try:
                    valid_at_datetime = ensure_utc(
                        datetime.fromisoformat(valid_at.replace('Z', '+00:00'))
                    )
                except ValueError as e:
                    logger.warning(f'警告: 解析valid_at日期错误: {e}. 输入: {valid_at}')
    
            if invalid_at:
                try:
                    invalid_at_datetime = ensure_utc(
                        datetime.fromisoformat(invalid_at.replace('Z', '+00:00'))
                    )
                except ValueError as e:
                    logger.warning(f'警告: 解析invalid_at日期错误: {e}. 输入: {invalid_at}')
                    
            source_node_name = edge_data.get('source_entity_name', '')
            target_node_name = edge_data.get('target_entity_name', '')
            
            # 检查源节点和目标节点是否存在
            if source_node_name not in node_uuids_by_name_map:
                logger.warning(f'源节点不存在: {source_node_name}，跳过此边')
                continue
                
            if target_node_name not in node_uuids_by_name_map:
                logger.warning(f'目标节点不存在: {target_node_name}，跳过此边')
                continue
                
            edge = EntityEdge(
                source_node_uuid=node_uuids_by_name_map.get(source_node_name, ''),
                target_node_uuid=node_uuids_by_name_map.get(target_node_name, ''),
                name=edge_data.get('relation_type', ''),
                group_id=group_id,
                fact=edge_data.get('fact', ''),
                episodes=[episode.uuid],
                created_at=utc_now(),
                valid_at=valid_at_datetime,
                invalid_at=invalid_at_datetime,
            )
            edges.append(edge)
            logger.debug(
                f'创建新边: {edge.name} 从 {source_node_name} (UUID: {edge.source_node_uuid}) 到 {target_node_name} (UUID: {edge.target_node_uuid})'
            )
    
        logger.debug(f'提取的边: {[(e.name, e.uuid) for e in edges]}')
    
        return edges
        
    except Exception as e:
        logger.error(f"提取边过程中发生错误: {e}")
        logger.error(traceback.format_exc())
        return [] 