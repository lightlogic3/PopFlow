# embeddings/openai_langchain_adapter.py
from langchain_core.embeddings import Embeddings

from knowledge_manage.embeddings.open_ai_embeddings import OpenAIEmbeddings


class OpenAILangChainAdapter(Embeddings):
    """
    将OpenAIEmbeddings适配为LangChain格式的嵌入函数
    """

    def __init__(self, openai_embeddings: OpenAIEmbeddings):
        """
        初始化适配器

        Args:
            openai_embeddings: OpenAIEmbeddings实例
        """
        self.openai_embeddings = openai_embeddings

    def embed_documents(self, texts):
        """
        实现LangChain的embed_documents方法
        """
        return self.openai_embeddings.embed_documents(texts)

    def embed_query(self, text):
        """
        实现LangChain的embed_query方法
        """
        return self.openai_embeddings.embed_query(text)