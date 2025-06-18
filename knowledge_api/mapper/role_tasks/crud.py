from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4

from sqlmodel import Session, select
from fastapi_pagination.ext.sqlalchemy import paginate

from knowledge_api.mapper.base_crud import BaseCRUD
from knowledge_api.mapper.role_subtasks import RoleSubtaskCRUD
from knowledge_api.mapper.role_tasks.base import RoleTask, RoleTaskCreate, RoleTaskUpdate, RoleTaskResponse
from knowledge_api.utils import generate_id


class RoleTaskCRUD(BaseCRUD[RoleTask, RoleTaskCreate, RoleTaskUpdate, Dict[str, Any], RoleTaskResponse, str]):
    def __init__(self, db: Session):
        """Initialize character task CRUD operation"""
        super().__init__(db, RoleTask)

    async def create(self, *, task: RoleTaskCreate = None, obj_in: RoleTaskCreate = None) -> RoleTask:
        """Create tasks (compatible with older APIs)"""
        # Use task or obj_in as parameters
        create_data = task if task is not None else obj_in
        
        db_task = RoleTask.from_orm(create_data)
        db_task.id = str(generate_id())
        db_task.create_time = datetime.now()
        db_task.update_time = datetime.now()

        self.db.add(db_task)
        self.db.commit()
        self.db.refresh(db_task)
        return db_task
        
    async def get_all_paginated(self):
        """Get all tasks (paginated version, supports fastapi-pagination)

Returns:
Page: paging task list"""
        query = self.db.query(RoleTask)
        return paginate(query)

    async def get_alls(self) -> List[RoleTask]:
        """Get all tasks (without paging restrictions)"""
        statement = select(self.model)
        results = self.db.exec(statement).all()
        return results

    async def get_by_role_id(self, role_id: str, skip: int = 0, limit: int = 100) -> List[RoleTask]:
        """Get task list by role ID"""
        return await self.get_all(filters={"role_id": role_id}, skip=skip, limit=limit)
        
    async def get_by_role_id_paginated(self, role_id: str):
        """Get task list by role ID (paginated version, supports fastapi-pagination)

Args:
role_id: Role ID

Returns:
Page: paging task list"""
        query = self.db.query(self.model).filter(self.model.role_id == role_id)
        return paginate(query)

    async def delete_by_role_id(self, role_id: str) -> bool:
        """Delete all related tasks by role ID"""
        tasks = await self.get_by_role_id(role_id=role_id)
        if not tasks:
            return False
        
        for task in tasks:
            self.db.delete(task)
            sub_task=RoleSubtaskCRUD(self.db)
            await sub_task.delete_by_task_id(task_id=task.id)
        
        self.db.commit()
        return True 