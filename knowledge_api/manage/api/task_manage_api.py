"""Timed Task Management API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi_pagination import Page

from knowledge_api.framework.database.database import get_session
from knowledge_api.framework.task_manage.scheduler import TaskScheduler
from knowledge_api.mapper.task_manage import (
    TaskManage,
    TaskManageCreate,
    TaskManageUpdate,
    TaskManageResponse,
    TaskStatus,
    TriggerType,
    TaskManageCRUD,
    TaskExecutionLog,
    TaskExecutionLogResponse,
    TaskExecutionLogCRUD
)
from knowledge_api.framework.database.db_config import get_db_settings
# Import task registrar
from knowledge_api.scheduler_task import get_all_tasks
# Import Temporary Task Manager
from knowledge_api.framework.task import get_task_manager

# Create a global scheduler instance
task_scheduler = TaskScheduler(get_db_settings().DATABASE_URL)

router_task_manage = APIRouter(prefix="/task-manage", tags=["timed task management"])


@router_task_manage.on_event("startup")
async def startup_event():
    """Start the scheduler and load tasks at app startup"""
    await task_scheduler.start()
    
    # Get database session
    db = next(get_session())
    try:
        # Load all active tasks
        await task_scheduler.load_tasks(db)
    finally:
        db.close()


@router_task_manage.on_event("shutdown")
async def shutdown_event():
    """Close scheduler when app closes"""
    await task_scheduler.shutdown()


@router_task_manage.get("/registered-tasks", response_model=List[Dict[str, Any]])
async def get_registered_tasks():
    """Get all registered timed task functions

Returns a list of all tasks registered with scheduled_task Decorator"""
    return get_all_tasks()


@router_task_manage.post("/", response_model=TaskManageResponse)
async def create_task(
    task: TaskManageCreate,
    db: Session = Depends(get_session)
) -> TaskManage:
    """Create a timed task

@Param task: task creation data
@Param db: database session
@Return: created task"""
    crud = TaskManageCRUD(db)
    db_task = await crud.create(task)
    
    # Add to scheduler
    await task_scheduler.add_job(db, db_task)
    
    return db_task


@router_task_manage.get("/", response_model=Page[TaskManageResponse])
async def list_tasks(
    status: Optional[TaskStatus] = None,
    task_type: Optional[str] = None,
    task_ids: Optional[str] = None,
    include_temp_tasks: bool = Query(default=True),
    db: Session = Depends(get_session)
) -> Page[TaskManageResponse]:
    """Get a timed task list, support filtering by status and type (pagination)

@param status: task status filter
@Param task_type: task type filtering
@Param task_ids: Task ID filtering, multiple IDs separated by commas
@Param include_temp_tasks: Whether to include system-generated temporary tasks
@Param db: database session
@Return: paging task list"""
    crud = TaskManageCRUD(db)
    
    # Handling multiple task ID filtering
    if task_ids:
        ids_list = [id.strip() for id in task_ids.split(",")]
        return await crud.get_by_ids_paginated(ids_list, include_temp_tasks)
    elif status:
        return await crud.get_by_status_paginated(status, include_temp_tasks)
    elif task_type:
        return await crud.get_by_type_paginated(task_type, include_temp_tasks)
    else:
        return await crud.get_all_paginated(include_temp_tasks)


@router_task_manage.put("/{task_id}", response_model=TaskManageResponse)
async def update_task(
    task_id: str,
    task_update: TaskManageUpdate,
    db: Session = Depends(get_session)
) -> TaskManage:
    """update timed task

@Param task_id: Task ID
@Param task_update: task update data
@Param db: database session
@Return: updated task"""
    crud = TaskManageCRUD(db)
    updated_task = await crud.update(task_id, task_update)
    if not updated_task:
        raise HTTPException(status_code=404, detail="Task does not exist")

    # Update tasks in the scheduler
    await task_scheduler.remove_job(db, task_id)
    await task_scheduler.add_job(db, updated_task)

    return updated_task


@router_task_manage.delete("/{task_id}", response_model=bool)
async def delete_task(
    task_id: str,
    db: Session = Depends(get_session)
) -> bool:
    """Delete a timed task

@Param task_id: Task ID
@Param db: database session
@Return: whether the deletion was successful"""
    # Remove from scheduler first
    await task_scheduler.remove_job(db, task_id)
    
    # Delete from the database
    crud = TaskManageCRUD(db)
    success = await crud.delete(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task does not exist")
    
    return True


@router_task_manage.post("/{task_id}/pause", response_model=bool)
async def pause_task(
    task_id: str,
    db: Session = Depends(get_session)
) -> bool:
    """Pause a scheduled task

@Param task_id: Task ID
@Param db: database session
@Return: whether to pause successfully"""
    crud = TaskManageCRUD(db)
    task = await crud.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task does not exist")
    
    success = await task_scheduler.pause_job(db, task_id)
    if not success:
        raise HTTPException(status_code=500, detail="Suspend task failed")
    
    return True


@router_task_manage.post("/{task_id}/resume", response_model=bool)
async def resume_task(
    task_id: str,
    db: Session = Depends(get_session)
) -> bool:
    """Resume timed task

