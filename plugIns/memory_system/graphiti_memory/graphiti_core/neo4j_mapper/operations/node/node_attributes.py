"""
节点属性提取相关操作
"""

import traceback
from contextlib import suppress
from typing import Any
from uuid import uuid4

import pydantic
from pydantic import BaseModel, Field

from knowledge_api.utils.log_config import get_logger
from plugIns.memory_system.graphiti_memory.graphiti_core.config import ModelSize
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.models.graphiti_types import GraphitiClients
from plugIns.memory_system.graphiti_memory.graphiti_core.llm_client import LLMClient
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes import EntityNode, EpisodicNode, \
    create_entity_node_embeddings
from plugIns.memory_system.graphiti_memory.graphiti_core.prompts import prompt_library
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.node.node_extraction import \
    _is_likely_technical_identifier
from plugIns.memory_system.graphiti_memory.graphiti_core.utils.utils import semaphore_gather

logger = get_logger()


async def extract_attributes_from_nodes(
        clients: GraphitiClients,
        nodes: list[EntityNode],
        episode: EpisodicNode | None = None,
        previous_episodes: list[EpisodicNode] | None = None,
        entity_types: dict[str, BaseModel] | None = None,
) -> list[EntityNode]:
    """从多个节点提取属性
    
    参数:
        clients: Graphiti客户端集合
        nodes: 实体节点列表
        episode: 当前剧情节点
        previous_episodes: 之前的剧情节点列表
        entity_types: 实体类型字典
        
    返回:
        更新后的实体节点列表
    """
    llm_client = clients.llm_client
    embedder = clients.embedder
    
    logger.debug(f"开始从 {len(nodes)} 个节点提取属性")

    # 并行从每个节点提取属性
    logger.debug("并行处理节点属性提取")
    updated_nodes: list[EntityNode] = await semaphore_gather(
        *[
            extract_attributes_from_node(
                llm_client,
                node,
                episode,
                previous_episodes,
                entity_types.get(next((item for item in node.labels if item != 'Entity'), ''))
                if entity_types is not None
                else None,
            )
            for node in nodes
        ]
    )
    logger.debug(f"完成 {len(updated_nodes)} 个节点的属性提取")

    # 为节点生成嵌入向量
    logger.debug("为节点生成嵌入向量")
    await create_entity_node_embeddings(embedder, updated_nodes)
    logger.debug("嵌入向量生成完成")

    return updated_nodes


async def extract_attributes_from_node(
        llm_client: LLMClient,
        node: EntityNode,
        episode: EpisodicNode | None = None,
        previous_episodes: list[EpisodicNode] | None = None,
        entity_type: BaseModel | None = None,
) -> EntityNode:
    """从单个节点提取属性
    
    参数:
        llm_client: LLM客户端
        node: 实体节点
        episode: 当前剧情节点
        previous_episodes: 之前的剧情节点列表
        entity_type: 实体类型
        
    返回:
        更新后的实体节点
    """
    logger.debug(f"开始从节点 '{node.name}' 提取属性")

    # 检查节点名称是否是技术标识符
    if _is_likely_technical_identifier(node.name):
        logger.info(f"节点名称 '{node.name}' 可能是技术标识符，跳过属性提取")
        return node

    try:
        # 准备节点上下文
        node_context: dict[str, Any] = {
            'name': node.name,
            'summary': node.summary,
            'entity_types': node.labels,
            'attributes': node.attributes,
        }
        logger.debug(f"准备节点上下文: {node.name}")

        # 定义属性模型字段
        attributes_definitions: dict[str, Any] = {
            'summary': (
                str,
                Field(
                    description='Summary 概括总结有关实体的重要信息。250 字以内',
                ),
            )
        }

        # 添加实体类型特定的字段
        if entity_type is not None:
            logger.debug(f"使用实体类型定义属性: {entity_type.__name__ if hasattr(entity_type, '__name__') else 'Unknown'}")
            for field_name, field_info in entity_type.model_fields.items():
                attributes_definitions[field_name] = (
                    field_info.annotation,
                    Field(description=field_info.description),
                )
                logger.debug(f"添加属性字段: {field_name} - {field_info.description}")

        # 创建动态属性模型
        unique_model_name = f'EntityAttributes_{uuid4().hex}'
        entity_attributes_model = pydantic.create_model(unique_model_name, **attributes_definitions)
        logger.debug(f"创建动态属性模型: {unique_model_name}")

        # 准备LLM上下文
        summary_context: dict[str, Any] = {
            'node': node_context,
            'episode_content': episode.content if episode is not None else '',
            'previous_episodes': [ep.content for ep in previous_episodes]
            if previous_episodes is not None
            else [],
        }

        logger.debug(f"调用LLM提取节点属性，节点名: {node.name}")

        try:
            # 调用LLM提取属性
            llm_response = await llm_client.generate_response(
                prompt_library.extract_nodes.extract_attributes(summary_context),
                response_model=entity_attributes_model,
                model_size=ModelSize.small,
            )
            logger.debug(f"LLM返回属性数据，字段数: {len(llm_response)}")

            # 更新节点摘要和属性
            if 'summary' in llm_response and llm_response['summary']:
                node.summary = llm_response.get('summary', node.summary)
                logger.debug(f"更新节点摘要: {node.summary[:50]}...")
                
            # 收集其他属性
            node_attributes = {key: value for key, value in llm_response.items()}

            # 移除摘要
            with suppress(KeyError):
                del node_attributes['summary']

            # 更新节点属性
            node.attributes.update(node_attributes)
            logger.debug(f"更新节点属性: {', '.join(node_attributes.keys())}")

        except Exception as e:
            logger.error(f"节点属性提取失败: {e}")
            logger.error(traceback.format_exc())

        return node

    except Exception as e:
        logger.error(f"节点属性处理失败: {e}")
        logger.error(traceback.format_exc())
        # 即使发生异常，也返回原始节点
        return node 