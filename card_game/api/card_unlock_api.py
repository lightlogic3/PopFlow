"""Card Game - Card Unlock API"""
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlmodel import Session
from typing import List, Optional, Dict, Any

from knowledge_api.framework.database.database import get_session
from knowledge_api.framework.auth.token_util import TokenUtil
from card_game.server.card_unlock_service import CardUnlockService

router_card_unlock = APIRouter(prefix="/unlock", tags=["Card Game - Card Unlock"])


@router_card_unlock.post("/{card_id}", response_model=Dict[str, Any])
async def unlock_card_with_points(
    card_id: int,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """Use Points to Unlock Cards

- Check if the user has enough points
- Check if the user has unlocked the card
- Deduct points and add cards to user deck

Parameter:
- card_id: Card ID to unlock

Return:
- Unlock result information"""
    # Get the current user ID
    user_id = TokenUtil.get_user_id(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="The user is not logged in or the login has expired")
    
    # Invoke the unlock service
    unlock_service = CardUnlockService(db)
    try:
        result = await unlock_service.unlock_card_with_points(user_id, card_id)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解锁卡牌失败: {str(e)}") 