@Param task_id: Task ID
@Param db: database session
@Return: whether the recovery was successful"""
    crud = TaskManageCRUD(db)
    task = await crud.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task does not exist")
    
    success = await task_scheduler.resume_job(db, task_id)
    if not success:
        raise HTTPException(status_code=500, detail="Recovery task failed")
    
    return True


@router_task_manage.post("/{task_id}/trigger", response_model=bool)
async def trigger_task(
    task_id: str,
    db: Session = Depends(get_session)
) -> bool:
    """Trigger timed task execution immediately

@Param task_id: Task ID
@Param db: database session
@Return: whether it was successfully triggered"""
    crud = TaskManageCRUD(db)
    task = await crud.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task does not exist")
    
    success = await task_scheduler.trigger_job(db, task_id)
    if not success:
        raise HTTPException(status_code=500, detail="Trigger task failed")
    
    return True


@router_task_manage.get("/{task_id}/logs", response_model=Page[TaskExecutionLogResponse])
async def get_task_logs(
    task_id: str,
    db: Session = Depends(get_session)
) -> Page[TaskExecutionLogResponse]:
    """Get timed task execution log (paging)

@Param task_id: Task ID
@Param db: database session
@Return: list of paging logs"""
    crud = TaskManageCRUD(db)
    task = await crud.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task does not exist")

    log_crud = TaskExecutionLogCRUD(db)
    return await log_crud.get_by_task_id_paginated(task_id)


@router_task_manage.get("/temp-tasks", response_model=List[Dict[str, Any]])
async def get_temp_tasks(
    status: Optional[str] = None,
    task_ids: Optional[str] = None
):
    """Get all temporary tasks

@param status: task status filter
@Param task_ids: Task ID filtering, multiple IDs separated by commas
@Return: temporary task list"""
    task_manager = get_task_manager()
    all_tasks = task_manager.get_all_tasks()
    
    # Filter out temporary tasks (IDs starting with temp_task_)
    temp_tasks = {task_id: task_info for task_id, task_info in all_tasks.items() 
                 if task_id.startswith("temp_task_")}
    
    # Handling multiple task ID filtering
    if task_ids:
        ids_list = [id.strip() for id in task_ids.split(",")]
        temp_tasks = {task_id: task_info for task_id, task_info in temp_tasks.items() 
                     if task_id in ids_list}
    
    # processing state filtering
    if status:
        temp_tasks = {task_id: task_info for task_id, task_info in temp_tasks.items() 
                     if task_info["status"] == status}
    
    # Convert to list form and return
    return [
        {
            "id": task_id,
            "description": task_info["description"],
            "status": task_info["status"],
            "start_time": task_info["start_time"],
            "end_time": task_info["end_time"],
            "duration": task_info["duration"],
            "error_message": task_info["error_message"]
        }
        for task_id, task_info in temp_tasks.items()
    ]


@router_task_manage.get("/temp-tasks/{task_id}", response_model=Dict[str, Any])
async def get_temp_task(task_id: str):
    """Get the details of a single temporary task

@Param task_id: Temporary Task ID
@Return: task details"""
    task_manager = get_task_manager()
    all_tasks = task_manager.get_all_tasks()
    
    task_info = all_tasks[task_id]
    return {
        "id": task_id,
        "description": task_info["description"],
        "status": task_info["status"],
        "start_time": task_info["start_time"],
        "end_time": task_info["end_time"],
        "duration": task_info["duration"],
        "error_message": task_info["error_message"]
    }


@router_task_manage.post("/temp-tasks/{task_id}/cancel", response_model=bool)
async def cancel_temp_task(task_id: str):
    """Cancel temporary task

@Param task_id: Temporary Task ID
@Return: whether the cancellation was successful"""
    task_manager = get_task_manager()
    success = await task_manager.cancel_task(task_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="The temporary task does not exist or cannot be cancelled")
    
    return True


@router_task_manage.get("/temp-tasks/{task_id}/logs", response_model=Page[TaskExecutionLogResponse])
async def get_temp_task_logs(
    task_id: str,
    db: Session = Depends(get_session)
) -> Page[TaskExecutionLogResponse]:
    """Get temporary task execution log (paging)

@Param task_id: Temporary Task ID
@Param db: database session
@Return: list of paging logs"""
    # Check if the task exists
    all_tasks = get_task_manager().get_all_tasks()
    if task_id not in all_tasks and not task_id.startswith("temp_task_"):
        # If not in memory, try searching from the database
        crud = TaskManageCRUD(db)
        task = await crud.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Temporary tasks do not exist")
    
    # Get log
    log_crud = TaskExecutionLogCRUD(db)
    return await log_crud.get_by_task_id_paginated(task_id)


@router_task_manage.get("/{task_id}", response_model=TaskManageResponse)
async def get_task(
        task_id: str,
        db: Session = Depends(get_session)
) -> TaskManage:
    """Get a single timed task

@Param task_id: Task ID
@Param db: database session
@return: task information"""
    crud = TaskManageCRUD(db)
    task = await crud.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task does not exist")
    return task