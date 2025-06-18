from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlmodel import Session, select

from knowledge_api.mapper.base_crud import BaseCRUD
from knowledge_api.mapper.limited_card_stats.base import (
    LimitedCardStats,
    LimitedCardStatsCreate,
    LimitedCardStatsUpdate
)


class LimitedCardStatsCRUD(BaseCRUD[
    LimitedCardStats, 
    LimitedCardStatsCreate, 
    LimitedCardStatsUpdate,
    Dict[str, Any], 
    LimitedCardStats,
    int
]):
    """Limited card extraction statistics table CRUD operation"""
    
    def __init__(self, db: Session):
        """initialization
: Param db: database session"""
        super().__init__(db, LimitedCardStats)
    
    async def get_by_card_id(self, card_id: int) -> Optional[LimitedCardStats]:
        """Get limited card statistics by card ID
: Param card_id: Card ID
: return: limited card statistics"""
        query = select(LimitedCardStats).where(LimitedCardStats.card_id == card_id)
        result = self.db.exec(query).first()
        return result

    async def get_sold_out_card_ids(self) -> List[int]:
        """Get a list of all sold out card IDs
: return: list of sold out card IDs"""
        query = select(LimitedCardStats.card_id).where(
            LimitedCardStats.is_sold_out == True  # noqa: E712
        )
        result = self.db.exec(query).all()
        return [row[0] for row in result]
    
    async def update_card_drawn(
        self, 
        card_id: int, 
        drawn_count: int = 1, 
        updater_id: Optional[int] = None
    ) -> Optional[LimitedCardStats]:
        """Update card draw status
: Param card_id: Card ID
: Param drawn_count: The number of draws this time, the default is 1
: Param updater_id: Update Person ID
: Return: Updated limited card statistics"""
        stats = await self.get_by_card_id(card_id)
        
        if not stats:
            # If no record exists, create a new record
            return None
        
        # Current time
        now = datetime.now()
        
        # update data
        update_data = {
            "total_drawn_count": stats.total_drawn_count + drawn_count,
            "remaining_count": max(0, stats.remaining_count - drawn_count),
            "last_drawn_time": now
        }
        
        # If it is the first extraction, set the first extraction time
        if stats.first_drawn_time is None:
            update_data["first_drawn_time"] = now
        
        # Check if it is sold out.
        if update_data["remaining_count"] == 0 and not stats.is_sold_out:
            update_data["is_sold_out"] = True
        
        # Set Updater
        if updater_id:
            update_data["updater_id"] = updater_id
        
        # execute update
        update_obj = LimitedCardStatsUpdate(**update_data)
        return await self.update(stats.id, update_obj)
    
    async def initialize_limited_card(
        self, 
        card_id: int, 
        limited_count: int, 
        creator_id: Optional[int] = None
    ) -> LimitedCardStats:
        """Initialize limited card statistics
: Param card_id: Limited Card ID
: Param limited_count: limited quantity
: Param creator_id: creator ID
: return: record created"""
        # Check if it already exists
        existing = await self.get_by_card_id(card_id)
        if existing:
            return existing
        
        # Create a new record
        create_obj = LimitedCardStatsCreate(
            card_id=card_id,
            total_drawn_count=0,
            remaining_count=limited_count,
            is_sold_out=False,
            creator_id=creator_id
        )
        
        return await self.create(create_obj) 