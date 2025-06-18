from typing import List, Dict, Any, Optional
import time

from knowledge_api.config import get_collection_name, EMBEDDING_MODEL_NAME, EMBEDDING_MODEL_DEVICE
from knowledge_api.framework.redis.cache_manager import CacheManager
from knowledge_api.utils.log_config import get_logger
from knowledge_api.utils.text_processor import clean_text, split_text
from knowledge_manage.embeddings.base import EmbeddingEngine
from knowledge_manage.embeddings.factory import EmbeddingFactory
from knowledge_manage.vectorstores.base import VectorStore
from knowledge_manage.vectorstores.factory import VectorStoreFactory
from runtime import ExecutionTimer

logger = get_logger()

class RAGService:
    """Unified RAG service class, integrating embedding models and vector storage capabilities"""
    def __init__(self, 
                 table_name: str,
                 embedding_type: str = "huggingface",
                 store_type: str = "dashvector",
                 collection_name: str = None,
                 model_name: str = None,
                 is_init_collection: bool = False,
                 **kwargs):
        """Initialize RAG service

Args:
table_name: table name
embedding_type: Embedded model types
store_type: Vector storage type
collection_name: Collection Name
model_name: Embedded model name
is_init_collection: whether to initialize the collection
** kwargs: other parameters"""
        self.table_name = table_name
        self.embedding_type = embedding_type
        self.store_type = store_type
        
        # Use the collection name passed in, or use the name generated in the configuration
        self.collection_name = collection_name or get_collection_name(table_name)
        
        # Get the model abbreviation for logging
        self.model_name = model_name or EMBEDDING_MODEL_NAME
        model_parts = self.model_name.split("/")
        self.model_short_name = model_parts[-1]
        
        # initialization flag
        self.is_init_collection = is_init_collection
        self.is_initialized = False
        self.kwargs = kwargs
        
        # The embedding engine and vector store will be created during asynchronous initialization
        self.embedding_engine = None
        self.vector_store = None
        
    async def initialize(self):
        """Initialize the service, create the embedding engine and vector store"""
        if self.is_initialized:
            logger.info(f"{self.table_name} RAG服务已经初始化")
            return
            
        # Initialize the embed engine
        self.embedding_engine = EmbeddingFactory.create_embedding(
            embedding_type=self.embedding_type,
            model_name=self.model_name,
            device=EMBEDDING_MODEL_DEVICE
        )
        
        # Initialize the vector database
        extra_kwargs = {}
        if self.store_type.lower() == "dashvector":
            extra_kwargs = {
                "api_key": await CacheManager().get_system_config_value("DASHVECTOR_API_KEY"),
                "endpoint": await CacheManager().get_system_config_value("DASHVECTOR_ENDPOINT"),
                "metric": "cosine",
                "dimension": 512 if "bge-small" in self.model_name else 1024
            }
            
        # Merge additional parameters
        vector_kwargs = {**self.kwargs, **extra_kwargs}
        
        self.vector_store = await VectorStoreFactory.create_vector_store(
            store_type=self.store_type,
            collection_name=self.collection_name,
            fields_schema=self.get_table_schema(),
            create_if_not_exists=True,
            is_init_collection=self.is_init_collection,
            **vector_kwargs
        )
        
        self.is_initialized = True
        logger.info(f"{self.table_name} RAG服务初始化完成")
        
    def get_table_schema(self) -> Dict[str, Any]:
        """Get the table structure, the default provides a common structure, subclasses can override

Returns:
Table Structure Dictionary"""
        return {
            "text": "STRING",  # Vectorized corpus required, required
            "doc_id": "STRING",  # document unique identifier
            "title": "STRING",  # title
            "source": "STRING",  # source
            "metadata": "STRING",  # Other meta-information
        }
    
    async def add_documents(self, documents: List[Dict[str, Any]], embeddings: List[List[float]] = None) -> int:
        """Add document to vector database

Args:
Documents: document list
Embeddings: List of embeddings (if None, automatically generated)

Returns:
Number of documents successfully added"""
        if not self.is_initialized:
            await self.initialize()
            
        if not documents:
            return 0
            
        # If no embedding vector is provided, generate
        if embeddings is None:
            texts = [doc.get("text", "") for doc in documents]
            logger.info(f"为 {len(texts)} 个文档生成嵌入向量...")
            embeddings = self.embedding_engine.embed_documents(texts)
            
        # Store to vector database
        count = await self.vector_store.add_documents(documents, embeddings)
        logger.info(f"成功存储 {count} 个文档到 {self.collection_name}")
        
        return count
        
    async def add_text(self, data: Dict[str, Any], doc_id: str) -> Dict[str, Any]:
        """Add text to the knowledge base

Args:
Data: Text data and metadata
doc_id: Document ID

Returns:
Processing result information"""
        if not self.is_initialized:
            await self.initialize()
            
        try:
            # Clean up text
            cleaned_text = clean_text(data.get("text", ""))
            if not cleaned_text:
                return {
                    "success": False,
                    "message": "Text content is empty",
                    "document_count": 0,
                    "documents": []
                }
                
            # Prepare metadata
            data["doc_id"] = doc_id
            
            # Split text
            documents = split_text(cleaned_text, data)
            
            # Embed and store
            doc_count = await self.add_documents(documents)
            
            return {
                "success": True,
                "message": f"成功添加 {doc_count} 个文档块到知识库",
                "document_count": doc_count,
                "documents": documents
            }
        except Exception as e:
            logger.error(f"添加文本时出错: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"添加文本失败: {str(e)}",
                "document_count": 0,
                "documents": []
            }
            
    async def update_text(self, data: Dict[str, Any], doc_id: str) -> Dict[str, Any]:
        """Update the text in the knowledge base

Args:
Data: updated data
doc_id: Document ID

Returns:
Processing result information"""
        if not self.is_initialized:
            await self.initialize()
            
        try:
            # Delete the original document first
            await self.delete_by_ids([doc_id])
            
            # Then add a new document
            result = await self.add_text(data, doc_id)
            result["message"] = f"成功更新文档 (ID: {doc_id})"
            return result
        except Exception as e:
            logger.error(f"更新文本时出错: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"更新文本失败: {str(e)}",
                "document_count": 0,
                "documents": []
            }
            
    async def query(self, query: str, top_k: int = 5, user_info: dict = None) -> Dict[str, Any]:
        """Query Knowledge Base

Args:
Query: query text
top_k: Number of results returned
user_info: user information for permission filtering, etc

Returns:
query result"""
        if not self.is_initialized:
            await self.initialize()
            
        try:
            # Get the embedding vector of the query
            logger.info(f"为查询生成嵌入向量: {query}")
            timer = ExecutionTimer("Vector database query time:")
            timer.start()
            
            query_embedding = self.embedding_engine.embed_query(query)
            
            # perform vector search
            results = await self.search(query_embedding, top_k, user_info or {})
            timer.stop()
            
            return {
                "success": True,
                "message": f"查询成功，找到 {len(results)} 条结果",
                "results": results
            }
        except Exception as e:
            logger.error(f"查询时出错: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"查询失败: {str(e)}",
                "results": []
            }
            
    async def search(self, query_embedding: List[float], top_k: int = 5, user_info: dict = None) -> List[Dict[str, Any]]:
        """Search for similar documents using embedding vectors

Args:
query_embedding: Query Embedding Vector
top_k: Number of results returned
user_info: user information for permission filtering, etc

Returns:
List of similar documents"""
        # Default implementation of direct call vector storage search method
        # Subclasses can override this method to implement more complex filtering logic
        filter_str = self._build_filter_string(user_info)
        return await self.vector_store.search(query_embedding, top_k=top_k, filter_str=filter_str)
        
    def _build_filter_string(self, user_info: dict = None) -> Optional[str]:
        """Build filters based on user information

Args:
user_info: User Information

Returns:
Filter condition string"""
        # No filtering by default, subclasses can be overridden to implement specific filtering logic
        return None
        
    async def delete_by_ids(self, doc_ids: List[str]) -> bool:
        """Delete documents based on ID

Args:
doc_ids: Document ID List

Returns:
Was it successful?"""
        if not self.is_initialized:
            await self.initialize()
            
        try:
            await self.vector_store.delete_by_ids(doc_ids)
            return True
        except Exception as e:
            logger.error(f"删除文档时出错: {e}")
            return False
            
    async def close(self):
        """Shut down the service and release resources"""
        if self.vector_store:
            await self.vector_store.close()
            
    def get_stats(self) -> Dict[str, Any]:
        """Obtain statistical information

Returns:
Statistical information dictionary"""
        if not hasattr(self.vector_store, 'get_stats'):
            return {
                "error": "Vector storage does not support obtaining statistics"
            }
            
        stats = self.vector_store.get_stats()
        
        # Add embedded model information
        stats.update({
            "embedding_model": self.model_name,
            "model_short_name": self.model_short_name,
            "table_name": self.table_name,
            "collection_name": self.collection_name
        })
        
        return stats 