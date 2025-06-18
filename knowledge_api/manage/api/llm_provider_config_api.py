from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Dict, Any

from knowledge_api.framework.database.database import get_session
from knowledge_api.framework.redis.cache_manager import CacheManager
from knowledge_api.mapper.llm_provider_config.base import (
    LLMProviderConfigCreate,
    LLMProviderConfigUpdate,
    LLMProviderConfigResponse,
    LLMProviderConfig
)
from knowledge_api.mapper.llm_provider_config.crud import LLMProviderConfigCRUD
from knowledge_api.mapper.llm_model_config.crud import LLMModelConfigCRUD

llm_config_router = APIRouter(prefix="/llm-provider-config", tags=["LLM Provider Configuration"])


@llm_config_router.post("/", response_model=LLMProviderConfigResponse)
async def create_provider_config(
    config: LLMProviderConfigCreate,
    db: Session = Depends(get_session)
) -> LLMProviderConfig:
    """Create Provider Configuration"""
    crud = LLMProviderConfigCRUD(db)
    
    # Check if the provider name already exists
    existing_config = await crud.get_by_provider_name(provider_name=config.provider_name)
    if existing_config:
        raise HTTPException(status_code=400, detail="Provider name already exists")
    
    return await crud.create(obj_in=config)


@llm_config_router.get("/{config_id}", response_model=LLMProviderConfigResponse)
async def get_provider_config(
    config_id: int,
    db: Session = Depends(get_session)
) -> LLMProviderConfig:
    """Get a single provider configuration"""
    crud = LLMProviderConfigCRUD(db)
    config = await crud.get_by_id(config_id=config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Provider configuration does not exist")
    return config


@llm_config_router.get("/by-name/{provider_name}", response_model=LLMProviderConfigResponse)
async def get_provider_config_by_name(
    provider_name: str,
    db: Session = Depends(get_session)
) -> LLMProviderConfig:
    """Get configuration by provider name"""
    crud = LLMProviderConfigCRUD(db)
    config = await crud.get_by_provider_name(provider_name=provider_name)
    if not config:
        raise HTTPException(status_code=404, detail="Provider configuration does not exist")
    return config


@llm_config_router.get("/", response_model=List[LLMProviderConfigResponse])
async def list_provider_configs(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_session)
) -> List[LLMProviderConfig]:
    """Get a list of provider configurations"""
    crud = LLMProviderConfigCRUD(db)
    return await crud.get_all(skip=skip, limit=limit)


@llm_config_router.get("/active/list", response_model=List[LLMProviderConfigResponse])
async def list_active_providers(
    db: Session = Depends(get_session)
) -> List[LLMProviderConfig]:
    """Get provider configurations for all enabled states"""
    crud = LLMProviderConfigCRUD(db)
    return await crud.get_active_providers()


@llm_config_router.put("/{config_id}", response_model=LLMProviderConfigResponse)
async def update_provider_config(
    config_id: int,
    config_update: LLMProviderConfigUpdate,
    db: Session = Depends(get_session)
) -> LLMProviderConfig:
    """Update Provider Configuration"""
    crud = LLMProviderConfigCRUD(db)
    
    # If the update contains the provider name, check if it conflicts with other configurations
    if config_update.provider_name:
        existing_config = await crud.get_by_provider_name(provider_name=config_update.provider_name)
        if existing_config and existing_config.id != config_id:
            raise HTTPException(status_code=400, detail="Provider name already exists")
    
    config = await crud.update(config_id, config_update)

    # update cache
    cache_manager = CacheManager()
    await cache_manager.llm_provider_cache.update(config,crud)
    if not config:
        raise HTTPException(status_code=404, detail="Provider configuration does not exist")
    return config


