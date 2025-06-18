from typing import Any, ClassVar, Dict, Optional

from pydantic import BaseModel, Field, model_validator

class DashVectorConfig(BaseModel):
    """DashVector 向量存储配置"""
    collection_name: str = "long_term_memory_user_m0_test_v1"
    api_key: Optional[str] = None
    endpoint: Optional[str] = None
    dimension: int = 512
    metric: str = "cosine"
    dtype: str = "FLOAT"
