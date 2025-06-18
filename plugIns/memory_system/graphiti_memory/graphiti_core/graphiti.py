from datetime import datetime
from time import time

from neo4j import AsyncGraphDatabase
from pydantic import BaseModel
from typing_extensions import LiteralString

from knowledge_manage.embeddings.base import EmbeddingEngine
from knowledge_manage.embeddings.factory import EmbeddingFactory
from knowledge_manage.rerank_model import BaseRankingModel, TextRankingModel
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.models.graphiti_types import GraphitiClients
from plugIns.memory_system.graphiti_memory.graphiti_core.llm_client.custom_llm_client import CustomLLMClient
from plugIns.memory_system.graphiti_memory.graphiti_core.config import DEFAULT_SEARCH_LIMIT, DEFAULT_DATABASE
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.edges import EntityEdge, EpisodicEdge
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.models.search_models import SearchFilters, \
    SearchResults, SearchConfig
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes import CommunityNode
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes.entity_node import EntityNode
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes.episode_type import EpisodeType
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes.episodic_node import EpisodicNode
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations import build_indices_and_constraints, \
    retrieve_episodes, extract_nodes, resolve_extracted_nodes, extract_edges, extract_attributes_from_nodes
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.bulk.db_bulk import \
    add_nodes_and_edges_bulk, extract_nodes_and_edges_bulk
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.bulk.edge_bulk import \
    resolve_edge_pointers, extract_edge_dates_bulk, dedupe_edges_bulk
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.bulk.helpers import RawEpisode
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.bulk.node_bulk import \
    retrieve_previous_episodes_bulk, dedupe_nodes_bulk
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.community import update_community, \
    remove_communities, build_communities
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.edge import resolve_extracted_edges, \
    build_episodic_edges, resolve_extracted_edge
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.entity_types_utils import \
    validate_entity_types
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.graph.graph_data import \
    EPISODE_WINDOW_LEN
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.search.ops import search
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.search.recipes import EDGE_HYBRID_SEARCH_RRF, \
    EDGE_HYBRID_SEARCH_NODE_DISTANCE, COMBINED_HYBRID_SEARCH_CROSS_ENCODER
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.search.utils import get_mentioned_nodes, \
    get_relevant_edges, get_edge_invalidation_candidates
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.search.utils.community_search import \
    RELEVANT_SCHEMA_LIMIT

from plugIns.memory_system.graphiti_memory.graphiti_core.utils.datetime_utils import utc_now

from plugIns.memory_system.graphiti_memory.graphiti_core.llm_client import LLMClient
from knowledge_api.utils.log_config import get_logger
from plugIns.memory_system.graphiti_memory.graphiti_core.utils.utils import semaphore_gather

logger = get_logger()


class AddEpisodeResults(BaseModel):
    episode: EpisodicNode
    nodes: list[EntityNode]
    edges: list[EntityEdge]


