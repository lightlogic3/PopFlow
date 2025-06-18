"""
功能: 评估和优化查询和结果 提示词设计:
query_expansion: 将问题改写为更适合数据库检索的查询
qa_prompt: 根据实体摘要和事实从第一人称视角回答问题
eval_prompt: 评判回答是否符合标准答案
eval_add_episode_results: 比较基准图构建结果和候选图构建结果的质量
"""

import json
import os
from typing import Any, Protocol, TypedDict
from jinja2 import Template
from pydantic import BaseModel, Field

from plugIns.memory_system.graphiti_memory.graphiti_core.prompts.models import PromptVersion, PromptFunction, Message


class QueryExpansion(BaseModel):
    query: str = Field(..., description='query optimized for database search')


class QAResponse(BaseModel):
    ANSWER: str = Field(..., description='how Alice would answer the question')


class EvalResponse(BaseModel):
    is_correct: bool = Field(..., description='boolean if the answer is correct or incorrect')
    reasoning: str = Field(
        ..., description='why you determined the response was correct or incorrect'
    )


class EvalAddEpisodeResults(BaseModel):
    candidate_is_worse: bool = Field(
        ...,
        description='boolean if the baseline extraction is higher quality than the candidate extraction.',
    )
    reasoning: str = Field(
        ..., description='why you determined the response was correct or incorrect'
    )


class Prompt(Protocol):
    qa_prompt: PromptVersion
    eval_prompt: PromptVersion
    query_expansion: PromptVersion
    eval_add_episode_results: PromptVersion


class Versions(TypedDict):
    qa_prompt: PromptFunction
    eval_prompt: PromptFunction
    query_expansion: PromptFunction
    eval_add_episode_results: PromptFunction


def load_template(template_name: str) -> Template:
    """加载指定的模板文件"""
    template_dir = os.path.join(os.path.dirname(__file__), 'templates', 'eval')
    with open(os.path.join(template_dir, f"{template_name}.j2"), 'r', encoding='utf-8') as f:
        return Template(f.read())


def query_expansion(context: dict[str, Any]) -> list[Message]:
    """将问题改写为更适合数据库检索的查询"""
    template = load_template('query_expansion')
    sys_prompt = """你是一个专家，能将问题改写成适用于数据库检索系统的查询"""
    user_prompt = template.render(**context)
    
    return [
        Message(role='system', content=sys_prompt),
        Message(role='user', content=user_prompt),
    ]


def qa_prompt(context: dict[str, Any]) -> list[Message]:
    """根据实体摘要和事实从第一人称视角回答问题"""
    template = load_template('qa_prompt')
    
    # 将entity_summaries和facts转换为JSON字符串（如果需要）
    if 'entity_summaries' in context and not isinstance(context['entity_summaries'], str):
        context['entity_summaries'] = json.dumps(context['entity_summaries'], indent=2,ensure_ascii=False)
    
    if 'facts' in context and not isinstance(context['facts'], str):
        context['facts'] = json.dumps(context['facts'], indent=2,ensure_ascii=False)
    
    sys_prompt = """你是Alice，应该从Alice的第一人称视角回答所有问题"""
    
    user_prompt = template.render(**context)
    
    return [
        Message(role='system', content=sys_prompt),
        Message(role='user', content=user_prompt),
    ]


def eval_prompt(context: dict[str, Any]) -> list[Message]:
    """评判回答是否符合标准答案"""
    template = load_template('eval_prompt')
    
    sys_prompt = (
        """你是一位评判，负责判断对问题的回答是否符合标准答案"""
    )
    
    user_prompt = template.render(**context)
    
    return [
        Message(role='system', content=sys_prompt),
        Message(role='user', content=user_prompt),
    ]


def eval_add_episode_results(context: dict[str, Any]) -> list[Message]:
    """比较基准图构建结果和候选图构建结果的质量"""
    template = load_template('eval_add_episode_results')
    
    sys_prompt = """你是一位评判，负责确定基于相同消息列表的基准图构建结果是否比候选图构建结果更好。"""
    
    user_prompt = template.render(**context)
    
    return [
        Message(role='system', content=sys_prompt),
        Message(role='user', content=user_prompt),
    ]


versions: Versions = {
    'qa_prompt': qa_prompt,
    'eval_prompt': eval_prompt,
    'query_expansion': query_expansion,
    'eval_add_episode_results': eval_add_episode_results,
}
