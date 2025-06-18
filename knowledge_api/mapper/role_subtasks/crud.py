"""Role subtask CRUD operation"""
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlmodel import Session, select, text
from fastapi_pagination.ext.sqlalchemy import paginate

from knowledge_api.mapper.base_crud import BaseCRUD
from knowledge_api.mapper.role_subtasks.base import (
    RoleSubtask, 
    RoleSubtaskCreate, 
    RoleSubtaskUpdate, 
    UserSubtaskRelation, 
    UserSubtaskRelationCreate, 
    UserSubtaskRelationUpdate,
    RoleSubtaskResponse
)
from knowledge_api.utils import generate_id


class RoleSubtaskCRUD(BaseCRUD[RoleSubtask, RoleSubtaskCreate, RoleSubtaskUpdate, Dict[str, Any], RoleSubtaskResponse, str]):
    """Role subtask CRUD operation class"""
    
    def __init__(self, db: Session):
        """Initialize CRUD operation

@Param db: database session"""
        super().__init__(db, RoleSubtask)

    async def create(self, *, subtask: RoleSubtaskCreate = None, obj_in: RoleSubtaskCreate = None) -> RoleSubtask:
        """Create subtasks (compatible with legacy APIs)

@Param subtask: Subtask creation model (old API)
@Param obj_in: Subtask creation model (new API)
@Return: created subtask"""
        create_data = subtask if subtask is not None else obj_in
        
        db_subtask = RoleSubtask.from_orm(create_data)
        db_subtask.id = str(generate_id())
        db_subtask.create_time = datetime.now()
        db_subtask.update_time = datetime.now()

        self.db.add(db_subtask)
        self.db.commit()
        self.db.refresh(db_subtask)
        return db_subtask
        
    async def get_all_paginated(self):
        """Get all subtasks (paginated version, supports fastapi-pagination)

@Return: paging subtask list"""
        query = self.db.query(self.model)
        return paginate(query)

    async def get_by_task_id(self, task_id: str, skip: int = 0, limit: int = 100) -> List[RoleSubtask]:
        """Get the subtask list by task ID

@Param task_id: main task ID
@param skip: number of records skipped
@Param limit: limit the number of records
@return: subtask list"""
        return await self.get_all(filters={"task_id": task_id}, skip=skip, limit=limit)
        
    async def get_by_task_id_paginated(self, task_id: str):
        """Get the subtask list by task ID (paginated version, supports fastapi-pagination)

@Param task_id: main task ID
@Return: paging subtask list"""
        query = self.db.query(self.model).filter(self.model.task_id == task_id)
        return paginate(query)

    async def delete_by_task_id(self, task_id: str) -> bool:
        """Delete all related subtasks with the main task ID

@Param task_id: main task ID
@Return: whether the deletion was successful"""
        # Direct SQL Delete All
        statement = text("DELETE FROM llm_role_subtasks WHERE task_id = :task_id")
        self.db.exec(statement.bindparams(task_id=task_id))
        self.db.commit()
        return True


