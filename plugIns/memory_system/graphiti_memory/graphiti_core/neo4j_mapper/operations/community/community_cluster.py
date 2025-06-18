"""
社区集群相关操作
"""

from collections import defaultdict

from neo4j import AsyncDriver
from pydantic import BaseModel

from knowledge_api.utils.log_config import get_logger
from plugIns.memory_system.graphiti_memory.graphiti_core.config import DEFAULT_DATABASE
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.nodes import EntityNode
from plugIns.memory_system.graphiti_memory.graphiti_core.neo4j_mapper.operations.template.community_templates import GET_GROUP_IDS, GET_ENTITY_RELATIONSHIPS_TEMPLATE
from plugIns.memory_system.graphiti_memory.graphiti_core.utils.utils import semaphore_gather

logger = get_logger()


class Neighbor(BaseModel):
    """代表一个邻居节点及其连接强度"""
    node_uuid: str
    edge_count: int


async def get_community_clusters(
    driver: AsyncDriver, group_ids: list[str] | None
) -> list[list[EntityNode]]:
    """获取社区集群
    
    参数:
        driver: Neo4j异步驱动
        group_ids: 组ID列表，如果为None则获取所有组
        
    返回:
        社区集群列表，每个集群包含多个实体节点
    """
    logger.debug(f"开始获取社区集群，组ID: {group_ids}")
    community_clusters: list[list[EntityNode]] = []

    # 如果未指定组ID，从数据库获取所有组ID
    if group_ids is None:
        logger.debug("未指定组ID，将查询所有组ID")
        group_id_values, _, _ = await driver.execute_query(
            GET_GROUP_IDS,
            database_=DEFAULT_DATABASE,
        )
        
        group_ids = group_id_values[0]['group_ids']
        logger.debug(f"查询到的组ID: {group_ids}")

    # 遍历每个组ID，构建社区集群
    for group_id in group_ids:
        logger.debug(f"处理组ID: {group_id}")
        # 创建投影图，记录每个节点及其邻居
        projection: dict[str, list[Neighbor]] = {}
        nodes = await EntityNode.get_by_group_ids(driver, [group_id])
        logger.debug(f"组ID {group_id} 中找到 {len(nodes)} 个节点")
        
        # 为每个节点查询其关系
        for node in nodes:
            logger.debug(f"为节点 {node.uuid} 查询关系")
            # 使用Jinja2模板渲染查询语句
            query = GET_ENTITY_RELATIONSHIPS_TEMPLATE.render(
                group_id=group_id,
                uuid=node.uuid
            )
            records, _, _ = await driver.execute_query(
                query,
                database_=DEFAULT_DATABASE,
            )

            # 构建邻居列表
            projection[node.uuid] = [
                Neighbor(node_uuid=record['uuid'], edge_count=record['count']) for record in records
            ]
            logger.debug(f"节点 {node.uuid} 找到 {len(projection[node.uuid])} 个邻居节点")

        # 使用标签传播算法生成集群
        cluster_uuids = label_propagation(projection)
        logger.debug(f"组ID {group_id} 通过标签传播算法生成了 {len(cluster_uuids)} 个集群")

        # 通过UUID获取实体节点对象
        clusters = await semaphore_gather(
            *[EntityNode.get_by_uuids(driver, cluster) for cluster in cluster_uuids]
        )
        logger.debug(f"成功获取集群的实体信息，加入社区集群列表中")
        community_clusters.extend(list(clusters))

    logger.debug(f"共获取到 {len(community_clusters)} 个社区集群")
    return community_clusters


def label_propagation(projection: dict[str, list[Neighbor]]) -> list[list[str]]:
    """标签传播算法实现社区检测
    
    参数:
        projection: 节点及其邻居的投影图
        
    返回:
        集群列表，每个集群包含多个节点UUID
        
    算法流程:
        1. 初始时，每个节点分配一个唯一的社区ID
        2. 迭代过程中，每个节点采用其邻居中出现最多的社区ID
        3. 如遇平局，选择最大的社区ID
        4. 当没有节点改变社区ID时，算法收敛
    """
    logger.debug("开始执行标签传播算法")
    # 初始化每个节点都是自己的社区
    community_map = {uuid: i for i, uuid in enumerate(projection.keys())}
    logger.debug(f"初始化 {len(community_map)} 个节点的社区标识")

    # 迭代直到收敛
    iteration = 0
    while True:
        iteration += 1
        logger.debug(f"标签传播迭代 #{iteration}")
        no_change = True  # 收敛标志
        new_community_map: dict[str, int] = {}

        # 对每个节点执行社区传播
        for uuid, neighbors in projection.items():
            curr_community = community_map[uuid]

            # 统计邻居节点所属社区及其权重
            community_candidates: dict[int, int] = defaultdict(int)
            for neighbor in neighbors:
                community_candidates[community_map[neighbor.node_uuid]] += neighbor.edge_count

            # 转换为列表并按权重排序
            community_lst = [
                (count, community) for community, count in community_candidates.items()
            ]
            community_lst.sort(reverse=True)
            
            # 选择权重最大的社区，如果没有合适的社区则保持原样
            candidate_rank, community_candidate = community_lst[0] if community_lst else (0, -1)
            if community_candidate != -1 and candidate_rank > 1:
                new_community = community_candidate
            else:
                new_community = max(community_candidate, curr_community)

            new_community_map[uuid] = new_community

            # 检查节点社区是否发生变化
            if new_community != curr_community:
                no_change = False

        # 如果没有节点发生变化，算法收敛
        if no_change:
            logger.debug(f"标签传播算法在迭代 {iteration} 后收敛")
            break

        community_map = new_community_map

    # 将相同社区ID的节点归为一组
    community_cluster_map = defaultdict(list)
    for uuid, community in community_map.items():
        community_cluster_map[community].append(uuid)

    # 提取每个社区包含的节点列表
    clusters = [cluster for cluster in community_cluster_map.values()]
    logger.debug(f"标签传播算法生成了 {len(clusters)} 个社区集群")
    return clusters 