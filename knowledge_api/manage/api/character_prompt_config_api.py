from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session
from typing import List
from fastapi_pagination import Page

from knowledge_api.framework.redis.cache_manager import CacheManager
from knowledge_api.manage.model.prompt_model import CharacterPromptConfigInput, CharacterPromptConfigUpdateInput
from knowledge_api.mapper.character_prompt_config.base import (
    CharacterPromptConfigCreate,
    CharacterPromptConfigUpdate,
    CharacterPromptConfigResponse,
    CharacterPromptConfig
)
from knowledge_api.mapper.character_prompt_config.crud import CharacterPromptConfigCRUD
from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.prompt_prologue import PromptPrologueCRUD, PromptPrologueCreate
from knowledge_api.framework.exception.custom_exceptions import BusinessException

router_role_prompt = APIRouter(prefix="/character-prompt-config", tags=["Role cue word configuration"])


def convert_to_response_model(config: CharacterPromptConfig) -> CharacterPromptConfigResponse:
    """Transforming the database model to a responsive model"""
    return CharacterPromptConfigResponse(
        id=config.id,
        role_id=config.role_id,
        level=config.level,
        prompt_text=config.prompt_text,
        prologue=[],  # Default to empty list in list interface
        dialogue=config.dialogue or "",
        timbre=config.timbre or "",
        status=config.status,
        type=config.type,
        title=config.title or "",
        created_at=config.created_at,
        updated_at=config.updated_at
    )


@router_role_prompt.post("/")
async def create_prompt_config(
        config: CharacterPromptConfigInput,
        db: Session = Depends(get_session)
) -> CharacterPromptConfig:
    """Create prompt word configuration"""
    crud = CharacterPromptConfigCRUD(db)
    try:
        data = await crud.create(obj_in=CharacterPromptConfigCreate(
            role_id=config.role_id,
            level=config.level,
            prompt_text=config.prompt_text,
            dialogue=config.dialogue,
            timbre=config.timbre,
            status=config.status,
            type=config.type,
            title=config.title,
        ))
    except IntegrityError:
        raise BusinessException(5001, detail="The character level already exists")

    if config.prologue:
        prompt = PromptPrologueCRUD(db)
        for prologue in config.prologue:
            await prompt.create(prompt_prologue=PromptPrologueCreate(
                prompt_id=data.id,
                prologue=prologue,
                create_at="admin",
            ))
        data.prologue = []


    return data


@router_role_prompt.get("/{config_id}", response_model=CharacterPromptConfigResponse)
async def get_prompt_config(
        config_id: int,
        db: Session = Depends(get_session)
) -> CharacterPromptConfig:
    """Get a single cue word configuration"""
    crud = CharacterPromptConfigCRUD(db)
    config = await crud.get_by_id(config_id=config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Cue word configuration does not exist")

    prompt = PromptPrologueCRUD(db)
    prompt_list = await prompt.get_by_prompt_id(prompt_id=config_id)
    config.prologue = prompt_list
    return config


@router_role_prompt.get("/", response_model=List[CharacterPromptConfigResponse])
async def list_prompt_configs(
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=100),
        role_ids: List[str] = Query(default=None),
        db: Session = Depends(get_session)
) -> List[CharacterPromptConfig]:
    """Get prompt word configuration list"""
    crud = CharacterPromptConfigCRUD(db)
    data = await crud.get_all(role_ids=role_ids, skip=skip, limit=limit, types=["system","task"])
    for info in data:
        info.prologue = []
    return data


@router_role_prompt.get("/by-role/{role_id}", response_model=Page[CharacterPromptConfigResponse])
async def get_prompts_by_role_paginated(
        role_id: str,
        db: Session = Depends(get_session)
) -> Page[CharacterPromptConfigResponse]:
    """Get a list of hint word configurations for pagination based on role ID"""
    crud = CharacterPromptConfigCRUD(db)
    result = await crud.get_all_paginated(role_ids=[role_id])
    
    # Convert to a responsive model
    response_items = [convert_to_response_model(item) for item in result.items]
    
    return Page[CharacterPromptConfigResponse](
        items=response_items,
        total=result.total,
        page=result.page,
        size=result.size,
        pages=result.pages
    )


