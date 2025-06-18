"""Timed Task Management CRUD Operations"""
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlmodel import Session, select, and_, or_, desc
from fastapi_pagination.ext.sqlalchemy import paginate

from knowledge_api.mapper.base_crud import BaseCRUD
from knowledge_api.mapper.task_manage.base import (
    TaskManage, 
    TaskManageCreate, 
    TaskManageUpdate, 
    TaskExecutionLog, 
    TaskExecutionLogCreate,
    TaskStatus,
    TaskManageResponse
)
from knowledge_api.utils import generate_id


class TaskManageCRUD(BaseCRUD[TaskManage, TaskManageCreate, TaskManageUpdate, Dict[str, Any], TaskManageResponse, str]):
    """Scheduled task management CRUD operation class"""

    def __init__(self, db: Session):
        """Initialize CRUD operation

@Param db: database session"""
        super().__init__(db, TaskManage)

    async def update_status(self, task_id: str, status: TaskStatus) -> Optional[TaskManage]:
        """Update task status

@Param task_id: Task ID
@param status: new status
@Return: Updated task or None"""
        task = await self.get_by_id(task_id)
        if not task:
            return None

        task.status = status
        task.update_time = datetime.now()

        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task


    async def create(self, task: TaskManageCreate = None, obj_in: TaskManageCreate = None) -> TaskManage:
        """Create a new task (compatible with the old API)

@Param task: task creation data (old API)
@Param obj_in: Task creation data (new API)
@Return: created task"""
        # Use task or obj_in as parameters
        create_data = task if task is not None else obj_in

        if not create_data.id:
            create_data.id = str(generate_id())

        return await super().create(obj_in=create_data)

    async def get_by_status(self, status: TaskStatus, skip: int = 0, limit: int = 100) -> List[TaskManage]:
        """Get tasks by status

@param status: task status
@param skip: number of records skipped
@Param limit: limit the number of records
@return: task list"""
        return await self.get_all(filters={"status": status}, skip=skip, limit=limit)
        
    async def get_by_status_paginated(self, status: TaskStatus, include_temp_tasks: bool = True):
        """Get tasks by status (paginated version)

@param status: task status
@Param include_temp_tasks: Whether to include system temporary tasks
@Return: paging task list"""
        query = self.db.query(self.model).filter(self.model.status == status)
        
        # If no system temporary tasks are included, filter them out
        if not include_temp_tasks:
            query = query.filter(~((self.model.task_type == "temporary task") & self.model.id.startswith("temp_task_")))
            
        return paginate(query)

    async def get_by_type(self, task_type: str, skip: int = 0, limit: int = 100) -> List[TaskManage]:
        """Get tasks by type

@Param task_type: task type
@param skip: number of records skipped
@Param limit: limit the number of records
@return: task list"""
        return await self.get_all(filters={"task_type": task_type}, skip=skip, limit=limit)
        
    async def get_by_type_paginated(self, task_type: str, include_temp_tasks: bool = True):
        """Get tasks by type (paginated version)

@Param task_type: task type
@Param include_temp_tasks: Whether to include system temporary tasks
@Return: paging task list"""
        query = self.db.query(self.model).filter(self.model.task_type == task_type)
        
        # If no system temporary tasks are included, filter them out
        if not include_temp_tasks:
            query = query.filter(~((self.model.task_type == "temporary task") & self.model.id.startswith("temp_task_")))
            
        return paginate(query)

    async def get_by_ids(self, task_ids: List[str]) -> List[TaskManage]:
        """Get task by ID list

@Param task_ids: Task ID list
@return: task list"""
        statement = select(self.model).where(self.model.id.in_(task_ids))
        results = self.db.exec(statement).all()
        return results
        
    async def get_by_ids_paginated(self, task_ids: List[str], include_temp_tasks: bool = True):
        """Get tasks by ID list (paginated version)

@Param task_ids: Task ID list
@Param include_temp_tasks: Whether to include system temporary tasks
@Return: paging task list"""
        query = self.db.query(self.model).filter(self.model.id.in_(task_ids))
        
        # If no system temporary tasks are included, filter them out
        if not include_temp_tasks:
            query = query.filter(~((self.model.task_type == "temporary task") & self.model.id.startswith("temp_task_")))
            
        return paginate(query)

    async def get_all_paginated(self, include_temp_tasks: bool = True, **kwargs):
        """Get all tasks (paginated version)

@Param include_temp_tasks: Whether to include system temporary tasks
@Return: paging task list"""
        query = self.db.query(self.model)
        
        # If no system temporary tasks are included, filter them out
        if not include_temp_tasks:
            query = query.filter(~((self.model.task_type == "temporary task") & self.model.id.startswith("temp_task_")))
            
        return paginate(query)

    async def get_pending_tasks(self, skip: int = 0, limit: int = 100) -> List[TaskManage]:
        """Get the task waiting to be executed

@param skip: number of records skipped
@Param limit: limit the number of records
@return: task list"""
        statement = select(self.model).where(
            and_(
                self.model.status.in_([TaskStatus.PENDING, TaskStatus.RUNNING]),
                self.model.next_run_time <= datetime.now()
            )
        ).order_by(self.model.next_run_time).offset(skip).limit(limit)
        
        results = self.db.exec(statement).all()
        return results
        
    async def get_pending_tasks_paginated(self, include_temp_tasks: bool = True):
        """Get the task waiting to be executed (paged version)

@Param include_temp_tasks: Whether to include system temporary tasks
@Return: paging task list"""
        query = self.db.query(self.model).filter(
            and_(
                self.model.status.in_([TaskStatus.PENDING, TaskStatus.RUNNING]),
                self.model.next_run_time <= datetime.now()
            )
        ).order_by(self.model.next_run_time)
        
        # If no system temporary tasks are included, filter them out
        if not include_temp_tasks:
            query = query.filter(~((self.model.task_type == "temporary task") & self.model.id.startswith("temp_task_")))
            
        return paginate(query)

    async def update_next_run_time(self, task_id: str, next_run_time: datetime) -> Optional[TaskManage]:
        """Update task next run time

@Param task_id: Task ID
@Param next_run_time: next run time
@Return: Updated task or None"""
        task = await self.get_by_id(task_id)
        if not task:
            return None
        
        # Update only the next runtime
        task.next_run_time = next_run_time
        task.update_time = datetime.now()
        
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task


