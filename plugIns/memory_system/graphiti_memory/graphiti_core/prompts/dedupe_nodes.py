"""
dedupe_nodes.py
功能: 去除重复的实体节点
提示词设计:
node: 判断新实体是否是现有实体的重复
nodes: 判断多个提取的实体是否是现有实体的重复
node_list: 对节点列表去重并合并摘要信息
"""

import json
import os
from typing import Any, Protocol, TypedDict

from jinja2 import Template
from pydantic import BaseModel, Field

from plugIns.memory_system.graphiti_memory.graphiti_core.prompts.models import PromptVersion, PromptFunction, Message


class NodeDuplicate(BaseModel):
    id: int = Field(..., description='实体的整数 ID')
    duplicate_idx: int = Field(
        ...,
        description='idx of the duplicate node. If no duplicate nodes are found, default to -1.',
    )
    name: str = Field(
        ...,
        description='Name of the entity. Should be the most complete and descriptive name possible.',
    )


class NodeResolutions(BaseModel):
    entity_resolutions: list[NodeDuplicate] = Field(..., description='List of resolved nodes')


class Prompt(Protocol):
    node: PromptVersion
    node_list: PromptVersion
    nodes: PromptVersion


class Versions(TypedDict):
    node: PromptFunction
    node_list: PromptFunction
    nodes: PromptFunction


def load_template(template_name: str) -> Template:
    """加载指定的模板文件"""
    template_dir = os.path.join(os.path.dirname(__file__), 'templates', 'dedupe_nodes')
    with open(os.path.join(template_dir, f"{template_name}.j2"), 'r', encoding='utf-8') as f:
        return Template(f.read())


def node(context: dict[str, Any]) -> list[Message]:
    """确定一个新实体是否是任何现有实体的重复"""
    template = load_template('node')
    # 将previous_episodes转换为JSON字符串
    if 'previous_episodes' in context:
        context['previous_episodes'] = json.dumps([ep for ep in context['previous_episodes']], indent=2,
                                                  ensure_ascii=False)
    # 将extracted_node和entity_type_description转换为JSON字符串
    if 'extracted_node' in context and not isinstance(context['extracted_node'], str):
        context['extracted_node'] = json.dumps(context['extracted_node'], indent=2, ensure_ascii=False)

    if 'entity_type_description' in context and not isinstance(context['entity_type_description'], str):
        context['entity_type_description'] = json.dumps(context['entity_type_description'], indent=2,
                                                        ensure_ascii=False)

    # 将existing_nodes转换为JSON字符串
    if 'existing_nodes' in context and not isinstance(context['existing_nodes'], str):
        context['existing_nodes'] = json.dumps(context['existing_nodes'], indent=2, ensure_ascii=False)
    sys_prompt = '你是一个有用的助手，负责确定一个新实体是否是任何现有实体的重复。'
    user_prompt = template.render(**context)
    return [
        Message(role='system', content=sys_prompt),
        Message(role='user', content=user_prompt),
    ]


def nodes(context: dict[str, Any]) -> list[Message]:
    """确定从对话中提取的实体是否是现有实体的重复"""
    template = load_template('nodes')

    # 将previous_episodes转换为JSON字符串
    if 'previous_episodes' in context:
        context['previous_episodes'] = json.dumps([ep for ep in context['previous_episodes']], indent=2,
                                                  ensure_ascii=False)

    # 将extracted_nodes转换为JSON字符串
    if 'extracted_nodes' in context and not isinstance(context['extracted_nodes'], str):
        context['extracted_nodes'] = json.dumps(context['extracted_nodes'], indent=2, ensure_ascii=False)
    sys_prompt = '你是一个有用的助手，负责确定从对话中提取的实体是否是现有实体的重复。'
    user_prompt = template.render(**context)
    return [
        Message(role='system', content=sys_prompt),
        Message(role='user', content=user_prompt),
    ]


def node_list(context: dict[str, Any]) -> list[Message]:
    """从节点列表中去除重复"""
    template = load_template('node_list')
    # 将nodes转换为JSON字符串
    if 'nodes' in context and not isinstance(context['nodes'], str):
        context['nodes'] = json.dumps(context['nodes'], indent=2, ensure_ascii=False)
    sys_prompt = '你是一个有用的助手，负责从节点列表中去除重复。'
    user_prompt = template.render(**context)
    return [
        Message(role='system', content=sys_prompt),
        Message(role='user', content=user_prompt),
    ]


versions: Versions = {'node': node, 'node_list': node_list, 'nodes': nodes}
