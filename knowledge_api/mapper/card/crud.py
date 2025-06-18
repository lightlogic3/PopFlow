"""Card CRUD operation"""
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, and_, text
from fastapi_pagination import Page

from knowledge_api.mapper.base_crud import BaseCRUD
from knowledge_api.mapper.card.base import (
    Card, 
    CardCreate, 
    CardUpdate, 
    CardFilter, 
    CardResponse
)

class CardCRUD(BaseCRUD[Card, CardCreate, CardUpdate, CardFilter, CardResponse, int]):
    """Card CRUD operation class"""
    
    def __init__(self, db: Session):
        """Initialize CRUD operation"""
        super().__init__(db, Card)
    
    async def create(self, obj_in: CardCreate, creator_id: Optional[int] = None) -> Card:
        """Create a card

Args:
obj_in: Creating Data
creator_id: Creator ID

Returns:
Cards: Created cards"""
        return await super().create(obj_in, creator_id=creator_id, updater_id=creator_id)
    
    async def update(self, id: int, obj_in: CardUpdate, updater_id: Optional[int] = None) -> Optional[Card]:
        """Update Card

Args:
ID: Card ID
obj_in: Update Data
updater_id: Updater ID

Returns:
Optional [Card]: Updated Card"""
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
    
    async def get_by_id(self, id: int) -> Optional[Card]:
        """Obtain cards by ID (excluding deleted)

Args:
ID: Card ID

Returns:
Optional [Card]: Card or None"""
        statement = select(self.model).where(
            and_(self.model.id == id, self.model.is_deleted == 0)
        )
        result = self.db.exec(statement).first()
        return result
    
    async def get_by_series_id(self, series_id: int, skip: int = 0, limit: int = 100) -> List[Card]:
        """Get a list of cards by series ID

Args:
series_id: Series ID
Skip: skip the number of records
Limit: limit the number of records

Returns:
List [Cards]: Card List"""
        statement = select(self.model).where(
            and_(self.model.series_id == series_id, self.model.is_deleted == 0)
        ).order_by(self.model.sort_order, self.model.rarity.desc(), self.model.create_time.desc()).offset(skip).limit(limit)
        
        results = self.db.exec(statement).all()
        return results
    
    async def get_series_cards_with_user_unlock_status(self, series_id: int, user_id: int, limit: int = 999) -> List[Dict[str, Any]]:
        """Acquire all cards in the series and mark whether the user has unlocked them

Args:
series_id: Series ID
user_id: User ID
Limit: limit the number of records

Returns:
List [Dict [str, Any]]: A list of cards, each containing is_unlocked fields"""
        # Get both card information and user unlock status using native SQL queries
        query = text("""
            SELECT 
                c.*,
                CASE WHEN uc.id IS NOT NULL THEN 1 ELSE 0 END AS is_unlocked,
                uc.obtain_type,
                uc.obtain_time,
                uc.use_count,
                uc.is_favorite
            FROM 
                card c
            LEFT JOIN 
                user_card uc ON c.id = uc.card_id AND uc.user_id = :user_id
            WHERE 
                c.series_id = :series_id 
                AND c.is_deleted = 0
            ORDER BY 
                c.sort_order, c.rarity DESC, c.create_time DESC
            LIMIT :limit
        """)
        
        results = self.db.exec(query.bindparams(
            series_id=series_id,
            user_id=user_id,
            limit=limit
        )).all()
        
        # Convert the result to a dictionary list
        cards_with_status = []
        for row in results:
            # First extract the basic information of the card
            card_dict = {
                "id": row.id,
                "name": row.name,
                "series_id": row.series_id,
                "rarity": row.rarity,
                "description": row.description,
                "image_url": row.image_url,
                "sort_order": row.sort_order,
                "unlock_type": row.unlock_type,
                "points_required": row.points_required,
                "duplicate_points": row.duplicate_points,
                "status": row.status,
                "role_id": row.role_id,
                "blind_box_id": row.blind_box_id,
                "box_drop_rate": row.box_drop_rate,
                "victory_points": row.victory_points,
                "game_cost_points": row.game_cost_points,
                "limited_count": row.limited_count,
                "is_limited": row.is_limited,
                "is_deleted": row.is_deleted,
                "creator_id": row.creator_id,
                "updater_id": row.updater_id,
                "create_time": row.create_time,
                "update_time": row.update_time,
                
                # Add user unlock status information
                "is_unlocked": bool(row.is_unlocked),
            }
            
            # If the user has unlocked, add the details of the user's card
            if row.is_unlocked:
                card_dict["user_card_info"] = {
                    "obtain_type": row.obtain_type,
                    "obtain_time": row.obtain_time,
                    "use_count": row.use_count,
                    "is_favorite": bool(row.is_favorite)
                }
            
            cards_with_status.append(card_dict)
            
        return cards_with_status
    
    async def get_by_rarity(self, rarity: int, skip: int = 0, limit: int = 100) -> List[Card]:
        """Get a card list based on rarity

Args:
Rarity: Rarity
Skip: skip the number of records
Limit: limit the number of records

Returns:
List [Cards]: Card List"""
        statement = select(self.model).where(
            and_(self.model.rarity == rarity, self.model.is_deleted == 0, self.model.status == 1)
        ).order_by(self.model.sort_order, self.model.create_time.desc()).offset(skip).limit(limit)
        
        results = self.db.exec(statement).all()
        return results
    
    async def get_by_role_id(self, role_id: str, skip: int = 0, limit: int = 100) -> List[Card]:
        """Get a list of cards based on character ID

Args:
role_id: Role ID
Skip: skip the number of records
Limit: limit the number of records

Returns:
List [Cards]: Card List"""
        statement = select(self.model).where(
            and_(self.model.role_id == role_id, self.model.is_deleted == 0)
        ).order_by(self.model.sort_order, self.model.rarity.desc()).offset(skip).limit(limit)
        
        results = self.db.exec(statement).all()
        return results
    
    async def get_limited_cards(self, skip: int = 0, limit: int = 100) -> List[Card]:
        """Get the limited card list

Args:
Skip: skip the number of records
Limit: limit the number of records

Returns:
List [Cards]: Limited Card List"""
        statement = select(self.model).where(
            and_(self.model.is_limited == 1, self.model.is_deleted == 0, self.model.status == 1)
        ).order_by(self.model.rarity.desc(), self.model.create_time.desc()).offset(skip).limit(limit)
        
        results = self.db.exec(statement).all()
        return results
    
    async def soft_delete(self, id: int, updater_id: Optional[int] = None) -> bool:
        """Soft Delete Card

Args:
ID: Card ID
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
    
    async def count_by_series(self, series_id: int) -> int:
        """Count the number of cards in the series

Args:
series_id: Series ID

Returns:
Int: Number of cards"""
        from sqlmodel import func
        statement = select(func.count()).select_from(self.model).where(
            and_(self.model.series_id == series_id, self.model.is_deleted == 0)
        )
        result = self.db.exec(statement).one()
        return result[0] if isinstance(result, tuple) else result
    
    def _apply_filters(self, query, filter_data: Dict[str, Any]):
        """Apply filter conditions

Args:
Query: Query object
filter_data: Filter Criteria

Returns:
Query objects after applying filter conditions"""
        # basic field filtering
        for field, value in filter_data.items():
            if value is None:
                continue
                
            if field == "name" and value:
                query = query.where(self.model.name.contains(value))
            elif hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)
                
        return query 