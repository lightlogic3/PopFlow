import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Optional

from knowledge_api.framework.redis.cache_manager import CacheManager
from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.llm_model_config.base import (
    LLMModelConfigCreate,
    LLMModelConfigUpdate,
    LLMModelConfigResponse,
    LLMModelConfig,
    UpdateTokensRequest
)
from knowledge_api.mapper.llm_model_config.crud import LLMModelConfigCRUD
from knowledge_api.mapper.llm_provider_config.crud import LLMProviderConfigCRUD
from knowledge_api.utils.volcano_api import VolcanoAPIClient

llm_model_router = APIRouter(prefix="/llm-model-config", tags=["LLM model configuration"])


@llm_model_router.post("/", response_model=LLMModelConfigResponse)
async def create_model_config(
    config: LLMModelConfigCreate,
    db: Session = Depends(get_session)
) -> LLMModelConfig:
    """Create model configuration"""
    # Verify that the supplier exists
    provider_crud = LLMProviderConfigCRUD(db)
    provider = await provider_crud.get_by_id(config_id=config.provider_id)
    if not provider:
        raise HTTPException(status_code=400, detail="Supplier does not exist")
        
    # If no provider_sign is provided, obtain it from the supplier
    if not config.provider_sign and provider.provider_sign:
        config.provider_sign = provider.provider_sign

    # Verify that the model ID already exists under the vendor
    model_crud = LLMModelConfigCRUD(db)
    existing_model = await model_crud.get_by_provider_and_model(
        provider_id=config.provider_id, model_id=config.model_id
    )
    if existing_model:
        raise HTTPException(status_code=400, detail="The same model ID already exists under this vendor.")

    return await model_crud.create(obj_in=config)


@llm_model_router.get("/{config_id}", response_model=LLMModelConfigResponse)
async def get_model_config(
    config_id: int,
    db: Session = Depends(get_session)
) -> LLMModelConfig:
    """Get a single model configuration"""
    crud = LLMModelConfigCRUD(db)
    config = await crud.get_by_id(id=config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Model configuration does not exist")
    return config


@llm_model_router.get("/by-provider/{provider_id}", response_model=List[LLMModelConfigResponse])
async def get_models_by_provider(
    provider_id: int,
    db: Session = Depends(get_session)
) -> List[LLMModelConfig]:
    """Get the model configuration list by vendor ID"""
    # Verify that the supplier exists
    provider_crud = LLMProviderConfigCRUD(db)
    provider = await provider_crud.get_by_id(config_id=provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Supplier does not exist")
    
    crud = LLMModelConfigCRUD(db)
    return await crud.get_by_provider_id(provider_id=provider_id)


@llm_model_router.get("/by-type/{model_type}", response_model=List[LLMModelConfigResponse])
async def get_models_by_type(
    model_type: str,
    db: Session = Depends(get_session)
) -> List[LLMModelConfig]:
    """Get the model configuration list by model type"""
    crud = LLMModelConfigCRUD(db)
    return await crud.get_by_model_type(model_type=model_type)


@llm_model_router.get("/by-provider-and-model/", response_model=Optional[LLMModelConfigResponse])
async def get_model_by_provider_and_model_id(
    provider_id: int = Query(..., description="Supplier ID"),
    model_id: str = Query(..., description="Model ID"),
    db: Session = Depends(get_session)
) -> Optional[LLMModelConfig]:
    """Get configuration based on vendor ID and model ID"""
    crud = LLMModelConfigCRUD(db)
    config = await crud.get_by_provider_and_model(provider_id=provider_id, model_id=model_id)
    if not config:
        raise HTTPException(status_code=404, detail="Model configuration does not exist")
    return config


@llm_model_router.get("/", response_model=List[LLMModelConfigResponse])
async def list_model_configs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_session)
) -> List[LLMModelConfig]:
    """Get the model configuration list"""
    crud = LLMModelConfigCRUD(db)
    return await crud.get_all(skip=skip, limit=limit)


@llm_model_router.get("/active/list", response_model=List[LLMModelConfigResponse])
async def list_active_models(
    db: Session = Depends(get_session)
) -> List[LLMModelConfig]:
    """Get model configurations for all enabled states"""
    crud = LLMModelConfigCRUD(db)
    return await crud.get_active_models()


