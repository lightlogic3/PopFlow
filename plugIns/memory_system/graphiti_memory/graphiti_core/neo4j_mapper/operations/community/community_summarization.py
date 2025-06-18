"""
社区摘要相关操作
"""

from knowledge_api.utils.log_config import get_logger
from plugIns.memory_system.graphiti_memory.graphiti_core.llm_client import LLMClient
from plugIns.memory_system.graphiti_memory.graphiti_core.prompts import prompt_library
from plugIns.memory_system.graphiti_memory.graphiti_core.prompts.summarize_nodes import Summary, SummaryDescription

logger = get_logger()


async def summarize_pair(llm_client: LLMClient, summary_pair: tuple[str, str]) -> str:
    """总结一对摘要
    
    参数:
        llm_client: LLM客户端
        summary_pair: 要总结的一对摘要
        
    返回:
        合并后的摘要
    """
    logger.debug(f"开始总结一对摘要")
    # 准备LLM上下文
    context = {'node_summaries': [{'summary': summary} for summary in summary_pair]}
    logger.debug(f"准备LLM上下文完成")

    logger.debug(f"调用LLM进行摘要合并")
    llm_response = await llm_client.generate_response(
        prompt_library.summarize_nodes.summarize_pair(context), response_model=Summary
    )

    pair_summary = llm_response.get('summary', '')
    logger.debug(f"获得合并摘要，长度: {len(pair_summary)}")

    return pair_summary


async def generate_summary_description(llm_client: LLMClient, summary: str) -> str:
    """为摘要生成描述
    
    参数:
        llm_client: LLM客户端
        summary: 要描述的摘要
        
    返回:
        摘要描述
    """
    logger.debug(f"为摘要生成描述，摘要长度: {len(summary)}")
    context = {'summary': summary}

    logger.debug(f"调用LLM生成摘要描述")
    llm_response = await llm_client.generate_response(
        prompt_library.summarize_nodes.summary_description(context),
        response_model=SummaryDescription,
    )

    description = llm_response.get('description', '')
    logger.debug(f"生成的摘要描述: {description}")

    return description 