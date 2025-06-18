"""user points service
Business logic related to handling user credit records"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlmodel import Session, select, desc
from fastapi import HTTPException

from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.point_record.crud import PointRecordCRUD
from knowledge_api.mapper.point_record.base import PointRecordCreate, PointChangeType
from knowledge_api.mapper.user_detail.crud import UserDetailCRUD
from knowledge_api.mapper.card.crud import CardCRUD


class UserPointService:
    """User points service"""
    
    def __init__(self, db: Session = None):
        """Initialize user points service"""
        self.db = db or next(get_session())
        self.point_record_crud = PointRecordCRUD(self.db)
        self.user_detail_crud = UserDetailCRUD(self.db)
        self.card_crud = CardCRUD(self.db)
    
    async def get_user_point_records(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get a list of user points

Args:
user_id: User ID
Limit: Returns the upper limit of the number of records

Returns:
user credit record list"""
        try:
            # Get user points record
            records = await self.point_record_crud.get_user_point_records(user_id=user_id, limit=limit)
            
            # Process the results, simplify and add the necessary information
            result = []
            for record in records:
                # Convert records to dictionaries
                record_dict = record.dict() if hasattr(record, 'dict') else record.model_dump()
                
                # Add change type display name
                from knowledge_api.mapper.point_record.base import POINT_CHANGE_TYPE_DISPLAY
                if record.change_type in POINT_CHANGE_TYPE_DISPLAY:
                    record_dict["change_type_display"] = POINT_CHANGE_TYPE_DISPLAY[record.change_type]
                
                # If there is an associated card, add card information
                if record.related_id and record.change_type in [PointChangeType.UNLOCK_CARD, PointChangeType.DUPLICATE_CARD]:
                    card = await self.card_crud.get_by_id(record.related_id)
                    if card:
                        record_dict["card_info"] = {
                            "id": card.id,
                            "name": card.name,
                            "rarity": card.rarity,
                            "image_url": card.image_url
                        }
                
                result.append(record_dict)
            
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"获取积分记录失败: {str(e)}")
    
    async def get_user_available_points(self, user_id: int) -> int:
        """Acquire User Available Points

Args:
user_id: User ID

Returns:
User Available Points"""
        try:
            user_detail = await self.user_detail_crud.get_by_user_id(user_id=user_id)
            if not user_detail:
                raise HTTPException(status_code=404, detail="User information does not exist")
            
            return user_detail.available_points
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"获取用户积分失败: {str(e)}")
    
    async def get_point_summary(self, user_id: int) -> Dict[str, Any]:
        """Get user points summary statistics

Args:
user_id: User ID

Returns:
user points summary statistics"""
        try:
            # Get user details
            user_detail = await self.user_detail_crud.get_by_user_id(user_id=user_id)
            if not user_detail:
                raise HTTPException(status_code=404, detail="User information does not exist")
            
            # Get the last 10 points
            recent_records = await self.point_record_crud.get_user_point_records(user_id=user_id, limit=10)
            
            # Calculate total revenue and total expenses
            total_earned = 0
            total_spent = 0
            
            # Acquire all points
            all_records = await self.point_record_crud.get_user_point_records(user_id=user_id, limit=999)
            
            for record in all_records:
                if record.change_amount > 0:
                    total_earned += record.change_amount
                else:
                    total_spent += abs(record.change_amount)
            
            # construction result
            return {
                "available_points": user_detail.available_points,
                "total_earned": total_earned,
                "total_spent": total_spent,
                "recent_records": [record.dict() if hasattr(record, 'dict') else record.model_dump() for record in recent_records]
            }
        except Exception as e:
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"获取积分统计失败: {str(e)}") 