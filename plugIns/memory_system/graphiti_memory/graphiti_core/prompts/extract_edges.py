"""
extract_edges.py
功能: 提取实体之间的关系（边） 提示词设计:
edge: 从文本中提取事实三元组，包括关系类型、源实体、目标实体和事实
reflexion: 检查哪些事实可能被漏提取
extract_attributes: 从文本中提取关系的属性
"""

import json
import os
from typing import Any, Protocol, TypedDict

from jinja2 import Template
from pydantic import BaseModel, Field

from plugIns.memory_system.graphiti_memory.graphiti_core.prompts.models import PromptVersion, PromptFunction, Message


class Edge(BaseModel):
    relation_type: str = Field(..., description='FACT_PREDICATE_IN_SCREAMING_SNAKE_CASE')
    source_entity_name: str = Field(..., description='The name of the source entity of the fact.')
    target_entity_name: str = Field(..., description='The name of the target entity of the fact.')
    fact: str = Field(..., description='fact representing the edge and nodes that it connects')
    valid_at: str | None = Field(
        None,
        description='The date and time when the relationship described by the edge fact became true or was established. Use ISO 8601 format (YYYY-MM-DDTHH:MM:SS.SSSSSSZ)',
    )
    invalid_at: str | None = Field(
        None,
        description='The date and time when the relationship described by the edge fact stopped being true or ended. Use ISO 8601 format (YYYY-MM-DDTHH:MM:SS.SSSSSSZ)',
    )


class ExtractedEdges(BaseModel):
    edges: list[Edge]


class MissingFacts(BaseModel):
    missing_facts: list[str] = Field(..., description="facts that weren't extracted")


class Prompt(Protocol):
    edge: PromptVersion
    reflexion: PromptVersion
    extract_attributes: PromptVersion


class Versions(TypedDict):
    edge: PromptFunction
    reflexion: PromptFunction
    extract_attributes: PromptFunction


def load_template(template_name: str) -> Template:
    """加载指定的模板文件"""
    template_dir = os.path.join(os.path.dirname(__file__), 'templates', 'extract_edges')
    with open(os.path.join(template_dir, f"{template_name}.j2"), 'r', encoding='utf-8') as f:
        return Template(f.read())


def edge(context: dict[str, Any]) -> list[Message]:
    """从文本中提取事实三元组"""
    template = load_template('edge')
    
    # 确保custom_prompt存在，如果不存在则设置为空字符串
    if 'custom_prompt' not in context:
        context['custom_prompt'] = ''
    
    # 将previous_episodes转换为JSON字符串
    if 'previous_episodes' in context:
        context['previous_episodes'] = json.dumps([ep for ep in context['previous_episodes']], indent=2,ensure_ascii=False)
    
    sys_prompt = '你是一位专业的事实提取专家，负责从文本中提取事实三元组。' \
                 '1. 提取的事实三元组还应该包含相关的日期信息。' \
                 '2. 将当前时间视为当前消息发送的时间。所有时间信息应相对于此时间提取。'
    
    user_prompt = template.render(**context)
    
    return [
        Message(role='system', content=sys_prompt),
        Message(role='user', content=user_prompt),
    ]


def reflexion(context: dict[str, Any]) -> list[Message]:
    """检查哪些事实可能被漏提取"""
    template = load_template('reflexion')
    
    # 将previous_episodes转换为JSON字符串
    if 'previous_episodes' in context:
        context['previous_episodes'] = json.dumps([ep for ep in context['previous_episodes']], indent=2,ensure_ascii=False)
    
    sys_prompt = """你是一个AI助手，负责确定哪些事实尚未从给定上下文中提取"""
    
    user_prompt = template.render(**context)
    
    return [
        Message(role='system', content=sys_prompt),
        Message(role='user', content=user_prompt),
    ]


def extract_attributes(context: dict[str, Any]) -> list[Message]:
    """从文本中提取事实属性"""
    template = load_template('extract_attributes')
    
    # 将episode_content转换为JSON字符串（如果需要）
    if 'episode_content' in context and not isinstance(context['episode_content'], str):
        context['episode_content'] = json.dumps(context['episode_content'], indent=2,ensure_ascii=False)
    
    sys_prompt = '你是一个有用的助手，从提供的文本中提取事实属性。'
    
    user_prompt = template.render(**context)
    
    return [
        Message(role='system', content=sys_prompt),
        Message(role='user', content=user_prompt),
    ]


versions: Versions = {
    'edge': edge,
    'reflexion': reflexion,
    'extract_attributes': extract_attributes,
}
