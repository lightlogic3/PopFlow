import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from knowledge_api.framework.redis.cache_manager import CacheManager
from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.system_config.base import SystemConfigResponse, SystemConfigCreate, SystemConfigUpdate, \
    SystemConfigBulkUpdate
from knowledge_api.mapper.system_config.crud import SystemConfigCRUD

router_system_config = APIRouter(prefix="/system/configs", tags=["System Configuration"])


@router_system_config.post("/", response_model=SystemConfigResponse)
async def create_system_config(
        config_in: SystemConfigCreate,
        db: Session = Depends(get_session)
) -> Any:
    """Create system configuration"""
    crud = SystemConfigCRUD(db)
    try:
        return await crud.create(obj_in=config_in)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router_system_config.get("/{config_id}", response_model=SystemConfigResponse)
async def get_system_config(
        config_id: int,
        db: Session = Depends(get_session)
) -> Any:
    """Get a single system configuration"""
    crud = SystemConfigCRUD(db)
    config = await crud.get_by_id(id=config_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"系统配置ID {config_id} 不存在")
    return config


@router_system_config.get("/", response_model=Dict[str, List[SystemConfigResponse]])
async def list_system_configs(
        keyword: Optional[str] = None,
        db: Session = Depends(get_session)
) -> Any:
    """Get a list of system configurations (grouped by usage type)

Parameter:
- keywords: search keywords

Return:
- Configuration dictionary grouped by use_type"""
    crud = SystemConfigCRUD(db)
    # Get all configuration items
    configs = await crud.get_all()

    # Handle configuration of password types, set value to empty string
    # Group by use_type
    grouped_configs = {}
    for config in configs:
        config_mask(config)
        group_name = config.use_type if hasattr(config, 'use_type') and config.use_type else 'other'
        if group_name not in grouped_configs:
            grouped_configs[group_name] = []
        grouped_configs[group_name].append(config)

    return grouped_configs

def config_mask(config):
    if hasattr(config, 'item_type'):
        if config.item_type == 'password':
            config.config_value = ''
        if config.item_type == 'json_object':
            try:
                data = json.loads(config.config_value)
                for key, value in data.items():
                    if key in ["ak", "sk"]:
                        data[key] = ""
                    if  "token" in key:
                        data[key] = ""
                config.config_value = json.dumps(data)
            except:
                pass
@router_system_config.get("/by-key/{config_key}", response_model=SystemConfigResponse)
async def get_system_config_by_key(
        config_key: str,
        db: Session = Depends(get_session)
) -> Any:
    """Get the system configuration through the configuration key"""
    crud = SystemConfigCRUD(db)
    config = await crud.get_by_key(config_key=config_key)
    config_mask(config)
    if not config:
        raise HTTPException(status_code=404, detail=f"系统配置 '{config_key}' 不存在")
    return config


@router_system_config.get("/value/{config_key}")
async def get_config_value_by_key(
        config_key: str,
        default: Optional[str] = None,
        db: Session = Depends(get_session)
) -> Any:
    """Get the configuration value through the configuration key"""
    crud = SystemConfigCRUD(db)
    config = await crud.get_by_key(config_key=config_key)
    value = config.config_value if config else default
    return {"value": value}


@router_system_config.get("/as-dict", response_model=Dict[str, Any])
async def get_system_configs_as_dict(
        db: Session = Depends(get_session)
) -> Any:
    """Get all system configurations as a dictionary"""
    crud = SystemConfigCRUD(db)
    return await crud.get_all_as_dict()


@router_system_config.put("/{config_id}", response_model=SystemConfigResponse)
async def update_system_config(
        config_id: int,
        config_in: SystemConfigUpdate,
        db: Session = Depends(get_session)
) -> Any:
    """Update system configuration"""
    crud = SystemConfigCRUD(db)
    config = await crud.update(id=config_id, obj_in=config_in)
    if not config:
        raise HTTPException(status_code=404, detail=f"系统配置ID {config_id} 不存在")

    # update cache
    if config_in.config_key:
        await CacheManager().system_config_cache.update(config.config_key,config.config_value,crud)

    return config


@router_system_config.put("/by-key/{config_key}", response_model=SystemConfigResponse)
async def update_system_config_by_key(
        config_key: str,
        config_in: SystemConfigUpdate,
        db: Session = Depends(get_session)
) -> Any:
    """Update system configuration via configuration key"""
    crud = SystemConfigCRUD(db)
    config = await crud.update_by_key(config_key=config_key, obj_in=config_in)
    if not config:
        raise HTTPException(status_code=404, detail=f"系统配置 '{config_key}' 不存在")
    return config


@router_system_config.post("/upsert", response_model=SystemConfigResponse)
async def upsert_system_config(
        config_in: SystemConfigCreate,
        db: Session = Depends(get_session)
) -> Any:
    """Create or update system configuration"""
    crud = SystemConfigCRUD(db)
    return await crud.create_or_update(obj_in=config_in)


@router_system_config.post("/bulk-upsert", response_model=List[SystemConfigResponse])
async def bulk_upsert_system_configs(
        configs_in: SystemConfigBulkUpdate,
        db: Session = Depends(get_session)
) -> Any:
    """Batch creation or updating of system configurations"""
    crud = SystemConfigCRUD(db)
    return await crud.bulk_create_or_update(objs_in=configs_in.configs)


@router_system_config.delete("/{config_id}", response_model=bool)
async def delete_system_config(
        config_id: int,
        db: Session = Depends(get_session)
) -> Any:
    """Delete system configuration"""
    crud = SystemConfigCRUD(db)
    success = await crud.delete(id=config_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"系统配置ID {config_id} 不存在")
    return True


@router_system_config.delete("/by-key/{config_key}", response_model=bool)
async def delete_system_config_by_key(
        config_key: str,
        db: Session = Depends(get_session)
) -> Any:
    """Delete system configuration via configuration key"""
    crud = SystemConfigCRUD(db)
    success = await crud.delete_by_key(config_key=config_key)
    if not success:
        raise HTTPException(status_code=404, detail=f"系统配置 '{config_key}' 不存在")
    return True
