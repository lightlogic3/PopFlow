from abc import abstractmethod
from typing import List, Dict, Any, Optional, Tuple, Callable

from knowledge_api.utils.log_config import get_logger


def _clean_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    清理元数据，确保类型兼容性

    Args:
        metadata: 原始元数据字典

    Returns:
        清理后的元数据字典
    """
    clean_meta = {}
    for k, v in metadata.items():
        if isinstance(v, (str, int, float, bool)):
            clean_meta[k] = v
        else:
            clean_meta[k] = str(v)
    return clean_meta


def _preprocess_documents(documents: List[Dict[str, Any]],
                          embeddings: Optional[List[List[float]]]) -> List[Dict[str, Any]]:
    """
    预处理文档，标准化格式

    Args:
        documents: 原始文档列表
        embeddings: 嵌入向量列表（可选）

    Returns:
        处理后的文档列表
    """
    processed_docs = []
    for i, doc in enumerate(documents):
        # 获取向量
        vector = None
        if embeddings is not None and i < len(embeddings):
            vector = embeddings[i]
        doc.update({"vector": vector})
        processed_docs.append(doc)
    return processed_docs


logger = get_logger()


class VectorStore:
    """向量数据库的基类，提供通用文档处理功能"""

    def __init__(self,
                 collection_name: str,  # 向量存储的集合名称
                 dimension: int,  # 向量的维度
                 metric: str,  # 距离度量方式
                 fields_schema: Optional[List[Tuple[str, str]]] = None,  # 字段模式
                 **kwargs):
        """
        初始化向量存储
        子类可以根据需要实现此方法
        """
        self.collection_name = collection_name
        self.dimension = dimension
        self.metric = metric
        self.fields_schema = fields_schema if fields_schema is not None else []
        self.kwargs = kwargs

    async def create_fields_schema(self, fields_schema: List[Tuple[str, str]]):
        """
        创建字段模式
        子类可以根据需要实现此方法

        Args:
            fields_schema: 字段模式列表，每个元素为 (字段名, 字段类型) 的元组
        """
        self.fields_schema = fields_schema

    async def add_documents(self, documents: List[Dict[str, Any]], embeddings: List[List[float]]) -> int:
        """
        异步添加文档到向量数据库

        Args:
            documents: 文档列表，每个文档包含文本和元数据
            embeddings: 文档对应的嵌入向量列表

        Returns:
            添加的文档数量
        """
        if not documents or (embeddings is not None and len(documents) != len(embeddings)):
            return 0

        try:
            # 预处理文档
            processed_docs = _preprocess_documents(documents, embeddings)
            # 执行存储特定的文档添加
            return await self._add_processed_documents(processed_docs)
        except Exception as e:
            logger.info(f"添加文档时出错: {e}")
            import traceback
            traceback.print_exc()
            return 0

    async def initialize(self):
        """
        初始化向量存储
        子类可以根据需要实现此方法
        """
        pass

    @abstractmethod
    async def _add_processed_documents(self, processed_docs: List[Dict[str, Any]]) -> int:
        """
        子类应实现此方法，将预处理后的文档异步添加到特定的向量存储

        Args:
            processed_docs: 预处理后的文档列表

        Returns:
            成功添加的文档数量
        """
        raise NotImplementedError("子类必须实现_add_processed_documents方法")

    @abstractmethod
    async def search(self,
                     query_embedding: List[float] = None,
                     top_k: int = 5,
                     filter_str: str = None) -> List[
        Dict[str, Any]]:
        """
        异步使用嵌入向量搜索相似文档

        Args:
            query_embedding: 查询的嵌入向量
            top_k: 返回的最相似文档数量
            filter_str: 过滤条件

        Returns:
            相似文档列表
        """
        raise NotImplementedError("子类必须实现search方法")

    @abstractmethod
    async def close(self):
        """
        关闭任何打开的连接或资源
        子类可以根据需要实现此方法
        """
        pass

    @abstractmethod
    async def delete_by_ids(self, ids: list[str]):
        """
        删除向量数据库
        :param ids:
        :return:
        """
