from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List
from fastapi_pagination import Page

from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.role_subtasks import RoleSubtaskCRUD
from knowledge_api.mapper.role_tasks.base import RoleTaskResponse, RoleTaskCreate, RoleTask, RoleTaskUpdate
from knowledge_api.mapper.role_tasks.crud import RoleTaskCRUD

router_role_task = APIRouter(prefix="/role-tasks", tags=["Role Task Management"])


@router_role_task.post("/", response_model=RoleTaskResponse)
async def create_role_task(
        task: RoleTaskCreate,
        db: Session = Depends(get_session)
) -> RoleTask:
    """Create Role Task"""
    crud = RoleTaskCRUD(db)
    return await crud.create(task=task)


@router_role_task.get("/{task_id}", response_model=RoleTaskResponse)
async def get_role_task(
        task_id: str,
        db: Session = Depends(get_session)
) -> RoleTask:
    """Get a single role task"""
    crud = RoleTaskCRUD(db)
    task = await crud.get_by_id(task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task does not exist")
    return task


@router_role_task.get("/", response_model=Page[RoleTaskResponse])
async def list_role_tasks(
        db: Session = Depends(get_session)
) -> Page[RoleTaskResponse]:
    """Get all roles task list (pagination)"""
    crud = RoleTaskCRUD(db)
    return await crud.get_all_paginated()


@router_role_task.get("/by-role/{role_id}", response_model=Page[RoleTaskResponse])
async def list_role_tasks_by_role_id(
        role_id: str,
        db: Session = Depends(get_session)
) -> Page[RoleTaskResponse]:
    """Get the task list (pagination) for the specified role"""
    crud = RoleTaskCRUD(db)
    return await crud.get_by_role_id_paginated(role_id=role_id)


@router_role_task.put("/{task_id}", response_model=RoleTaskResponse)
async def update_role_task(
        task_id: str,
        task_update: RoleTaskUpdate,
        db: Session = Depends(get_session)
) -> RoleTask:
    """Update Role Task"""
    crud = RoleTaskCRUD(db)
    task = await crud.update(task_id, task_update)
    if not task:
        raise HTTPException(status_code=404, detail="Task does not exist")
    return task


@router_role_task.delete("/{task_id}", response_model=bool)
async def delete_role_task(
        task_id: str,
        db: Session = Depends(get_session)
) -> bool:
    """Delete Role Task"""
    crud = RoleTaskCRUD(db)
    success = await crud.delete(id=task_id)

    # 删除相关子任务
    crud = RoleSubtaskCRUD(db)
    await crud.delete_by_task_id(task_id=task_id)

    if not success:
        raise HTTPException(status_code=404, detail="Task does not exist")
    return True


@router_role_task.delete("/by-role/{role_id}", response_model=bool)
async def delete_role_tasks_by_role_id(
        role_id: str,
        db: Session = Depends(get_session)
) -> bool:
    """Delete all tasks for the specified role"""
    crud = RoleTaskCRUD(db)
    return await crud.delete_by_role_id(role_id=role_id) 