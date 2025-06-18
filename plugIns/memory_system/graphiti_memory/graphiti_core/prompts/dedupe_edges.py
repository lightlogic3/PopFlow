"""
功能: 去除重复的边（关系） 提示词设计:

edge: 判断新边是否代表与现有边相同的事实
edge_list: 查找边列表中的所有重复项
resolve_edge: 去除重复事实并确定相互矛盾的事实
"""
import json
import os
from typing import Any, Protocol, TypedDict
from jinja2 import Template
from pydantic import BaseModel, Field

from plugIns.memory_system.graphiti_memory.graphiti_core.prompts.models import PromptVersion, PromptFunction, Message


class EdgeDuplicate(BaseModel):
    duplicate_fact_id: int = Field(
        ...,
        description='id of the duplicate fact. If no duplicate facts are found, default to -1.',
    )
    contradicted_facts: list[int] = Field(
        ...,
        description='List of ids of facts that should be invalidated. If no facts should be invalidated, the list should be empty.',
    )
    fact_type: str = Field(..., description='One of the provided fact types or DEFAULT')


class UniqueFact(BaseModel):
    uuid: str = Field(..., description='unique identifier of the fact')
    fact: str = Field(..., description='fact of a unique edge')


class UniqueFacts(BaseModel):
    unique_facts: list[UniqueFact]


class Prompt(Protocol):
    edge: PromptVersion
    edge_list: PromptVersion
    resolve_edge: PromptVersion


class Versions(TypedDict):
    edge: PromptFunction
    edge_list: PromptFunction
    resolve_edge: PromptFunction


def load_template(template_name: str) -> Template:
    """加载指定的模板文件"""
    template_dir = os.path.join(os.path.dirname(__file__), 'templates', 'dedupe_edges')
    with open(os.path.join(template_dir, f"{template_name}.j2"), 'r', encoding='utf-8') as f:
        return Template(f.read())


def edge(context: dict[str, Any]) -> list[Message]:
    """判断新边是否代表现有边列表中的任何边"""
    template = load_template('edge')
    
    # 将相关数据转换为JSON字符串（如果需要）
    if 'related_edges' in context and not isinstance(context['related_edges'], str):
        context['related_edges'] = json.dumps(context['related_edges'], indent=2,ensure_ascii=False)
    
    if 'extracted_edges' in context and not isinstance(context['extracted_edges'], str):
        context['extracted_edges'] = json.dumps(context['extracted_edges'], indent=2,ensure_ascii=False)
    
    sys_prompt = '你是一个有用的助手，负责从边列表中去除重复边。'
    
    user_prompt = template.render(**context)
    
    return [
        Message(role='system', content=sys_prompt),
        Message(role='user', content=user_prompt),
    ]


def edge_list(context: dict[str, Any]) -> list[Message]:
    """查找事实列表中的所有重复项"""
    template = load_template('edge_list')
    
    # 将edges转换为JSON字符串（如果需要）
    if 'edges' in context and not isinstance(context['edges'], str):
        context['edges'] = json.dumps(context['edges'], indent=2,ensure_ascii=False)
    
    sys_prompt = '你是一个有用的助手，负责从边列表中去除重复边。'
    
    user_prompt = template.render(**context)
    
    return [
        Message(role='system', content=sys_prompt),
        Message(role='user', content=user_prompt),
    ]


def resolve_edge(context: dict[str, Any]) -> list[Message]:
    """去除重复事实并确定相互矛盾的事实"""
    template = load_template('resolve_edge')
    
    # 将相关数据转换为JSON字符串（如果需要）
    if 'new_edge' in context and not isinstance(context['new_edge'], str):
        context['new_edge'] = json.dumps(context['new_edge'], indent=2,ensure_ascii=False)
    
    if 'existing_edges' in context and not isinstance(context['existing_edges'], str):
        context['existing_edges'] = json.dumps(context['existing_edges'], indent=2,ensure_ascii=False)
    
    if 'edge_invalidation_candidates' in context and not isinstance(context['edge_invalidation_candidates'], str):
        context['edge_invalidation_candidates'] = json.dumps(context['edge_invalidation_candidates'], indent=2,ensure_ascii=False)
    
    if 'edge_types' in context and not isinstance(context['edge_types'], str):
        context['edge_types'] = json.dumps(context['edge_types'], indent=2,ensure_ascii=False)
    
    sys_prompt = '你是一个有用的助手，负责从事实列表中去除重复事实并确定哪些现有事实与新事实相矛盾。'
    
    user_prompt = template.render(**context)
    
    return [
        Message(role='system', content=sys_prompt),
        Message(role='user', content=user_prompt),
    ]


versions: Versions = {'edge': edge, 'edge_list': edge_list, 'resolve_edge': resolve_edge}
