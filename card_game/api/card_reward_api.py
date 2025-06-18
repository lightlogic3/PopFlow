from fastapi import APIRouter, Depends, HTTPException, Path, Header, Query
from sqlmodel import Session
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime

from knowledge_api.framework.auth import TokenUtil
from knowledge_api.framework.database.database import get_session
from card_game.server.reward_service import RewardService

# Create route
reward_router = APIRouter(prefix="/reward", tags=["Card Reward"])

class RewardItem(BaseModel):
    """reward project model"""
    type: str  # Reward type: points, blind_box (blind box)
    message: str  # reward description information
    
class PointReward(RewardItem):
    """Points reward model"""
    amount: int  # number of points
    
class CardInfo(BaseModel):
    """Basic Information Model of Cards"""
    id: int
    name: str
    rarity: int
    image_url: Optional[str] = None
    
class CardDetail(CardInfo):
    """Card Detail Model"""
    description: Optional[str] = None
    
class BlindBoxInfo(BaseModel):
    """Blind Box Information Model"""
    id: int
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    cards: List[CardInfo]
    
class BlindBoxReward(RewardItem):
    """Blind Box Reward Model"""
    blind_box: BlindBoxInfo
    drawn_card: Optional[CardDetail] = None
    is_duplicate: bool = False
    points_gained: int = 0
    
class ChallengeRewardResponse(BaseModel):
    """challenge reward response model"""
    rewards: List[Any]  # Can be PointReward or BlindBoxReward
    total_points: int
    message: str

class RewardHistoryItem(BaseModel):
    """Reward History Project Model"""
    challenge_id: str
    card_id: int
    challenge_time: datetime
    completed_time: Optional[datetime] = None
    points_earned: int = 0
    total_points: int = 0
    card_info: Optional[Dict[str, Any]] = None
    rewards: List[Dict[str, Any]]

class RewardHistoryResponse(BaseModel):
    """reward historical response model"""
    items: List[RewardHistoryItem]
    total: int
    limit: int
    offset: int

@reward_router.get("/challenge/{challenge_id}", response_model=ChallengeRewardResponse)
async def get_challenge_reward(
    challenge_id: str = Path(..., description="Challenge ID"),
    authorization: Optional[str] = Header(None, description="Authentication Token"),
    db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """Get challenge rewards

Args:
challenge_id: Challenge ID
Authorization: Authentication Token
DB: database session

Returns:
reward information"""
    # Get the current user ID
    user_id = TokenUtil.get_user_id(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized, please log in first")
    
    # Create a reward service
    reward_service = RewardService(db)
    
    try:
        # Get challenge rewards
        reward_info = await reward_service.get_challenge_reward(user_id, challenge_id)
        return reward_info
    except HTTPException as e:
        # Passing HTTP Exceptions Directly
        raise e
    except Exception as e:
        # Other exceptions are converted to HTTP exceptions
        raise HTTPException(status_code=500, detail=f"获取奖励失败: {str(e)}")

@reward_router.get("/history", response_model=RewardHistoryResponse)
async def get_reward_history(
    limit: int = Query(20, description="records per page"),
    offset: int = Query(0, description="Offset"),
    authorization: Optional[str] = Header(None, description="Authentication Token"),
    db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """Get the user's reward history

Args:
Limit: Number of records per page
Offset: Offset
Authorization: Authentication Token
DB: database session

Returns:
reward history"""
    # Get the current user ID
    user_id = TokenUtil.get_user_id(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized, please log in first")
    
    # Create a reward service
    reward_service = RewardService(db)
    
    try:
        # Get reward history
        history = await reward_service.get_challenge_rewards_history(user_id, limit, offset)
        return history
    except HTTPException as e:
        # Passing HTTP Exceptions Directly
        raise e
    except Exception as e:
        # Other exceptions are converted to HTTP exceptions
        raise HTTPException(status_code=500, detail=f"获取奖励历史失败: {str(e)}")