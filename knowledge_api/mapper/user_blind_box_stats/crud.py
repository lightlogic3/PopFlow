from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlmodel import Session, select, col, func, and_

from knowledge_api.mapper.base_crud import BaseCRUD, IdType
from knowledge_api.mapper.user_blind_box_stats.base import (
    UserBlindBoxStats, 
    UserBlindBoxStatsCreate, 
    UserBlindBoxStatsUpdate
)


class UserBlindBoxStatsCRUD(BaseCRUD[UserBlindBoxStats, UserBlindBoxStatsCreate, UserBlindBoxStatsUpdate, Dict[str, Any], UserBlindBoxStats, int]):
    def __init__(self, db: Session):
        """Initialize user blind box statistics CRUD operation"""
        super().__init__(db, UserBlindBoxStats)

    async def get_by_user_and_box(self, user_id: int, blind_box_id: int) -> Optional[UserBlindBoxStats]:
        """Obtain statistics for user-specific blind boxes"""
        stmt = select(self.model).where(
            (col(self.model.user_id) == user_id) &
            (col(self.model.blind_box_id) == blind_box_id)
        )
        return self.db.exec(stmt).first()

    async def get_by_user_id(self, user_id: int) -> List[UserBlindBoxStats]:
        """Get statistics on all user blind boxes"""
        stmt = select(self.model).where(col(self.model.user_id) == user_id)
        return self.db.exec(stmt).all()

    async def update(self, stats_id: int, stats_update: UserBlindBoxStatsUpdate) -> Optional[UserBlindBoxStats]:
        """Update user blind box statistics"""
        db_stats = await self.get_by_id(stats_id)
        if not db_stats:
            return None
        
        update_data = stats_update.dict(exclude_unset=True) if hasattr(stats_update, 'dict') else stats_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_stats, key, value)
        
        db_stats.update_time = datetime.now()
        self.db.add(db_stats)
        self.db.commit()
        self.db.refresh(db_stats)
        return db_stats
    
    async def increment_draw_count(self, user_id: int, blind_box_id: int) -> Optional[UserBlindBoxStats]:
        """Increase the number of blind box extraction and guarantee count"""
        db_stats = await self.get_by_user_and_box(user_id, blind_box_id)
        
        if not db_stats:
            # Create a new record if it doesn't exist
            db_stats = UserBlindBoxStats(
                user_id=user_id,
                blind_box_id=blind_box_id,
                total_draws=1,
                current_pity_count=1,
                guaranteed_trigger_count=0,
                special_reward_count=0
            )
            self.db.add(db_stats)
        else:
            # existence update count
            db_stats.total_draws += 1
            db_stats.current_pity_count += 1
            db_stats.update_time = datetime.now()
            self.db.add(db_stats)
            
        self.db.commit()
        self.db.refresh(db_stats)
        return db_stats
    
    async def trigger_guaranteed(self, user_id: int, blind_box_id: int) -> Optional[UserBlindBoxStats]:
        """Trigger the guarantee, reset the guarantee count and increase the number of guarantee triggers"""
        db_stats = await self.get_by_user_and_box(user_id, blind_box_id)
        
        if not db_stats:
            # Create a new record if it doesn't exist
            db_stats = UserBlindBoxStats(
                user_id=user_id,
                blind_box_id=blind_box_id,
                total_draws=1,
                current_pity_count=0,  # Reset guaranteed count
                guaranteed_trigger_count=1,
                special_reward_count=0
            )
            self.db.add(db_stats)
        else:
            # existence update count
            db_stats.current_pity_count = 0  # Reset guaranteed count
            db_stats.guaranteed_trigger_count += 1
            db_stats.update_time = datetime.now()
            self.db.add(db_stats)
            
        self.db.commit()
        self.db.refresh(db_stats)
        return db_stats
    
    async def add_special_reward(self, user_id: int, blind_box_id: int) -> Optional[UserBlindBoxStats]:
        """Increase the number of special rewards"""
        db_stats = await self.get_by_user_and_box(user_id, blind_box_id)
        
        if not db_stats:
            # Create a new record if it doesn't exist
            db_stats = UserBlindBoxStats(
                user_id=user_id,
                blind_box_id=blind_box_id,
                total_draws=1,
                current_pity_count=1,
                guaranteed_trigger_count=0,
                special_reward_count=1
            )
            self.db.add(db_stats)
        else:
            # existence update count
            db_stats.special_reward_count += 1
            db_stats.update_time = datetime.now()
            self.db.add(db_stats)
            
        self.db.commit()
        self.db.refresh(db_stats)
        return db_stats
    
    async def reset_pity_counter(self, user_id: int, blind_box_id: int, new_count: int = 0) -> Optional[UserBlindBoxStats]:
        """Manual reset user blind box guaranteed bottom count"""
        db_stats = await self.get_by_user_and_box(user_id, blind_box_id)
        
        if not db_stats:
            # Create a new record if it doesn't exist
            db_stats = UserBlindBoxStats(
                user_id=user_id,
                blind_box_id=blind_box_id,
                total_draws=0,
                current_pity_count=new_count,
                guaranteed_trigger_count=0,
                special_reward_count=0
            )
            self.db.add(db_stats)
        else:
            # existence update count
            db_stats.current_pity_count = new_count
            db_stats.update_time = datetime.now()
            self.db.add(db_stats)
            
        self.db.commit()
        self.db.refresh(db_stats)
        return db_stats

    async def update_by_user_and_box(
        self, user_id: int, blind_box_id: int, 
        obj_in: UserBlindBoxStatsUpdate, updater_id: Optional[int] = None
    ) -> Optional[UserBlindBoxStats]:
        """Update records with user ID and blind box ID
: Param user_id: user ID
: Param blind_box_id: blind box ID
: Param obj_in: update object
: Param updater_id: Update Person ID
: return: updated record"""
        db_obj = await self.get_by_user_and_box(user_id, blind_box_id)
        if not db_obj:
            return None
        
        # Set Updater ID
        if updater_id is not None:
            obj_in.updater_id = updater_id

        # update data
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    async def get_multi_by_user(self, user_id: int) -> List[UserBlindBoxStats]:
        """Get all blind box statistics for users
: Param user_id: user ID
: return: record list"""
        query = select(UserBlindBoxStats).where(UserBlindBoxStats.user_id == user_id)
        result = self.db.exec(query).all()
        return result