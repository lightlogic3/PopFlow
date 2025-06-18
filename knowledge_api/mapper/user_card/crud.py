from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import HTTPException
from sqlmodel import Session, select, col, join

from knowledge_api.mapper.base_crud import BaseCRUD, IdType
from knowledge_api.mapper.user_card.base import UserCard, UserCardCreate, UserCardUpdate
from knowledge_api.mapper.card.base import Card


class UserCardCRUD(BaseCRUD[UserCard, UserCardCreate, UserCardUpdate, Dict[str, Any], UserCard, int]):
    def __init__(self, db_session: Session):
        """Initialize user card CRUD operation"""
        super().__init__(db_session, UserCard)
    
    async def create(self, user_card: UserCardCreate) -> UserCard:
        """Create a user card record"""
        # Check if the record already exists
        stmt = select(self.model).where(
            (col(self.model.user_id) == user_card.user_id) &
            (col(self.model.card_id) == user_card.card_id)
        )
        existing = self.db.exec(stmt).first()
        if existing:
            raise HTTPException(status_code=400, detail="The user already owns this card")
        
        db_user_card = UserCard.from_orm(user_card)
        self.db.add(db_user_card)
        self.db.commit()
        self.db.refresh(db_user_card)
        return db_user_card
    
    async def get_by_id(self, user_card_id: int) -> Optional[UserCard]:
        """Get user card according to ID"""
        stmt = select(self.model).where(col(self.model.id) == user_card_id)
        return self.db.exec(stmt).first()
    
    async def get_by_user_and_card(self, user_id: int, card_id: int) -> Optional[UserCard]:
        """Obtain user card records based on user ID and card ID"""
        stmt = select(self.model).where(
            (col(self.model.user_id) == user_id) &
            (col(self.model.card_id) == card_id)
        )
        return self.db.exec(stmt).first()
    
    async def get_by_user_id(self, user_id: int, limit: int = 100) -> List[UserCard]:
        """Acquire all user cards"""
        stmt = select(self.model).where(col(self.model.user_id) == user_id).limit(limit)
        return self.db.exec(stmt).all()
    
    async def get_by_user_id_with_card_details(self, user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all the user's cards and include card details"""
        # Connect user card table and card table
        stmt = select(
            self.model,
            Card
        ).join(
            Card, 
            self.model.card_id == Card.id
        ).where(
            col(self.model.user_id) == user_id
        ).limit(limit)
        
        results = self.db.exec(stmt).all()
        
        # Process the result, combining the data from the two tables into a dictionary
        combined_results = []
        for user_card, card in results:
            user_card_dict = user_card.model_dump()
            card_dict = card.model_dump()
            
            # Add card details
            user_card_dict["card_detail"] = card_dict
            
            combined_results.append(user_card_dict)
            
        return combined_results
    
    async def update(self, user_card_id: int, user_card_update: UserCardUpdate) -> Optional[UserCard]:
        """Update user card information"""
        db_user_card = await self.get_by_id(user_card_id)
        if not db_user_card:
            return None
        
        update_data = user_card_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_user_card, key, value)
        
        self.db.add(db_user_card)
        self.db.commit()
        self.db.refresh(db_user_card)
        return db_user_card
    
    async def update_favorite(self, user_id: int, card_id: int, is_favorite: bool) -> Optional[UserCard]:
        """Update user card collection status"""
        user_card = await self.get_by_user_and_card(user_id, card_id)
        if not user_card:
            return None
        
        user_card.is_favorite = is_favorite
        self.db.add(user_card)
        self.db.commit()
        self.db.refresh(user_card)
        return user_card
    
    async def increment_use_count(self, user_id: int, card_id: int) -> Optional[UserCard]:
        """Increase card usage"""
        user_card = await self.get_by_user_and_card(user_id, card_id)
        if not user_card:
            return None
        
        user_card.use_count += 1
        user_card.last_use_time = datetime.now()
        self.db.add(user_card)
        self.db.commit()
        self.db.refresh(user_card)
        return user_card
    
    async def delete(self, user_card_id: int) -> bool:
        """Delete user card records"""
        user_card = await self.get_by_id(user_card_id)
        if not user_card:
            return False
        
        self.db.delete(user_card)
        self.db.commit()
        return True
    
    async def delete_by_user_and_card(self, user_id: int, card_id: int) -> bool:
        """Delete user card records based on user ID and card ID"""
        user_card = await self.get_by_user_and_card(user_id, card_id)
        if not user_card:
            return False
        
        self.db.delete(user_card)
        self.db.commit()
        return True 