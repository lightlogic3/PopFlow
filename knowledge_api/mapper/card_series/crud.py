"""Card series CRUD operation"""
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, and_
from fastapi_pagination import Page

from knowledge_api.mapper.base_crud import BaseCRUD
from knowledge_api.mapper.card_series.base import (
    CardSeries, 
    CardSeriesCreate, 
    CardSeriesUpdate, 
    CardSeriesFilter, 
    CardSeriesResponse
)

class CardSeriesCRUD(BaseCRUD[CardSeries, CardSeriesCreate, CardSeriesUpdate, CardSeriesFilter, CardSeriesResponse, int]):
    """Card series CRUD operation class"""
    
    def __init__(self, db: Session):
        """Initialize CRUD operation"""
        super().__init__(db, CardSeries)
    
    async def create(self, obj_in: CardSeriesCreate, creator_id: Optional[int] = None) -> CardSeries:
        """Create a card series

Args:
obj_in: Creating Data
creator_id: Creator ID

Returns:
CardSeries: Created card series"""
        return await super().create(obj_in, creator_id=creator_id, updater_id=creator_id)
    
    async def update(self, id: int, obj_in: CardSeriesUpdate, updater_id: Optional[int] = None) -> Optional[CardSeries]:
        """Update Card Series

Args:
ID: Series ID
obj_in: Update Data
updater_id: Updater ID

Returns:
Optional [CardSeries]: Updated Card Series"""
        # Get the current record
        db_obj = await self.get_by_id(id=id)
        if db_obj is None or db_obj.is_deleted == 1:
            return None
            
        # Get updated data
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Add Updater ID
        if updater_id is not None:
            update_data["updater_id"] = updater_id
        
        # Update object properties
        for key, value in update_data.items():
            setattr(db_obj, key, value)
        
        # commit changes
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    async def get_by_id(self, id: int) -> Optional[CardSeries]:
        """Obtain card series by ID (excluding deleted)

Args:
ID: Series ID

Returns:
Optional [CardSeries]: Card Series or None"""
        statement = select(self.model).where(
            and_(self.model.id == id, self.model.is_deleted == 0)
        )
        result = self.db.exec(statement).first()
        return result
    
    async def get_by_code(self, code: str) -> Optional[CardSeries]:
        """Obtain a card series through code

Args:
Code: series code

Returns:
Optional [CardSeries]: Card Series or None"""
        statement = select(self.model).where(
            and_(self.model.code == code, self.model.is_deleted == 0)
        )
        result = self.db.exec(statement).first()
        return result
    
    async def get_active_series(self, skip: int = 0, limit: int = 100) -> List[CardSeries]:
        """Get a list of enabled series

Args:
Skip: skip the number of records
Limit: limit the number of records

Returns:
List [CardSeries]: Series List"""
        statement = select(self.model).where(
            and_(self.model.status == 1, self.model.is_deleted == 0)
        ).order_by(self.model.sort_order, self.model.create_time.desc()).offset(skip).limit(limit)
        
        results = self.db.exec(statement).all()
        return results
    
    async def soft_delete(self, id: int, updater_id: Optional[int] = None) -> bool:
        """Soft Delete Card Series

Args:
ID: Series ID
updater_id: Updater ID

Returns:
Bool: whether the deletion was successful"""
        db_obj = await self.get_by_id(id=id)
        if db_obj is None:
            return False
            
        db_obj.is_deleted = 1
        if updater_id is not None:
            db_obj.updater_id = updater_id
            
        self.db.add(db_obj)
        self.db.commit()
        return True
    
    def _apply_filters(self, query, filter_data: Dict[str, Any]):
        """Apply Filter Criteria to Queries

Args:
Query: SQLModel query object
filter_data: Filter Dictionary

Returns:
Query objects to which filter criteria have been applied"""
        # By default, only undeleted records are queried.
        query = query.where(self.model.is_deleted == 0)
        
        for field, value in filter_data.items():
            if value is not None and hasattr(self.model, field):
                if field == "name":
                    # Name support fuzzy query
                    query = query.where(self.model.name.like(f"%{value}%"))
                elif field == "code":
                    # Encoding supports fuzzy queries
                    query = query.where(self.model.code.like(f"%{value}%"))
                else:
                    # Other fields match exactly
                    query = query.where(getattr(self.model, field) == value)
        
        return query 