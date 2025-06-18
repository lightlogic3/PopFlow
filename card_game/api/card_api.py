"""Card Game - Card API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Optional, Dict, Any

from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.card import RARITY_CHOICES, UNLOCK_TYPE_CHOICES
from card_game.server.card_service import CardService

router_card_game = APIRouter(prefix="/cards", tags=["Card Game - Card Game"])


@router_card_game.get("/{card_id}", response_model=Dict[str, Any])
async def get_card_detail(
    card_id: int,
    db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """Get individual card details"""
    card_service = CardService(db)
    try:
        return await card_service.get_card_detail(card_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取卡牌数据失败: {str(e)}")


@router_card_game.get("/enums/rarity")
async def get_rarity_choices():
    """Get Rarity Option"""
    return RARITY_CHOICES


@router_card_game.get("/enums/unlock-type")
async def get_unlock_type_choices():
    """Get unlock type option"""
    return UNLOCK_TYPE_CHOICES 