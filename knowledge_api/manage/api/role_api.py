from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List
from fastapi_pagination import Page

from knowledge_api.framework.redis.cache_system.role_cache import RoleCache
from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.roles.base import RoleResponse, RoleCreate, Role, RoleUpdate
from knowledge_api.mapper.roles.crud import RoleCRUD
from knowledge_api.mapper.roles_world.crud import RolesWorldCRUD

router_role = APIRouter(prefix="/roles", tags=["Role Management"])


@router_role.post("/", response_model=RoleResponse)
async def create_role(
        role: RoleCreate,
        db: Session = Depends(get_session)
) -> Role:
    """Create role"""
    crud = RoleCRUD(db)
    return await crud.create(role=role)

@router_role.get("/all", response_model=List[RoleResponse])
async def list_all_roles(
        db: Session = Depends(get_session)
) -> List[Role]:
    """Get a list of all roles (without pagination)"""
    crud = RoleCRUD(db)
    return await crud.get_all(limit=1000)  # Set a large limit to acquire all roles


@router_role.get("/{role_id}", response_model=RoleResponse)
async def get_role(
        role_id: str,
        db: Session = Depends(get_session)
) -> Role:
    """Acquire a single role"""
    crud = RoleCRUD(db)
    role = await crud.get_by_id(role_id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Character does not exist")
    return role


@router_role.get("/", response_model=Page[RoleResponse])
async def list_roles(
        db: Session = Depends(get_session)
) -> Page[RoleResponse]:
    """Get a list of roles (pagination)"""
    crud = RoleCRUD(db)
    return await crud.get_all_paginated()



@router_role.put("/{role_id}", response_model=RoleResponse)
async def update_role(
        role_id: str,
        role_update: RoleUpdate,
        db: Session = Depends(get_session)
) -> Role:
    """update role"""
    crud = RoleCRUD(db)
    role = await crud.update(role_id, role_update)
    if not role:
        raise HTTPException(status_code=404, detail="Character does not exist")
    await RoleCache().update(role)
    return role


@router_role.delete("/{role_id}", response_model=bool)
async def delete_role(
        role_id: str,
        db: Session = Depends(get_session)
) -> bool:
    """delete role"""
    # First, remove the relationship between the character and the worldview
    roles_world_crud = RolesWorldCRUD(db)
    await roles_world_crud.delete_by_role_id(role_id=role_id)
    
    # Then delete the role
    crud = RoleCRUD(db)
    success = await crud.delete(role_id=role_id)
    if not success:
        raise HTTPException(status_code=404, detail="Character does not exist")
    return True
