import logging
from typing import List

from knowledge_api.utils.log_config import get_logger
from plugIns.memory_system.graphiti_memory.graphiti_core.utils.utils import lucene_sanitize

logger = get_logger()

MAX_QUERY_LENGTH = 32


def fulltext_query(query: str, group_ids: List[str] | None = None):
    """
    构建Lucene全文搜索查询，用于Neo4j全文索引搜索
    
    参数:
    ----
    query : str
        要搜索的文本查询
    group_ids : List[str] | None, optional
        要过滤的组ID列表
        
    返回:
    ----
    str
        格式化的Lucene查询字符串，如果查询过长则返回空字符串
    """
    group_ids_filter_list = (
        [f'group_id:"{lucene_sanitize(g)}"' for g in group_ids] if group_ids is not None else []
    )
    group_ids_filter = ''
    for f in group_ids_filter_list:
        group_ids_filter += f if not group_ids_filter else f'OR {f}'

    group_ids_filter += ' AND ' if group_ids_filter else ''

    lucene_query = lucene_sanitize(query)
    # 如果lucene查询太长则返回空查询
    if len(lucene_query.split(' ')) + len(group_ids or '') >= MAX_QUERY_LENGTH:
        return ''

    full_query = group_ids_filter + '(' + lucene_query + ')'

    return full_query 