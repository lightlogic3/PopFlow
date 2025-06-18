# vectorstores/faiss_store.py
import os
import pickle
import logging
import traceback
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from knowledge_manage.vectorstores.base import VectorStore, _clean_metadata
from knowledge_api.utils.log_config import get_logger

logger = get_logger()
try:
    # 抑制FAISS日志
    logging.getLogger("faiss").setLevel(logging.WARNING)
    logging.getLogger("faiss.loader").setLevel(logging.WARNING)

    import faiss
except ImportError:
    logger.info("faiss不可用如需启用，- 对于支持CUDA的GPU: `pip install faiss-gpu,- 对于CPU: `pip install faiss-cpu``")




class FAISSStore(VectorStore):
    """
    基于FAISS的向量存储实现，适用于大规模向量集合和高性能相似性搜索
    """

    def __init__(
        self,
        collection_name: str,
        dimension: int,
        metric: str = "cosine",
        fields_schema: Optional[List[Tuple[str, str]]] = None,
        path: Optional[str] = None,
        normalize_L2: bool = False,
        create_if_not_exists: bool = True,
        **kwargs
    ):
        """
        初始化FAISS向量存储

        Args:
            collection_name: 集合名称
            dimension: 向量维度
            metric: 距离度量方式("cosine", "euclidean", "dot")
            fields_schema: 字段模式列表
            path: 索引持久化目录路径
            normalize_L2: 是否对向量进行L2归一化
            create_if_not_exists: 集合不存在时是否创建
            **kwargs: 额外参数
        """
        super().__init__(collection_name, dimension, metric, fields_schema, **kwargs)
        self.normalize_L2 = normalize_L2
        self.create_if_not_exists = create_if_not_exists
        
        # 设置路径
        self.path = path or "./faiss_indices"
        
        # 初始化存储结构
        self.index = None
        self.docstore = {}  # 存储文档内容和元数据
        self.index_to_id = {}  # 映射FAISS索引ID到文档ID
        
        logger.info(f"初始化FAISS向量存储: {collection_name}, 维度: {dimension}, 度量: {metric}")

    async def initialize(self):
        """初始化FAISS索引，必须在添加文档或搜索前调用"""
        try:
            # 创建目录（如果不存在）
            if self.path:
                os.makedirs(self.path, exist_ok=True)
                
                # 尝试加载现有索引
                index_path = os.path.join(self.path, f"{self.collection_name}.faiss")
                docstore_path = os.path.join(self.path, f"{self.collection_name}.pkl")
                
                if os.path.exists(index_path) and os.path.exists(docstore_path):
                    await self._load(index_path, docstore_path)
                    logger.info(f"从{index_path}加载FAISS索引，包含{self.index.ntotal if self.index else 0}个向量")
                    return
            
            # 如果没有现有索引或无法加载，创建新索引
            await self._create_index()
            logger.info(f"为集合{self.collection_name}创建了新的FAISS索引")
        
        except Exception as e:
            logger.error(f"初始化FAISS索引时出错: {e}")
            traceback.print_exc()
            if not self.create_if_not_exists:
                raise
            logger.info("尝试创建新的FAISS索引...")
            await self._create_index()

    async def _create_index(self):
        """创建新的FAISS索引"""
        # 根据度量方式创建索引
        if self.metric.lower() in ["inner_product", "dot", "cosine"]:
            self.index = faiss.IndexFlatIP(self.dimension)
        else:  # 默认使用L2距离
            self.index = faiss.IndexFlatL2(self.dimension)
        
        # 重置文档存储
        self.docstore = {}
        self.index_to_id = {}
        
        # 保存索引
        await self._save()

    async def _load(self, index_path: str, docstore_path: str):
        """加载FAISS索引和文档存储"""
        try:
            self.index = faiss.read_index(index_path)
            with open(docstore_path, "rb") as f:
                loaded_data = pickle.load(f)
                self.docstore = loaded_data[0]
                self.index_to_id = loaded_data[1]
        except Exception as e:
            logger.error(f"加载FAISS索引失败: {e}")
            traceback.print_exc()
            # 重置存储结构
            self.docstore = {}
            self.index_to_id = {}
            self.index = None
            raise

    async def _save(self):
        """保存FAISS索引和文档存储"""
        if not self.path or not self.index:
            return
            
        try:
            os.makedirs(self.path, exist_ok=True)
            index_path = os.path.join(self.path, f"{self.collection_name}.faiss")
            docstore_path = os.path.join(self.path, f"{self.collection_name}.pkl")
            
            # 保存索引
            faiss.write_index(self.index, index_path)
            
            # 保存文档存储和ID映射
            with open(docstore_path, "wb") as f:
                pickle.dump((self.docstore, self.index_to_id), f)
            
            logger.info(f"已保存FAISS索引到{index_path}")
        except Exception as e:
            logger.error(f"保存FAISS索引失败: {e}")
            traceback.print_exc()

    async def _add_processed_documents(self, processed_docs: List[Dict[str, Any]]) -> int:
        """
        将预处理后的文档添加到FAISS索引

        Args:
            processed_docs: 预处理后的文档列表，必须包含向量嵌入

        Returns:
            成功添加的文档数量
        """
        if not self.index:
            await self.initialize()
        
        try:
            # 准备要添加的数据
            doc_vectors = []
            doc_ids = []
            doc_payloads = []
            
            for doc in processed_docs:
                # 检查向量是否存在
                vector = doc.get("vector")
                if vector is None:
                    logger.warning(f"跳过没有向量的文档: {doc.get('id', 'unknown')}")
                    continue
                
                # 获取或生成文档ID
                doc_id = str(doc.get("id", str(uuid.uuid4())))
                
                # 准备元数据
                metadata = doc.get("metadata", {})
                if not isinstance(metadata, dict):
                    metadata = {"content": str(metadata)}
                    
                # 添加原始文本到元数据
                metadata["text"] = doc.get("text", "")
                
                doc_vectors.append(vector)
                doc_ids.append(doc_id)
                doc_payloads.append(metadata)
            
            if not doc_vectors:
                logger.warning("没有有效向量可添加")
                return 0
            
            # 将向量转换为NumPy数组
            vectors_np = np.array(doc_vectors, dtype=np.float32)
            
            # 对向量进行归一化（如果需要）
            if self.normalize_L2 and self.metric.lower() in ["cosine", "inner_product", "dot"]:
                logger.info("对向量进行L2归一化")
                faiss.normalize_L2(vectors_np)
            
            # 添加向量到FAISS索引
            starting_idx = len(self.index_to_id)
            self.index.add(vectors_np)
            
            # 更新文档存储和ID映射
            for i, (doc_id, payload) in enumerate(zip(doc_ids, doc_payloads)):
                self.docstore[doc_id] = payload
                self.index_to_id[starting_idx + i] = doc_id
            
            # 保存索引
            await self._save()
            
            logger.info(f"成功添加{len(doc_vectors)}个向量到FAISS索引")
            return len(doc_vectors)
            
        except Exception as e:
            logger.error(f"添加文档到FAISS索引时出错: {e}")
            traceback.print_exc()
            return 0

    async def search(self, query_embedding: List[float] = None, top_k: int = 5, filter_str: str = None) -> List[Dict[str, Any]]:
        """
        使用向量嵌入搜索相似文档

        Args:
            query_embedding: 查询向量嵌入（必需）
            top_k: 返回结果数量
            filter_str: 过滤条件JSON字符串

        Returns:
            相似文档列表
        """
        if not self.index:
            await self.initialize()
        
        if query_embedding is None:
            logger.error("搜索需要提供查询向量嵌入")
            return []
        
        try:
            # 解析过滤条件
            filters = None
            if filter_str:
                try:
                    import json
                    filters = json.loads(filter_str)
                    logger.info(f"使用过滤条件: {filters}")
                except Exception as e:
                    logger.warning(f"解析过滤条件时出错: {e}，忽略过滤条件")
            
            # 将查询向量转换为numpy数组
            query_vector = np.array([query_embedding], dtype=np.float32)
            
            # 对查询向量进行归一化（如果需要）
            if self.normalize_L2 and self.metric.lower() in ["cosine", "inner_product", "dot"]:
                faiss.normalize_L2(query_vector)
            
            # 获取更多结果用于过滤
            fetch_k = top_k * 10 if filters else top_k
            
            # 执行搜索
            distances, indices = self.index.search(query_vector, min(fetch_k, self.index.ntotal))
            
            # 处理搜索结果
            results = []
            seen_ids = set()  # 避免重复
            
            for i in range(len(indices[0])):
                idx = indices[0][i]
                if idx == -1:  # FAISS返回-1表示没有更多结果
                    continue
                
                # 获取文档ID和元数据
                doc_id = self.index_to_id.get(int(idx))
                if not doc_id or doc_id in seen_ids:
                    continue
                
                seen_ids.add(doc_id)
                metadata = self.docstore.get(doc_id, {})
                
                # 应用过滤器（如果有）
                if filters and not self._apply_filters(metadata, filters):
                    continue
                
                # 从元数据中提取文本
                text = metadata.pop("text", "") if isinstance(metadata, dict) else ""
                
                # 计算相似度分数（将距离转换为相似度）
                distance = distances[0][i]
                if self.metric.lower() in ["cosine", "inner_product", "dot"]:
                    # 对于这些度量，值越大表示越相似
                    score = float(distance)
                else:
                    # 对于欧氏距离等，值越小表示越相似，需要转换
                    score = float(1.0 / (1.0 + distance))
                
                # 添加到结果
                results.append({
                    "id": doc_id,
                    "text": text,
                    "metadata": metadata,
                    "score": score
                })
                
                # 达到所需数量后退出
                if len(results) >= top_k:
                    break
            
            logger.info(f"搜索返回{len(results)}个结果")
            return results
            
        except Exception as e:
            logger.error(f"FAISS搜索时出错: {e}")
            traceback.print_exc()
            return []

    def _apply_filters(self, metadata: Dict, filters: Dict) -> bool:
        """应用过滤条件"""
        if not filters or not metadata:
            return True
        
        for key, value in filters.items():
            # 检查键是否存在
            if key not in metadata:
                return False
            
            # 处理列表值（OR关系）
            if isinstance(value, list):
                if metadata[key] not in value:
                    return False
            # 处理精确匹配
            elif metadata[key] != value:
                return False
        
        return True

    async def close(self):
        """关闭资源连接并保存索引"""
        logger.info("关闭FAISS索引连接")
        try:
            await self._save()
        except Exception as e:
            logger.warning(f"关闭FAISS索引连接时出错: {e}")
    
    async def delete_by_ids(self, ids: List[str]):
        """
        根据ID列表删除文档（注意：FAISS不支持真正的删除，只是逻辑删除）

        Args:
            ids: 要删除的文档ID列表
        """
        if not self.index:
            await self.initialize()
        
        try:
            deleted_count = 0
            for doc_id in ids:
                # 找到索引映射
                idx_to_delete = None
                for idx, stored_id in self.index_to_id.items():
                    if stored_id == doc_id:
                        idx_to_delete = idx
                        break
                
                if idx_to_delete is not None:
                    # 从文档存储中删除
                    self.docstore.pop(doc_id, None)
                    # 从映射中删除
                    self.index_to_id.pop(idx_to_delete, None)
                    deleted_count += 1
            
            # 保存更改
            if deleted_count > 0:
                await self._save()
                logger.info(f"从集合{self.collection_name}中删除了{deleted_count}个文档")
            else:
                logger.warning(f"没有找到指定的文档ID: {ids}")
                
        except Exception as e:
            logger.error(f"删除文档时出错: {e}")
            traceback.print_exc()
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        获取索引统计信息

        Returns:
            包含统计信息的字典
        """
        if not self.index:
            await self.initialize()
        
        try:
            return {
                "collection_name": self.collection_name,
                "document_count": self.index.ntotal if self.index else 0,
                "dimension": self.dimension,
                "metric": self.metric,
                "storage_path": self.path if self.path else "内存存储"
            }
        except Exception as e:
            logger.error(f"获取统计信息时出错: {e}")
            traceback.print_exc()
            return {"error": str(e)}
    
    async def reset(self):
        """重置索引，删除所有文档"""
        logger.warning(f"重置FAISS索引: {self.collection_name}")
        try:
            # 删除现有的索引文件
            if self.path:
                index_path = os.path.join(self.path, f"{self.collection_name}.faiss")
                docstore_path = os.path.join(self.path, f"{self.collection_name}.pkl")
                
                if os.path.exists(index_path):
                    os.remove(index_path)
                if os.path.exists(docstore_path):
                    os.remove(docstore_path)
            
            # 重新创建索引
            await self._create_index()
            logger.info(f"成功重置FAISS索引")
        except Exception as e:
            logger.error(f"重置索引时出错: {e}")
            traceback.print_exc()
            
    async def list_collections(self) -> List[str]:
        """
        列出索引目录中的所有集合名称

        Returns:
            集合名称列表
        """
        if not self.path:
            return [self.collection_name] if self.index else []
        
        try:
            collections = []
            path = Path(self.path)
            for file in path.glob("*.faiss"):
                collections.append(file.stem)
            return collections
        except Exception as e:
            logger.error(f"列出集合时出错: {e}")
            traceback.print_exc()
            return [self.collection_name] if self.index else [] 