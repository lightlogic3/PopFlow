"""Card Game Service Layer
Handle card series and card-related business logic"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlmodel import Session
import uuid

from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.card_series import CardSeriesCRUD
from knowledge_api.mapper.card import CardCRUD
from knowledge_api.mapper.user_detail import UserDetailCRUD
from knowledge_api.mapper.card_usage_record.crud import CardUsageRecordCRUD
from knowledge_api.mapper.card_usage_record.base import CardUsageRecordCreate, CardUsageRecordUpdate
from knowledge_api.mapper.point_record.crud import PointRecordCRUD
from knowledge_api.mapper.point_record.base import PointRecordCreate, PointChangeType


class CardService:
    """Card Services"""
    
    def __init__(self, db: Session = None):
        """Initialize Card Service"""
        self.db = db or next(get_session())
        self.series_crud = CardSeriesCRUD(self.db)
        self.card_crud = CardCRUD(self.db)
        self.user_detail_crud = UserDetailCRUD(self.db)
        self.card_usage_record_crud = CardUsageRecordCRUD(self.db)
        self.point_record_crud = PointRecordCRUD(self.db)
    
    async def get_all_series_with_cards(self, status: str = "active", name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Acquire all card series and the cards they contain

Args:
Status: series status, only the active state is returned by default
Name: Series name filter, optional

Returns:
Contains a list of all series and their cards"""
        # Build filter conditions
        filters = {}
        if status:
            filters["status"] = status
        if name:
            filters["name"] = name
        
        # Acquire all eligible series
        if filters:
            series_list = await self.series_crud.filter(filters, limit=999)
        else:
            series_list = await self.series_crud.get_active_series(limit=999)
        
        result = []
        for series in series_list:
            # Acquire all cards in the series
            cards = await self.card_crud.get_by_series_id(series.id, limit=999)
            
            # build result
            series_data = series.dict() if hasattr(series, 'dict') else series.model_dump()
            series_data["cards"] = [card.dict() if hasattr(card, 'dict') else card.model_dump() for card in cards]
            result.append(series_data)
        
        return result
    
    async def get_all_series_with_cards_and_unlock_status(self, user_id: int, status: str = "active", name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Acquire all card series and the cards they contain, with user unlock status

Args:
user_id: User ID
Status: series status, only the active state is returned by default
Name: Series name filter, optional

Returns:
Contains a list of all series and their cards, including the user's unlocked status"""
        # Build filter conditions
        filters = {}
        if status:
            filters["status"] = 1
        if name:
            filters["name"] = name
        
        # Acquire all eligible series
        if filters:
            series_list = await self.series_crud.filter(filters, limit=999)
        else:
            series_list = await self.series_crud.get_active_series(limit=999)
        
        result = []
        for series in series_list:
            # Obtain all cards and user unlock status under the series
            cards_with_status = await self.card_crud.get_series_cards_with_user_unlock_status(
                series_id=series.id, 
                user_id=user_id,
                limit=999
            )
            
            # build result
            series_data = series.dict() if hasattr(series, 'dict') else series.model_dump()
            series_data["cards"] = cards_with_status
            result.append(series_data)
        
        return result
    
    async def get_series_with_cards(self, series_id: int) -> Dict[str, Any]:
        """Acquire a single card series and all the cards it contains

Args:
series_id: Series ID

Returns:
A dictionary containing a series and its cards"""
        # Get series information
        series = await self.series_crud.get_by_id(series_id)
        if not series:
            raise ValueError("The card series does not exist")
        
        # Acquire all cards in the series
        cards = await self.card_crud.get_by_series_id(series_id, limit=999)
        
        # build result
        series_data = series.dict() if hasattr(series, 'dict') else series.model_dump()
        series_data["cards"] = [card.dict() if hasattr(card, 'dict') else card.model_dump() for card in cards]
        
        return series_data
    
    async def get_series_with_cards_and_unlock_status(self, series_id: int, user_id: int) -> Dict[str, Any]:
        """Get a single card series and all the cards it contains, with user unlock status

Args:
series_id: Series ID
user_id: User ID

Returns:
A dictionary containing the series and its cards, including the user's unlocked status"""
        # Get series information
        series = await self.series_crud.get_by_id(series_id)
        if not series:
            raise ValueError("The card series does not exist")
        
        # Obtain all cards and user unlock status under the series
        cards_with_status = await self.card_crud.get_series_cards_with_user_unlock_status(
            series_id=series_id, 
            user_id=user_id,
            limit=999
        )
        
        # build result
        series_data = series.dict() if hasattr(series, 'dict') else series.model_dump()
        series_data["cards"] = cards_with_status
        
        return series_data
    
    async def get_card_detail(self, card_id: int) -> Dict[str, Any]:
        """Get individual card details

Args:
card_id: Card ID

Returns:
Card Details Dictionary"""
        card = await self.card_crud.get_by_id(card_id)
        if not card:
            raise ValueError("The card does not exist")
        
        return card.dict() if hasattr(card, 'dict') else card.model_dump()

    async def get_card_by_id(self, card_id):
        """Get card information according to card ID

Args:
card_id: Card ID

Returns:
Card Information Dictionary"""
        card = await self.card_crud.get_by_id(card_id)
        if not card:
            raise ValueError("The card does not exist")

        return card

    async def get_user_points(self, user_id):
        """Get user points

Args:
user_id: User ID

Returns:
user points"""
        # It is assumed that there is a method to obtain user points, and the specific implementation is adjusted according to the actual situation
        user_points = await self.user_detail_crud.get_by_user_id(user_id=user_id)
        if user_points is None:
            raise ValueError("User points information does not exist")

        return user_points.available_points

    async def deduct_user_points(self, user_id, unlock_cost, card_id=None):
        """Deduct user points

Args:
user_id: User ID
unlock_cost: Number of points deducted
card_id: Card ID (optional)

Returns:
Bool: Whether the deduction was successful

Raises:
ValueError: Insufficient user points or other errors"""
        # Update user points (consumption points)
        result = await self.user_detail_crud.update_points(
            user_id=user_id,
            points_change=unlock_cost,
            is_earned=False  # Marked as spending credits
        )
        
        if not result:
            raise ValueError("User points are insufficient or the update of points fails.")
            
        # Create points record
        await self.point_record_crud.create(
            obj_in=PointRecordCreate(
                user_id=user_id,
                change_amount=-unlock_cost,  # Negative numbers represent expenses
                current_amount=await self.get_user_points(user_id),  # Get the latest points
                change_type=PointChangeType.UNLOCK_CARD,  # Use the correct enumeration value: unlock cards
                card_id=card_id,  # Associated Card ID
                description="Card Challenge Spending Points",
                creator_id=user_id
            )
        )
        
        return True

    async def create_challenge_task(self, card_id, user_id,task_id):
        """Create Card Challenge Quest

Args:
card_id: Card ID
user_id: User ID

Returns:
STR: Challenge Session ID"""
        # 1. Generate the challenge session ID
        series_id = str(uuid.uuid4())
        
        # 2. Create a card usage record
        usage_record = await self.card_usage_record_crud.create(
            obj_in=CardUsageRecordCreate(
                user_id=user_id,
                card_id=card_id,
                usage_type="ai_challenge",  # Type of use for AI challenges
                related_id=task_id,  # Association ID Use session ID
                start_time=datetime.now(),
                creator_id=user_id
            )
        )
        
        # 3. Update user challenge statistics
        await self.user_detail_crud.update_challenge_stats(
            user_id=user_id,
            success=False  # The initial creation was unsuccessful
        )
        
        # 4. Return the challenge session ID
        return series_id

    async def reward_challenge_points(self, user_id: int, card_id: int, points: int):
        """Reward users with challenge success points

Args:
user_id: User ID
card_id: Card ID
Points: Number of Reward Points

Returns:
Bool: Whether the reward is successful or not"""
        if points <= 0:
            return False
            
        # Update user points (add points)
        result = await self.user_detail_crud.update_points(
            user_id=user_id,
            points_change=points,
            is_earned=True  # Mark to earn points
        )
        
        if not result:
            return False
            
        # Create points record
        await self.point_record_crud.create(
            obj_in=PointRecordCreate(
                user_id=user_id,
                change_amount=points,  # Positive numbers represent income
                current_amount=await self.get_user_points(user_id),  # Get the latest points
                change_type=PointChangeType.AI_CHALLENGE,  # Using the correct enumeration values: AI challenge rewards
                card_id=card_id,  # Associated Card ID
                description="Card Challenge Successful Reward Points",
                creator_id=user_id
            )
        )
        
        return True