@router_role_prompt.post("/search", response_model=Page[CharacterPromptConfigResponse])
async def search_prompt_configs(
        request: Request,
        db: Session = Depends(get_session)
) -> Page[CharacterPromptConfigResponse]:
    """Query prompt word configuration list by type"""
    data = await request.json()
    types = data.get("types", None)
    role_ids = data.get("role_ids", None)
    if types is None and role_ids is None:
        # Returns empty paging results
        return Page[CharacterPromptConfigResponse](
            items=[], 
            total=0, 
            page=1, 
            size=10,
            pages=0
        )
    
    crud = CharacterPromptConfigCRUD(db)
    if types:
        result = await crud.get_all_paginated(types=types)
    else:
        result = await crud.get_all_paginated(role_ids=role_ids)
    
    # Convert to a responsive model
    response_items = [convert_to_response_model(item) for item in result.items]
    
    return Page[CharacterPromptConfigResponse](
        items=response_items,
        total=result.total,
        page=result.page,
        size=result.size,
        pages=result.pages
    )


@router_role_prompt.put("/{config_id}", response_model=CharacterPromptConfigResponse)
async def update_prompt_config(
        config_id: int,
        config_update: CharacterPromptConfigUpdateInput,
        db: Session = Depends(get_session)
) -> CharacterPromptConfig:
    """Update prompt word configuration"""
    crud = CharacterPromptConfigCRUD(db)
    config = await crud.update(config_id, CharacterPromptConfigUpdate(
        prompt_text=config_update.prompt_text,
        dialogue=config_update.dialogue,
        timbre=config_update.timbre,
        status=config_update.status,
        level=config_update.level,
        title=config_update.title,
    ))
    if not config:
        raise HTTPException(status_code=404, detail="Cue word configuration does not exist")
    if config_update.prologue:
        prompt = PromptPrologueCRUD(db)
        # Empty and re-add.
        await prompt.delete_by_prompt_id(prompt_id=config_id)
        for prologue in config_update.prologue:
            await prompt.create(prompt_prologue=PromptPrologueCreate(
                prompt_id=config_id,
                prologue=prologue,
                create_at="admin",
            ))
    await CacheManager().update_character_prompt(config,crud)
    config.prologue = []
    return config


@router_role_prompt.patch("/{config_id}/status", response_model=CharacterPromptConfigResponse)
async def update_prompt_config_status(
        config_id: int,
        status: int = Query(..., description="Status: 1-enabled 0-disabled"),
        db: Session = Depends(get_session)
) -> CharacterPromptConfig:
    """Modify prompt word configuration status"""
    if status not in [0, 1]:
        raise HTTPException(status_code=400, detail="The status value is invalid and must be 0 or 1.")

    crud = CharacterPromptConfigCRUD(db)
    config_update = CharacterPromptConfigUpdate(status=status)
    config = await crud.update(config_id, config_update)
    if not config:
        raise HTTPException(status_code=404, detail="Cue word configuration does not exist")
    return config


@router_role_prompt.delete("/{config_id}", response_model=bool)
async def delete_prompt_config(
        config_id: int,
        db: Session = Depends(get_session)
) -> bool:
    """Remove prompt word configuration"""
    crud = CharacterPromptConfigCRUD(db)
    success = await crud.delete(id=config_id)

    prompt = PromptPrologueCRUD(db)
    # Empty and re-add.
    await prompt.delete_by_prompt_id(prompt_id=config_id)

    if not success:
        raise HTTPException(status_code=404, detail="Cue word configuration does not exist")
    return True




@router_role_prompt.post("/add_system")
async def create_prompt_config(
        config: CharacterPromptConfigInput,
        db: Session = Depends(get_session)
) -> CharacterPromptConfig:
    """Create prompt word configuration (system section)"""
    config.type="system"
    crud = CharacterPromptConfigCRUD(db)
    try:
        data = await crud.create(config=CharacterPromptConfigCreate(
            role_id=config.role_id,
            level=config.level,
            prompt_text=config.prompt_text,
            dialogue=config.dialogue,
            timbre=config.timbre,
            status=config.status,
            type=config.type,
            title=config.title,
        ))
    except IntegrityError:
        raise BusinessException(5001, detail="The configuration already exists")

    return data