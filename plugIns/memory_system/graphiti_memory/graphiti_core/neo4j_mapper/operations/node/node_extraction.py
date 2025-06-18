"""
节点提取相关操作
"""

import traceback
import re
from time import time

from pydantic import BaseModel

from knowledge_api.utils.log_config import get_logger
from plugIns.memory_system.graphiti_memory.graphiti_core.config import MAX_REFLEXION_ITERATIONS
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.models.graphiti_types import GraphitiClients
from plugIns.memory_system.graphiti_memory.graphiti_core.llm_client import LLMClient
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes import EntityNode, EpisodicNode
from plugIns.memory_system.graphiti_memory.graphiti_core.prompts import prompt_library
from plugIns.memory_system.graphiti_memory.graphiti_core.prompts.extract_nodes import (
    ExtractedEntities,
    ExtractedEntity,
    MissedEntities,
)
from plugIns.memory_system.graphiti_memory.graphiti_core.utils.datetime_utils import utc_now

logger = get_logger()


async def extract_nodes_reflexion(
        llm_client: LLMClient,
        episode: EpisodicNode,
        previous_episodes: list[EpisodicNode],
        node_names: list[str],
) -> list[str]:
    """针对已提取的节点进行反思，找出可能遗漏的实体
    
    参数:
        llm_client: LLM客户端
        episode: 当前剧情节点
        previous_episodes: 之前的剧情节点列表
        node_names: 已提取的节点名称列表
        
    返回:
        遗漏的实体列表
    """
    logger.debug(f"开始实体提取反思，已有实体数: {len(node_names)}")
    
    # 准备LLM上下文
    context = {
        'episode_content': episode.content,
        'previous_episodes': [ep.content for ep in previous_episodes],
        'extracted_entities': node_names,
    }

    # 调用LLM进行反思
    llm_response = await llm_client.generate_response(
        prompt_library.extract_nodes.reflexion(context), MissedEntities
    )
    missed_entities = llm_response.get('missed_entities', [])
    
    logger.debug(f"反思发现遗漏实体数: {len(missed_entities)}")
    return missed_entities


