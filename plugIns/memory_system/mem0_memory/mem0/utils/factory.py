import importlib
from typing import Optional, Dict, Any, Type
import logging

from plugIns.memory_system.mem0_memory.mem0.configs.embeddings.base import BaseEmbedderConfig
from plugIns.memory_system.mem0_memory.mem0.configs.llms.base import BaseLlmConfig



logger = logging.getLogger(__name__)


def load_class(class_type):
    # 使用 rsplit 从右侧开始分割字符串，确保将模块路径和类名正确分离
    module_path, class_name = class_type.rsplit(".", 1)
    
    # 动态导入模块
    module = importlib.import_module(module_path)
    
    # 返回模块中的类对象
    return getattr(module, class_name)


class LlmFactory:
    provider_to_class = {
        "doubao": "plugIns.memory_system.mem0_memory.mem0.llms.doubao.DoubaoLLM",
    }

    @classmethod
    def create(cls, provider_name, config):
        class_type = cls.provider_to_class.get(provider_name)
        if class_type:
            llm_instance = load_class(class_type)
            base_config = BaseLlmConfig(**config)
            return llm_instance(base_config)
        else:
            raise ValueError(f"Unsupported Llm provider: {provider_name}")


class EmbedderFactory:
    provider_to_class = {
        "huggingface": "plugIns.memory_system.mem0_memory.mem0.embeddings.huggingface.HuggingFaceEmbedding",
    }

    @classmethod
    def create(cls, provider_name, config, vector_config: Optional[dict]):
        class_type = cls.provider_to_class.get(provider_name)
        if class_type:
            embedder_instance = load_class(class_type)
            base_config = BaseEmbedderConfig(**config)
            return embedder_instance(base_config)
        else:
            raise ValueError(f"Unsupported Embedder provider: {provider_name}")


class VectorStoreFactory:
    provider_to_class = {
        "chroma": "plugIns.memory_system.mem0_memory.mem0.vector_stores.chroma.ChromaDB",
        "dashvector": "plugIns.memory_system.mem0_memory.mem0.vector_stores.dashvector.DashVectorAdapter",
    }

    @classmethod
    def create(cls, provider_name, config):
        """
        创建向量存储实例的同步方法
        
        Args:
            provider_name: 向量存储提供者名称
            config: 配置参数
            
        Returns:
            创建的向量存储实例
        """
        class_type = cls.provider_to_class.get(provider_name)
        if class_type:
            if not isinstance(config, dict):
                config = config.model_dump()
            vector_store_instance = load_class(class_type)
            return vector_store_instance(**config)
        else:
            raise ValueError(f"Unsupported VectorStore provider: {provider_name}")

    @classmethod
    async def reset(cls, instance):
        """
        重置向量存储实例的异步方法
        
        Args:
            instance: 要重置的向量存储实例
            
        Returns:
            重置后的向量存储实例
        """
        await instance.reset()
        return instance
        
