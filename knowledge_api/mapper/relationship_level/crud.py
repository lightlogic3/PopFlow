from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from datetime import datetime

from knowledge_api.mapper.base_crud import BaseCRUD
from .base import (
    RelationshipLevel,
    RelationshipLevelCreate,
    RelationshipLevelUpdate,
    RelationshipLevelResponse
)

class RelationshipLevelCRUD(BaseCRUD[RelationshipLevel, RelationshipLevelCreate, RelationshipLevelUpdate, Dict[str, Any], RelationshipLevelResponse, int]):
    """Relationship level CRUD operation class"""
    
    def __init__(self, db: Session):
        """Initialize relational level CRUD operation"""
        super().__init__(db, RelationshipLevel)

    async def get_by_role_id(self, role_id: str) -> List[RelationshipLevel]:
        """Get relationship level based on role ID"""
        return await self.get_all(filters={"role_id": role_id})

    async def get_by_relationship_name(self, relationship_name: str) -> Optional[RelationshipLevel]:
        """Get relationship rank by relationship name"""
        records = await self.get_all(filters={"relationship_name": relationship_name}, limit=1)
        return records[0] if records else None

    async def delete_by_role_id(self, role_id):
        """Delete relationship level based on role ID"""
        statement = select(RelationshipLevel).where(RelationshipLevel.role_id == role_id)
        result = self.db.exec(statement).all()
        for record in result:
            self.db.delete(record)
        self.db.commit()
        return None