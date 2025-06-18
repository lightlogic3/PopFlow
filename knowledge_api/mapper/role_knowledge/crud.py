from sqlmodel import Session, select, or_
from typing import Optional, List, Dict, Any
from sqlalchemy import text

from knowledge_api.mapper.base_crud import BaseCRUD
from knowledge_api.utils.snowflake import generate_id
from .base import RoleKnowledge, RoleKnowledgeCreate, RoleKnowledgeUpdate, RoleKnowledgeResponse


class RoleKnowledgeCRUD(BaseCRUD[RoleKnowledge, RoleKnowledgeCreate, RoleKnowledgeUpdate, Dict[str, Any], RoleKnowledgeResponse, str]):
    """Role Knowledge Base CRUD Operation"""

    def __init__(self, db: Session):
        """Initialize the role knowledge base CRUD operation"""
        super().__init__(db, RoleKnowledge)

    async def get(self, *, knowledge_id: str) -> Optional[RoleKnowledge]:
        """Get role knowledge items by ID (compatible with old API)"""
        return await self.get_by_id(id=knowledge_id)

    async def create(self, *, obj_in: RoleKnowledgeCreate) -> RoleKnowledge:
        """Create character knowledge entries (maintain compatibility with legacy APIs)"""
        # Generate an ID using the snowflake algorithm
        db_obj = RoleKnowledge(**obj_in.dict() if hasattr(obj_in, 'dict') else obj_in.model_dump())
        db_obj.id = str(generate_id())
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    async def update(self, *, knowledge_id: str, obj_in: RoleKnowledgeUpdate) -> Optional[RoleKnowledge]:
        """Updated character knowledge items (compatible with older APIs)"""
        return await super().update(knowledge_id, obj_in)

    async def get_by_role_id(self, *, role_id: str, skip: int = 0, limit: int = 100) -> List[RoleKnowledge]:
        """Gets all knowledge items for the specified role"""
        return await self.get_all(filters={"role_id": role_id}, skip=skip, limit=limit)

    async def get_by_type(self, *, type_name: str, skip: int = 0, limit: int = 100) -> List[RoleKnowledge]:
        """Acquire knowledge items by type"""
        return await self.get_all(filters={"type": type_name}, skip=skip, limit=limit)

    async def search(self, *,
                     keyword: Optional[str] = None,
                     role_id: Optional[str] = None,
                     type_name: Optional[str] = None,
                     skip: int = 0,
                     limit: int = 100) -> List[RoleKnowledge]:
        """Search for character knowledge items"""
        query = select(self.model)

        # Add search criteria
        conditions = []
        if keyword:
            conditions.append(
                or_(
                    self.model.title.contains(keyword),
                    self.model.text.contains(keyword),
                    self.model.tags.contains(keyword)
                )
            )

        if role_id:
            conditions.append(self.model.role_id == role_id)

        if type_name:
            conditions.append(self.model.type == type_name)

        if conditions:
            for condition in conditions:
                query = query.where(condition)

        # paging
        query = query.offset(skip).limit(limit)

        # Execute Query
        results = self.db.exec(query)
        return results.all()

    async def bulk_create(self, *, objs_in: List[RoleKnowledgeCreate]) -> List[RoleKnowledge]:
        """Batch creation of character knowledge items"""
        db_objs = []
        for obj_in in objs_in:
            db_obj = RoleKnowledge(**obj_in.dict() if hasattr(obj_in, 'dict') else obj_in.model_dump())
            db_obj.id = str(generate_id())
            db_objs.append(db_obj)
            
        self.db.add_all(db_objs)
        self.db.commit()

        for obj in db_objs:
            self.db.refresh(obj)

        return db_objs

    async def delete(self, *, knowledge_id: str) -> tuple[bool, str]:
        """Delete the role knowledge entry (override the base class method to return the role ID)"""
        db_obj = await self.get_by_id(id=knowledge_id)
        if not db_obj:
            return False, ""

        self.db.delete(db_obj)
        self.db.commit()
        return True, db_obj.role_id

    async def count_by_role_id(self, *, role_id: str) -> int:
        """Count the number of knowledge items for a given role"""
        return await self.count(filters={"role_id": role_id})

    async def get_by_role_share_id(self, *, role_id: str, skip: int = 0, limit: int = 100) -> List[RoleKnowledge]:
        """Gets the knowledge item of the shared type associated with the specified role

@Param {string} role_id - Role ID to query
@param {number} skip - number of records skipped by page
@Param {number} limit - the maximum number of records returned per page
@Return {List [RoleKnowledge]} List of eligible knowledge items"""
        # Building native SQL queries using SQLAlchemy's text function
        query = text("""
            SELECT * FROM role_knowledge 
            WHERE type = 'join' 
            AND (FIND_IN_SET(:role_id, relations_role) > 0 OR relations_role = :role_id)
            LIMIT :limit OFFSET :skip
        """)
        
        # Execute native SQL queries and bind parameters
        result = self.db.exec(query.bindparams(role_id=role_id, limit=limit, skip=skip))
        
        # Convert the result to a list of RoleKnowledge objects
        return list(result)

    async def delete_by_role_id(self, role_id)->list[str]:
        """Delete all knowledge items for the specified role"""
        # Check first
        db_obj = await self.get_by_role_id(role_id=role_id)
        if not db_obj:
            return []
        # delete
        for obj in db_obj:
            self.db.delete(obj)
        self.db.commit()
        return [obj.id for obj in db_obj]