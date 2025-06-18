"""Card Unlock Service
Handle the business logic related to user card unlocking"""
from typing import Dict, Any, Optional
from datetime import datetime
from sqlmodel import Session
from fastapi import HTTPException

from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.card.crud import CardCRUD
from knowledge_api.mapper.user_card.crud import UserCardCRUD
from knowledge_api.mapper.user_card.base import UserCardCreate
from knowledge_api.mapper.user_detail.crud import UserDetailCRUD
from knowledge_api.mapper.point_record.crud import PointRecordCRUD
from knowledge_api.mapper.point_record.base import PointRecordCreate, PointChangeType


class CardUnlockService:
    """Card unlocking service"""
    
    def __init__(self, db: Session = None):
        """Initialize the card unlock service"""
        self.db = db or next(get_session())
        self.card_crud = CardCRUD(self.db)
        self.user_card_crud = UserCardCRUD(self.db)
        self.user_detail_crud = UserDetailCRUD(self.db)
        self.point_record_crud = PointRecordCRUD(self.db)
    
    async def unlock_card_with_points(self, user_id: int, card_id: int) -> Dict[str, Any]:
        """Use Points to Unlock Cards

Args:
user_id: User ID
card_id: Card ID

Returns:
Dict [str, Any]: Unlock result information

Raises:
HTTPException: Thrown when unlocking fails"""
        # 1. Check if the card exists
        card = await self.card_crud.get_by_id(card_id)
        if not card:
            raise HTTPException(status_code=404, detail="The card does not exist")
        
        # 2. Check whether the card supports points unlocking
        if card.unlock_type != "both":
            raise HTTPException(status_code=400, detail="This card does not support points unlocking and can only be obtained through the blind box.")
        
        # 3. Check if the card is activated
        if card.status != 1:
            raise HTTPException(status_code=400, detail="This card is currently unavailable")
        
        # 4. Check if the user already owns the card
        existing_card = await self.user_card_crud.get_by_user_and_card(user_id, card_id)
        if existing_card:
            raise HTTPException(status_code=400, detail="You already own the card")
        
        # 5. Check if the points are sufficient
        if not card.points_required or card.points_required <= 0:
            raise HTTPException(status_code=400, detail="This card does not support points unlocking.")
        
        user_detail = await self.user_detail_crud.get_by_user_id(user_id=user_id)
        if not user_detail:
            raise HTTPException(status_code=404, detail="User information does not exist")
        
        if user_detail.available_points < card.points_required:
            raise HTTPException(status_code=400, detail=f"积分不足，需要{card.points_required}积分，您当前有{user_detail.available_points}积分")
        
        # 6. Begin the transaction unlocking process
        try:
            # 6.1. Creating a Points Record (Consuming Points)
            point_record = await self.point_record_crud.create(obj_in=PointRecordCreate(
                user_id=user_id,
                change_type=PointChangeType.UNLOCK_CARD,
                change_amount=-card.points_required,  # Negative value indicates consumption
                description=f"解锁卡牌【{card.name}】",
                current_amount=user_detail.available_points - card.points_required,
                related_id=card_id
            ), creator_id=user_id)
            
            # 6.2. Update user points
            await self.user_detail_crud.update_points(
                user_id=user_id, 
                points_change=card.points_required, 
                is_earned=False  # False means spending points
            )
            
            # 6.3. Creating a user card record
            user_card = await self.user_card_crud.create(UserCardCreate(
                user_id=user_id,
                card_id=card_id,
                obtain_type="points",  # Points unlocked
                obtain_time=datetime.now(),
                creator_id=user_id
            ))
            
            # 6.4. Update user card count
            await self.user_detail_crud.update_card_count(user_id=user_id, count_change=1)
            
            # Construct return result
            return {
                "success": True,
                "message": f"成功解锁卡牌【{card.name}】",
                "card": {
                    "id": card.id,
                    "name": card.name,
                    "rarity": card.rarity,
                    "image_url": card.image_url
                },
                "cost_points": card.points_required,
                "remaining_points": user_detail.available_points - card.points_required
            }
            
        except Exception as e:
            # Roll back the transaction when an exception occurs
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"解锁卡牌失败: {str(e)}") 