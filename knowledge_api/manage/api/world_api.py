from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Optional
from fastapi_pagination import Page

from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.world.base import WorldResponse, WorldCreate, World, WorldUpdate
from knowledge_api.mapper.world.crud import WorldCRUD
from knowledge_api.mapper.roles_world.crud import RolesWorldCRUD

router_world = APIRouter(prefix="/worlds", tags=["Worldview management"])


@router_world.get("/all", response_model=List[WorldResponse])
async def list_all_worlds(
        type: Optional[str] = Query(None, description="Worldview type"),
        db: Session = Depends(get_session)
) -> List[WorldResponse]:
    """Get a list of all worldviews (without pagination, for scenarios such as drop-down selectors)"""
    crud = WorldCRUD(db)
    filters = {}
    if type:
        filters["type"] = type
    return await crud.get_all(filters=filters, order_by="sort", order_desc=True, limit=1000)


@router_world.post("/", response_model=WorldResponse)
async def create_world(
        world: WorldCreate,
        db: Session = Depends(get_session)
) -> World:
    """Create a worldview"""
    crud = WorldCRUD(db)
    return await crud.create(world=world)


@router_world.get("/{world_id}", response_model=WorldResponse)
async def get_world(
        world_id: str,
        db: Session = Depends(get_session)
) -> World:
    """Acquire a single worldview"""
    crud = WorldCRUD(db)
    world = await crud.get_by_id(world_id)
    if not world:
        raise HTTPException(status_code=404, detail="Worldview does not exist")
    return world


@router_world.get("/", response_model=Page[WorldResponse])
async def list_worlds(
        type: Optional[str] = Query(None, description="Worldview type"),
        db: Session = Depends(get_session)
) -> Page[WorldResponse]:
    """Get a list of worldviews (pagination)"""
    crud = WorldCRUD(db)
    filters = {}
    if type:
        filters["type"] = type
    return await crud.get_all_paginated(filters=filters, order_by="sort", order_desc=True)


@router_world.get("/type/{world_type}", response_model=Page[WorldResponse])
async def list_worlds_by_type(
        world_type: str,
        db: Session = Depends(get_session)
) -> Page[WorldResponse]:
    """Get a list of worldviews by type (pagination)"""
    crud = WorldCRUD(db)
    filters = {"type": world_type}
    return await crud.get_all_paginated(filters=filters, order_by="sort", order_desc=True)


@router_world.put("/{world_id}", response_model=WorldResponse)
async def update_world(
        world_id: str,
        world_update: WorldUpdate,
        db: Session = Depends(get_session)
) -> World:
    """Update your worldview"""
    crud = WorldCRUD(db)
    world = await crud.update(world_id, world_update)
    if not world:
        raise HTTPException(status_code=404, detail="Worldview does not exist")
    return world


@router_world.delete("/{world_id}", response_model=bool)
async def delete_world(
        world_id: str,
        db: Session = Depends(get_session)
) -> bool:
    """Delete Worldview"""
    # First, remove the connection between the worldview and the role
    try:
        world_id_int = int(world_id)
        roles_world_crud = RolesWorldCRUD(db)
        await roles_world_crud.delete_by_world_id(world_id=world_id_int)
    except ValueError:
        pass  # If world_id cannot be converted to int, ignore association deletion

    # Delete Worldview
    crud = WorldCRUD(db)
    success = await crud.delete(world_id)
    if not success:
        raise HTTPException(status_code=404, detail="Worldview does not exist")
    return True
