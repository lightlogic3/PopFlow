"""
extract_nodes.py
功能: 从文本中提取实体节点 提示词设计:

extract_message: 从对话消息中提取实体，特别关注发言者和重要实体
extract_json: 从JSON数据中提取实体
extract_text: 从普通文本中提取实体
reflexion: 检查哪些实体可能被漏提取
classify_nodes: 根据实体类型对提取的实体分类
extract_attributes: 从文本中提取实体属性
"""

import json
import os
from typing import Any, Protocol, TypedDict

from jinja2 import Template
from pydantic import BaseModel, Field

from plugIns.memory_system.graphiti_memory.graphiti_core.prompts.models import PromptVersion, PromptFunction, Message


class ExtractedEntity(BaseModel):
    name: str = Field(..., description='Name of the extracted entity')
    entity_type_id: int = Field(
        description='ID of the classified entity type. '
        'Must be one of the provided entity_type_id integers.',
    )


class ExtractedEntities(BaseModel):
    extracted_entities: list[ExtractedEntity] = Field(..., description='List of extracted entities')


class MissedEntities(BaseModel):
    missed_entities: list[str] = Field(..., description="Names of entities that weren't extracted")


class EntityClassificationTriple(BaseModel):
    uuid: str = Field(description='UUID of the entity')
    name: str = Field(description='Name of the entity')
    entity_type: str | None = Field(
        default=None, description='Type of the entity. Must be one of the provided types or None'
    )


class EntityClassification(BaseModel):
    entity_classifications: list[EntityClassificationTriple] = Field(
        ..., description='List of entities classification triples.'
    )


class Prompt(Protocol):
    extract_message: PromptVersion
    extract_json: PromptVersion
    extract_text: PromptVersion
    reflexion: PromptVersion
    classify_nodes: PromptVersion
    extract_attributes: PromptVersion
    extract_nodes: PromptVersion


class Versions(TypedDict):
    extract_message: PromptFunction
    extract_json: PromptFunction
    extract_text: PromptFunction
    reflexion: PromptFunction
    classify_nodes: PromptFunction
    extract_attributes: PromptFunction
    extract_nodes: PromptFunction


def load_template(template_name: str) -> Template:
    """加载指定的模板文件"""
    template_dir = os.path.join(os.path.dirname(__file__), 'templates', 'extract_nodes')
    with open(os.path.join(template_dir, f"{template_name}.j2"), 'r', encoding='utf-8') as f:
        return Template(f.read())


def extract_message(context: dict[str, Any]) -> list[Message]:
    """从对话消息中提取实体节点"""
    template = load_template('extract_message')
    
    # 确保custom_prompt存在，如果不存在则设置为空字符串
    if 'custom_prompt' not in context:
        context['custom_prompt'] = ''
    
    # 将previous_episodes转换为JSON字符串
    if 'previous_episodes' in context:
        context['previous_episodes'] = json.dumps([ep for ep in context['previous_episodes']], indent=2)
    
    sys_prompt = """你是一个AI助手，负责从对话消息中提取实体节点。
    你的主要任务是提取和分类对话中的发言者和其他重要实体。"""
    
    user_prompt = template.render(**context)
    
    return [
        Message(role='system', content=sys_prompt),
        Message(role='user', content=user_prompt),
    ]

def extract_nodes(context: dict[str, Any]) -> list[Message]:
    """从文本或JSON中提取实体节点"""
    source= context.get('source', 'message')
    if source == 'message':
        return extract_message(context)
    elif source == 'json':
        return extract_json(context)
    else:
        return extract_text(context)


def extract_json(context: dict[str, Any]) -> list[Message]:
    """从JSON数据中提取实体"""
    template = load_template('extract_json')
    
    # 确保custom_prompt存在，如果不存在则设置为空字符串
    if 'custom_prompt' not in context:
        context['custom_prompt'] = ''
    
    sys_prompt = """你是一个AI助手，负责从JSON中提取实体节点。
    你的主要任务是从JSON文件中提取和分类相关实体。"""
    
    user_prompt = template.render(**context)
    
    return [
        Message(role='system', content=sys_prompt),
        Message(role='user', content=user_prompt),
    ]


def extract_text(context: dict[str, Any]) -> list[Message]:
    """从普通文本中提取实体"""
    template = load_template('extract_text')
    
    # 确保custom_prompt存在，如果不存在则设置为空字符串
    if 'custom_prompt' not in context:
        context['custom_prompt'] = ''
    
    sys_prompt = """你是一个AI助手，负责从文本中提取实体节点。
    你的主要任务是提取和分类在提供的文本中提到的说话者和其他重要实体。"""
    
    user_prompt = template.render(**context)
    
    return [
        Message(role='system', content=sys_prompt),
        Message(role='user', content=user_prompt),
    ]


def reflexion(context: dict[str, Any]) -> list[Message]:
    """检查哪些实体可能被漏提取"""
    template = load_template('reflexion')
    
    # 将previous_episodes转换为JSON字符串
    if 'previous_episodes' in context:
        context['previous_episodes'] = json.dumps([ep for ep in context['previous_episodes']], indent=2,ensure_ascii=False)
    
    sys_prompt = """你是一个AI助手，负责确定哪些实体尚未从给定上下文中提取"""
    
    user_prompt = template.render(**context)
    
    return [
        Message(role='system', content=sys_prompt),
        Message(role='user', content=user_prompt),
    ]


def classify_nodes(context: dict[str, Any]) -> list[Message]:
    """根据实体类型对提取的实体分类"""
    template = load_template('classify_nodes')
    
    # 将previous_episodes转换为JSON字符串
    if 'previous_episodes' in context:
        context['previous_episodes'] = json.dumps([ep for ep in context['previous_episodes']], indent=2,ensure_ascii=False)
    
    # 将extracted_entities转换为JSON字符串
    if 'extracted_entities' in context and not isinstance(context['extracted_entities'], str):
        context['extracted_entities'] = json.dumps(context['extracted_entities'], indent=2,ensure_ascii=False)
    
    sys_prompt = """你是一个AI助手，根据提取实体的上文对实体节点进行分类"""
    
    user_prompt = template.render(**context)
    
    return [
        Message(role='system', content=sys_prompt),
        Message(role='user', content=user_prompt),
    ]


def extract_attributes(context: dict[str, Any]) -> list[Message]:
    """从文本中提取实体属性"""
    template = load_template('extract_attributes')
    
    # 将previous_episodes和episode_content转换为JSON字符串
    if 'previous_episodes' in context and not isinstance(context['previous_episodes'], str):
        context['previous_episodes'] = json.dumps(context['previous_episodes'], indent=2,ensure_ascii=False)
    
    if 'episode_content' in context and not isinstance(context['episode_content'], str):
        context['episode_content'] = json.dumps(context['episode_content'], indent=2,ensure_ascii=False)
    
    sys_prompt = '你是一个有用的助手，从提供的文本中提取实体属性。'
    
    user_prompt = template.render(**context)
    
    return [
        Message(role='system', content=sys_prompt),
        Message(role='user', content=user_prompt),
    ]


versions: Versions = {
    'extract_message': extract_message,
    'extract_json': extract_json,
    'extract_text': extract_text,
    'reflexion': reflexion,
    'classify_nodes': classify_nodes,
    'extract_attributes': extract_attributes,
    'extract_nodes': extract_nodes,
}