class TaskExecutionLogCRUD(BaseCRUD[TaskExecutionLog, TaskExecutionLogCreate, Dict[str, Any], Dict[str, Any], TaskExecutionLog, str]):
    """Task execution log CRUD operation class"""

    def __init__(self, db: Session):
        """Initialize CRUD operation

@Param db: database session"""
        super().__init__(db, TaskExecutionLog)

    async def create(self, log: TaskExecutionLogCreate = None, obj_in: TaskExecutionLogCreate = None) -> TaskExecutionLog:
        """Create execution logs (compatible with legacy APIs)

@Param log: log creation data (old API)
@Param obj_in: log creation data (new API)
@Return: Created log"""
        # Use log or obj_in as parameters
        create_data = log if log is not None else obj_in
        
        # 先创建一个字典并添加ID，然后用它创建模型实例
        data_dict = create_data.model_dump()
        data_dict['id'] = str(generate_id())
        
        # 使用包含ID的数据创建模型实例
        db_log = TaskExecutionLog.model_validate(data_dict)
        db_log.start_time = datetime.now()
        
        self.db.add(db_log)
        self.db.commit()
        self.db.refresh(db_log)
        return db_log

    async def update(self, log_id: str, end_time: datetime, status: TaskStatus, 
                    result: Optional[str] = None, error: Optional[str] = None) -> Optional[TaskExecutionLog]:
        """update execution log

@Param log_id: Log ID
@Param end_time: end time
@param status: task status
@Param result: execution result
@param error: error message
@Return: Updated log or None"""
        log = await self.get_by_id(log_id)
        if not log:
            return None
        
        log.end_time = end_time
        log.status = status
        if result is not None:
            log.result = result
        if error is not None:
            log.error = error
        
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    async def get_by_task_id(self, task_id: str, skip: int = 0, limit: int = 100) -> List[TaskExecutionLog]:
        """Get the execution log of the task

@Param task_id: Task ID
@param skip: number of records skipped
@Param limit: limit the number of records
@return: log list"""
        return await self.get_all(filters={"task_id": task_id}, skip=skip, limit=limit)
        
    async def get_by_task_id_paginated(self, task_id: str):
        """Get the execution log of the task (paged version)

@Param task_id: Task ID
@Return: list of paging logs"""
        query = self.db.query(self.model).filter(self.model.task_id == task_id).order_by(desc(self.model.start_time))
        return paginate(query)

    async def get_latest_by_task_id(self, task_id: str) -> Optional[TaskExecutionLog]:
        """Get the latest execution log of the task

@Param task_id: Task ID
@Return: Latest log or None"""
        statement = select(self.model).where(self.model.task_id == task_id).order_by(desc(self.model.start_time)).limit(1)
        result = self.db.exec(statement).first()
        return result