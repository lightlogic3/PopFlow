"""Card Game - Card Series API"""
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlmodel import Session
from typing import List, Optional, Dict, Any

from knowledge_api.framework.database.database import get_session
from knowledge_api.framework.auth.token_util import TokenUtil
from card_game.server.card_service import CardService

router_card_game_series = APIRouter(prefix="/series", tags=["Card Game - Card Series"])


@router_card_game_series.get("/", response_model=List[Dict[str, Any]])
async def get_all_series_with_cards(
    status: Optional[str] = Query("active", description="Status, only the active state is returned by default."),
    name: Optional[str] = Query(None, description="Series name, optional filter"),
    authorization: Optional[str] = Header(None, description="Authentication Token, optional, will return the card unlock status after providing"),
    db: Session = Depends(get_session)
) -> List[Dict[str, Any]]:
    """Get a list of all card series and the cards they contain (return all data at once)

- By default, only active series are returned
Each series contains a complete list of cards
- If an authentication token is provided, the status of whether the card has been unlocked by the current user is returned
- Return format: [{series info, cards: [card list]},...]"""
    card_service = CardService(db)
    try:
        # Get the current user ID (if logged in)
        user_id = TokenUtil.get_user_id(authorization) if authorization else None
        
        # Select different query methods based on whether there is a user ID
        if user_id:
            # Query with user unlock status
            return await card_service.get_all_series_with_cards_and_unlock_status(user_id, status, name)
        else:
            # Normal query (excluding user unlock status)
            return await card_service.get_all_series_with_cards(status, name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取卡牌系列数据失败: {str(e)}")


@router_card_game_series.get("/{series_id}", response_model=Dict[str, Any])
async def get_series_with_cards(
    series_id: int,
    authorization: Optional[str] = Header(None, description="Authentication Token, optional, will return the card unlock status after providing"),
    db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """Acquire a single card series and all the cards it contains

- If an authentication token is provided, the status of whether the card has been unlocked by the current user is returned"""
    card_service = CardService(db)
    try:
        # Get the current user ID (if logged in)
        user_id = TokenUtil.get_user_id(authorization) if authorization else None
        
        # Select different query methods based on whether there is a user ID
        if user_id:
            # Query with user unlock status
            return await card_service.get_series_with_cards_and_unlock_status(series_id, user_id)
        else:
            # Normal query (excluding user unlock status)
            return await card_service.get_series_with_cards(series_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取卡牌系列数据失败: {str(e)}") 