@llm_model_router.put("/{config_id}", response_model=LLMModelConfigResponse)
async def update_model_config(
    config_id: int,
    config_update: LLMModelConfigUpdate,
    db: Session = Depends(get_session)
) -> LLMModelConfig:
    """Update model configuration"""
    crud = LLMModelConfigCRUD(db)
    
    # Get the current configuration to check if it exists
    current_config = await crud.get_by_id(id=config_id)
    if not current_config:
        raise HTTPException(status_code=404, detail="Model configuration does not exist")
    
    # If provider_id is updated but not provider_sign, get provider_sign from the vendor
    if config_update.provider_id is not None and config_update.provider_sign is None:
        provider_crud = LLMProviderConfigCRUD(db)
        provider = await provider_crud.get_by_id(config_id=config_update.provider_id)
        if provider:
            config_update.provider_sign = provider.provider_sign
    
    # If the update contains provider_id and model_id, check for conflicts with other configurations
    if config_update.provider_id is not None and config_update.model_id is not None:
        existing_config = await crud.get_by_provider_and_model(
            provider_id=config_update.provider_id, 
            model_id=config_update.model_id
        )
        if existing_config and existing_config.id != config_id:
            raise HTTPException(status_code=400, detail="The same model ID already exists under this vendor.")
    
    # If only updating provider_id, check if using the current model_id conflicts
    elif config_update.provider_id is not None:
        existing_config = await crud.get_by_provider_and_model(
            provider_id=config_update.provider_id, 
            model_id=current_config.model_id
        )
        if existing_config and existing_config.id != config_id:
            raise HTTPException(status_code=400, detail="The same model ID already exists under this vendor.")
    
    # If only updating model_id, check if using the current provider_id conflicts
    elif config_update.model_id is not None:
        existing_config = await crud.get_by_provider_and_model(
            provider_id=current_config.provider_id, 
            model_id=config_update.model_id
        )
        if existing_config and existing_config.id != config_id:
            raise HTTPException(status_code=400, detail="The same model ID already exists under this vendor.")
    
    return await crud.update(config_id, config_update)


@llm_model_router.patch("/{config_id}/status", response_model=LLMModelConfigResponse)
async def update_model_status(
    config_id: int,
    status: int = Query(..., description="Status: 1-enabled 0-disabled"),
    db: Session = Depends(get_session)
) -> LLMModelConfig:
    """Modify model configuration status"""
    if status not in [0, 1]:
        raise HTTPException(status_code=400, detail="The status value is invalid and must be 0 or 1.")
    
    crud = LLMModelConfigCRUD(db)
    config_update = LLMModelConfigUpdate(status=status)
    config = await crud.update(config_id, config_update)
    if not config:
        raise HTTPException(status_code=404, detail="Model configuration does not exist")
    return config


@llm_model_router.post("/{config_id}/update-tokens", response_model=LLMModelConfigResponse)
async def update_model_tokens(
    config_id: int,
    token_data: UpdateTokensRequest,
    db: Session = Depends(get_session)
) -> LLMModelConfig:
    """Update model token usage and synchronize total price to vendor table

Description:
The number of input and output tokens is added to the total amount of the model
The system will automatically calculate the cost of this use and update it to the supplier's total price"""
    crud = LLMModelConfigCRUD(db)
    updated_config = await crud.update_tokens(model_id=config_id, token_data=token_data)
    if not updated_config:
        raise HTTPException(status_code=404, detail="Model configuration does not exist")
    return updated_config


@llm_model_router.post("/provider/{provider_id}/recalculate-price", response_model=float)
async def recalculate_provider_price(
    provider_id: int,
    db: Session = Depends(get_session)
) -> float:
    """Recalculate the total price of the supplier

Description:
- Recalculate the total price based on token usage for all models under the vendor
- Returns the updated total price value"""
    # Verify that the supplier exists
    provider_crud = LLMProviderConfigCRUD(db)
    provider = await provider_crud.get_by_id(config_id=provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Supplier does not exist")
    
    model_crud = LLMModelConfigCRUD(db)
    total_price = await model_crud.calculate_provider_total_price(provider_id=provider_id)
    
    # Convert to floating point number return
    return float(total_price)


@llm_model_router.delete("/{config_id}", response_model=bool)
async def delete_model_config(
    config_id: int,
    db: Session = Depends(get_session)
) -> bool:
    """Delete model configuration"""
    crud = LLMModelConfigCRUD(db)
    success = await crud.delete(id=config_id)
    if not success:
        raise HTTPException(status_code=404, detail="Model configuration does not exist")
    return True


async def get_volcano_client():
    data=await CacheManager().system_config_cache.get_value("BYTE_DANCE_TTS_CONFIG")
    configJson = json.loads(data)
    ak = configJson.get("ak","")
    sk = configJson.get("sk","")
    return VolcanoAPIClient(
        access_key_id=str(ak),
        secret_access_key=sk,
    )

@llm_model_router.get("/getList/models")
async def list_models(
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=100),
        client: VolcanoAPIClient = Depends(get_volcano_client)):
    # asynchronous call API
    response = await client.request_async(
        action="ListFoundationModels",
        payload={
            "PageNumber": skip,
            "PageSize": limit,
        }
    )
    return response

@llm_model_router.get("/getList/model_versions")
async def list_models(
        model_name:str,
        client: VolcanoAPIClient = Depends(get_volcano_client)):
    # asynchronous call API
    response = await client.request_async(
        action="ListFoundationModelVersions",
        payload={
            "PageNumber": 1,
            "PageSize": 100,
            "FoundationModelName": model_name
        }
    )
    return response