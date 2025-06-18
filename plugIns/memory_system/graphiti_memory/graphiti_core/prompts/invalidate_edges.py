"""
功能: 确定哪些边应被标记为失效 提示词设计:

v1: 根据新边和现有边的时间戳确定哪些关系应标记为过期
v2: 确定新事实与哪些现有事实相矛盾
"""

import os
from typing import Any, Protocol, TypedDict

from jinja2 import Template
from pydantic import BaseModel, Field

from plugIns.memory_system.graphiti_memory.graphiti_core.prompts.models import PromptVersion, PromptFunction, Message


class InvalidatedEdges(BaseModel):
    contradicted_facts: list[int] = Field(
        ...,
        description='List of ids of facts that should be invalidated. If no facts should be invalidated, the list should be empty.',
    )


class Prompt(Protocol):
    v1: PromptVersion
    v2: PromptVersion


class Versions(TypedDict):
    v1: PromptFunction
    v2: PromptFunction


def load_template(template_name: str) -> Template:
    """加载指定的模板文件"""
    template_dir = os.path.join(os.path.dirname(__file__), 'templates', 'invalidate_edges')
    with open(os.path.join(template_dir, f"{template_name}.j2"), 'r', encoding='utf-8') as f:
        return Template(f.read())


def v1(context: dict[str, Any]) -> list[Message]:
    """确定哪些关系应该仅根据较新信息中的明确矛盾而失效"""
    template = load_template('v1')
    
    sys_prompt = '你是一个AI助手，帮助确定知识图谱中的哪些关系应该仅根据较新信息中的明确矛盾而失效。'
    
    user_prompt = template.render(**context)
    
    return [
        Message(role='system', content=sys_prompt),
        Message(role='user', content=user_prompt),
    ]


def v2(context: dict[str, Any]) -> list[Message]:
    """确定新事实与哪些现有事实相矛盾"""
    template = load_template('v2')
    
    sys_prompt = '你是一个AI助手，负责确定哪些事实相互矛盾。'
    
    user_prompt = template.render(**context)
    
    return [
        Message(role='system', content=sys_prompt),
        Message(role='user', content=user_prompt),
    ]


versions: Versions = {'v1': v1, 'v2': v2}
