"""
搜索相关工具函数
"""

from typing import Optional, List, Dict, Any, Union

from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.edges import EntityEdge
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.models.search_models import SearchFilters, \
    ComparisonOperator, DateFilter, SearchConfig
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes import EntityNode
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.search.recipes import \
    COMBINED_HYBRID_SEARCH_CROSS_ENCODER, EDGE_HYBRID_SEARCH_CROSS_ENCODER, COMBINED_HYBRID_SEARCH_RRF, \
    EDGE_HYBRID_SEARCH_RRF
from plugIns.memory_system.graphiti_memory.utils.time_utils import to_local_time, from_local_time
from datetime import datetime
from knowledge_api.utils.log_config import get_logger
logger = get_logger()

def select_search_config(use_reranker: bool, entity_filter: Optional[List[str]], top_k: int) -> SearchConfig:
    """选择合适的搜索配置
    
    Args:
        use_reranker: 是否使用重排序
        entity_filter: 实体类型过滤
        top_k: 返回结果数量
        
    Returns:
        搜索配置
    """
    # 选择搜索配置
    if use_reranker:
        if entity_filter:
            search_config = COMBINED_HYBRID_SEARCH_CROSS_ENCODER
            logger.info("使用综合交叉编码器搜索配置")
        else:
            search_config = EDGE_HYBRID_SEARCH_CROSS_ENCODER
            logger.info("使用边交叉编码器搜索配置")
    else:
        if entity_filter:
            search_config = COMBINED_HYBRID_SEARCH_RRF
            logger.info("使用综合RRF搜索配置")
        else:
            search_config = EDGE_HYBRID_SEARCH_RRF
            logger.info("使用边RRF搜索配置")
    
    # 设置搜索结果数量
    search_config.limit = top_k * 3  # 获取更多结果供后续过滤
    return search_config

