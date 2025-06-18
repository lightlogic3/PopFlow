from sqlmodel import Session, select
from typing import Optional, List, Dict, Any
import uuid

from .base import World, WorldCreate, WorldUpdate, WorldResponse
from knowledge_api.mapper.base_crud import BaseCRUD


class WorldCRUD(BaseCRUD[World, WorldCreate, WorldUpdate, Dict[str, Any], WorldResponse, str]):
    """Worldview CRUD operation"""

    def __init__(self, db: Session):
        super().__init__(db, World)

    async def create(self, *, world: WorldCreate) -> World:
        """Create a worldview"""
        # Generate UUID as primary key
        world_data = world.dict()
        world_data["id"] = str(uuid.uuid4())
        return await super().create(world, id=world_data["id"])

    # Override _apply_filters methods to support worldview-specific filtering logic
    def _apply_filters(self, query, filter_data: Dict[str, Any]):
        """Apply Filter Criteria to Queries"""
        for field, value in filter_data.items():
            if value is not None:
                if field == "type" and hasattr(self.model, "type"):
                    query = query.where(self.model.type == value)
                elif hasattr(self.model, field):
                    query = query.where(getattr(self.model, field) == value)
        return query

    async def get_by_type(self, *, world_type: str, skip: int = 0, limit: int = 100) -> List[World]:
        """Get a list of worldviews by type"""
        filters = {"type": world_type}
        return await self.get_all(skip=skip, limit=limit, filters=filters, order_by="sort", order_desc=True)

    async def increment_knowledge_count(self, *, id: str, count: int) -> Optional[World]:
        """Increase character knowledge_count count"""
        db_world = await self.get_by_id(id)
        if not db_world:
            return None

        db_world.knowledge_count += count

        self.db.add(db_world)
        self.db.commit()
        self.db.refresh(db_world)
        return db_world
