# vectorstores/chroma_store.py

# SQLite3补丁 - 必须在导入chromadb之前执行
import sys
try:
    import pysqlite3.dbapi2 as sqlite3_new
    sys.modules['sqlite3'] = sqlite3_new
    sys.modules['sqlite3.dbapi2'] = sqlite3_new
    print(f"🔧 ChromaStore: SQLite3补丁已应用，版本: {sqlite3_new.sqlite_version}")
except ImportError:
    print("⚠️  ChromaStore: 未找到pysqlite3-binary")

import os
from typing import List, Dict, Any, Optional, Tuple
import traceback
from langchain_core.documents import Document

from knowledge_manage.vectorstores.base import VectorStore, _clean_metadata
from knowledge_api.utils.log_config import get_logger
logger = get_logger()
try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    logger.info("chromadb不可用如需启用，请使用'pip install chromadb'安装。")






class ChromaStore(VectorStore):
    """基于ChromaDB的向量数据库实现，支持本地持久化和远程服务器连接模式"""

    def __init__(self,
                 collection_name: str,
                 dimension: int,
                 metric: str = "cosine",
                 fields_schema: Optional[List[Tuple[str, str]]] = None,
                 host: Optional[str] = None,
                 port: Optional[int] = None,
                 path: Optional[str] = None,
                 client: Optional[Any] = None,
                 create_if_not_exists: bool = True,
                 **kwargs):
        """
        初始化ChromaDB向量存储

        Args:
            collection_name: 集合名称
            dimension: 向量维度
            metric: 距离度量方式("cosine", "euclidean", "dot")
            fields_schema: 字段模式列表
            host: ChromaDB服务器主机地址
            port: ChromaDB服务器端口
            path: 本地持久化目录路径
            client: 现有的ChromaDB客户端实例
            create_if_not_exists: 集合不存在时是否创建
            **kwargs: 额外参数，支持以下选项:
                - persist_directory: 旧版兼容参数，等同于path
                - embedding_function: 自定义嵌入函数(仅用于通过工厂类集成LangChain)
        """
        super().__init__(collection_name, dimension, metric, fields_schema, **kwargs)
        
        # 兼容旧版参数
        if path is None and 'persist_directory' in kwargs:
            path = kwargs['persist_directory']
        
        if client:
            logger.info("使用提供的ChromaDB客户端")
            self.client = client
        else:
            self.settings = Settings(anonymized_telemetry=False)

            if host and port:
                # 使用远程服务器模式
                logger.info(f"连接到远程ChromaDB服务器: {host}:{port}")
                self.settings.chroma_server_host = host
                self.settings.chroma_server_http_port = port
                self.settings.chroma_api_impl = "chromadb.api.fastapi.FastAPI"
            else:
                # 使用本地持久化模式
                if path is None:
                    path = "chroma_data"
                
                logger.info(f"使用本地持久化目录: {path}")
                self.settings.persist_directory = path
                self.settings.is_persistent = True

            try:
                self.client = chromadb.Client(self.settings)
                logger.info(f"成功初始化ChromaDB客户端")
            except Exception as e:
                logger.error(f"初始化ChromaDB客户端时出错: {e}")
                traceback.print_exc()
                raise
        
        self.collection = None
        self.create_if_not_exists = create_if_not_exists
        self.embedding_function = kwargs.get('embedding_function')

    async def initialize(self):
        """初始化向量集合，必须在添加文档前调用"""
        try:
            if self.embedding_function:
                logger.info(f"使用自定义嵌入函数初始化集合: {self.collection_name}")
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"dimension": self.dimension, "hnsw:space": self.metric},
                    embedding_function=self.embedding_function
                )
            else:
                self.collection = self.client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"dimension": self.dimension, "hnsw:space": self.metric}
                )
            logger.info(f"成功初始化集合: {self.collection_name}")
            
            # 尝试创建字段模式(如果提供)
            if self.fields_schema:
                await self.create_fields_schema(self.fields_schema)
                
        except Exception as e:
            logger.error(f"初始化ChromaDB集合时出错: {e}")
            traceback.print_exc()
            if not self.create_if_not_exists:
                raise
            logger.info("尝试创建新集合...")
            try:
                # 强制创建新集合
                if self.collection_name in [col.name for col in self.client.list_collections()]:
                    self.client.delete_collection(self.collection_name)
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"dimension": self.dimension, "hnsw:space": self.metric},
                    embedding_function=self.embedding_function if self.embedding_function else None
                )
            except Exception as sub_error:
                logger.error(f"创建新集合失败: {sub_error}")
                traceback.print_exc()
                raise

    async def _add_processed_documents(self, processed_docs: List[Dict[str, Any]]) -> int:
        """
        将预处理后的文档异步添加到ChromaDB

        Args:
            processed_docs: 预处理后的文档列表

        Returns:
            成功添加的文档数量
        """
        if not self.collection:
            logger.info("集合未初始化，自动初始化")
            await self.initialize()
        
        try:
            ids = []
            embeddings = []
            metadatas = []
            documents = []
            
            for doc in processed_docs:
                # 获取文档ID
                doc_id = str(doc.get("id", ""))
                if not doc_id:
                    logger.warning(f"跳过没有ID的文档: {doc}")
                    continue
                
                ids.append(doc_id)
                
                # 获取向量
                vector = doc.get("vector")
                if vector:
                    embeddings.append(vector)
                
                # 处理元数据，确保类型兼容性
                metadata = doc.get("metadata", {})
                if metadata:
                    metadata = _clean_metadata(metadata)
                metadatas.append(metadata)
                
                # 获取文本内容
                text = doc.get("text", "")
                documents.append(text)
            
            if not ids:
                logger.warning("没有有效文档可添加")
                return 0
            
            # 检查是否有embeddings，如果没有则不传入(由ChromaDB自己计算或使用设置的embedding_function)
            if len(embeddings) == len(ids):
                logger.info(f"添加 {len(ids)} 个文档(使用预计算嵌入)")
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    documents=documents
                )
            else:
                if self.embedding_function:
                    logger.info(f"添加 {len(ids)} 个文档(使用自定义嵌入函数)")
                else:
                    logger.info(f"添加 {len(ids)} 个文档(未提供嵌入向量)")
                self.collection.add(
                    ids=ids,
                    metadatas=metadatas,
                    documents=documents
                )
            
            logger.info(f"成功添加 {len(ids)} 个文档到ChromaDB集合 {self.collection_name}")
            return len(ids)
        
        except Exception as e:
            logger.error(f"添加文档到ChromaDB时出错: {e}")
            traceback.print_exc()
            return 0

    async def search(self, query_embedding: List[float] = None, top_k: int = 5, filter_str: str = None) -> List[Dict[str, Any]]:
        """
        使用嵌入向量异步搜索相似文档

        Args:
            query_embedding: 查询的嵌入向量
            top_k: 返回的最相似文档数量
            filter_str: 过滤条件(ChromaDB的where子句形式的JSON字符串)

        Returns:
            相似文档列表
        """
        if not self.collection:
            logger.info("集合未初始化，自动初始化")
            await self.initialize()
        
        try:
            # 解析过滤条件
            where_clause = None
            if filter_str:
                try:
                    import json
                    where_clause = json.loads(filter_str)
                    logger.info(f"使用过滤条件: {where_clause}")
                except Exception as e:
                    logger.warning(f"解析过滤条件时出错: {e}，忽略过滤条件")
            
            # 执行查询
            logger.info(f"在集合 {self.collection_name} 中搜索Top-{top_k}文档")
            results = self.collection.query(
                query_embeddings=[query_embedding] if query_embedding else None,
                where=where_clause,
                n_results=top_k
            )
            
            # 解析结果
            matches = []
            if results:
                # 获取查询结果的各个部分
                ids = results.get("ids", [[]])[0]
                distances = results.get("distances", [[]])[0]
                metadatas = results.get("metadatas", [[]])[0]
                documents = results.get("documents", [[]])[0]
                
                for i in range(len(ids)):
                    match = {
                        "id": ids[i] if i < len(ids) else None,
                        "text": documents[i] if i < len(documents) else None,
                        "metadata": metadatas[i] if i < len(metadatas) else {},
                        "score": float(1 - distances[i]) if i < len(distances) else None  # 将距离转换为相似性分数
                    }
                    matches.append(match)
            
            logger.info(f"搜索返回 {len(matches)} 个结果")
            return matches
        
        except Exception as e:
            logger.error(f"ChromaDB搜索时出错: {e}")
            traceback.print_exc()
            return []

    async def close(self):
        """关闭资源连接，确保数据持久化"""
        logger.info("关闭ChromaDB连接")
        try:
            if hasattr(self, 'client') and hasattr(self.client, 'persist'):
                self.client.persist()
        except Exception as e:
            logger.warning(f"关闭ChromaDB连接时出错: {e}")
    
    async def delete_by_ids(self, ids: List[str]):
        """
        根据ID列表删除文档

        Args:
            ids: 要删除的文档ID列表
        """
        if not self.collection:
            logger.info("集合未初始化，自动初始化")
            await self.initialize()
        
        try:
            self.collection.delete(ids=ids)
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
        if not self.collection:
            logger.info("集合未初始化，自动初始化")
            await self.initialize()
        
        try:
            # 获取所有文档ID以计算数量
            result = self.collection.get()
            count = len(result.get("ids", [])) if result else 0
            
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "dimension": self.dimension,
                "metric": self.metric
            }
        except Exception as e:
            logger.error(f"获取统计信息时出错: {e}")
            traceback.print_exc()
            return {"error": str(e)}
    
    async def reset(self):
        """重置集合，删除所有文档"""
        if not self.collection:
            logger.info("集合未初始化，自动初始化")
            await self.initialize()
        
        try:
            self.client.delete_collection(self.collection_name)
            logger.warning(f"已删除集合 {self.collection_name}")
            # 重新创建集合
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
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            logger.error(f"列出集合时出错: {e}")
            traceback.print_exc()
            return []