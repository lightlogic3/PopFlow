"""
summarize_nodes.py
功能: 为实体节点生成摘要 提示词设计:

summarize_pair: 合并两个摘要中的信息
summarize_context: 根据消息和实体上下文创建实体摘要
summary_description: 为摘要创建一句话描述
"""

import json
import os
from typing import Any, Protocol, TypedDict

from jinja2 import Template
from pydantic import BaseModel, Field

from plugIns.memory_system.graphiti_memory.graphiti_core.prompts.models import PromptVersion, PromptFunction, Message


class Summary(BaseModel):
    summary: str = Field(
        ...,
        description='Summary containing the important information about the entity. Under 250 words',
    )


class SummaryDescription(BaseModel):
    description: str = Field(..., description='One sentence description of the provided summary')


class Prompt(Protocol):
    summarize_pair: PromptVersion
    summarize_context: PromptVersion
    summary_description: PromptVersion


class Versions(TypedDict):
    summarize_pair: PromptFunction
    summarize_context: PromptFunction
    summary_description: PromptFunction


def load_template(template_name: str) -> Template:
    """加载指定的模板文件"""
    template_dir = os.path.join(os.path.dirname(__file__), 'templates', 'summarize_nodes')
    with open(os.path.join(template_dir, f"{template_name}.j2"), 'r', encoding='utf-8') as f:
        return Template(f.read())


def summarize_pair(context: dict[str, Any]) -> list[Message]:
    """合并两个摘要中的信息"""
    template = load_template('summarize_pair')
    
    # 将node_summaries转换为JSON字符串（如果需要）
    if 'node_summaries' in context and not isinstance(context['node_summaries'], str):
        context['node_summaries'] = json.dumps(context['node_summaries'], indent=2,ensure_ascii=False)
    sys_prompt = '你是一个有用的助手，负责合并摘要。'
    
    user_prompt = template.render(**context)
    
    return [
        Message(role='system', content=sys_prompt),
        Message(role='user', content=user_prompt),
    ]


def summarize_context(context: dict[str, Any]) -> list[Message]:
    """根据消息和实体上下文创建实体摘要"""
    template = load_template('summarize_context')
    
    # 将previous_episodes和episode_content转换为JSON字符串
    if 'previous_episodes' in context and not isinstance(context['previous_episodes'], str):
        context['previous_episodes'] = json.dumps(context['previous_episodes'], indent=2,ensure_ascii=False)
    
    if 'episode_content' in context and not isinstance(context['episode_content'], str):
        context['episode_content'] = json.dumps(context['episode_content'], indent=2,ensure_ascii=False)
    
    # 将attributes转换为JSON字符串
    if 'attributes' in context and not isinstance(context['attributes'], str):
        context['attributes'] = json.dumps(context['attributes'], indent=2,ensure_ascii=False)
    
    sys_prompt = '你是一个有用的助手，从提供的文本中提取实体属性。'
    
    user_prompt = template.render(**context)
    
    return [
        Message(role='system', content=sys_prompt),
        Message(role='user', content=user_prompt),
    ]


def summary_description(context: dict[str, Any]) -> list[Message]:
    """为摘要创建一句话描述"""
    template = load_template('summary_description')
    
    # 将summary转换为JSON字符串（如果需要）
    if 'summary' in context and not isinstance(context['summary'], str):
        context['summary'] = json.dumps(context['summary'], indent=2,ensure_ascii=False)
    
    sys_prompt = '你是一个有用的助手，用一句话描述提供的内容。'
    
    user_prompt = template.render(**context)
    
    return [
        Message(role='system', content=sys_prompt),
        Message(role='user', content=user_prompt),
    ]


versions: Versions = {
    'summarize_pair': summarize_pair,
    'summarize_context': summarize_context,
    'summary_description': summary_description,
}
