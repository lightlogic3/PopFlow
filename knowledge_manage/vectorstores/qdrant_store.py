# vectorstores/qdrant_store.py
import os
import logging
import shutil
import traceback
import uuid
import json
from typing import List, Dict, Any, Optional, Tuple

from knowledge_manage.vectorstores.base import VectorStore, _clean_metadata
from knowledge_api.utils.log_config import get_logger

logger = get_logger()
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as rest
    from qdrant_client.models import (
        Distance,
        VectorParams,
        PointIdsList,
        PointStruct,
        FilterSelector,
        Filter
    )
except ImportError:
    logger.info("qdrant_client不可用如需启用Qdrant向量存储，请安装qdrant_client库")



class QdrantStore(VectorStore):
    """
    基于Qdrant的向量存储实现，支持本地存储和远程服务器连接
    """

    def __init__(
        self,
        collection_name: str,
        dimension: int,
        metric: str = "cosine",
        fields_schema: Optional[List[Tuple[str, str]]] = None,
        client: Optional[Any] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        path: Optional[str] = None,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        prefix: Optional[str] = None,
        timeout: Optional[float] = None,
        on_disk: bool = True,
        create_if_not_exists: bool = True,
        **kwargs
    ):
        """
        初始化Qdrant向量存储

        Args:
            collection_name: 集合名称
            dimension: 向量维度
            metric: 距离度量方式("cosine", "euclidean", "dot")
            fields_schema: 字段模式列表
            client: 现有的QdrantClient实例
            host: Qdrant服务器主机地址
            port: Qdrant服务器端口
            path: 本地持久化目录路径
            url: Qdrant服务器完整URL
            api_key: Qdrant API密钥
            prefix: URL前缀
            timeout: 连接超时时间（秒）
            on_disk: 是否使用磁盘存储（而非内存）
            create_if_not_exists: 集合不存在时是否创建
            **kwargs: 额外参数
        """
        super().__init__(collection_name, dimension, metric, fields_schema, **kwargs)
        
        self.on_disk = on_disk
        self.create_if_not_exists = create_if_not_exists
        
        # 初始化客户端
        if client:
            logger.info("使用提供的Qdrant客户端")
            self.client = client
        else:
            params = {}
            
            # API密钥认证
            if api_key:
                params["api_key"] = api_key
                
            # 使用完整URL
            if url:
                params["url"] = url
            # 或者使用主机和端口
            elif host and port:
                params["host"] = host
                params["port"] = port
            # 否则使用本地路径
            else:
                # 默认路径
                local_path = path or "./qdrant_data"
                params["path"] = local_path
                
                # 是否需要清理现有数据
                if not on_disk and os.path.exists(local_path) and os.path.isdir(local_path):
                    logger.warning(f"清除内存模式下的旧数据目录: {local_path}")
                    shutil.rmtree(local_path)
            
            # 添加其他参数
            if prefix:
                params["prefix"] = prefix
            if timeout:
                params["timeout"] = timeout
            
            try:
                logger.info(f"创建Qdrant客户端, 参数: {params}")
                self.client = QdrantClient(**params)
            except Exception as e:
                logger.error(f"初始化Qdrant客户端时出错: {e}")
                traceback.print_exc()
                raise
        
        # 将度量方式映射到Qdrant的Distance枚举
        self.distance_map = {
            "cosine": Distance.COSINE,
            "euclid": Distance.EUCLID,
            "euclidean": Distance.EUCLID,
            "dot": Distance.DOT,
        }
        
        # 在初始化方法中不创建集合，而是在initialize方法中创建
        self.collection_initialized = False
        
    async def initialize(self):
        """初始化向量集合，必须在添加文档前调用"""
        try:
            # 获取所有集合列表
            collections = self.client.get_collections()
            exists = False
            
            # 检查集合是否已存在
            for collection in collections.collections:
                if collection.name == self.collection_name:
                    exists = True
                    break
            
            if exists:
                logger.info(f"集合 {self.collection_name} 已存在，跳过创建步骤")
            else:
                if not self.create_if_not_exists:
                    raise ValueError(f"集合 {self.collection_name} 不存在且未启用自动创建")
                
                # 确定距离度量方式
                distance = self.distance_map.get(self.metric.lower(), Distance.COSINE)
                logger.info(f"创建集合 {self.collection_name}，维度: {self.dimension}，度量: {distance}")
                
                # 创建集合
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.dimension,
                        distance=distance,
                        on_disk=self.on_disk
                    )
                )
                logger.info(f"成功创建集合 {self.collection_name}")
            
            # 尝试创建字段模式(如果提供)
            if self.fields_schema:
                await self.create_fields_schema(self.fields_schema)
            
            self.collection_initialized = True
            
        except Exception as e:
            logger.error(f"初始化Qdrant集合时出错: {e}")
            traceback.print_exc()
            raise

    async def _add_processed_documents(self, processed_docs: List[Dict[str, Any]]) -> int:
        """
        将预处理后的文档添加到Qdrant集合中

        Args:
            processed_docs: 预处理后的文档列表

        Returns:
            成功添加的文档数量
        """
        if not self.collection_initialized:
            logger.info("集合未初始化，自动初始化")
            await self.initialize()
        
        try:
            points = []
            
            for doc in processed_docs:
                # 获取文档ID
                doc_id = doc.get("id")
                if not doc_id:
                    doc_id = str(uuid.uuid4())
                    logger.warning(f"文档缺少ID，自动生成ID: {doc_id}")
                
                # 获取向量
                vector = doc.get("vector")
                if vector is None:
                    logger.warning(f"跳过没有向量的文档: {doc_id}")
                    continue
                
                # 处理元数据，确保类型兼容性
                metadata = doc.get("metadata", {})
                if metadata:
                    metadata = _clean_metadata(metadata)
                
                # 添加文本内容到元数据
                text = doc.get("text", "")
                if text:
                    metadata["text"] = text
                
                # 创建点结构
                point = PointStruct(
                    id=doc_id,
                    vector=vector,
                    payload=metadata
                )
                points.append(point)
            
            if not points:
                logger.warning("没有有效文档可添加")
                return 0
            
            # 添加点到集合
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"成功添加 {len(points)} 个文档到Qdrant集合 {self.collection_name}")
            return len(points)
            
        except Exception as e:
            logger.error(f"添加文档到Qdrant时出错: {e}")
            traceback.print_exc()
            return 0
    
    def _parse_filter(self, filter_str: str) -> Optional[Filter]:
        """解析过滤条件字符串为Qdrant Filter对象"""
        if not filter_str:
            return None
            
        try:
            filter_dict = json.loads(filter_str)
            
            # 构建过滤条件
            conditions = []
            
            for key, value in filter_dict.items():
                if isinstance(value, list):
                    # 处理列表（任一匹配）
                    match_any = []
                    for val in value:
                        match_any.append(rest.FieldCondition(
                            key=key,
                            match=rest.MatchValue(value=val)
                        ))
                    conditions.append(rest.Filter(should=match_any, minimum_should_match=1))
                elif isinstance(value, dict) and ("gte" in value or "lte" in value):
                    # 处理范围条件
                    range_args = {}
                    if "gte" in value:
                        range_args["gte"] = value["gte"]
                    if "lte" in value:
                        range_args["lte"] = value["lte"]
                    conditions.append(rest.FieldCondition(
                        key=key,
                        range=rest.Range(**range_args)
                    ))
                else:
                    # 处理精确匹配
                    conditions.append(rest.FieldCondition(
                        key=key,
                        match=rest.MatchValue(value=value)
                    ))
            
            # 组合所有条件（全部满足）
            if conditions:
                return rest.Filter(must=conditions)
            
        except Exception as e:
            logger.warning(f"解析过滤条件时出错: {e}，忽略过滤条件")
            traceback.print_exc()
        
        return None

    async def search(self, query_embedding: List[float] = None, top_k: int = 5, filter_str: str = None) -> List[Dict[str, Any]]:
        """
        使用嵌入向量搜索相似文档

        Args:
            query_embedding: 查询的嵌入向量
            top_k: 返回的最相似文档数量
            filter_str: 过滤条件(JSON字符串)

        Returns:
            相似文档列表
        """
        if not self.collection_initialized:
            logger.info("集合未初始化，自动初始化")
            await self.initialize()
            
        if query_embedding is None:
            logger.error("搜索需要提供查询向量嵌入")
            return []
        
        try:
            # 解析过滤条件
            query_filter = self._parse_filter(filter_str)
            
            # 执行搜索
            logger.info(f"在集合 {self.collection_name} 中搜索Top-{top_k}文档")
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=query_filter,
                limit=top_k,
                with_payload=True
            )
            
            # 处理结果
            results = []
            for point in search_result:
                # 从载荷中提取文本
                payload = point.payload or {}
                text = payload.pop("text", "") if isinstance(payload, dict) else ""
                
                result = {
                    "id": point.id,
                    "text": text,
                    "metadata": payload,
                    "score": point.score
                }
                results.append(result)
            
            logger.info(f"搜索返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"Qdrant搜索时出错: {e}")
            traceback.print_exc()
            return []

    async def close(self):
        """关闭资源连接"""
        logger.info("关闭Qdrant连接")
        try:
            if hasattr(self, 'client'):
                # 没有显式的关闭方法，但如果将来添加，可在此处调用
                pass
        except Exception as e:
            logger.warning(f"关闭Qdrant连接时出错: {e}")
    
    async def delete_by_ids(self, ids: List[str]):
        """
        根据ID列表删除文档

        Args:
            ids: 要删除的文档ID列表
        """
        if not self.collection_initialized:
            logger.info("集合未初始化，自动初始化")
            await self.initialize()
        
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=PointIdsList(points=ids)
            )
            logger.info(f"从集合 {self.collection_name} 中删除了 {len(ids)} 个文档")
        except Exception as e:
            logger.error(f"删除文档时出错: {e}")
            traceback.print_exc()
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        获取集合统计信息

        Returns:
            包含统计信息的字典
        """
        if not self.collection_initialized:
            logger.info("集合未初始化，自动初始化")
            await self.initialize()
        
        try:
            collection_info = self.client.get_collection(collection_name=self.collection_name)
            
            # 获取向量数量
            count = collection_info.vectors_count
            
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "dimension": self.dimension,
                "metric": self.metric,
                "on_disk": self.on_disk
            }
        except Exception as e:
            logger.error(f"获取统计信息时出错: {e}")
            traceback.print_exc()
            return {"error": str(e)}
    
    async def reset(self):
        """重置集合，删除所有文档"""
        try:
            logger.warning(f"重置集合 {self.collection_name}")
            self.client.delete_collection(collection_name=self.collection_name)
            logger.info(f"已删除集合 {self.collection_name}")
            
            # 重新创建集合
            self.collection_initialized = False
            await self.initialize()
        except Exception as e:
            logger.error(f"重置集合时出错: {e}")
            traceback.print_exc()
            
    async def list_collections(self) -> List[str]:
        """
        列出所有可用的集合名称

        Returns:
            集合名称列表
        """
        try:
            collections = self.client.get_collections()
            return [col.name for col in collections.collections]
        except Exception as e:
            logger.error(f"列出集合时出错: {e}")
            traceback.print_exc()
            return []

    async def get_points(self, limit: int = 100, filter_str: str = None) -> List[Dict[str, Any]]:
        """
        获取集合中的所有点（文档）

        Args:
            limit: 返回的最大文档数量
            filter_str: 过滤条件(JSON字符串)

        Returns:
            文档列表
        """
        if not self.collection_initialized:
            logger.info("集合未初始化，自动初始化")
            await self.initialize()
        
        try:
            # 解析过滤条件
            scroll_filter = self._parse_filter(filter_str)
            
            # 获取点
            result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=scroll_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            # 处理结果
            points = result[0]  # 第一个元素是点列表，第二个是下一个分页的偏移量
            
            documents = []
            for point in points:
                # 从载荷中提取文本
                payload = point.payload or {}
                text = payload.pop("text", "") if isinstance(payload, dict) else ""
                
                doc = {
                    "id": point.id,
                    "text": text,
                    "metadata": payload
                }
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"获取集合点时出错: {e}")
            traceback.print_exc()
            return [] 