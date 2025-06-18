from sqlmodel import Session, select, desc
from typing import Optional, List, Dict, Any

from knowledge_api.mapper.base_crud import BaseCRUD
from knowledge_api.mapper.llm_provider_config.base import (
    LLMProviderConfig, 
    LLMProviderConfigCreate,
    LLMProviderConfigUpdate,
    LLMProviderConfigResponse
)


class LLMProviderConfigCRUD(BaseCRUD[LLMProviderConfig, LLMProviderConfigCreate, LLMProviderConfigUpdate, Dict[str, Any], LLMProviderConfigResponse, int]):
    """LLM Provider Configuring CRUD Operations"""

    def __init__(self, db: Session):
        """Initialize LLM provider configuration CRUD operation

Args:
DB: database session"""
        super().__init__(db, LLMProviderConfig)

    # Backwards compatible with primitive API call methods
    async def get_by_id(self, id=None, config_id=None) -> Optional[LLMProviderConfig]:
        """Get provider configuration by ID

Args:
ID: record ID
config_id: Record ID (compatible with old API)

Returns:
Optional [LLMProviderConfig]: Configuration found or None"""
        # Using config_id as Alternative Parameters
        _id = id if id is not None else config_id
        return await super().get_by_id(_id)

    async def get_by_provider_name(self, provider_name: str) -> Optional[LLMProviderConfig]:
        """Get configuration by provider name

Args:
provider_name: Provider Name

Returns:
Optional [LLMProviderConfig]: Configuration found or None"""
        records = await self.get_all(filters={"provider_name": provider_name}, limit=1)
        return records[0] if records else None

    async def get_active_providers(self) -> List[LLMProviderConfig]:
        """Get provider configurations for all enabled states

Returns:
List [LLMProviderConfig]: List of provider configurations enabled"""
        return await self.get_all(filters={"status": 1}, limit=1000)
        
    async def get_by_name(self, provider_name: str) -> Optional[LLMProviderConfig]:
        """Get configuration by provider name

Args:
provider_name: Provider Name

Returns:
Optional [LLMProviderConfig]: Configuration found or None"""
        return await self.get_by_provider_name(provider_name)
        
    async def get_by_price_desc(self, skip: int = 0, limit: int = 100) -> List[LLMProviderConfig]:
        """Get provider profiles in descending order of total price

Args:
Skip: skip the number of records
Limit: limit the number of records

Returns:
List [LLMProviderConfig]: Provider configuration list"""
        return await self.get_all(skip=skip, limit=limit, order_by="total_price", order_desc=True) 