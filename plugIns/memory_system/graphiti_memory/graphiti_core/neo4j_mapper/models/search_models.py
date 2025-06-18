"""
搜索模型类定义
包含搜索方法、重排序策略和配置选项的数据模型
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field
from typing import List, Optional

from plugIns.memory_system.graphiti_memory.graphiti_core.config import DEFAULT_SEARCH_LIMIT
from ..edges import EntityEdge
from ..nodes import EntityNode, EpisodicNode, CommunityNode

# 默认搜索配置常量
DEFAULT_MIN_SCORE = 0.6
DEFAULT_MMR_LAMBDA = 0.5
MAX_SEARCH_DEPTH = 3


class EdgeSearchMethod(Enum):
    """边搜索方法枚举"""
    cosine_similarity = 'cosine_similarity'  # 余弦相似度搜索
    bm25 = 'bm25'  # 全文搜索
    bfs = 'breadth_first_search'  # 广度优先搜索


class NodeSearchMethod(Enum):
    """节点搜索方法枚举"""
    cosine_similarity = 'cosine_similarity'  # 余弦相似度搜索
    bm25 = 'bm25'  # 全文搜索
    bfs = 'breadth_first_search'  # 广度优先搜索


class EpisodeSearchMethod(Enum):
    """情节搜索方法枚举"""
    bm25 = 'bm25'  # 全文搜索


class CommunitySearchMethod(Enum):
    """社区搜索方法枚举"""
    cosine_similarity = 'cosine_similarity'  # 余弦相似度搜索
    bm25 = 'bm25'  # 全文搜索


class EdgeReranker(Enum):
    """边重排序策略枚举"""
    rrf = 'reciprocal_rank_fusion'  # 倒数排名融合
    node_distance = 'node_distance'  # 节点距离
    episode_mentions = 'episode_mentions'  # 情节提及
    mmr = 'mmr'  # 最大边际相关性
    cross_encoder = 'cross_encoder'  # 交叉编码器


class NodeReranker(Enum):
    """节点重排序策略枚举"""
    rrf = 'reciprocal_rank_fusion'  # 倒数排名融合
    node_distance = 'node_distance'  # 节点距离
    episode_mentions = 'episode_mentions'  # 情节提及
    mmr = 'mmr'  # 最大边际相关性
    cross_encoder = 'cross_encoder'  # 交叉编码器


class EpisodeReranker(Enum):
    """情节重排序策略枚举"""
    rrf = 'reciprocal_rank_fusion'  # 倒数排名融合
    cross_encoder = 'cross_encoder'  # 交叉编码器


class CommunityReranker(Enum):
    """社区重排序策略枚举"""
    rrf = 'reciprocal_rank_fusion'  # 倒数排名融合
    mmr = 'mmr'  # 最大边际相关性
    cross_encoder = 'cross_encoder'  # 交叉编码器


class ComparisonOperator(Enum):
    """比较运算符枚举"""
    equals = '='  # 等于
    not_equals = '<>'  # 不等于
    greater_than = '>'  # 大于
    less_than = '<'  # 小于
    greater_than_equal = '>='  # 大于等于
    less_than_equal = '<='  # 小于等于


class DateFilter(BaseModel):
    """日期过滤器"""
    date: datetime = Field(description='要过滤的日期时间')
    comparison_operator: ComparisonOperator = Field(
        description='日期过滤的比较运算符'
    )


class SearchFilters(BaseModel):
    """搜索过滤器配置"""
    node_labels: Optional[List[str]] = Field(
        default=None, description='要过滤的节点标签列表'
    )
    valid_at: Optional[List[List[DateFilter]]] = Field(default=None)
    invalid_at: Optional[List[List[DateFilter]]] = Field(default=None)
    created_at: Optional[List[List[DateFilter]]] = Field(default=None)
    expired_at: Optional[List[List[DateFilter]]] = Field(default=None)


class EdgeSearchConfig(BaseModel):
    """边搜索配置"""
    search_methods: list[EdgeSearchMethod]  # 搜索方法列表
    reranker: EdgeReranker = Field(default=EdgeReranker.rrf)  # 重排序策略
    sim_min_score: float = Field(default=DEFAULT_MIN_SCORE)  # 最小相似度分数
    mmr_lambda: float = Field(default=DEFAULT_MMR_LAMBDA)  # MMR lambda参数
    bfs_max_depth: int = Field(default=MAX_SEARCH_DEPTH)  # BFS最大深度


class NodeSearchConfig(BaseModel):
    """节点搜索配置"""
    search_methods: list[NodeSearchMethod]  # 搜索方法列表
    reranker: NodeReranker = Field(default=NodeReranker.rrf)  # 重排序策略
    sim_min_score: float = Field(default=DEFAULT_MIN_SCORE)  # 最小相似度分数
    mmr_lambda: float = Field(default=DEFAULT_MMR_LAMBDA)  # MMR lambda参数
    bfs_max_depth: int = Field(default=MAX_SEARCH_DEPTH)  # BFS最大深度


class EpisodeSearchConfig(BaseModel):
    """情节搜索配置"""
    search_methods: list[EpisodeSearchMethod]  # 搜索方法列表
    reranker: EpisodeReranker = Field(default=EpisodeReranker.rrf)  # 重排序策略
    sim_min_score: float = Field(default=DEFAULT_MIN_SCORE)  # 最小相似度分数
    mmr_lambda: float = Field(default=DEFAULT_MMR_LAMBDA)  # MMR lambda参数
    bfs_max_depth: int = Field(default=MAX_SEARCH_DEPTH)  # BFS最大深度


class CommunitySearchConfig(BaseModel):
    """社区搜索配置"""
    search_methods: list[CommunitySearchMethod]  # 搜索方法列表
    reranker: CommunityReranker = Field(default=CommunityReranker.rrf)  # 重排序策略
    sim_min_score: float = Field(default=DEFAULT_MIN_SCORE)  # 最小相似度分数
    mmr_lambda: float = Field(default=DEFAULT_MMR_LAMBDA)  # MMR lambda参数
    bfs_max_depth: int = Field(default=MAX_SEARCH_DEPTH)  # BFS最大深度


class SearchConfig(BaseModel):
    """搜索配置"""
    edge_config: EdgeSearchConfig | None = Field(default=None)  # 边搜索配置
    node_config: NodeSearchConfig | None = Field(default=None)  # 节点搜索配置
    episode_config: EpisodeSearchConfig | None = Field(default=None)  # 情节搜索配置
    community_config: CommunitySearchConfig | None = Field(default=None)  # 社区搜索配置
    limit: int = Field(default=DEFAULT_SEARCH_LIMIT)  # 默认结果限制
    reranker_min_score: float = Field(default=0)  # 重排序最小分数
    
    # 添加边搜索结果重排序配置
    edge_reordering: dict | None = Field(default=None)  # 边重排序配置
    
    # 添加不同类型搜索的结果数量限制
    edge_limit: int = Field(default=DEFAULT_SEARCH_LIMIT)  # 边结果限制
    node_limit: int = Field(default=DEFAULT_SEARCH_LIMIT)  # 节点结果限制
    episode_limit: int = Field(default=DEFAULT_SEARCH_LIMIT)  # 情节结果限制
    community_limit: int = Field(default=DEFAULT_SEARCH_LIMIT)  # 社区结果限制


class SearchResults(BaseModel):
    """搜索结果"""
    edges: list[EntityEdge] = Field(default_factory=list)  # 边结果列表
    nodes: list[EntityNode] = Field(default_factory=list)  # 节点结果列表
    episodes: list[EpisodicNode] = Field(default_factory=list)  # 情节结果列表
    communities: list[CommunityNode] = Field(default_factory=list)  # 社区结果列表 