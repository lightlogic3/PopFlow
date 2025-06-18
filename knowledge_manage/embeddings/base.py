from typing import List


class EmbeddingEngine:
    """嵌入引擎的基类"""

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """将文本列表转换为嵌入向量列表"""
        raise NotImplementedError("子类必须实现embed_documents方法")

    def embed_query(self, text: str) -> List[float]:
        """将单个查询文本转换为嵌入向量"""
        raise NotImplementedError("子类必须实现embed_query方法")


    async def async_embed_documents(self, texts: List[str]) -> List[List[float]]:
        """将文本列表转换为嵌入向量列表"""
        return self.embed_documents(texts)

    async def async_embed_query(self, text: str) -> List[float]:
        """将单个查询文本转换为嵌入向量"""
        return self.embed_query(text)