from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.models import SearchConfig
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.models.search_models import EdgeSearchConfig, \
    EdgeSearchMethod, EdgeReranker, NodeSearchConfig, NodeSearchMethod, NodeReranker, EpisodeSearchConfig, \
    EpisodeSearchMethod, EpisodeReranker, CommunitySearchConfig, CommunitySearchMethod, CommunityReranker

COMBINED_HYBRID_SEARCH_RRF = SearchConfig(
    edge_config=EdgeSearchConfig(
        search_methods=[EdgeSearchMethod.bm25, EdgeSearchMethod.cosine_similarity],
        reranker=EdgeReranker.rrf,
    ),
    node_config=NodeSearchConfig(
        search_methods=[NodeSearchMethod.bm25, NodeSearchMethod.cosine_similarity],
        reranker=NodeReranker.rrf,
    ),
    episode_config=EpisodeSearchConfig(
        search_methods=[
            EpisodeSearchMethod.bm25,
        ],
        reranker=EpisodeReranker.rrf,
    ),
    community_config=CommunitySearchConfig(
        search_methods=[CommunitySearchMethod.bm25, CommunitySearchMethod.cosine_similarity],
        reranker=CommunityReranker.rrf,
    ),
    edge_reordering={"method": "rrf"},
    edge_limit=10,
    node_limit=10,
    episode_limit=10,
    community_limit=10,
)

# Performs a hybrid search with rrf reranking over edges, nodes, and communities

# Performs a hybrid search with mmr reranking over edges, nodes, and communities
COMBINED_HYBRID_SEARCH_MMR = SearchConfig(
    edge_config=EdgeSearchConfig(
        search_methods=[EdgeSearchMethod.bm25, EdgeSearchMethod.cosine_similarity],
        reranker=EdgeReranker.mmr,
        mmr_lambda=1,
    ),
    node_config=NodeSearchConfig(
        search_methods=[NodeSearchMethod.bm25, NodeSearchMethod.cosine_similarity],
        reranker=NodeReranker.mmr,
        mmr_lambda=1,
    ),
    episode_config=EpisodeSearchConfig(
        search_methods=[
            EpisodeSearchMethod.bm25,
        ],
        reranker=EpisodeReranker.rrf,
    ),
    community_config=CommunitySearchConfig(
        search_methods=[CommunitySearchMethod.bm25, CommunitySearchMethod.cosine_similarity],
        reranker=CommunityReranker.mmr,
        mmr_lambda=1,
    ),
    edge_reordering={"method": "mmr", "mmr_lambda": 1},
    edge_limit=10,
    node_limit=10,
    episode_limit=10,
    community_limit=10,
)

# Performs a full-text search, similarity search, and bfs with cross_encoder reranking over edges, nodes, and communities
COMBINED_HYBRID_SEARCH_CROSS_ENCODER = SearchConfig(
    edge_config=EdgeSearchConfig(
        search_methods=[
            EdgeSearchMethod.bm25,
            EdgeSearchMethod.cosine_similarity,
            EdgeSearchMethod.bfs,
        ],
        reranker=EdgeReranker.cross_encoder,
    ),
    node_config=NodeSearchConfig(
        search_methods=[
            NodeSearchMethod.bm25,
            NodeSearchMethod.cosine_similarity,
            NodeSearchMethod.bfs,
        ],
        reranker=NodeReranker.cross_encoder,
    ),
    episode_config=EpisodeSearchConfig(
        search_methods=[
            EpisodeSearchMethod.bm25,
        ],
        reranker=EpisodeReranker.cross_encoder,
    ),
    community_config=CommunitySearchConfig(
        search_methods=[CommunitySearchMethod.bm25, CommunitySearchMethod.cosine_similarity],
        reranker=CommunityReranker.cross_encoder,
    ),
    edge_reordering={"method": "cross_encoder"},
    edge_limit=10,
    node_limit=10,
    episode_limit=10,
    community_limit=10,
)

# performs a hybrid search over edges with rrf reranking
EDGE_HYBRID_SEARCH_RRF = SearchConfig(
    edge_config=EdgeSearchConfig(
        search_methods=[EdgeSearchMethod.bm25, EdgeSearchMethod.cosine_similarity],
        reranker=EdgeReranker.rrf,
    ),
    edge_reordering={"method": "rrf"},
    edge_limit=10,
)

# performs a hybrid search over edges with mmr reranking
EDGE_HYBRID_SEARCH_MMR = SearchConfig(
    edge_config=EdgeSearchConfig(
        search_methods=[EdgeSearchMethod.bm25, EdgeSearchMethod.cosine_similarity],
        reranker=EdgeReranker.mmr,
    ),
    edge_reordering={"method": "mmr"},
    edge_limit=10,
)

