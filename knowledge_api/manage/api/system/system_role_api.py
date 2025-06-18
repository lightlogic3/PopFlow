from fastapi import APIRouter, Depends, HTTPException, Request, Query, Path, Body
from sqlmodel import Session
from typing import Dict, Any, List
from pydantic import BaseModel

from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.system.base import (
    SystemRoleCreate, SystemRoleUpdate, SystemRoleResponse
)
from knowledge_api.mapper.system.crud import (
    SystemRoleCRUD, SystemRoleMenuCRUD, SystemMenuCRUD
)
from knowledge_api.framework.auth.auth_decorator import require_permissions

# Define the request body model
class RoleMenusRequest(BaseModel):
    menu_ids: List[int]

router_system_role = APIRouter(prefix="/system/roles", tags=["Role Management"])


@router_system_role.post("/", response_model=SystemRoleResponse)
@require_permissions(["system:role:add"])
async def create_role(
    role_create: SystemRoleCreate,
    request: Request,
    db: Session = Depends(get_session)
):
    """Create role"""
    creator = request.state.token_data.get("username", "")
    
    # Check if the role code already exists
    role_crud = SystemRoleCRUD(db)
    existing_role = await role_crud.get_by_code(code=role_create.code)
    if existing_role:
        raise HTTPException(status_code=400, detail="Role code already exists")
    
    # Create role
    role = await role_crud.create(obj_in=role_create, creator=creator)
    
    return role


@router_system_role.get("/{role_id}", response_model=SystemRoleResponse)
@require_permissions(["system:role:query"])
async def get_role(
    request: Request,
    role_id: int = Path(..., title="Role ID"),
    db: Session = Depends(get_session)
):
    """Get role by ID"""
    role_crud = SystemRoleCRUD(db)
    role = await role_crud.get_by_id(id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Character does not exist")
    
    return role


@router_system_role.put("/{role_id}", response_model=SystemRoleResponse)
@require_permissions(["system:role:edit"])
async def update_role(
    role_update: SystemRoleUpdate,
    request: Request,
    role_id: int = Path(..., title="Role ID"),
    db: Session = Depends(get_session)
):
    """update role"""
    updater = request.state.token_data.get("username", "")
    
    role_crud = SystemRoleCRUD(db)
    role = await role_crud.update(id=role_id, obj_in=role_update, updater=updater)
    if not role:
        raise HTTPException(status_code=404, detail="Character does not exist")
    
    return role


@router_system_role.delete("/{role_id}", response_model=Dict[str, Any])
@require_permissions(["system:role:remove"])
async def delete_role(
    request: Request,
    role_id: int = Path(..., title="Role ID"),
    db: Session = Depends(get_session)
):
    """delete role"""
    updater = request.state.token_data.get("username", "")
    
    role_crud = SystemRoleCRUD(db)
    success = await role_crud.delete(id=role_id, updater=updater)
    if not success:
        raise HTTPException(status_code=404, detail="Character does not exist")
    
    return {"code": 200, "message": "Deleted successfully"}


@router_system_role.get("/", response_model=Dict[str, Any])
@require_permissions(["system:role:list"])
async def list_roles(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    name: str = Query(None),
    code: str = Query(None),
    status: int = Query(None),
    db: Session = Depends(get_session)
):
    """Get a list of roles"""
    role_crud = SystemRoleCRUD(db)
    roles, total = await role_crud.get_all(
        skip=skip,
        limit=limit,
        name=name,
        code=code,
        status=status
    )
    
    return {
        "items": roles,
        "total": total
    }


@router_system_role.get("/{role_id}/menus", response_model=Dict[str, Any])
@require_permissions(["system:role:query"])
async def get_role_menus(
    request: Request,
    role_id: int = Path(..., title="Role ID"),
    db: Session = Depends(get_session)
):
    """Get Role Menu Permissions"""
    # Check if the role exists
    role_crud = SystemRoleCRUD(db)
    role = await role_crud.get_by_id(id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Character does not exist")
    
    # Get character menu
    menu_crud = SystemMenuCRUD(db)
    role_menus = await menu_crud.get_menus_by_role_id(role_id=role_id)
    role_menu_ids = [menu.id for menu in role_menus]
    
    # Get all menu trees
    all_menus_tree = await menu_crud.get_all_menus_tree(status=0)  # Get only normal menus
    
    return {
        "role_id": role_id,
        "menus": all_menus_tree,
        "checkedKeys": role_menu_ids
    }


@router_system_role.put("/{role_id}/menus", response_model=Dict[str, Any])
@require_permissions(["system:role:edit"])
async def assign_role_menus(
    request: Request,
    role_id: int = Path(..., title="Role ID"),
    data: RoleMenusRequest = Body(...),  # Get data from the request body
    db: Session = Depends(get_session)
):
    """Assign Role Menu Permissions"""
    updater = request.state.token_data.get("username", "")
    
    # Check if the role exists
    role_crud = SystemRoleCRUD(db)
    role = await role_crud.get_by_id(id=role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Character does not exist")
    
    # Get the current menu permissions for the role
    menu_crud = SystemMenuCRUD(db)
    current_menus = await menu_crud.get_menus_by_role_id(role_id=role_id)
    current_menu_ids = set(menu.id for menu in current_menus)
    
    # Calculation requires additional menu permissions
    new_menu_ids = set(data.menu_ids) - current_menu_ids
    
    # Get the menu permissions to be removed
    removed_menu_ids = current_menu_ids - set(data.menu_ids)
    
    # Assign menu permissions
    role_menu_crud = SystemRoleMenuCRUD(db)
    
    # Only deal with the changed parts
    if new_menu_ids or removed_menu_ids:
        success = await role_menu_crud.update_role_menus(
            role_id=role_id,
            add_menu_ids=list(new_menu_ids),
            remove_menu_ids=list(removed_menu_ids),
            operator=updater
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Menu permission update failed")
        
        # Record operation details
        added_count = len(new_menu_ids)
        removed_count = len(removed_menu_ids)
        operation_detail = f"新增{added_count}项权限，移除{removed_count}项权限"
        
        return {
            "code": 200, 
            "message": f"菜单权限更新成功：{operation_detail}",
            "data": {
                "added": list(new_menu_ids),
                "removed": list(removed_menu_ids)
            }
        }
    else:
        return {"code": 200, "message": "Menu permissions remain unchanged"} 