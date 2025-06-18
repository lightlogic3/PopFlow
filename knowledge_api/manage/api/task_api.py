from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List
from fastapi_pagination import Page

from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.tasks.base import TaskResponse, TaskCreate, Task, TaskUpdate
from knowledge_api.mapper.tasks.crud import TaskCRUD
from knowledge_api.mapper.task_character_relations.base import TaskCharacterRelationUpdate
from knowledge_api.mapper.task_character_relations.crud import TaskCharacterRelationCRUD
from knowledge_api.mapper.roles.crud import RoleCRUD

router_task = APIRouter(prefix="/tasks", tags=["Task Management"])


@router_task.post("/", response_model=TaskResponse)
async def create_task(
        task: TaskCreate,
        db: Session = Depends(get_session)
) -> Task:
    """Create task"""
    # 1. Create the task first
    task_crud = TaskCRUD(db)
    db_task = await task_crud.create(task=task)
    
    # 2. If there is a role association, create a role association
    if task.role_relations and len(task.role_relations) > 0:
        # Verify that the role exists
        role_crud = RoleCRUD(db)
        for relation in task.role_relations:
            role = await role_crud.get_by_id(role_id=relation["role_id"])
            if not role:
                # Roll back task creation, throw exception
                await task_crud.delete(task_id=db_task.id)
                raise HTTPException(status_code=404, detail=f"角色 {relation['role_id']} 不存在")
        
        # Create role associations
        relation_crud = TaskCharacterRelationCRUD(db)
        await relation_crud.bulk_create(task_id=db_task.id, relations=task.role_relations)
    
    return db_task


@router_task.get("/{task_id}", response_model=TaskResponse)
async def get_task(
        task_id: int,
        db: Session = Depends(get_session)
) -> Task:
    """Get a single task"""
    crud = TaskCRUD(db)
    task = await crud.get_by_id(id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task does not exist")
    return task


@router_task.get("/", response_model=Page[TaskResponse])
async def list_tasks(
        db: Session = Depends(get_session)
) -> Page[TaskResponse]:
    """Get task list (pagination)"""
    crud = TaskCRUD(db)
    return await crud.get_all_paginated()


@router_task.put("/{task_id}", response_model=TaskResponse)
async def update_task(
        task_id: int,
        task_update: TaskUpdate,
        db: Session = Depends(get_session)
) -> Task:
    """update task"""
    crud = TaskCRUD(db)
    # Create role associations
    relation_crud = TaskCharacterRelationCRUD(db)
    # 检查是否存在role_relations并且不为空
    # if task_update.role_relations and len(task_update.role_relations) > 0:
        # Verify that the role exists
        # role_crud = RoleCRUD(db)
        # for relation in task_update.role_relations:
        #     role = await role_crud.get_by_id(role_id=relation["role_id"])
        #     if not role:
        #         # Roll back task creation, throw exception
        #         await crud.delete(task_id=task_id)
        #         raise HTTPException(status_code=404, detail=f"角色 {relation['role_id']} 不存在")

    await relation_crud.delete_by_task_id(task_id=task_id)
    await relation_crud.bulk_create(task_id=task_id, relations=task_update.role_relations)
    
    task = await crud.update(task_id, task_update)
    if not task:
        raise HTTPException(status_code=404, detail="Task does not exist")
    return task


@router_task.delete("/{task_id}", response_model=bool)
async def delete_task(
        task_id: int,
        db: Session = Depends(get_session)
) -> bool:
    """Delete task"""
    # First, delete the relationship between tasks and roles
    relation_crud = TaskCharacterRelationCRUD(db)
    await relation_crud.delete_by_task_id(task_id=task_id)
    
    # Then delete the task
    task_crud = TaskCRUD(db)
    success = await task_crud.delete(task_id=task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task does not exist")
    return True


@router_task.get("/{task_id}/relations", response_model=List[dict])
async def get_task_relations(
        task_id: int,
        db: Session = Depends(get_session)
) -> List[dict]:
    """Get the role association of the task"""
    # First check if the task exists
    task_crud = TaskCRUD(db)
    task = await task_crud.get_by_id(id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task does not exist")
    
    # Get the role association of the task
    relation_crud = TaskCharacterRelationCRUD(db)
    relations = await relation_crud.get_by_task_id(task_id=task_id)
    
    # Get role details
    role_crud = RoleCRUD(db)
    result = []
    for relation in relations:
        role = await role_crud.get_by_id(role_id=relation.role_id)
        if role:
            result.append({
                "relation_id": relation.id,
                "task_id": relation.task_id,
                "role_id": relation.role_id,
                "role_name": role.name,
                "image_url": role.image_url,
                "llm_model": relation.llm_model,
                "voice": relation.voice,
                "character_setting": relation.character_setting
            })
    
    return result


@router_task.put("/relations/{relation_id}", response_model=dict)
async def update_task_relation(
        relation_id: int,
        relation_update: TaskCharacterRelationUpdate,
        db: Session = Depends(get_session)
) -> dict:
    """Update task role associations"""
    relation_crud = TaskCharacterRelationCRUD(db)
    relation = await relation_crud.update(relation_id, relation_update)
    if not relation:
        raise HTTPException(status_code=404, detail="Task role association does not exist")
    
    # Get role details
    role_crud = RoleCRUD(db)
    role = await role_crud.get_by_id(role_id=relation.role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Character does not exist")
    
    return {
        "relation_id": relation.id,
        "task_id": relation.task_id,
        "role_id": relation.role_id,
        "role_name": role.name,
        "image_url": role.image_url,
        "llm_model": relation.llm_model,
        "voice": relation.voice,
        "character_setting": relation.character_setting
    } 