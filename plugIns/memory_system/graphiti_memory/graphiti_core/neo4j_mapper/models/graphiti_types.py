
from neo4j import AsyncDriver
from pydantic import BaseModel, ConfigDict

from knowledge_manage.embeddings.base import EmbeddingEngine
from knowledge_manage.rerank_model import BaseRankingModel
from plugIns.memory_system.graphiti_memory.graphiti_core.llm_client import LLMClient


class GraphitiClients(BaseModel):
    driver: AsyncDriver
    llm_client: LLMClient
    embedder: EmbeddingEngine
    cross_encoder: BaseRankingModel
    model_config = ConfigDict(arbitrary_types_allowed=True)
