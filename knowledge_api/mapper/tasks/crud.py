from typing import List, Optional, Dict, Any

from sqlmodel import Session, select
from fastapi_pagination.ext.sqlmodel import paginate
from knowledge_api.mapper.base_crud import BaseCRUD
from knowledge_api.mapper.tasks.base import Task, TaskCreate, TaskUpdate, TaskResponse


class TaskCRUD(BaseCRUD[Task, TaskCreate, TaskUpdate, Dict[str, Any], TaskResponse, int]):
    """Task CRUD operation class"""
    def __init__(self, db: Session):
        """initialization

@Param db: database session"""
        super().__init__(db, Task)

    async def create(self, task: TaskCreate = None, obj_in: TaskCreate = None) -> Task:
        """Create tasks (compatible with older APIs)

@Param task: Task creation model (old API)
@Param obj_in: Task Creation Model (New API)
@Return: created task"""
        # Use task or obj_in as parameters
        create_data = task if task is not None else obj_in
        
        # Remove role_relations field because it is not in the Task model
        role_relations = None
        if hasattr(create_data, 'role_relations'):
            role_relations = create_data.role_relations
            task_dict = create_data.model_dump(exclude={"role_relations"}) if hasattr(create_data, 'model_dump') else create_data.dict(exclude={"role_relations"})
            create_data = TaskCreate.model_validate(task_dict) if hasattr(TaskCreate, 'model_validate') else TaskCreate(**task_dict)
        
        # Create using base class methods
        return await super().create(obj_in=create_data)

    async def get_by_id(self, id: int) -> Optional[Task]:
        """Get task by ID

@Param task_id: Task ID
@Return: Task object or None"""
        return await super().get_by_id(id=id)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Task]:
        """Get all tasks

@param skip: number of skips
@Param limit: limit quantity
@return: task list"""
        return await super().get_all(skip=skip, limit=limit)
    
    async def update(self, task_id: int, task_update: TaskUpdate) -> Optional[Task]:
        """update task

@Param task_id: Task ID
@Param task_update: Task Update Model
@Return: Updated task or None"""
        # 处理 role_relations 字段，将其从更新数据中排除
        update_data = task_update
        if hasattr(update_data, 'role_relations'):
            # 使用模型的 model_dump 或 dict 方法
            update_dict = update_data.model_dump(exclude={"role_relations"}) if hasattr(update_data, 'model_dump') else update_data.dict(exclude={"role_relations"})
            update_data = TaskUpdate.model_validate(update_dict) if hasattr(TaskUpdate, 'model_validate') else TaskUpdate(**update_dict)
            
        return await super().update(id=task_id, obj_in=update_data)

    async def delete(self, task_id: int) -> bool:
        """Delete task

@Param task_id: Task ID
@Return: whether the deletion was successful"""
        return await super().delete(id=task_id) 