class UserSubtaskRelationCRUD(BaseCRUD[UserSubtaskRelation, UserSubtaskRelationCreate, UserSubtaskRelationUpdate, Dict[str, Any], UserSubtaskRelation, int]):
    """User subtask association CRUD action class"""
    
    def __init__(self, db: Session):
        """Initialize CRUD operation

@Param db: database session"""
        super().__init__(db, UserSubtaskRelation)

    async def create(self, *, relation: UserSubtaskRelationCreate = None, obj_in: UserSubtaskRelationCreate = None) -> UserSubtaskRelation:
        """Create user subtask associations (compatible with legacy APIs)

@Param relation: User subtask association creation model (old API)
@Param obj_in: User subtask association creation model (new API)
@Return: Created user subtask association"""
        create_data = relation if relation is not None else obj_in
        
        db_relation = UserSubtaskRelation.from_orm(create_data)
        db_relation.create_time = datetime.now()
        db_relation.update_time = datetime.now()
        db_relation.start_time = datetime.now()

        self.db.add(db_relation)
        self.db.commit()
        self.db.refresh(db_relation)
        return db_relation

    async def get_by_task(self, subtask_id: str) -> Optional[UserSubtaskRelation]:
        """Get association based on subtask ID"""
        records = await self.get_all(filters={"subtask_id": subtask_id}, limit=1)
        return records[0] if records else None

    async def get_by_user_subtask(self, user_id: str, subtask_id: str) -> Optional[UserSubtaskRelation]:
        """Get associations by user ID and subtask ID

@Param user_id: User ID
@Param subtask_id: subtask ID
@Return: User subtask associated or None"""
        statement = select(self.model).where(
            (self.model.user_id == user_id) & 
            (self.model.subtask_id == subtask_id)
        )
        result = self.db.exec(statement).first()
        return result

    async def get_by_user_id(self, user_id: str, skip: int = 0, limit: int = 100) -> List[UserSubtaskRelation]:
        """Get all subtask associations completed by the user

@Param user_id: User ID
@param skip: number of records skipped
@Param limit: limit the number of records
@Return: User subtask association list"""
        return await self.get_all(filters={"user_id": user_id}, skip=skip, limit=limit)

    async def update_by_user_id_skip(self, user_id: str, subtask_id: str, status=2) -> Optional[UserSubtaskRelation]:
        """Update subtask status - fix: remove unnecessary data overwrite logic

@Param user_id: User ID
@Param subtask_id: subtask ID
@param status: status value
@Return: Updated Association or None"""
        relation = await self.get_by_user_subtask(user_id, subtask_id)
        if not relation:
            return None
        
        # Update status and time directly to remove unnecessary data overwrites
        relation.status = status
        relation.update_time = datetime.now()
        
        self.db.add(relation)
        self.db.commit()
        self.db.refresh(relation)
        return relation

    async def get_unfinished_subtasks_by_user(self, user_id: str, task_id: str = None) -> List[RoleSubtask]:
        """Get a list of unfinished subtasks for the user

@Param user_id: User ID
@Param task_id: main task ID (optional)
@Return: List of unfinished subtasks"""
        # Using native SQL queries
        if task_id:
            query = text("""
                SELECT s.* FROM llm_role_subtasks s
                LEFT JOIN user_subtask_relations r 
                ON s.id = r.subtask_id AND r.user_id = :user_id
                WHERE s.task_id = :task_id AND (r.id IS NULL OR r.status = 0)
                ORDER BY s.create_time
            """)
            result = self.db.exec(query.bindparams(user_id=user_id, task_id=task_id))
        else:
            query = text("""
                SELECT s.* FROM llm_role_subtasks s
                LEFT JOIN user_subtask_relations r 
                ON s.id = r.subtask_id AND r.user_id = :user_id
                WHERE r.id IS NULL OR r.status = 0
                ORDER BY s.create_time
            """)
            result = self.db.exec(query.bindparams(user_id=user_id))
            
        return list(result)

    async def get_random_unfinished_subtask(self, user_id: str, task_id: str = None) -> Optional[RoleSubtask]:
        """Get a random completely unused subtask - not by user dimension, as long as it appears in the user_subtask_relations can not be used

@Param user_id: User ID (Parameter compatibility reserved, but not used in queries)
@Param task_id: main task ID (optional)
@Return: Random unused subtasks or None"""
        # Modify logic: only query subtask_id that have not appeared in the user_subtask_relations table at all
        if task_id:
            query = text("""
                SELECT s.* FROM llm_role_subtasks s
                LEFT JOIN user_subtask_relations r ON s.id = r.subtask_id
                WHERE s.task_id = :task_id AND r.subtask_id IS NULL
                ORDER BY RAND()
                LIMIT 1
            """)
            result = self.db.exec(query.bindparams(task_id=task_id)).first()
        else:
            query = text("""
                SELECT s.* FROM llm_role_subtasks s
                LEFT JOIN user_subtask_relations r ON s.id = r.subtask_id
                WHERE r.subtask_id IS NULL
                ORDER BY RAND()
                LIMIT 1
            """)
            result = self.db.exec(query).first()
            
        return result

    async def get_user_in_progress_subtasks(self, user_id: str, task_id: str = None) -> List[RoleSubtask]:
        """Get a list of the user's ongoing subtasks

@Param user_id: User ID
@Param task_id: main task ID (optional)
@Return: List of subtasks in progress"""
        # Using native SQL queries
        if task_id:
            query = text("""
                SELECT s.* FROM llm_role_subtasks s
                JOIN user_subtask_relations r 
                ON s.id = r.subtask_id AND r.user_id = :user_id
                WHERE s.task_id = :task_id AND r.status = 0
                ORDER BY r.create_time DESC
            """)
            result = self.db.exec(query.bindparams(user_id=user_id, task_id=task_id))
        else:
            query = text("""
                SELECT s.* FROM llm_role_subtasks s
                JOIN user_subtask_relations r 
                ON s.id = r.subtask_id AND r.user_id = :user_id
                WHERE r.status = 0
                ORDER BY r.create_time DESC
            """)
            result = self.db.exec(query.bindparams(user_id=user_id))
            
        return list(result)

    async def get_first_in_progress_subtask(self, user_id: str, task_id: str = None) -> Optional[RoleSubtask]:
        """Gets the user's first ongoing subtask - changed to refer only to the state of the task_game_sessions table

@Param user_id: User ID
@Param task_id: main task ID (optional)
@Return: First ongoing subtask or None"""
        # Modified to refer only to task_game_sessions table to avoid double maintenance status
        if task_id:
            query = text("""
                SELECT s.* FROM llm_role_subtasks s
                JOIN task_game_sessions tgs 
                ON s.id = tgs.subtask_id AND tgs.user_id = :user_id
                WHERE s.task_id = :task_id AND tgs.status = 0
                ORDER BY tgs.create_time DESC
                LIMIT 1
            """)
            result = self.db.exec(query.bindparams(user_id=user_id, task_id=task_id)).first()
        else:
            query = text("""
                SELECT s.* FROM llm_role_subtasks s
                JOIN task_game_sessions tgs 
                ON s.id = tgs.subtask_id AND tgs.user_id = :user_id
                WHERE tgs.status = 0
                ORDER BY tgs.create_time DESC
                LIMIT 1
            """)
            result = self.db.exec(query.bindparams(user_id=user_id)).first()
            
        return result

    async def get_by_subtask(self,subtask_id):
        """Get associations by user ID and subtask ID

@Param user_id: User ID
@Param subtask_id: subtask ID
@Return: User subtask associated or None"""
        statement = select(self.model).where(
            (self.model.subtask_id == subtask_id)
        )
        result = self.db.exec(statement).first()
        return result