class Graphiti:
    def __init__(
            self,
            uri: str,
            user: str,
            password: str,
            llm_client: LLMClient | None = None,
            embedder: EmbeddingEngine | None = None,
            cross_encoder: BaseRankingModel | None = None,
            store_raw_episode_content: bool = True,
            model_id: str = "doubao-pro-256k-241115",
    ):
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
        self.database = DEFAULT_DATABASE
        self.store_raw_episode_content = store_raw_episode_content

        # 初始化LLM客户端
        if llm_client:
            self.llm_client = llm_client
        else:
            # 使用自定义LLM客户端
            self.llm_client = CustomLLMClient(model_id=model_id)
            logger.info(f"已初始化自定义LLM客户端，使用模型: {model_id}")

        # 初始化嵌入模型
        if embedder:
            self.embedder = embedder
        else:
            # 使用自定义嵌入模型
            self.embedder = EmbeddingFactory().create_embedding()
            logger.info(f"已初始化自定义嵌入模型")

        # 初始化重排序模型
        if cross_encoder:
            self.cross_encoder = cross_encoder
        else:
            # 使用自定义重排序模型
            self.cross_encoder = TextRankingModel()
            logger.info(f"已初始化自定义重排序模型")

        # 创建客户端集合
        self.clients = GraphitiClients(
            driver=self.driver,
            llm_client=self.llm_client,
            embedder=self.embedder,
            cross_encoder=self.cross_encoder,
        )



    async def build_indices_and_constraints(self, delete_existing: bool = False):
        """
        在Neo4j数据库中构建索引和约束。
        参数
        ----------
        delete_existing : bool, 可选
            是否在创建新索引前删除现有索引。
        返回
        -------
        无
        """
        await build_indices_and_constraints(self.driver, delete_existing)

    async def retrieve_episodes(
            self,
            reference_time: datetime,
            last_n: int = EPISODE_WINDOW_LEN,
            group_ids: list[str] | None = None,
            source: EpisodeType | None = None,
    ) -> list[EpisodicNode]:
        """
        从图中检索最近的n个情节节点。

        参数
        ----------
        reference_time : datetime
            检索在此时间之前的情节。
        last_n : int, 可选
            要检索的情节数量。默认为EPISODE_WINDOW_LEN。
        group_ids : list[str | None], 可选
            要返回数据的组ID列表。
        source : EpisodeType | None, 可选
            情节来源类型。

        返回
        -------
        list[EpisodicNode]
            最近的EpisodicNode对象列表。
        """
        return await retrieve_episodes(self.driver, reference_time, last_n, group_ids, source)

    async def add_episode(
            self,
            name: str,
            episode_body: str,
            source_description: str,
            reference_time: datetime,
            source: EpisodeType = EpisodeType.message,
            group_id: str = '',
            uuid: str | None = None,
            update_communities: bool = False,
            entity_types: dict[str, BaseModel] | None = None,
            previous_episode_uuids: list[str] | None = None,
            edge_types: dict[str, BaseModel] | None = None,
            edge_type_map: dict[tuple[str, str], list[str]] | None = None,
            custom_prompt: str = '',
    ) -> AddEpisodeResults:
        """
        添加一个情节节点到知识图谱，并从中提取实体和关系。

        参数
        ----------
        name : str
            情节节点的名称，用于标识和检索。
        episode_body : str
            情节的原始内容，可以是纯文本、消息格式或JSON。
        source_description : str
            数据来源的描述，如"用户对话"、"系统消息"等。
        reference_time : datetime
            情节的参考时间点，通常是创建时间或有效时间。
        source : EpisodeType, 可选
            情节的类型/来源，默认为EpisodeType.message。
            可能的值：message(消息格式)、text(纯文本)、json(JSON格式)
        group_id : str, 可选
            图分区ID，用于多租户隔离，默认为空字符串。
        uuid : str | None, 可选
            【重要】若提供，将尝试更新已存在的EpisodicNode(情节节点)。
            必须是一个有效的情节节点UUID，而非实体节点UUID。
            若UUID对应的情节节点不存在，会抛出NodeNotFoundError异常。
            若为None(默认)，则创建新的情节节点。
        update_communities : bool, 可选
            是否更新社区，默认为False。启用后会增强图的结构。
        entity_types : dict[str, BaseModel] | None, 可选
            自定义实体类型的定义，键为类型名称，值为对应的Pydantic模型。
        previous_episode_uuids : list[str] | None, 可选
            前序情节的UUID列表，用于建立时间序列关系。
            若为None，会自动检索近期的情节。
        edge_types : dict[str, BaseModel] | None, 可选
            自定义边类型的定义，键为类型名称，值为对应的Pydantic模型。
        edge_type_map : dict[tuple[str, str], list[str]] | None, 可选
            定义不同节点类型间可能的边类型，键为(源类型,目标类型)元组，
            值为可能的边类型列表。
        custom_prompt : str, 可选
            用于节点提取的自定义提示，默认为空。

        返回
        -------
        AddEpisodeResults
            包含添加的情节节点、实体节点和关系边的结果对象。
            
        异常
        -----
        NodeNotFoundError
            如果提供了uuid但找不到对应的情节节点。
        """
        try:
            start = time()
            now = utc_now()
            validate_entity_types(entity_types)
            previous_episodes = (
                await self.retrieve_episodes(
                    reference_time,
                    last_n=RELEVANT_SCHEMA_LIMIT,
                    group_ids=[group_id],
                    source=source,
                )
                if previous_episode_uuids is None
                else await EpisodicNode.get_by_uuids(self.driver, previous_episode_uuids)
            )
            episode = (
                await EpisodicNode.get_by_uuid(self.driver, uuid)
                if uuid is not None
                else EpisodicNode(
                    name=name,
                    group_id=group_id,
                    labels=[],
                    source=source,
                    content=episode_body,
                    source_description=source_description,
                    created_at=now,
                    valid_at=reference_time,
                )
            )

            # 创建默认边缘类型映射
            edge_type_map_default = (
                {('Entity', 'Entity'): list(edge_types.keys())}
                if edge_types is not None
                else {('Entity', 'Entity'): []}
            )
            # ====**** 将实体提取为节点 ***====
            extracted_nodes = await extract_nodes(
                self.clients, episode, previous_episodes, entity_types, custom_prompt
            )
            extract_nodes_end = time()
            logger.info(f'Time to extract and dedupe nodes: {extract_nodes_end - start} seconds')
            # 提取边并解析节点
            (nodes, uuid_map), extracted_edges = await semaphore_gather(
                resolve_extracted_nodes(
                    self.clients,
                    extracted_nodes,
                    episode,
                    previous_episodes,
                    entity_types,
                ),
                extract_edges(
                    self.clients, episode, extracted_nodes, previous_episodes, group_id, edge_types
                ),
            )

            edges = resolve_edge_pointers(extracted_edges, uuid_map)

            (resolved_edges, invalidated_edges), hydrated_nodes = await semaphore_gather(
                # 解析提取的边缘（逻辑没有完全理解）
                resolve_extracted_edges(
                    self.clients,
                    edges,
                    episode,
                    nodes,
                    edge_types or {},
                    edge_type_map or edge_type_map_default,
                ),
                extract_attributes_from_nodes(
                    self.clients, nodes, episode, previous_episodes, entity_types
                ),
            )
            entity_edges = resolved_edges + invalidated_edges
            episodic_edges = build_episodic_edges(nodes, episode, now)

            episode.entity_edges = [edge.uuid for edge in entity_edges]
            if not self.store_raw_episode_content:
                episode.content = ''
            await add_nodes_and_edges_bulk(
                self.driver, [episode], episodic_edges, hydrated_nodes, entity_edges, self.embedder
            )
            # 更新任何社区
            if update_communities:
                await semaphore_gather(
                    *[
                        update_community(self.driver, self.llm_client, self.embedder, node)
                        for node in nodes
                    ]
                )
            end = time()
            logger.info(f'Completed add_episode in {(end - start) * 1000} ms')

            return AddEpisodeResults(episode=episode, nodes=nodes, edges=entity_edges)
        except Exception as e:
            raise e

    #### WIP: USE AT YOUR OWN RISK ####
    async def add_episode_bulk(self, bulk_episodes: list[RawEpisode], group_id: str = ''):
        """
        批量处理多个情节并更新图。

        参数
        ----------
        bulk_episodes : list[RawEpisode]
            要处理并添加到图中的RawEpisode对象列表。
        group_id : str
            情节所属的图分区ID。

        返回
        -------
        无

        注意
        -----
        此方法不执行边缘失效或日期提取步骤。
        如果需要这些操作，请为每个情节使用add_episode方法。
        """
        try:
            start = time()
            now = utc_now()

            episodes = [
                EpisodicNode(
                    name=episode.name,
                    labels=[],
                    source=episode.source,
                    content=episode.content,
                    source_description=episode.source_description,
                    group_id=group_id,
                    created_at=now,
                    valid_at=episode.reference_time,
                )
                for episode in bulk_episodes
            ]

            # Save all the episodes
            await semaphore_gather(*[episode.save(self.driver) for episode in episodes])

            # Get previous episode context for each episode
            episode_pairs = await retrieve_previous_episodes_bulk(self.driver, episodes)

            # Extract all nodes and edges
            (
                extracted_nodes,
                extracted_edges,
                episodic_edges,
            ) = await extract_nodes_and_edges_bulk(self.clients, episode_pairs)

            # Generate embeddings
            await semaphore_gather(
                *[node.generate_name_embedding(self.embedder) for node in extracted_nodes],
                *[edge.generate_embedding(self.embedder) for edge in extracted_edges],
            )

            # Dedupe extracted nodes, compress extracted edges
            (nodes, uuid_map), extracted_edges_timestamped = await semaphore_gather(
                dedupe_nodes_bulk(self.driver, self.llm_client, extracted_nodes),
                extract_edge_dates_bulk(self.llm_client, extracted_edges, episode_pairs),
            )

            # save nodes to KG
            await semaphore_gather(*[node.save(self.driver) for node in nodes])

            # re-map edge pointers so that they don't point to discard dupe nodes
            extracted_edges_with_resolved_pointers: list[EntityEdge] = resolve_edge_pointers(
                extracted_edges_timestamped, uuid_map
            )
            episodic_edges_with_resolved_pointers: list[EpisodicEdge] = resolve_edge_pointers(
                episodic_edges, uuid_map
            )

            # save episodic edges to KG
            await semaphore_gather(
                *[edge.save(self.driver) for edge in episodic_edges_with_resolved_pointers]
            )

            # Dedupe extracted edges
            edges = await dedupe_edges_bulk(
                self.driver, self.llm_client, extracted_edges_with_resolved_pointers
            )
            logger.debug(f'extracted edge length: {len(edges)}')

            # invalidate edges

            # save edges to KG
            await semaphore_gather(*[edge.save(self.driver) for edge in edges])

            end = time()
            logger.info(f'Completed add_episode_bulk in {(end - start) * 1000} ms')

        except Exception as e:
            raise e

    async def build_communities(self, group_ids: list[str] | None = None) -> list[CommunityNode]:
        """
        使用社区聚类算法查找节点社区，并创建汇总这些社区内容的社区节点。
        参数
        ----------
        group_ids : list[str] | None
            可选。仅为列出的group_ids创建社区。如果为空则使用整个图。
        返回
        -------
        list[CommunityNode]
            创建的社区节点列表。
        """
        # Clear existing communities
        await remove_communities(self.driver)

        community_nodes, community_edges = await build_communities(
            self.driver, self.llm_client, group_ids
        )

        await semaphore_gather(
            *[node.generate_name_embedding(self.embedder) for node in community_nodes]
        )

        await semaphore_gather(*[node.save(self.driver) for node in community_nodes])
        await semaphore_gather(*[edge.save(self.driver) for edge in community_edges])

        return community_nodes

    async def search(
            self,
            query: str,
            center_node_uuid: str | None = None,
            group_ids: list[str] | None = None,
            num_results=DEFAULT_SEARCH_LIMIT,
            search_filter: SearchFilters | None = None,
    ) -> list[EntityEdge]:
        """
        在知识图谱上执行混合搜索。

        参数
        ----------
        query : str
            搜索查询字符串。
        center_node_uuid: str, 可选
            事实将基于与此节点的接近度重新排序。
        group_ids : list[str | None] | None, 可选
            返回数据的图分区。
        num_results : int, 可选
            返回的最大结果数。默认为10。
        search_filter : SearchFilters | None, 可选
            搜索过滤器。

        返回
        -------
        list[EntityEdge]
            与搜索查询相关的EntityEdge对象列表。
        """
        search_config = (
            EDGE_HYBRID_SEARCH_RRF if center_node_uuid is None else EDGE_HYBRID_SEARCH_NODE_DISTANCE
        )
        search_config.limit = num_results

        edges = (
            await search(
                self.clients,
                query,
                group_ids,
                search_config,
                search_filter if search_filter is not None else SearchFilters(),
                center_node_uuid,
            )
        ).edges

        return edges

    async def search_(
            self,
            query: str,
            config: SearchConfig = COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
            group_ids: list[str] | None = None,
            center_node_uuid: str | None = None,
            bfs_origin_node_uuids: list[str] | None = None,
            search_filter: SearchFilters | None = None,
    ) -> SearchResults:
        """
        高级搜索方法，返回Graph对象（节点和边），而非事实列表。
        允许使用更高级功能，如过滤器和图中不同层的不同搜索和重排序方法。

        参数
        ----------
        query : str
            搜索查询字符串。
        config : SearchConfig, 可选
            搜索配置。默认为COMBINED_HYBRID_SEARCH_CROSS_ENCODER。
        group_ids : list[str] | None, 可选
            返回数据的图分区。
        center_node_uuid : str | None, 可选
            中心节点UUID。
        bfs_origin_node_uuids : list[str] | None, 可选
            BFS起源节点UUID列表。
        search_filter : SearchFilters | None, 可选
            搜索过滤器。

        返回
        -------
        SearchResults
            搜索结果，包含边、节点、情节和社区。
        """

        return await search(
            self.clients,
            query,
            group_ids,
            config,
            search_filter if search_filter is not None else SearchFilters(),
            center_node_uuid,
            bfs_origin_node_uuids,
        )

    async def get_nodes_and_edges_by_episode(self, episode_uuids: list[str]) -> SearchResults:
        """
        通过情节UUID获取节点和边。

        参数
        ----------
        episode_uuids : list[str]
            情节UUID列表。
        返回
        -------
        SearchResults
            包含从给定情节中提取的节点和边的搜索结果。
        """
        episodes = await EpisodicNode.get_by_uuids(self.driver, episode_uuids)

        edges_list = await semaphore_gather(
            *[EntityEdge.get_by_uuids(self.driver, episode.entity_edges) for episode in episodes]
        )

        edges: list[EntityEdge] = [edge for lst in edges_list for edge in lst]

        nodes = await get_mentioned_nodes(self.driver, episodes)

        return SearchResults(edges=edges, nodes=nodes, episodes=[], communities=[])

    async def add_triplet(self, source_node: EntityNode, edge: EntityEdge, target_node: EntityNode):
        """
        添加三元组（源节点、边、目标节点）到图中。

        参数
        ----------
        source_node : EntityNode
            源节点。
        edge : EntityEdge
            边。
        target_node : EntityNode
            目标节点。

        返回
        -------
        无
        """
        if source_node.name_embedding is None:
            await source_node.generate_name_embedding(self.embedder)
        if target_node.name_embedding is None:
            await target_node.generate_name_embedding(self.embedder)
        if edge.fact_embedding is None:
            await edge.generate_embedding(self.embedder)

        resolved_nodes, uuid_map = await resolve_extracted_nodes(
            self.clients,
            [source_node, target_node],
        )

        updated_edge = resolve_edge_pointers([edge], uuid_map)[0]

        related_edges = (await get_relevant_edges(self.driver, [updated_edge], SearchFilters()))[0]
        existing_edges = (
            await get_edge_invalidation_candidates(self.driver, [updated_edge], SearchFilters())
        )[0]
        resolved_edge, invalidated_edges = await resolve_extracted_edge(
            self.llm_client,
            updated_edge,
            related_edges,
            existing_edges,
            EpisodicNode(
                name='',
                source=EpisodeType.text,
                source_description='',
                content='',
                valid_at=edge.valid_at or utc_now(),
                entity_edges=[],
                group_id=edge.group_id,
            ),
        )

        await add_nodes_and_edges_bulk(
            self.driver, [], [], resolved_nodes, [resolved_edge] + invalidated_edges, self.embedder
        )

    async def remove_episode(self, episode_uuid: str):
        """
        删除指定的情节及其相关节点和边。

        参数
        ----------
        episode_uuid : str
            要删除的情节UUID。
        """
        # Find the episode to be deleted
        episode = await EpisodicNode.get_by_uuid(self.driver, episode_uuid)

        # Find edges mentioned by the episode
        edges = await EntityEdge.get_by_uuids(self.driver, episode.entity_edges)

        # We should only delete edges created by the episode
        edges_to_delete: list[EntityEdge] = []
        for edge in edges:
            if edge.episodes and edge.episodes[0] == episode.uuid:
                edges_to_delete.append(edge)

        # Find nodes mentioned by the episode
        nodes = await get_mentioned_nodes(self.driver, [episode])
        # We should delete all nodes that are only mentioned in the deleted episode
        nodes_to_delete: list[EntityNode] = []
        for node in nodes:
            query: LiteralString = 'MATCH (e:Episodic)-[:MENTIONS]->(n:Entity {uuid: $uuid}) RETURN count(*) AS episode_count'
            records, _, _ = await self.driver.execute_query(
                query, uuid=node.uuid, database_=DEFAULT_DATABASE, routing_='r'
            )

            for record in records:
                if record['episode_count'] == 1:
                    nodes_to_delete.append(node)

        await semaphore_gather(*[node.delete(self.driver) for node in nodes_to_delete])
        await semaphore_gather(*[edge.delete(self.driver) for edge in edges_to_delete])
        await episode.delete(self.driver)

    async def close(self):
        await self.driver.close()