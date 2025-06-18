"""
功能: 提取边的有效日期和失效日期 提示词设计:
v1: 分析对话并提取与关系建立或变化相关的日期时间信息
"""

import os
from typing import Any, Protocol, TypedDict

from jinja2 import Template
from pydantic import BaseModel, Field

from plugIns.memory_system.graphiti_memory.graphiti_core.prompts.models import PromptVersion, PromptFunction, Message


class EdgeDates(BaseModel):
    valid_at: str | None = Field(
        None,
        description='The date and time when the relationship described by the edge fact became true or was established. YYYY-MM-DDTHH:MM:SS.SSSSSSZ or null.',
    )
    invalid_at: str | None = Field(
        None,
        description='The date and time when the relationship described by the edge fact stopped being true or ended. YYYY-MM-DDTHH:MM:SS.SSSSSSZ or null.',
    )


class Prompt(Protocol):
    v1: PromptVersion


class Versions(TypedDict):
    v1: PromptFunction


def load_template(template_name: str) -> Template:
    """加载指定的模板文件"""
    template_dir = os.path.join(os.path.dirname(__file__), 'templates', 'extract_edge_dates')
    with open(os.path.join(template_dir, f"{template_name}.j2"), 'r', encoding='utf-8') as f:
        return Template(f.read())

def v1(context: dict[str, Any]) -> list[Message]:
    """提取与关系建立或变化相关的日期时间信息"""
    template = load_template('v1')
    sys_prompt = '你是一个AI助手，负责为图边提取日期时间信息，只关注与边事实中描述的关系的建立或变化直接相关的日期。'
    user_prompt = template.render(**context)
    return [
        Message(role='system', content=sys_prompt),
        Message(role='user', content=user_prompt),
    ]


versions: Versions = {'v1': v1}
