from typing import Optional, Dict, Any

from knowledge_api.utils.log_config import get_logger
from knowledge_manage.embeddings.base import EmbeddingEngine
from knowledge_manage.embeddings.huggingface_embeddings import HuggingFaceEmbeddings
from knowledge_manage.embeddings.open_ai_embeddings import OpenAIEmbeddings

logger = get_logger()

class EmbeddingFactory:
    """
    嵌入模型工厂类，用于创建不同的嵌入模型实例
    """
    # 缓存已创建的嵌入模型实例
    _instances: Dict[str, EmbeddingEngine] = {}

    @classmethod
    def create_embedding(cls,
                         embedding_type: str="huggingface",
                         model_name: str = None,
                         device: str = "cpu",
                         **kwargs) -> EmbeddingEngine:
        """
        创建嵌入模型实例

        Args:
            embedding_type: 嵌入模型类型，支持 'huggingface', 'openai' 等
            model_name: 模型名称
            device: 设备类型，'cpu' 或 'cuda'
            **kwargs: 其他参数

        Returns:
            嵌入模型实例
        """
        # 创建缓存键
        cache_key = f"{embedding_type}:{model_name}:{device}"

        # 检查缓存
        if cache_key in cls._instances:
            logger.info(f"使用缓存的嵌入模型: {cache_key}")
            return cls._instances[cache_key]

        if embedding_type.lower() == "huggingface":
            embedding = HuggingFaceEmbeddings.get_instance(
                model_name=model_name or "./model/models--BAAI--bge-small-zh-v1.5",
                device=device
            )
        elif embedding_type.lower() == "openai":
            embedding = OpenAIEmbeddings(
                model_name=model_name or "text-embedding-3-small",
                **kwargs
            )
        else:
            raise ValueError(f"不支持的嵌入模型类型: {embedding_type}")

        # 缓存实例
        cls._instances[cache_key] = embedding
        return embedding

    @classmethod
    def get_available_models(cls) -> Dict[str, Any]:
        """
        获取可用的嵌入模型列表

        Returns:
            可用模型信息
        """
        return {
            "huggingface": {
                "models": ["BAAI/bge-small-zh-v1.5", "BAAI/bge-large-zh-v1.5"],
                "devices": ["cpu", "cuda"]
            },
            "openai": {
                "models": ["text-embedding-3-small", "text-embedding-3-large"]
            }
        }