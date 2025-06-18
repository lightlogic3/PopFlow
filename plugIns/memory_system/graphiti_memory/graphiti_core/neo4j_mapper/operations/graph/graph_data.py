"""
图数据库基础操作，包括数据清除和检索
"""

import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from neo4j import AsyncDriver, Record

from knowledge_api.utils.log_config import get_logger
from plugIns.memory_system.graphiti_memory.graphiti_core.config import DEFAULT_DATABASE, EPISODE_WINDOW_LEN
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes import EpisodicNode, EpisodeType
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.template.graph_templates import (
    CLEAR_DATA_BY_GROUP_TEMPLATE,
    CLEAR_ALL_DATA_TEMPLATE,
    RETRIEVE_EPISODES_TEMPLATE,
    RETRIEVE_EPISODES_BY_REFERENCE_TIME_TEMPLATE,
)

logger = get_logger()



async def clear_data(driver: AsyncDriver, group_id: str = None):
    """清除数据库中的数据
    
    参数:
        driver: Neo4j驱动
        group_id: 分组ID，如果提供则只清除指定分组的数据
    """
    start_time = time.time()
    
    if group_id:
        logger.info(f"清除分组 {group_id} 的所有数据")
        await driver.execute_query(
            CLEAR_DATA_BY_GROUP_TEMPLATE.render(),
            group_id=group_id,
            database_=DEFAULT_DATABASE,
        )
    else:
        logger.info("清除所有数据")
        await driver.execute_query(
            CLEAR_ALL_DATA_TEMPLATE,
            database_=DEFAULT_DATABASE,
        )
    
    end_time = time.time()
    logger.info(f"数据清除完成，用时: {end_time - start_time:.2f}秒")


async def retrieve_episodes(
    driver: AsyncDriver,
    reference_time: datetime,
    last_n: int = EPISODE_WINDOW_LEN,
    group_ids: Optional[List[str]] = None,
    source: Optional[EpisodeType] = None,
) -> List[EpisodicNode]:
    """检索剧情节点
    
    根据参考时间检索最近的剧情节点。
    
    参数:
        driver: Neo4j驱动
        reference_time: 参考时间，只检索valid_at小于等于此时间的节点
        last_n: 返回的最近节点数量
        group_ids: 分组ID列表，如果提供则只检索指定分组的数据
        source: 源类型过滤器
        
    返回:
        检索到的剧情节点列表，按时间正序排列
    """
    logger.debug(f"检索剧情节点，参考时间: {reference_time}, 数量: {last_n}")
    start_time = time.time()
    
    # 构建查询参数
    parameters = {
        "reference_time": reference_time,
        "num_episodes": last_n,
    }
    
    if group_ids and len(group_ids) > 0:
        parameters["group_ids"] = group_ids
        
    if source is not None:
        parameters["source"] = source.name
    
    # 构建模板上下文
    template_context = {
        "group_ids": bool(group_ids and len(group_ids) > 0),
        "source": bool(source is not None)
    }
    
    # 渲染查询
    query = RETRIEVE_EPISODES_BY_REFERENCE_TIME_TEMPLATE.render(**template_context)
    
    logger.debug(f"执行查询: {query}")
    logger.debug(f"查询参数: {parameters}")
    
    # 执行查询
    result, _, _ = await driver.execute_query(
        query,
        parameters,
        database_=DEFAULT_DATABASE,
    )
    
    # 转换结果
    episodes = []
    for record in result:
        episode = EpisodicNode(
            content=record['content'],
            created_at=record['created_at'].to_native(),
            valid_at=record['valid_at'].to_native(),
            uuid=record['uuid'],
            group_id=record['group_id'],
            source=EpisodeType.from_str(record['source']),
            name=record['name'],
            source_description=record['source_description'],
        )
        episodes.append(episode)
    
    # 反转结果，返回按时间正序排列的列表
    episodes = list(reversed(episodes))
    
    end_time = time.time()
    logger.debug(f"检索到 {len(episodes)} 个节点，用时: {end_time - start_time:.2f}秒")
    
    return episodes


async def retrieve_episodes_advanced(
    driver: AsyncDriver,
    group_id: str,
    exclude_uuids: Optional[List[str]] = None,
    limit: int = 100,
    offset: int = 0,
    content_contain: Optional[str] = None,
    include_hidden: bool = False,
    source: Optional[str] = None,
    query_result_timeout: int = 60,
    long_term_cutoff_valid_at: Optional[int] = None,
) -> List[EpisodicNode]:
    """高级剧情节点检索
    
    使用更多筛选条件检索剧情节点。
    
    参数:
        driver: Neo4j驱动
        group_id: 分组ID
        exclude_uuids: 要排除的UUID列表
        limit: 返回的最大记录数
        offset: 查询的偏移量
        content_contain: 内容包含的文本
        include_hidden: 是否包含隐藏的节点
        source: 源过滤器
        query_result_timeout: 查询超时时间（秒）
        long_term_cutoff_valid_at: 长期记忆的有效期截止时间
        
    返回:
        检索到的剧情节点列表
    """
    logger.debug(f"高级检索分组 {group_id} 的剧情节点")
    start_time = time.time()
    
    # 构建查询条件
    exclude_uuids = exclude_uuids or []
    conditions = []
    parameters: Dict[str, Any] = {"group_id": group_id}
    
    conditions.append("n.group_id = $group_id")
    
    if exclude_uuids:
        conditions.append("NOT n.uuid IN $exclude_uuids")
        parameters["exclude_uuids"] = exclude_uuids
        
    if not include_hidden:
        conditions.append("(NOT EXISTS(n.hidden) OR n.hidden = false)")
    
    if source:
        conditions.append("n.source = $source")
        parameters["source"] = source
    
    if content_contain:
        conditions.append("n.content CONTAINS $content_contain")
        parameters["content_contain"] = content_contain
    
    if long_term_cutoff_valid_at:
        conditions.append("n.valid_at >= $long_term_cutoff_valid_at")
        parameters["long_term_cutoff_valid_at"] = long_term_cutoff_valid_at
    
    # 构建完整的查询语句
    conditions_str = " AND ".join(conditions)
    query = RETRIEVE_EPISODES_TEMPLATE.render(conditions=conditions_str)
    
    parameters["offset"] = offset
    parameters["limit"] = limit
    
    logger.debug(f"执行查询: {query}")
    logger.debug(f"查询参数: {parameters}")
    
    # 执行查询
    records, _, _ = await driver.execute_query(
        query,
        parameters,
        database_=DEFAULT_DATABASE,
        result_timeout=query_result_timeout,
    )
    
    result = [_record_to_episodic_node(record["n"]) for record in records]
    
    end_time = time.time()
    logger.debug(f"检索到 {len(result)} 个节点，用时: {end_time - start_time:.2f}秒")
    
    return result


def _record_to_episodic_node(record: Record) -> EpisodicNode:
    """将数据库记录转换为EpisodicNode对象
    
    参数:
        record: 数据库记录
        
    返回:
        EpisodicNode对象
    """
    # 从记录中提取属性
    props = {**record}
    
    # 确保必要的字段存在
    if "uuid" not in props:
        logger.warning("记录中缺少uuid字段")
        props["uuid"] = ""
    
    if "created_at" not in props:
        logger.warning("记录中缺少created_at字段")
        props["created_at"] = int(time.time())
    
    if "valid_at" not in props:
        logger.warning("记录中缺少valid_at字段")
        props["valid_at"] = int(time.time())
    
    # 创建并返回EpisodicNode对象
    return EpisodicNode(**props) 