# performs a hybrid search over edges with node distance reranking
EDGE_HYBRID_SEARCH_NODE_DISTANCE = SearchConfig(
    edge_config=EdgeSearchConfig(
        search_methods=[EdgeSearchMethod.bm25, EdgeSearchMethod.cosine_similarity],
        reranker=EdgeReranker.node_distance,
    ),
    edge_reordering={"method": "distance"},
    edge_limit=10,
)

# performs a hybrid search over edges with episode mention reranking
EDGE_HYBRID_SEARCH_EPISODE_MENTIONS = SearchConfig(
    edge_config=EdgeSearchConfig(
        search_methods=[EdgeSearchMethod.bm25, EdgeSearchMethod.cosine_similarity],
        reranker=EdgeReranker.episode_mentions,
    ),
    edge_reordering={"method": "episode_mentions"},
    edge_limit=10,
)

# performs a hybrid search over edges with cross encoder reranking
EDGE_HYBRID_SEARCH_CROSS_ENCODER = SearchConfig(
    edge_config=EdgeSearchConfig(
        search_methods=[
            EdgeSearchMethod.bm25,
            EdgeSearchMethod.cosine_similarity,
            EdgeSearchMethod.bfs,
        ],
        reranker=EdgeReranker.cross_encoder,
    ),
    node_config=NodeSearchConfig(
        search_methods=[
            NodeSearchMethod.bm25,
            NodeSearchMethod.cosine_similarity,
            NodeSearchMethod.bfs,
        ],
        reranker=NodeReranker.cross_encoder,
    ),
    edge_reordering={"method": "cross_encoder"},
    edge_limit=10,
    limit=10,
)

# performs a hybrid search over nodes with rrf reranking
NODE_HYBRID_SEARCH_RRF = SearchConfig(
    node_config=NodeSearchConfig(
        search_methods=[NodeSearchMethod.bm25, NodeSearchMethod.cosine_similarity],
        reranker=NodeReranker.rrf,
    ),
    node_limit=10,
    edge_limit=0
)

# performs a hybrid search over nodes with mmr reranking
NODE_HYBRID_SEARCH_MMR = SearchConfig(
    node_config=NodeSearchConfig(
        search_methods=[NodeSearchMethod.bm25, NodeSearchMethod.cosine_similarity],
        reranker=NodeReranker.mmr,
    ),
    node_limit=10,
    edge_limit=0
)

# performs a hybrid search over nodes with node distance reranking
NODE_HYBRID_SEARCH_NODE_DISTANCE = SearchConfig(
    node_config=NodeSearchConfig(
        search_methods=[NodeSearchMethod.bm25, NodeSearchMethod.cosine_similarity],
        reranker=NodeReranker.node_distance,
    ),
    node_limit=10,
    edge_limit=0
)

# performs a hybrid search over nodes with episode mentions reranking
NODE_HYBRID_SEARCH_EPISODE_MENTIONS = SearchConfig(
    node_config=NodeSearchConfig(
        search_methods=[NodeSearchMethod.bm25, NodeSearchMethod.cosine_similarity],
        reranker=NodeReranker.episode_mentions,
    ),
    node_limit=10,
    edge_limit=0
)

# performs a hybrid search over nodes with cross encoder reranking
NODE_HYBRID_SEARCH_CROSS_ENCODER = SearchConfig(
    node_config=NodeSearchConfig(
        search_methods=[
            NodeSearchMethod.bm25,
            NodeSearchMethod.cosine_similarity,
            NodeSearchMethod.bfs,
        ],
        reranker=NodeReranker.cross_encoder,
    ),
    node_limit=10,
    edge_limit=0,
    limit=10,
)

# performs a hybrid search over communities with rrf reranking
COMMUNITY_HYBRID_SEARCH_RRF = SearchConfig(
    community_config=CommunitySearchConfig(
        search_methods=[
            CommunitySearchMethod.bm25,
            CommunitySearchMethod.cosine_similarity,
        ],
        reranker=CommunityReranker.rrf,
    ),
    community_limit=10,
    edge_limit=0,
    node_limit=0
)

# performs a hybrid search over communities with mmr reranking
COMMUNITY_HYBRID_SEARCH_MMR = SearchConfig(
    community_config=CommunitySearchConfig(
        search_methods=[
            CommunitySearchMethod.bm25,
            CommunitySearchMethod.cosine_similarity,
        ],
        reranker=CommunityReranker.mmr,
    ),
    community_limit=10,
    edge_limit=0,
    node_limit=0
)

# performs a hybrid search over communities with cross encoder reranking
COMMUNITY_HYBRID_SEARCH_CROSS_ENCODER = SearchConfig(
    community_config=CommunitySearchConfig(
        search_methods=[
            CommunitySearchMethod.bm25,
            CommunitySearchMethod.cosine_similarity,
        ],
        reranker=CommunityReranker.cross_encoder,
    ),
    community_limit=10,
    edge_limit=0,
    node_limit=0
)