@llm_config_router.patch("/{config_id}/status", response_model=LLMProviderConfigResponse)
async def update_provider_status(
    config_id: int,
    status: int = Query(..., description="Status: 1-enabled 0-disabled"),
    db: Session = Depends(get_session)
) -> LLMProviderConfig:
    """Modify Provider Configuration Status"""
    if status not in [0, 1]:
        raise HTTPException(status_code=400, detail="The status value is invalid and must be 0 or 1.")
    
    crud = LLMProviderConfigCRUD(db)
    config_update = LLMProviderConfigUpdate(status=status)
    config = await crud.update(config_id, config_update)
    if not config:
        raise HTTPException(status_code=404, detail="Provider configuration does not exist")
    return config


@llm_config_router.delete("/{config_id}", response_model=bool)
async def delete_provider_config(
    config_id: int,
    db: Session = Depends(get_session)
) -> bool:
    """Delete Provider Configuration"""
    crud = LLMProviderConfigCRUD(db)
    success = await crud.delete(id=config_id)
    # Delete submodel configuration
    model_crud = LLMModelConfigCRUD(db)
    await model_crud.delete_by_provider_id(provider_id=config_id)
    if not success:
        raise HTTPException(status_code=404, detail="Provider configuration does not exist")
    return True


@llm_config_router.get("/hierarchy/all", response_model=List[Dict[str, Any]])
async def get_providers_with_models(
    db: Session = Depends(get_session)
) -> List[Dict[str, Any]]:
    """Get the hierarchy of all providers and their submodels"""
    provider_crud = LLMProviderConfigCRUD(db)
    model_crud = LLMModelConfigCRUD(db)
    
    # Acquire all providers
    providers = await provider_crud.get_all(skip=0, limit=1000)
    result = []
    
    # Build a hierarchy
    for provider in providers:
        # Get all models from this provider
        models = await model_crud.get_by_provider_id(provider_id=provider.id)
        
        # build provider information
        provider_info = {
            "id": provider.id,
            "provider_name": provider.provider_name,
            "provider_sign": provider.provider_sign,
            "model_name": provider.model_name,
            "api_url": provider.api_url,
            "status": provider.status,
            "remark": provider.remark,
            "models": [
                {
                    "id": model.id,
                    "model_name": model.model_name,
                    "model_id": model.model_id,
                    "model_type": model.model_type,
                    "provider_sign": model.provider_sign,
                    "status": model.status,
                    "capabilities": model.capabilities,
                    "introduction": model.introduction,
                    "icon_url": model.icon_url,
                    "input_price": float(model.input_price) if model.input_price else 0,
                    "output_price": float(model.output_price) if model.output_price else 0,
                }
                for model in models
            ]
        }
        
        result.append(provider_info)
    
    return result


@llm_config_router.get("/hierarchy/active", response_model=List[Dict[str, Any]])
async def get_active_providers_with_models(
    db: Session = Depends(get_session)
) -> List[Dict[str, Any]]:
    """Gets the hierarchy of all enabled state providers and their enabled state submodels"""
    provider_crud = LLMProviderConfigCRUD(db)
    model_crud = LLMModelConfigCRUD(db)
    
    # Get all enabled providers
    providers = await provider_crud.get_active_providers()
    result = []
    
    # Build a hierarchy
    for provider in providers:
        # Get all models from this provider
        models = await model_crud.get_by_provider_id(provider_id=provider.id)
        
        # Keep only models enabled
        active_models = [model for model in models if model.status == 1]
        
        # build provider information
        provider_info = {
            "id": provider.id,
            "provider_name": provider.provider_name,
            "provider_sign": provider.provider_sign,
            "model_name": provider.model_name,
            "api_url": provider.api_url,
            "status": provider.status,
            "remark": provider.remark,
            "models": [
                {
                    "id": model.id,
                    "model_name": model.model_name,
                    "model_id": model.model_id,
                    "model_type": model.model_type,
                    "provider_sign": model.provider_sign,
                    "status": model.status,
                    "capabilities": model.capabilities,
                    "introduction": model.introduction,
                    "icon_url": model.icon_url,
                    "input_price": float(model.input_price) if model.input_price else 0,
                    "output_price": float(model.output_price) if model.output_price else 0,
                }
                for model in active_models
            ]
        }
        
        # If there is an enabled model under that provider, add it to the results
        if provider_info["models"]:
            result.append(provider_info)
    
    return result 