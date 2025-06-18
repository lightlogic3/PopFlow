from fastapi import APIRouter, Depends, HTTPException, Request, Query, Path, Body
from sqlmodel import Session
from typing import Dict, Any, List
from pydantic import BaseModel

from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.system.base import (
    SystemUserCreate, SystemUserUpdate, SystemUserResponse
)
from knowledge_api.mapper.system.crud import (
    SystemUserCRUD, SystemUserRoleCRUD
)
from knowledge_api.framework.auth.auth_decorator import require_permissions

router_system_user = APIRouter(prefix="/system/users", tags=["user management"])

# Define the request body model
class UserRolesRequest(BaseModel):
    role_ids: List[int]


@router_system_user.post("/", response_model=SystemUserResponse)
@require_permissions(["system:user:add"])
async def create_user(
        user_create: SystemUserCreate,
        request: Request,
        db: Session = Depends(get_session)
):
    """Create user"""
    creator = request.state.token_data.get("username", "")

    # Check if the username already exists
    user_crud = SystemUserCRUD(db)
    existing_user = await user_crud.get_by_username(username=user_create.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Create user
    user = await user_crud.create(obj_in=user_create, creator=creator)

    return user


@router_system_user.get("/{user_id}", response_model=SystemUserResponse)
@require_permissions(["system:user:query"])
async def get_user(
        request: Request,
        user_id: int = Path(..., title="user ID"),
        db: Session = Depends(get_session)
):
    """Get users by ID"""
    user_crud = SystemUserCRUD(db)
    user = await user_crud.get_by_id(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User does not exist")

    return user


@router_system_user.put("/{user_id}", response_model=SystemUserResponse)
@require_permissions(["system:user:edit"])
async def update_user(
        user_update: SystemUserUpdate,
        request: Request,
        user_id: int = Path(..., title="user ID"),
        db: Session = Depends(get_session)
):
    """update user"""
    updater = request.state.token_data.get("username", "")

    user_crud = SystemUserCRUD(db)
    user = await user_crud.update(id=user_id, obj_in=user_update, updater=updater)
    if not user:
        raise HTTPException(status_code=404, detail="User does not exist")

    return user


@router_system_user.delete("/{user_id}", response_model=Dict[str, Any])
@require_permissions(["system:user:remove"])
async def delete_user(
        request: Request,
        user_id: int = Path(..., title="user ID"),
        db: Session = Depends(get_session),
):
    """Delete user
: type request: object"""
    updater = request.state.token_data.get("username", "")

    user_crud = SystemUserCRUD(db)
    success = await user_crud.delete(id=user_id, updater=updater)
    if not success:
        raise HTTPException(status_code=404, detail="User does not exist")

    return {"code": 200, "message": "Deleted successfully"}


@router_system_user.get("/", response_model=Dict[str, Any])
@require_permissions(["system:user:list"])
async def list_users(
        request: Request,
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        username: str = Query(None),
        nickname: str = Query(None),
        mobile: str = Query(None),
        status: int = Query(None),
        db: Session = Depends(get_session)
):
    """Get user list"""
    user_crud = SystemUserCRUD(db)
    users, total = await user_crud.get_all(
        skip=skip,
        limit=limit,
        username=username,
        nickname=nickname,
        mobile=mobile,
        status=status
    )

    return {
        "items": users,
        "total": total
    }


@router_system_user.put("/{user_id}/password", response_model=Dict[str, Any])
@require_permissions(["system:user:resetPwd"])
async def reset_password(
        request: Request,
        user_id: int = Path(..., title="user ID"),
        password: str = Query(..., min_length=6, max_length=20),
        db: Session = Depends(get_session)
):
    """Reset user password"""
    updater = request.state.token_data.get("username", "")

    user_crud = SystemUserCRUD(db)
    success = await user_crud.update_password(
        user_id=user_id,
        new_password=password,
        updater=updater
    )

    if not success:
        raise HTTPException(status_code=404, detail="User does not exist")

    return {"code": 200, "message": "Password reset successful"}


@router_system_user.put("/{user_id}/status", response_model=Dict[str, Any])
@require_permissions(["system:user:edit"])
async def update_user_status(
        request: Request,
        user_id: int = Path(..., title="user ID"),
        status: int = Query(..., ge=0, le=1),
        db: Session = Depends(get_session)
):
    """Update user status"""
    updater = request.state.token_data.get("username", "")

    user_crud = SystemUserCRUD(db)
    success = await user_crud.update_status(
        user_id=user_id,
        status=status,
        updater=updater
    )

    if not success:
        raise HTTPException(status_code=404, detail="User does not exist")

    return {"code": 200, "message": "Status update successful"}


@router_system_user.get("/{user_id}/roles", response_model=Dict[str, Any])
@require_permissions(["system:user:query"])
async def get_user_roles(
        request: Request,
        user_id: int = Path(..., title="user ID"),
        db: Session = Depends(get_session)
):
    """Get user role"""
    from knowledge_api.mapper.system.crud import SystemRoleCRUD

    # Check if the user exists
    user_crud = SystemUserCRUD(db)
    user = await user_crud.get_by_id(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User does not exist")

    # Get user role
    role_crud = SystemRoleCRUD(db)
    roles = await role_crud.get_roles_by_user_id(user_id=user_id)
    role_ids = [role.id for role in roles]

    # Acquire all roles
    all_roles, _ = await role_crud.get_all(status=0)  # Get only normal roles

    return {
        "user_id": user_id,
        "roles": [
            {
                "id": role.id,
                "name": role.name,
                "code": role.code,
                "selected": role.id in role_ids
            }
            for role in all_roles
        ]
    }


@router_system_user.put("/{user_id}/roles", response_model=Dict[str, Any])
@require_permissions(["system:user:edit"])
async def assign_user_roles(
    request: Request,
    user_id: int = Path(..., title="user ID"),
    data: UserRolesRequest = Body(...),  # Get data from the request body
    db: Session = Depends(get_session)
):
    """Assign user roles"""
    updater = request.state.token_data.get("username", "")

    # Check if the user exists
    user_crud = SystemUserCRUD(db)
    user = await user_crud.get_by_id(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User does not exist")

    # Assign roles
    user_role_crud = SystemUserRoleCRUD(db)
    success = await user_role_crud.assign_user_roles(
        user_id=user_id,
        role_ids=data.role_ids,  # Use the role_ids in the request body
        creator=updater
    )

    if not success:
        raise HTTPException(status_code=500, detail="Role assignment failed")

    return {"code": 200, "message": "Role assignment successful"}
