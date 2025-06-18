from typing import List
from openai import OpenAI
from knowledge_manage.embeddings.base import EmbeddingEngine


class OpenAIEmbeddings(EmbeddingEngine):
    """使用OpenAI API的嵌入引擎"""

    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        """
        初始化OpenAI嵌入引擎

        Args:
            api_key: OpenAI API密钥
            model: 使用的嵌入模型名称
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """将文本列表转换为嵌入向量列表"""
        if not texts:
            return []

        try:
            response = self.client.embeddings.create(
                input=texts,
                model=self.model
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            print(f"获取嵌入向量时出错: {e}")
            return []

    def embed_query(self, text: str) -> List[float]:
        """将单个查询文本转换为嵌入向量"""
        result = self.embed_documents([text])
        return result[0] if result else []