from typing import Dict, Any, Optional, List, Tuple

from knowledge_api.utils.log_config import get_logger
from knowledge_manage.vectorstores.base import VectorStore
from knowledge_manage.vectorstores.chroma_store import ChromaStore
from knowledge_manage.vectorstores.dashvector_http_store import DashVectorHTTPStore

logger = get_logger()


class VectorStoreFactory:
    """
    向量存储工厂类，用于创建不同类型的向量存储对象
    """
    # 缓存已创建的向量存储实例
    _instances: Dict[str, VectorStore] = {}

    @classmethod
    def get_available_stores(cls) -> List[str]:
        """
        获取所有可用的向量存储类型
        
        Returns:
            支持的向量存储类型列表
        """
        stores = ["chroma", "faiss", "qdrant", "langchain"]
        available_stores = []
        
        # 检查ChromaStore是否可用
        try:
            import chromadb
            available_stores.append("chroma")
        except ImportError:
            pass
        
        # 检查FAISSStore是否可用
        try:
            import faiss
            available_stores.append("faiss")
        except ImportError:
            pass
        
        # 检查QdrantStore是否可用
        try:
            import qdrant_client
            available_stores.append("qdrant")
        except ImportError:
            pass
        
        # 检查LangchainStore是否可用
        try:
            from langchain_community.vectorstores import VectorStore as LangchainVectorStore
            available_stores.append("langchain")
        except ImportError:
            pass
        
        return available_stores

    @classmethod
    async def create_vector_store(cls,
                                  store_type: str,
                                  collection_name: str,
                                  dimension: int = 512,
                                  fields_schema: Dict[str, Any] = None,
                                  create_if_not_exists: bool = True,
                                  is_init_collection: bool = False,
                                  **kwargs) -> VectorStore:
        """
        创建向量存储实例
        
        Args:
            store_type: 向量存储类型，支持 'dashvector', 'chroma', 'faiss', 'qdrant', 'langchain' 等
            collection_name: 集合名称
            dimension: 向量维度
            fields_schema: 字段模式
            create_if_not_exists: 不存在则创建
            is_init_collection: 是否初始化集合
            **kwargs: 其他参数
            
        Returns:
            向量存储实例
        """
        # 创建缓存键
        cache_key = f"{store_type}:{collection_name}"

        # 检查缓存
        if cache_key in cls._instances:
            logger.info(f"使用缓存的向量存储: {cache_key}")
            return cls._instances[cache_key]

        # 创建新实例
        if store_type.lower() == "dashvector":
            # 确保必要参数存在
            if "api_key" not in kwargs or "endpoint" not in kwargs:
                raise ValueError("使用DashVector需要提供api_key和endpoint参数")

            vector_store = DashVectorHTTPStore(
                api_key=kwargs.get("api_key"),
                endpoint=kwargs.get("endpoint"),
                collection_name=collection_name,
                dimension=dimension,
                metric=kwargs.get("metric", "cosine"),
                fields_schema=fields_schema or {},
                create_if_not_exists=create_if_not_exists,
                is_init_collection=is_init_collection
            )

        elif store_type.lower() == "chroma":
            vector_store = ChromaStore(
                collection_name=collection_name,
                dimension=dimension,
                metric=kwargs.get("metric", "cosine"),
                path=kwargs.get("persist_directory", "./chroma_db"),
                embedding_function=kwargs.get("embedding_function"),
                create_if_not_exists=create_if_not_exists
            )
        
        elif store_type.lower() == "faiss":
            try:
                from knowledge_manage.vectorstores.faiss_store import FAISSStore
                vector_store = FAISSStore(
                    collection_name=collection_name,
                    dimension=dimension,
                    metric=kwargs.get("metric", "cosine"),
                    path=kwargs.get("path", "./faiss_indices"),
                    normalize_L2=kwargs.get("normalize_L2", False),
                    create_if_not_exists=create_if_not_exists
                )
            except ImportError:
                raise ImportError("使用FAISS需要安装faiss-cpu或faiss-gpu库")
        
        elif store_type.lower() == "qdrant":
            try:
                from knowledge_manage.vectorstores.qdrant_store import QdrantStore
                vector_store = QdrantStore(
                    collection_name=collection_name,
                    dimension=dimension,
                    metric=kwargs.get("metric", "cosine"),
                    host=kwargs.get("host"),
                    port=kwargs.get("port"),
                    path=kwargs.get("path", "./qdrant_data"),
                    url=kwargs.get("url"),
                    api_key=kwargs.get("api_key"),
                    on_disk=kwargs.get("on_disk", True),
                    create_if_not_exists=create_if_not_exists
                )
            except ImportError:
                raise ImportError("使用Qdrant需要安装qdrant-client库")
                
        elif store_type.lower() == "langchain":
            try:
                from knowledge_manage.vectorstores.langchain_store import LangchainStore
                
                if "langchain_client" not in kwargs:
                    raise ValueError("使用LangchainStore必须提供langchain_client参数，该参数应为LangChain向量存储实例")
                    
                vector_store = LangchainStore(
                    collection_name=collection_name,
                    dimension=dimension,
                    metric=kwargs.get("metric", "cosine"),
                    langchain_client=kwargs.get("langchain_client"),
                    fields_schema=fields_schema
                )
            except ImportError:
                raise ImportError("使用LangChain需要安装langchain_community库")
        
        else:
            raise ValueError(f"不支持的向量存储类型: {store_type}")

        # 如果需要初始化向量存储
        if is_init_collection and hasattr(vector_store, 'initialize'):
            await vector_store.initialize()

        # 缓存实例
        cls._instances[cache_key] = vector_store
        return vector_store

    @classmethod
    def get_available_types(cls) -> Dict[str, Any]:
        """
        获取可用的向量存储列表
        
        Returns:
            可用存储信息
        """
        info = {
            "dashvector": {
                "description": "阿里云向量数据库",
                "requires_api_key": True,
                "supports_async": True
            },
            "chroma": {
                "description": "本地向量数据库",
                "requires_api_key": False,
                "supports_async": False
            }
        }
        
        # 检查FAISS是否可用
        try:
            import faiss
            info["faiss"] = {
                "description": "Facebook AI相似性搜索",
                "requires_api_key": False,
                "supports_async": True,
                "best_for": "大规模向量检索"
            }
        except ImportError:
            pass
        
        # 检查Qdrant是否可用
        try:
            import qdrant_client
            info["qdrant"] = {
                "description": "高性能向量数据库",
                "requires_api_key": False,
                "supports_async": True,
                "best_for": "生产环境和多过滤条件查询"
            }
        except ImportError:
            pass
        
        # 检查LangChain是否可用
        try:
            from langchain_community.vectorstores import VectorStore as LangchainVectorStore
            info["langchain"] = {
                "description": "LangChain向量存储包装器",
                "requires_api_key": False,
                "supports_async": True,
                "best_for": "集成LangChain生态系统",
                "note": "需要提供langchain_client参数"
            }
        except ImportError:
            pass
        
        return info
