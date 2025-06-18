# vectorstores/langchain_store.py
import logging
import json
import traceback
from typing import Dict, List, Any, Optional, Tuple

try:
    from langchain_community.vectorstores import VectorStore as LangchainVectorStore
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    LangchainVectorStore = object

from knowledge_manage.vectorstores.base import VectorStore, _clean_metadata
from knowledge_api.utils.log_config import get_logger

logger = get_logger()


class LangchainStore(VectorStore):
    """
    基于LangChain向量存储的包装类，允许在知识管理系统中使用各种LangChain支持的向量存储
    """

    def __init__(
        self,
        collection_name: str,
        dimension: int,
        metric: str = "cosine",
        fields_schema: Optional[List[Tuple[str, str]]] = None,
        langchain_client: Optional[LangchainVectorStore] = None,
        **kwargs
    ):
        """
        初始化LangChain向量存储包装器

        Args:
            collection_name: 集合名称
            dimension: 向量维度
            metric: 距离度量方式
            fields_schema: 字段模式列表
            langchain_client: LangChain向量存储实例
            **kwargs: 其他参数
        """
        if not HAS_LANGCHAIN:
            raise ImportError(
                "缺少'langchain_community'库。请使用'pip install langchain_community'安装。"
            )
            
        super().__init__(collection_name, dimension, metric, fields_schema, **kwargs)

        if not isinstance(langchain_client, LangchainVectorStore):
            raise ValueError("必须提供一个有效的LangChain向量存储实例")
        
        self.client = langchain_client
        self.collection_name = collection_name
        logger.info(f"初始化LangChainStore，集合名称: {collection_name}，向量维度: {dimension}")
        
    async def initialize(self):
        """初始化向量存储，对于LangChain包装器，大多数初始化已在创建LangChain客户端时完成"""
        logger.info(f"LangChainStore {self.collection_name} 初始化")
        # LangChain实例在创建时已经初始化，所以这里不需要额外操作
        return True

    async def _add_processed_documents(self, processed_docs: List[Dict[str, Any]]) -> int:
        """
        将预处理的文档添加到LangChain向量存储中

        Args:
            processed_docs: 预处理的文档列表

        Returns:
            成功添加的文档数量
        """
        try:
            ids = []
            vectors = []
            metadatas = []
            
            for doc in processed_docs:
                doc_id = doc.get("id")
                if not doc_id:
                    logger.warning(f"跳过没有ID的文档")
                    continue
                    
                vector = doc.get("vector")
                if vector is None:
                    logger.warning(f"跳过没有向量的文档: {doc_id}")
                    continue
                
                # 处理元数据
                metadata = doc.get("metadata", {})
                if metadata:
                    metadata = _clean_metadata(metadata)
                    
                # 添加文本到元数据
                text = doc.get("text", "")
                if text:
                    metadata["text"] = text
                    
                ids.append(doc_id)
                vectors.append(vector)
                metadatas.append(metadata)
            
            if not ids:
                logger.warning("没有有效的文档可添加")
                return 0
                
            # 根据LangChain客户端类型调用合适的方法
            if hasattr(self.client, "add_embeddings"):
                self.client.add_embeddings(
                    embeddings=vectors,
                    metadatas=metadatas,
                    ids=ids
                )
            elif hasattr(self.client, "add_vectors"):
                self.client.add_vectors(
                    vectors=vectors,
                    metadatas=metadatas,
                    ids=ids
                )
            else:
                # 回退方法：对于不支持直接添加向量的LangChain实例
                # 使用空文本和嵌入向量添加文档
                texts = [""] * len(ids)
                self.client.add_texts(
                    texts=texts,
                    metadatas=metadatas,
                    ids=ids,
                    embeddings=vectors
                )
                
            logger.info(f"添加了 {len(ids)} 个文档到LangChain存储")
            return len(ids)
            
        except Exception as e:
            logger.error(f"添加文档到LangChain存储时出错: {e}")
            traceback.print_exc()
            return 0

    def _parse_output(self, data) -> List[Dict[str, Any]]:
        """
        解析LangChain返回的输出数据

        Args:
            data: LangChain搜索结果

        Returns:
            标准格式的结果列表
        """
        results = []
        
        # 处理Document对象列表
        if isinstance(data, list) and all(hasattr(doc, "metadata") for doc in data if hasattr(doc, "__dict__")):
            for doc in data:
                metadata = getattr(doc, "metadata", {}) or {}
                text = metadata.pop("text", "") if isinstance(metadata, dict) else ""
                if not text and hasattr(doc, "page_content"):
                    text = doc.page_content
                    
                result = {
                    "id": getattr(doc, "id", None) or metadata.get("id"),
                    "text": text,
                    "metadata": metadata,
                    "score": getattr(doc, "score", None)
                }
                results.append(result)
            return results
            
        # 处理标准字典格式
        if isinstance(data, dict):
            keys = ["ids", "distances", "metadatas"]
            values = []

            for key in keys:
                value = data.get(key, [])
                if isinstance(value, list) and value and isinstance(value[0], list):
                    value = value[0]
                values.append(value)

            ids, distances, metadatas = values
            max_length = max(len(v) for v in values if isinstance(v, list) and v is not None)

            for i in range(max_length):
                id_val = ids[i] if isinstance(ids, list) and ids and i < len(ids) else None
                score = distances[i] if isinstance(distances, list) and distances and i < len(distances) else None
                metadata = metadatas[i] if isinstance(metadatas, list) and metadatas and i < len(metadatas) else {}
                
                # 从元数据中提取文本
                text = ""
                if isinstance(metadata, dict):
                    text = metadata.pop("text", "")
                    
                result = {
                    "id": id_val,
                    "text": text,
                    "metadata": metadata,
                    "score": score
                }
                results.append(result)
                
        return results

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
        if query_embedding is None:
            logger.error("搜索需要提供查询向量嵌入")
            return []
            
        try:
            query_filter = None
            if filter_str:
                try:
                    query_filter = json.loads(filter_str)
                except json.JSONDecodeError:
                    logger.warning(f"无法解析过滤条件: {filter_str}，将忽略过滤")
            
            # 搜索
            if hasattr(self.client, "similarity_search_by_vector"):
                if query_filter:
                    results = self.client.similarity_search_by_vector(
                        embedding=query_embedding, 
                        k=top_k,
                        filter=query_filter
                    )
                else:
                    results = self.client.similarity_search_by_vector(
                        embedding=query_embedding, 
                        k=top_k
                    )
            elif hasattr(self.client, "similarity_search_with_score_by_vector"):
                if query_filter:
                    results = self.client.similarity_search_with_score_by_vector(
                        embedding=query_embedding, 
                        k=top_k,
                        filter=query_filter
                    )
                else:
                    results = self.client.similarity_search_with_score_by_vector(
                        embedding=query_embedding, 
                        k=top_k
                    )
            else:
                logger.error("不支持的LangChain向量存储类型，无法执行向量搜索")
                return []
                
            parsed_results = self._parse_output(results)
            logger.info(f"搜索返回 {len(parsed_results)} 个结果")
            return parsed_results
            
        except Exception as e:
            logger.error(f"LangChain搜索时出错: {e}")
            traceback.print_exc()
            return []

    async def close(self):
        """关闭连接并释放资源"""
        logger.info(f"关闭LangChainStore {self.collection_name}")
        try:
            # 尝试调用关闭方法（如果有）
            if hasattr(self.client, "close"):
                self.client.close()
        except Exception as e:
            logger.warning(f"关闭LangChain存储时出错: {e}")

    async def delete_by_ids(self, ids: List[str]):
        """
        根据ID列表删除文档

        Args:
            ids: 要删除的文档ID列表
        """
        try:
            if hasattr(self.client, "delete"):
                self.client.delete(ids=ids)
                logger.info(f"从LangChain存储中删除了 {len(ids)} 个文档")
            else:
                logger.warning("此LangChain向量存储不支持删除操作")
        except Exception as e:
            logger.error(f"删除文档时出错: {e}")
            traceback.print_exc()

    async def get_stats(self) -> Dict[str, Any]:
        """
        获取存储统计信息

        Returns:
            包含统计信息的字典
        """
        try:
            # 尝试获取文档数量
            count = 0
            try:
                if hasattr(self.client, "_collection") and hasattr(self.client._collection, "count"):
                    count = self.client._collection.count()
            except:
                logger.warning("无法获取文档数量")
                
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "dimension": self.dimension,
                "metric": self.metric,
                "store_type": self.client.__class__.__name__
            }
        except Exception as e:
            logger.error(f"获取统计信息时出错: {e}")
            traceback.print_exc()
            return {"error": str(e)}

    async def reset(self):
        """重置存储，删除所有文档"""
        try:
            logger.warning(f"重置LangChain存储 {self.collection_name}")
            
            # 尝试多种可能的重置方法
            if hasattr(self.client, "delete_collection"):
                self.client.delete_collection()
            elif hasattr(self.client, "reset"):
                self.client.reset()
            elif hasattr(self.client, "reset_collection"):
                self.client.reset_collection()
            elif hasattr(self.client, "delete"):
                self.client.delete(ids=None)  # 某些实现允许传递None来删除所有内容
            else:
                logger.warning("此LangChain向量存储不支持重置操作")
                
        except Exception as e:
            logger.error(f"重置存储时出错: {e}")
            traceback.print_exc()
            
    async def list_collections(self) -> List[str]:
        """
        列出所有可用的集合名称

        Returns:
            集合名称列表
        """
        # 大多数LangChain实现不支持多集合
        return [self.collection_name] 