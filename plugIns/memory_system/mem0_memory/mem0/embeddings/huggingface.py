import logging
from typing import Literal, Optional

from openai import OpenAI
from sentence_transformers import SentenceTransformer

from plugIns.memory_system.mem0_memory.mem0.configs.embeddings.base import BaseEmbedderConfig
from plugIns.memory_system.mem0_memory.mem0.embeddings.base import EmbeddingBase
from knowledge_manage.embeddings.factory import EmbeddingFactory

logging.getLogger("transformers").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.WARNING)

class HuggingFaceEmbedding(EmbeddingBase):
    def __init__(self, config: Optional[BaseEmbedderConfig] = None):
        super().__init__(config)
        self.config.model = self.config.model or "BAAI/bge-small-zh-v1.5"
        self.model =EmbeddingFactory.create_embedding(
            embedding_type="huggingface",
            model_name=self.config.model,
        )

    def embed(self, text, memory_action: Optional[Literal["add", "search", "update"]] = None):
        """
        Get the embedding for the given text using Hugging Face.

        Args:
            text (str): The text to embed.
            memory_action (optional): The type of embedding to use. Must be one of "add", "search", or "update". Defaults to None.
        Returns:
            list: The embedding vector.
        """
        return self.model.embed_query(text)
