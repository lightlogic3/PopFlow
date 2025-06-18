from sqlmodel import Session, select, update, and_, or_
from typing import Optional, List, Dict, Any
from decimal import Decimal

from knowledge_api.mapper.base_crud import BaseCRUD
from knowledge_api.mapper.llm_model_config.base import (
    LLMModelConfigCreate,
    LLMModelConfig,
    LLMModelConfigUpdate,
    UpdateTokensRequest,
    LLMModelConfigResponse
)
from knowledge_api.mapper.llm_provider_config.base import LLMProviderConfig


class LLMModelConfigCRUD(BaseCRUD[LLMModelConfig, LLMModelConfigCreate, LLMModelConfigUpdate, Dict[str, Any], LLMModelConfigResponse, int]):
    """LLM model configuration CRUD operation

Provides create, read, update, delete, and query capabilities for model configurations
Including special business functions such as token statistics and price calculation"""

    def __init__(self, db: Session):
        """Initialize LLM model configuration CRUD operation

Args:
DB: database session"""
        super().__init__(db, LLMModelConfig)

    async def get_by_provider_and_model(self, provider_id: int, model_id: str) -> Optional[LLMModelConfig]:
        """Get configuration based on vendor ID and model ID

Args:
provider_id: Supplier ID
model_id: Model ID

Returns:
Optional [LLMModelConfig]: Model configuration found or None"""
        records = await self.get_all(filters={"provider_id": provider_id, "model_id": model_id}, limit=1)
        return records[0] if records else None

    async def get_by_provider_id(self, provider_id: int) -> List[LLMModelConfig]:
        """Get all model configurations by vendor ID

Args:
provider_id: Supplier ID

Returns:
List [LLMModelConfig]: Model configuration list"""
        return await self.get_all(filters={"provider_id": provider_id})

    async def get_by_model_type(self, model_type: str) -> List[LLMModelConfig]:
        """Get all model configurations by model type

Args:
model_type: Model types such as chat, multimodal, etc

Returns:
List [LLMModelConfig]: Model configuration list"""
        return await self.get_all(filters={"model_type": model_type})

    async def get_active_models(self) -> List[LLMModelConfig]:
        """Get model configurations for all enabled states

Returns:
List [LLMModelConfig]: List of model configurations enabled"""
        return await self.get_all(filters={"status": 1})
    
    async def update_tokens(self, model_id: int, token_data: UpdateTokensRequest) -> Optional[LLMModelConfig]:
        """Update model token usage and synchronize total price to vendor table

Args:
model_id: Model ID
token_data: Request object containing the number of input and output tokens

Returns:
Optional [LLMModelConfig]: updated model configuration or None"""
        # Get model configuration
        model_config = await self.get_by_id(model_id)
        if not model_config:
            return None
            
        # Update the token count of the model
        model_config.total_input_tokens += token_data.input_tokens
        model_config.total_output_tokens += token_data.output_tokens
        
        # Calculate the price for this use
        input_cost = (Decimal(token_data.input_tokens) / 1000) * model_config.input_price
        output_cost = (Decimal(token_data.output_tokens) / 1000) * model_config.output_price
        total_cost = input_cost + output_cost
        
        # Save model updates
        self.db.add(model_config)
        self.db.commit()
        self.db.refresh(model_config)
        
        # Update the total supplier price
        provider = self.db.get(LLMProviderConfig, model_config.provider_id)
        if provider:
            provider.total_price += total_cost
            self.db.add(provider)
            self.db.commit()
        
        return model_config
    
    async def calculate_provider_total_price(self, provider_id: int) -> Decimal:
        """Recalculate and update the total price of the supplier

Args:
provider_id: Supplier ID

Returns:
Decimal: Updated total price"""
        # Get all models under the supplier
        models = await self.get_by_provider_id(provider_id=provider_id)
        
        # Calculate the total price
        total_price = Decimal(0)
        for model in models:
            input_cost = (Decimal(model.total_input_tokens) / 1000) * model.input_price
            output_cost = (Decimal(model.total_output_tokens) / 1000) * model.output_price
            total_price += input_cost + output_cost
        
        # Update the total supplier price
        provider = self.db.get(LLMProviderConfig, provider_id)
        if provider:
            provider.total_price = total_price
            self.db.add(provider)
            self.db.commit()
            
        return total_price

    async def delete_by_provider_id(self, provider_id):
        """Delete all model configurations under the specified vendor

Args:
provider_id: Supplier ID

Returns:
None"""
        # Get all model configurations
        models = await self.get_by_provider_id(provider_id)

        # Delete each model configuration
        for model in models:
            await self.delete(id=model.id)
