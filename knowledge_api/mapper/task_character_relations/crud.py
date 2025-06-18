from sqlmodel import Session, select
from typing import List, Optional, Dict, Any

from knowledge_api.mapper.base_crud import BaseCRUD
from knowledge_api.mapper.task_character_relations.base import (
    TaskCharacterRelation, 
    TaskCharacterRelationCreate, 
    TaskCharacterRelationUpdate,
    TaskCharacterRelationResponse
)


class TaskCharacterRelationCRUD(BaseCRUD[TaskCharacterRelation, TaskCharacterRelationCreate, TaskCharacterRelationUpdate, Dict[str, Any], TaskCharacterRelationResponse, int]):
    """Task role association CRUD action class"""
    def __init__(self, db: Session):
        """initialization

@Param db: database session"""
        super().__init__(db, TaskCharacterRelation)

    async def create(self, *, relation: TaskCharacterRelationCreate = None, obj_in: TaskCharacterRelationCreate = None) -> TaskCharacterRelation:
        """Create task role associations (compatible with legacy APIs)

@Param relation: Task role association creation model (old API parameter)
@Param obj_in: Task role association creation model (new API parameters)
@Return: created task role association"""
        create_data = relation if relation is not None else obj_in
        return await super().create(obj_in=create_data)

    async def get_by_relation_id(self, relation_id: int) -> Optional[TaskCharacterRelation]:
        """Get role associations by ID (backward compatible with old method names)

@Param relation_id: Association ID
@Return: Task Role Association"""
        return await self.get_by_id(id=relation_id)

    async def bulk_create(self, task_id: int, relations: List[dict]) -> List[TaskCharacterRelation]:
        """Batch creation of task role associations

@Param task_id: Task ID
@Param relations: Role association list, each element contains role_id and character_level, optional llm_model, voice, character_setting
@Return: Created task role association list"""
        created_relations = []
        for relation in relations:
            db_relation = TaskCharacterRelation(
                task_id=task_id,
                role_id=relation["role_id"],
                llm_model=relation.get("llm_model"),
                voice=relation.get("voice"),
                character_setting=relation.get("character_setting")
            )
            self.db.add(db_relation)
            created_relations.append(db_relation)
        
        self.db.commit()
        for relation in created_relations:
            self.db.refresh(relation)
        
        return created_relations

    async def get_by_task_id(self, task_id: int) -> List[TaskCharacterRelation]:
        """Get all role associations by task ID

@Param task_id: Task ID
@Return: task role association list"""
        return await self.get_all(filters={"task_id": task_id})

    async def get_by_role_id(self, role_id: str) -> List[TaskCharacterRelation]:
        """Get all task associations by role ID

@Param role_id: Role ID
@Return: task role association list"""
        return await self.get_all(filters={"role_id": role_id})

    async def delete_by_task_id(self, task_id: int) -> bool:
        """Delete all role associations by task ID

@Param task_id: Task ID
@Return: whether the deletion was successful"""
        relations = await self.get_by_task_id(task_id=task_id)
        
        if not relations:
            return False
            
        for relation in relations:
            self.db.delete(relation)
        
        self.db.commit()
        return True

    async def delete_by_role_id(self, role_id: str) -> bool:
        """Delete all task associations by role ID

@Param role_id: Role ID
@Return: whether the deletion was successful"""
        relations = await self.get_by_role_id(role_id=role_id)
        
        if not relations:
            return False
            
        for relation in relations:
            self.db.delete(relation)
        
        self.db.commit()
        return True 