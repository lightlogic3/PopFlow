from sqlmodel import Session, select, or_, func
from typing import Optional, List, Dict, Any, Literal
import uuid
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate

from knowledge_api.mapper.base_crud import BaseCRUD
from knowledge_api.utils.snowflake import generate_id
from .base import WorldKnowledge, WorldKnowledgeCreate, WorldKnowledgeUpdate, WorldKnowledgeResponse


class WorldKnowledgeCRUD(BaseCRUD[WorldKnowledge, WorldKnowledgeCreate, WorldKnowledgeUpdate, Dict[str, Any], WorldKnowledgeResponse, str]):
    """Worldview Knowledge Base CRUD Operation"""
    
    def __init__(self, db: Session):
        """Initialize the Worldview Knowledge Base CRUD operation"""
        super().__init__(db, WorldKnowledge)
    
    async def create(self, *, obj_in: WorldKnowledgeCreate) -> WorldKnowledge:
        """Create worldview knowledge items"""
        # Generate an ID using the snowflake algorithm
        db_obj = WorldKnowledge(**obj_in.dict() if hasattr(obj_in, 'dict') else obj_in.model_dump())
        db_obj.id = str(generate_id())
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    async def get(self, *, knowledge_id: str) -> Optional[WorldKnowledge]:
        """Obtain worldview knowledge items according to ID (compatible with old API)"""
        return await self.get_by_id(id=knowledge_id)
    
    async def get_by_worlds_id(self, *, worlds_id: str, skip: int = 0, limit: int = 100) -> List[WorldKnowledge]:
        """Acquire all knowledge items for a given world design"""
        return await self.get_all(filters={"worlds_id": worlds_id}, skip=skip, limit=limit)
    
    async def get_by_type(self, *, type_name: Literal["scene", "world view"], skip: int = 0, limit: int = 100) -> List[WorldKnowledge]:
        """Acquire knowledge items by type"""
        return await self.get_all(filters={"type": type_name}, skip=skip, limit=limit)
    
    async def get_by_relations_role(self, *, role_id: str, skip: int = 0, limit: int = 100) -> List[WorldKnowledge]:
        """Gets the world view knowledge item associated with the specified role"""
        statement = select(WorldKnowledge).where(WorldKnowledge.relations_role.contains(role_id)).offset(skip).limit(limit)
        results = self.db.exec(statement).all()
        return results
    
    async def search(self, *,
               keyword: Optional[str] = None,
               worlds_id: Optional[str] = None,
               type_name: Optional[Literal["scene", "world view"]] = None,
               role_id: Optional[str] = None,
               skip: int = 0,
               limit: int = 100) -> List[WorldKnowledge]:
        """Search for worldview knowledge items"""
        query = select(WorldKnowledge)

        # Add search criteria
        conditions = []
        if keyword:
            conditions.append(
                or_(
                    WorldKnowledge.title.contains(keyword),
                    WorldKnowledge.text.contains(keyword),
                    WorldKnowledge.tags.contains(keyword)
                )
            )
        
        if worlds_id:
            conditions.append(WorldKnowledge.worlds_id == worlds_id)
            
        if type_name:
            conditions.append(WorldKnowledge.type == type_name)
            
        if role_id:
            conditions.append(WorldKnowledge.relations_role.contains(role_id))
        
        if conditions:
            for condition in conditions:
                query = query.where(condition)

        # paging
        query = query.offset(skip).limit(limit)

        # Execute Query
        results = self.db.exec(query)
        return results.all()
    
    async def update(
        self,
        knowledge_id: str,
        obj_in: WorldKnowledgeUpdate
    ) -> Optional[WorldKnowledge]:
        """Update worldview knowledge items"""
        return await super().update(id=knowledge_id, obj_in=obj_in)
    
    async def bulk_create(self, *, objs_in: List[WorldKnowledgeCreate]) -> List[WorldKnowledge]:
        """Batch creation of worldview knowledge items"""
        db_objs = []
        for obj_in in objs_in:
            db_obj = WorldKnowledge(**obj_in.dict() if hasattr(obj_in, 'dict') else obj_in.model_dump())
            db_obj.id = str(generate_id())
            db_objs.append(db_obj)
            
        self.db.add_all(db_objs)
        self.db.commit()
        
        for obj in db_objs:
            self.db.refresh(obj)
            
        return db_objs
    
    async def delete(self, *, knowledge_id: str) -> tuple[bool,str]:
        """Delete worldview knowledge entries (extend base class methods to return additional information)"""
        db_obj = await self.get_by_id(id=knowledge_id)
        if not db_obj:
            return False, ""

        worlds_id = db_obj.worlds_id
        result = await super().delete(id=knowledge_id)
        return result, worlds_id
    
    async def count_by_worlds_id(self, *, worlds_id: str) -> int:
        """Count the number of knowledge items for a given world design"""
        return await self.count(filters={"worlds_id": worlds_id})

    async def get_by_id(self, *, knowledge_id: str = None, id: str = None) -> Optional[WorldKnowledge]:
        """Acquire worldview knowledge points according to ID (compatible with old and new APIs)"""
        id_value = id if id is not None else knowledge_id
        return await super().get_by_id(id=id_value)
        
    async def get_by_ids(self, knowledge_ids: List[str]) -> List[WorldKnowledge]:
        """Obtain world view knowledge points in batches according to the ID list"""
        if not knowledge_ids:
            return []
            
        query = select(WorldKnowledge).where(WorldKnowledge.id.in_(knowledge_ids))
        return self.db.exec(query).all()

    async def get_by_world_id(self, *, world_id: str, skip: int = 0, limit: int = 100) -> List[WorldKnowledge]:
        """Get a list of knowledge points according to the world ID (compatible with old parameter names)"""
        return await self.get_by_worlds_id(worlds_id=world_id, skip=skip, limit=limit)

    async def get_by_worlds_ids(self, worlds_ids: List[str]) -> List[WorldKnowledge]:
        """Get a list of knowledge points based on multiple world IDs"""
        if not worlds_ids:
            return []

        query = select(WorldKnowledge).where(WorldKnowledge.worlds_id.in_(worlds_ids))
        return self.db.exec(query).all()

    async def get_by_worlds_id_paginated(self, *, worlds_id: str, params: Optional[Params] = None) -> Page[WorldKnowledge]:
        """Acquire knowledge items for the specified world design (paginated version)"""
        query = select(WorldKnowledge).where(WorldKnowledge.worlds_id == worlds_id)
        return paginate(self.db, query, params)