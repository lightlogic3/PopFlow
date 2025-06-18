"""Role subtask API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List
from fastapi_pagination import Page
import datetime
from uuid import uuid4

from knowledge_api.back_task.role_task_sub import RoleTaskSub
from knowledge_api.framework.database.database import get_session
from knowledge_api.framework.task_manage.scheduler import TaskScheduler
from knowledge_api.manage.model.task_model import AutoTaskMode
from knowledge_api.mapper.role_subtasks.base import RoleSubtaskResponse, RoleSubtaskCreate, RoleSubtask, \
    RoleSubtaskUpdate
from knowledge_api.mapper.role_subtasks.crud import RoleSubtaskCRUD
from knowledge_api.mapper.task_manage.base import TaskManage, TaskStatus, TriggerType
from knowledge_api.mapper.task_manage.crud import TaskManageCRUD
from knowledge_api.mapper.task_manage.base import TaskManageCreate

router_role_subtask = APIRouter(prefix="/role-subtasks", tags=["Role subtask management"])


@router_role_subtask.post("/", response_model=RoleSubtaskResponse)
async def create_role_subtask(
        subtask: RoleSubtaskCreate,
        db: Session = Depends(get_session)
) -> RoleSubtask:
    """Create a role subtask

@Param subtask: subtask creation data
@Param db: database session
@Return: created subtask"""
    crud = RoleSubtaskCRUD(db)
    return await crud.create(subtask=subtask)


@router_role_subtask.get("/{subtask_id}", response_model=RoleSubtaskResponse)
async def get_role_subtask(
        subtask_id: str,
        db: Session = Depends(get_session)
) -> RoleSubtask:
    """Get a single role subtask

@Param subtask_id: subtask ID
@Param db: database session
@Return: subtask information"""
    crud = RoleSubtaskCRUD(db)
    subtask = await crud.get_by_id(subtask_id=subtask_id)
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask does not exist")
    return subtask


@router_role_subtask.get("/", response_model=Page[RoleSubtaskResponse])
async def list_role_subtasks(
        db: Session = Depends(get_session)
) -> Page[RoleSubtaskResponse]:
    """Get a list of all role subtasks (pagination)

@Param db: database session
@Return: subtask list (pagination)"""
    crud = RoleSubtaskCRUD(db)
    return await crud.get_all_paginated()


@router_role_subtask.get("/by-task/{task_id}", response_model=Page[RoleSubtaskResponse])
async def list_role_subtasks_by_task_id(
        task_id: str,
        db: Session = Depends(get_session)
) -> Page[RoleSubtaskResponse]:
    """Get the list of subtasks of the specified main task (pagination)

@Param task_id: main task ID
@Param db: database session
@Return: subtask list (pagination)"""
    crud = RoleSubtaskCRUD(db)
    return await crud.get_by_task_id_paginated(task_id=task_id)


@router_role_subtask.put("/{subtask_id}", response_model=RoleSubtaskResponse)
async def update_role_subtask(
        subtask_id: str,
        subtask_update: RoleSubtaskUpdate,
        db: Session = Depends(get_session)
) -> RoleSubtask:
    """Update role subtask

@Param subtask_id: subtask ID
@Param subtask_update: Subtask update data
@Param db: database session
@Return: Updated subtask"""
    crud = RoleSubtaskCRUD(db)
    subtask = await crud.update(subtask_id, subtask_update)
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask does not exist")
    return subtask


@router_role_subtask.delete("/{subtask_id}", response_model=bool)
async def delete_role_subtask(
        subtask_id: str,
        db: Session = Depends(get_session)
) -> bool:
    """Delete Role Subtask

@Param subtask_id: subtask ID
@Param db: database session
@Return: whether the deletion was successful"""
    crud = RoleSubtaskCRUD(db)
    success = await crud.delete(id=subtask_id)
    if not success:
        raise HTTPException(status_code=404, detail="Subtask does not exist")
    return True


@router_role_subtask.delete("/by-task/{task_id}", response_model=bool)
async def delete_role_subtasks_by_task_id(
        task_id: str,
        db: Session = Depends(get_session)
) -> bool:
    """Delete all subtasks of the specified main task

@Param task_id: main task ID
@Param db: database session
@Return: whether the deletion was successful"""
    crud = RoleSubtaskCRUD(db)
    return await crud.delete_by_task_id(task_id=task_id)


@router_role_subtask.post("/auto_task", response_model=bool)
async def auto_task_subtask(
        auto_task: AutoTaskMode,
        db: Session = Depends(get_session)) -> bool:
    """Create role automatic subtask

@Param auto_task: auto task mode
@Param db: database session
@Return: whether it was successful"""
    # If it is a timed task, create a timed task
    if hasattr(auto_task, 'regular_time') and auto_task.regular_time and hasattr(auto_task, 'daily_time') and auto_task.daily_time:
        # Extract time and minutes - get from datetime
        daily_time = auto_task.daily_time
        hour = daily_time.hour
        minute = daily_time.minute
        
        # Create cron trigger parameters (executed at a specified time every day)
        trigger_args = {
            "minute": str(minute),
            "hour": str(hour),
            "day": "*",
            "month": "*",
            "day_of_week": "*"
        }
        
        # Generate a shorter task ID using the first 8 bits of the UUID
        short_uuid = str(uuid4())[:8]
        
        # Add a timed task
        task_name = f"子任务生成_{auto_task.task_id[:8]}_{datetime.datetime.now().strftime('%Y%m%d%H%M')}"
        task_id = f"sub_gen_{short_uuid}"
        description = f"每天 {hour:02d}:{minute:02d} 自动生成 {auto_task.number} 个子任务 (主任务: {auto_task.task_id})"
        
        # 1. Create the task record to the database first
        task_crud = TaskManageCRUD(db)
        task_create = TaskManageCreate(
            id=task_id,
            name=task_name,
            task_type="subtask timing generation",
            status=TaskStatus.PENDING,
            trigger_type=TriggerType.CRON,
            trigger_args=trigger_args,
            func_path="knowledge_api.back_task.role_task_sub.create_subtasks_job",
            func_args={
                "task_id": auto_task.task_id,
                "number": auto_task.number
            },
            max_instances=1,
            description=description
        )
        
        # Create database records
        db_task = await task_crud.create(task_create)
        
        # 2. Then add the task to the scheduler
        from knowledge_api.manage.api.task_manage_api import task_scheduler
        await task_scheduler.add_job(db=db, task=db_task)
        
    else:
        # Create subtask
        await RoleTaskSub(db).create_tasks(auto_task.task_id, number=auto_task.number)
    
    return True