def build_search_filter(entity_filter=None, time_filter=None) -> SearchFilters:
    """构建搜索过滤器
    
    Args:
        entity_filter: 实体类型过滤
        time_filter: 时间过滤参数
        
    Returns:
        搜索过滤器
    """
    search_filter = SearchFilters()
    
    # 添加实体类型过滤
    if entity_filter:
        search_filter.node_labels = entity_filter
        logger.info(f"已设置实体类型过滤: {entity_filter}")
    
    # 添加时间过滤
    if time_filter:
        filter_type = time_filter.get("type", "valid_at")
        operator = time_filter.get("operator", "gt")
        date_value = time_filter.get("value")
        
        if date_value:
            # 转换日期格式
            if isinstance(date_value, str):
                try:
                    date_value = datetime.fromisoformat(date_value)
                except ValueError:
                    logger.warning(f"无效的日期格式: {date_value}")
                    return search_filter
            
            # 确保日期值是UTC时区
            date_value = from_local_time(date_value)
            
            # 创建日期过滤器
            date_filter = DateFilter(
                comparison_operator=getattr(ComparisonOperator, operator.upper()),
                date=date_value
            )
            
            # 设置过滤条件
            filter_attr = f"{filter_type}"
            if hasattr(search_filter, filter_attr):
                setattr(search_filter, filter_attr, [[date_filter]])
                local_time = to_local_time(date_value)
                logger.info(f"添加时间过滤器: {filter_type} {operator} {local_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    return search_filter

def add_time_info(result: Dict[str, Any], edge_or_node: Union[EntityEdge, EntityNode]):
    """添加时间信息到结果
    
    Args:
        result: 结果字典
        edge_or_node: 边或节点对象
    """
    # 处理valid_at时间
    if hasattr(edge_or_node, "valid_at") and edge_or_node.valid_at:
        utc_time = edge_or_node.valid_at
        if utc_time.tzinfo is None:
            from datetime import timezone
            utc_time = utc_time.replace(tzinfo=timezone.utc)
        
        local_time = to_local_time(utc_time)
        
        result["valid_at"] = utc_time.isoformat()
        result["valid_at_local"] = local_time.isoformat()
        result["timestamp"] = utc_time.isoformat()  # 兼容旧代码
        result["timestamp_local"] = local_time.isoformat()
        result["formatted_time"] = local_time.strftime("%Y-%m-%d %H:%M:%S")
    
    # 处理invalid_at时间
    if hasattr(edge_or_node, "invalid_at") and edge_or_node.invalid_at:
        utc_time = edge_or_node.invalid_at
        if utc_time.tzinfo is None:
            from datetime import timezone
            utc_time = utc_time.replace(tzinfo=timezone.utc)
        
        local_time = to_local_time(utc_time)
        
        result["invalid_at"] = utc_time.isoformat()
        result["invalid_at_local"] = local_time.isoformat()
        result["formatted_invalid_time"] = local_time.strftime("%Y-%m-%d %H:%M:%S")

def log_sample_results(edges, nodes, sample_size=2):
    """记录样本结果用于调试
    
    Args:
        edges: 边列表
        nodes: 节点列表
        sample_size: 样本大小
    """
    # 记录边样本
    for i, edge in enumerate(edges[:sample_size]):
        if i >= sample_size:
            break
        score = edge.score if hasattr(edge, "score") else 0.0
        content = edge.fact[:50] + "..." if hasattr(edge, "fact") and len(edge.fact) > 50 else "无内容"
        logger.info(f"边结果样本 {i+1}: 分数={score:.4f}, 内容={content}")
    
    # 记录节点样本
    for i, node in enumerate(nodes[:sample_size]):
        if i >= sample_size:
            break
        score = node.score if hasattr(node, "score") else 0.0
        name = node.name if hasattr(node, "name") else "未命名"
        summary = node.summary[:50] + "..." if hasattr(node, "summary") and node.summary and len(node.summary) > 50 else "无描述"
        logger.info(f"节点结果样本 {i+1}: 分数={score:.4f}, 名称={name}, 描述={summary}")

def format_search_results(search_results, user_id: str, filter_terms: Optional[List[str]]) -> List[Dict[str, Any]]:
    """格式化搜索结果
    
    Args:
        search_results: 搜索结果
        user_id: 用户ID
        filter_terms: 过滤关键词
        
    Returns:
        格式化后的结果列表
    """
    results = []
    
    # 获取所有结果
    search_edges = search_results.edges
    search_nodes = search_results.nodes if hasattr(search_results, 'nodes') else []
    
    # 记录结果数量
    total_results = len(search_edges) + len(search_nodes)
    logger.info(f"检索到 {total_results} 条原始结果 (边: {len(search_edges)}, 节点: {len(search_nodes)})")
    
    # 记录部分结果的详情
    log_sample_results(search_edges, search_nodes)
    
    # 处理边结果
    for edge in search_edges:
        if not hasattr(edge, "fact") or not edge.fact:
            continue
        
        # 关键词过滤
        if filter_terms and all(term.lower() not in edge.fact.lower() for term in filter_terms):
            continue
        
        # 创建基本结果
        result = {
            "id": edge.uuid,
            "content": edge.fact,
            "score": edge.score if hasattr(edge, "score") else 0.0,
            "user_id": user_id,
            "source_node": edge.source_node_uuid,
            "target_node": edge.target_node_uuid,
            "type": "edge"
        }
        
        # 添加边类型
        if hasattr(edge, "type") and edge.type:
            result["relation_type"] = edge.type
        
        # 添加时间信息
        add_time_info(result, edge)
        
        results.append(result)
    
    # 处理节点结果
    for node in search_nodes:
        if not hasattr(node, "name") or not node.name:
            continue
        
        # 构建节点内容
        node_content = f"{node.name}"
        if hasattr(node, "summary") and node.summary:
            node_content += f": {node.summary}"
        
        # 关键词过滤
        if filter_terms and all(term.lower() not in node_content.lower() for term in filter_terms):
            continue
        
        result = {
            "id": node.uuid,
            "content": node_content,
            "name": node.name,
            "score": node.score if hasattr(node, "score") else 0.0,
            "user_id": user_id,
            "type": "node"
        }
        
        # 添加节点标签
        if hasattr(node, "labels") and node.labels:
            result["entity_type"] = node.labels
        
        # 添加节点属性
        if hasattr(node, "attributes") and node.attributes:
            result["attributes"] = node.attributes
            
            # 添加描述到内容
            if "description" in node.attributes:
                result["content"] += f"\n描述: {node.attributes['description']}"
        
        results.append(result)
    
    return results 