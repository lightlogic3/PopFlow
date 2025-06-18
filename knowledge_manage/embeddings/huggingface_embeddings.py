# embeddings/huggingface_embeddings.py
from typing import List, Optional
from langchain_community.embeddings import HuggingFaceBgeEmbeddings

from knowledge_api.utils.log_config import get_logger
from knowledge_manage.embeddings.base import EmbeddingEngine

logger=get_logger()
class HuggingFaceEmbeddings(EmbeddingEngine):
    """使用HuggingFace模型的嵌入引擎（单例模式）"""

    # 单例实例
    _instance: Optional['HuggingFaceEmbeddings'] = None

    def __new__(cls, *args, **kwargs):
        """确保只创建一个实例"""
        if cls._instance is None:
            cls._instance = super(HuggingFaceEmbeddings, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_name: str = "BAAI/bge-small-zh-v1.5", device: str = "cpu"):
        """
        初始化HuggingFace嵌入引擎（只在首次创建实例时执行）

        Args:
            model_name: HuggingFace模型名称
            device: 运行设备，可以是'cpu'或'cuda'
        """
        # 确保初始化只执行一次
        if getattr(self, "_initialized", False):
            return

        self.model_name = model_name
        self.device = device

        # 初始化嵌入模型
        logger.info(f"初始化HuggingFace嵌入模型: {model_name} 在 {device} 上")
        self.embedder = HuggingFaceBgeEmbeddings(
            model_name=model_name,
            model_kwargs={"device": device}
        )

        self._initialized = True

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """将文本列表转换为嵌入向量列表"""
        if not texts:
            return []

        try:
            embeddings = self.embedder.embed_documents(texts)
            return embeddings
        except Exception as e:
            logger.error(f"获取嵌入向量时出错: {e}")
            return []

    def embed_query(self, text: str) -> List[float]:
        """将单个查询文本转换为嵌入向量"""
        try:
            return self.embedder.embed_query(text)
        except Exception as e:
            logger.error(f"获取查询嵌入时出错: {e}")
            return []

    @classmethod
    def get_instance(cls, model_name: str = "BAAI/bge-small-zh-v1.5", device: str = "cpu") -> 'HuggingFaceEmbeddings':
        """获取单例实例的便捷方法"""
        return cls(model_name, device)