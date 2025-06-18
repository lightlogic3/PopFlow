import os
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from plugIns.memory_system.mem0_memory.mem0.embeddings.configs import EmbedderConfig
from plugIns.memory_system.mem0_memory.mem0.graphs.configs import GraphStoreConfig
from plugIns.memory_system.mem0_memory.mem0.llms.configs import LlmConfig
from plugIns.memory_system.mem0_memory.mem0.vector_stores.configs import VectorStoreConfig

# Set up the directory path
home_dir = os.path.expanduser("~")
mem0_dir = os.environ.get("MEM0_DIR") or os.path.join(home_dir, ".mem0")


class MemoryItem(BaseModel):
    id: str = Field(..., description="文本数据的唯一标识符")
    memory: str = Field(
        ..., description="从文本数据推导出的记忆"
    )  # TODO After prompt changes from platform, update this
    hash: Optional[str] = Field(None, description="记忆的哈希值")
    # The metadata value can be anything and not just string. Fix it
    metadata: Optional[Dict[str, Any]] = Field(None, description="文本数据的附加元数据")
    score: Optional[float] = Field(None, description="与文本数据关联的分数")
    created_at: Optional[str] = Field(None, description="记忆创建的时间戳")
    updated_at: Optional[str] = Field(None, description="记忆更新的时间戳")


class MemoryConfig(BaseModel):
    vector_store: VectorStoreConfig = Field(
        description="向量存储的配置",
        default_factory=VectorStoreConfig,
    )
    llm: LlmConfig = Field(
        description="语言模型的配置",
        default_factory=LlmConfig,
    )
    embedder: EmbedderConfig = Field(
        description="嵌入模型的配置",
        default_factory=EmbedderConfig,
    )
    history_db_path: str = Field(
        description="历史数据库的路径",
        default=os.path.join(mem0_dir, "history.db"),
    )
    graph_store: GraphStoreConfig = Field(
        description="图的配置",
        default_factory=GraphStoreConfig,
    )
    version: str = Field(
        description="API的版本",
        default="v1.1",
    )
    custom_fact_extraction_prompt: Optional[str] = Field(
        description="事实提取的自定义提示",
        default=None,
    )
    custom_update_memory_prompt: Optional[str] = Field(
        description="更新记忆的自定义提示",
        default=None,
    )


class AzureConfig(BaseModel):
    """
    Azure的配置设置。

    参数:
        api_key (str): 用于Azure服务认证的API密钥。
        azure_deployment (str): Azure部署的名称。
        azure_endpoint (str): Azure服务的端点URL。
        api_version (str): 正在使用的Azure API版本。
        default_headers (Dict[str, str]): 在请求Azure API时包含的头信息。
    """

    api_key: str = Field(
        description="用于Azure服务认证的API密钥。",
        default=None,
    )
    azure_deployment: str = Field(description="Azure部署的名称。", default=None)
    azure_endpoint: str = Field(description="Azure服务的端点URL。", default=None)
    api_version: str = Field(description="正在使用的Azure API版本。", default=None)
    default_headers: Optional[Dict[str, str]] = Field(
        description="在请求Azure API时包含的头信息。", default=None
    )