async def extract_nodes(
        clients: GraphitiClients,
        episode: EpisodicNode,
        previous_episodes: list[EpisodicNode],
        entity_types: dict[str, BaseModel] | None = None,
        custom_prompt: str = '',
) -> list[EntityNode]:
    """从剧情节点中提取实体节点
    
    参数:
        clients: Graphiti客户端集合
        episode: 当前剧情节点
        previous_episodes: 之前的剧情节点列表
        entity_types: 实体类型字典，键为类型名称，值为模型类
        custom_prompt: 自定义提示词
        
    返回:
        提取的实体节点列表
    """
    llm_client = clients.llm_client
    if not llm_client:
        logger.warning("未提供LLM客户端，无法提取实体")
        return []

    if not episode.content or not entity_types:
        logger.warning("缺少必要信息(episode内容或实体类型)，无法提取实体")
        return []

    start = time()
    
    # 记录更详细的日志，帮助诊断问题
    logger.info(f"开始提取实体节点，来源: {episode.source}, 内容长度: {len(episode.content) if hasattr(episode, 'content') else '未知'}")
    logger.info(f"历史Episodes数量: {len(previous_episodes)}, 自定义提示词长度: {len(custom_prompt)}")
    
    llm_response = {}
    entities_missed = True
    reflexion_iterations = 0
    
    # 基础实体类型
    entity_types_context = [{'entity_type_id': 0, 'entity_type_name': 'Entity','entity_type_description': '默认实体分类。如果实体不是列出的其他类型之一，请使用此实体类型。'}]

    # 添加自定义实体类型
    if entity_types is not None:
        for i, (type_name, type_model) in enumerate(entity_types.items()):
            entity_types_context.append({
                'entity_type_id': i + 1,
                'entity_type_name': type_name,
                'entity_type_description': type_model.__doc__,
            })
            logger.debug(f"添加实体类型: {i + 1} - {type_name}: {type_model.__doc__}")

    # 准备上下文，增加对历史episodes的筛选和处理
    relevant_previous_episodes = []
    if len(previous_episodes) > 0:
        # 仅使用相同group_id的前几个历史episodes，避免上下文过大
        max_prev_episodes = 3
        same_group_episodes = [ep for ep in previous_episodes if ep.group_id == episode.group_id][:max_prev_episodes]

        relevant_previous_episodes = []
        for ep in same_group_episodes:
            if hasattr(ep, 'content') and ep.content:
                # 预览内容，限制长度
                content_preview = ep.content[:300] + ("..." if len(ep.content) > 300 else "")
                relevant_previous_episodes.append(content_preview)
                logger.debug(f"添加历史Episode预览: {content_preview[:50]}...")

    # 构建LLM上下文
    context = {'episode_content': episode.content,
               'episode_timestamp': episode.valid_at.isoformat(),
               'previous_episodes': relevant_previous_episodes,
               'custom_prompt': custom_prompt,
               'entity_types': entity_types_context,
               'source_description': episode.source_description,
               'group_id': episode.group_id,
               'source': episode.source,
               'extraction_guidance': """请确保对每个人物实体设置正确的is_speaker属性:
- 真正的发言者(一般只有user/assistant)设为true
- 被提及的人物(如对话中提到的游戏角色)设为false
- 每个提取的实体必须有source_text属性，包含原文中相关的文本段落
"""}

    # 迭代提取实体，直到没有遗漏或达到最大迭代次数
    while entities_missed and reflexion_iterations <= MAX_REFLEXION_ITERATIONS:
        try:
            logger.debug(f"实体提取迭代 #{reflexion_iterations + 1}")
            
            # 调用LLM提取实体
            llm_response = await llm_client.generate_response(
                prompt_library.extract_nodes.extract_nodes(context),
                response_model=ExtractedEntities,
            )
            
            # 检查extracted_entities是否为列表
            extracted_entities_data = llm_response.get('extracted_entities', [])
            extracted_entities: list[ExtractedEntity] = []
            
            # 安全地转换每个实体数据
            for entity_data in extracted_entities_data:
                if not isinstance(entity_data, dict):
                    logger.warning(f"实体数据不是字典类型，跳过: {entity_data}")
                    continue
                try:
                    # 确保实体数据包含必要字段
                    if 'name' not in entity_data or 'entity_type_id' not in entity_data:
                        logger.warning(f"实体数据缺少必要字段(name或entity_type_id): {entity_data}")
                        continue
                    # 创建ExtractedEntity实例
                    extracted_entity = ExtractedEntity(**entity_data)
                    extracted_entities.append(extracted_entity)
                except Exception as e:
                    logger.error(f"创建ExtractedEntity实例失败: {e}, 数据: {entity_data}")
                    continue
                    
            reflexion_iterations += 1
            
            # 检查是否需要进行反思迭代
            if reflexion_iterations < MAX_REFLEXION_ITERATIONS:
                # 调用反思函数检查遗漏的实体
                missing_entities = await extract_nodes_reflexion(
                    llm_client,
                    episode,
                    previous_episodes,
                    [entity.name for entity in extracted_entities],
                )
                entities_missed = len(missing_entities) != 0
                
                # 如果有遗漏实体，添加到自定义提示中
                if entities_missed:
                    custom_prompt += '\n请确保提取以下实体: '
                    for entity in missing_entities:
                        custom_prompt += f'\n- {entity}'
                    logger.info(f"检测到遗漏的实体，迭代: {reflexion_iterations}, 遗漏实体: {missing_entities}")
                else:
                    logger.info(f"未检测到遗漏的实体，迭代: {reflexion_iterations}")
            else:
                logger.warning(f"达到最大反思迭代次数: {MAX_REFLEXION_ITERATIONS}")

        except Exception as e:
            logger.error(f"提取实体过程中发生错误: {e}")
            logger.error(traceback.format_exc())
            # 出错时返回空列表
            return []

    # 过滤掉名称为空的实体
    filtered_extracted_entities = [entity for entity in extracted_entities if entity.name.strip()]
    end = time()
    logger.info(f'提取了 {len(filtered_extracted_entities)} 个新节点，耗时: {(end - start) * 1000} ms')

    # 如果没有提取到实体，直接返回空列表
    if not filtered_extracted_entities:
        logger.warning(f"未能提取到任何有效实体")
        return []

    # 转换提取的数据为EntityNode对象
    try:
        extracted_nodes = []
        for extracted_entity in filtered_extracted_entities:
            # 安全获取实体类型
            entity_type_id = getattr(extracted_entity, 'entity_type_id', 0)
            if not 0 <= entity_type_id < len(entity_types_context):
                logger.warning(f"实体类型ID超出范围: {entity_type_id}，使用默认类型(0)")
                entity_type_id = 0

            entity_type_name = entity_types_context[entity_type_id]['entity_type_name']
            labels: list[str] = list({'Entity', str(entity_type_name)})

            # 创建EntityNode实例
            new_node = EntityNode(
                name=extracted_entity.name,
                group_id=episode.group_id,
                labels=labels,
                summary='',  # 将在后续过程中填充
                created_at=utc_now(),
                attributes={}  # 初始化空属性字典
            )

            # 添加额外属性
            # 检查是否有source_text属性
            if hasattr(extracted_entity, 'source_text'):
                new_node.attributes['source_text'] = extracted_entity.source_text

            # 检查是否有is_speaker属性（用于人物实体）
            if hasattr(extracted_entity, 'is_speaker'):
                new_node.attributes['is_speaker'] = extracted_entity.is_speaker
                # 记录发言者信息
                if new_node.attributes['is_speaker']:
                    logger.info(f"标记为发言者的实体: {new_node.name}")
            else:
                # 对人物实体，默认不是发言者
                if 'Person' in labels:
                    new_node.attributes['is_speaker'] = False
                    logger.debug(f"为人物实体 {new_node.name} 默认设置is_speaker=False")

            # 检查是否有原始上下文
            if hasattr(extracted_entity, 'original_context'):
                new_node.attributes['original_context'] = extracted_entity.original_context

            extracted_nodes.append(new_node)
            logger.debug(f'创建新节点: {new_node.name} (UUID: {new_node.uuid}, 类型: {labels})')

        logger.info(f'提取节点总结: {[(n.name, n.labels) for n in extracted_nodes]}')
        return extracted_nodes
        
    except Exception as e:
        logger.error(f"创建EntityNode对象时发生错误: {e}")
        logger.error(traceback.format_exc())
        return []


def _is_likely_technical_identifier(text: str) -> bool:
    """
    判断文本是否可能是技术标识符
    
    参数:
        text: 要检查的文本
        
    返回:
        如果文本看起来像技术标识符，返回True，否则返回False
    """
    # 检查输入是否为空或太长
    if not text or len(text) > 1000:
        return False

    # 标识符模式
    patterns = [
        # 检查是否是时间戳格式 如 2025-05-25T23:21:41.263326
        r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
        # 检查是否是UUID格式 如 8d6dc39f-4af4-4a20-87de-d2f20c0c0be4
        r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}',
        # 检查是否主要由数字和特殊字符组成
        r'^[\d\-_.:/]+$',
        # 检查是否看起来像命名空间或系统标识符
        r'^(test_user_\d+|game_chat|namespace)$'
    ]

    for pattern in patterns:
        if re.search(pattern, text):
            logger.info(f"文本 '{text}' 匹配技术标识符模式 '{pattern}'，跳过提取")
            return True

    # 检查内容是否像JSON对象或片段
    if (text.startswith('{') and text.endswith('}')) or (text.startswith('[') and text.endswith(']')):
        logger.info(f"文本 '{text[:30]}...' 看起来像JSON数据，不作为实体提取")
        return True

    return False 