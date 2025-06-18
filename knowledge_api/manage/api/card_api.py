"""Card API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Optional
from fastapi_pagination import Page

from knowledge_api.framework.database.database import get_session
from knowledge_api.framework.utils.param_utils import build_filters
from knowledge_api.mapper.card import (
    Card, 
    CardCreate, 
    CardUpdate, 
    CardFilter, 
    CardResponse,
    CardCRUD,
    RARITY_CHOICES,
    UNLOCK_TYPE_CHOICES
)

router_card = APIRouter(prefix="/cards", tags=["Card Management"])


@router_card.post("/", response_model=CardResponse)
async def create_card(
    card: CardCreate,
    db: Session = Depends(get_session)
) -> Card:
    """Create a card"""
    crud = CardCRUD(db)
    
    # Verify whether the series exists
    from knowledge_api.mapper.card_series import CardSeriesCRUD
    series_crud = CardSeriesCRUD(db)
    series = await series_crud.get_by_id(card.series_id)
    if not series:
        raise HTTPException(status_code=400, detail="The specified card series does not exist")
    
    return await crud.create(card)


@router_card.get("/{card_id}", response_model=CardResponse)
async def get_card(
    card_id: int,
    db: Session = Depends(get_session)
) -> Card:
    """Acquire a single card"""
    crud = CardCRUD(db)
    card = await crud.get_by_id(card_id)
    if not card:
        raise HTTPException(status_code=404, detail="The card does not exist")
    return card


@router_card.get("/", response_model=Page[CardResponse])
async def list_cards(
    name: Optional[str] = Query(None, description="Card Name"),
    series_id: Optional[str] = Query(None, description="Series ID"),
    rarity: Optional[str] = Query(None, description="rarity"),
    unlock_type: Optional[str] = Query(None, description="Unlock type"),
    status: Optional[str] = Query(None, description="state"),
    role_id: Optional[str] = Query(None, description="Role ID"),
    is_limited: Optional[str] = Query(None, description="Whether to qualify the card"),
    db: Session = Depends(get_session)
) -> Page[CardResponse]:
    """Get a list of cards (pagination)"""
    crud = CardCRUD(db)
    
    # Build filter conditions
    filters = build_filters(
        name=name,
        series_id=series_id,
        rarity=rarity,
        unlock_type=unlock_type,
        status=status,
        role_id=role_id,
        is_limited=is_limited
    )
    
    return await crud.get_all_paginated(filters=filters, order_by="sort_order")


@router_card.get("/series/{series_id}/list", response_model=List[CardResponse])
async def get_cards_by_series(
    series_id: int,
    skip: int = Query(0, description="skip record count"),
    limit: int = Query(100, description="Limit the number of records"),
    db: Session = Depends(get_session)
) -> List[Card]:
    """Get a list of cards by series ID"""
    crud = CardCRUD(db)
    return await crud.get_by_series_id(series_id, skip=skip, limit=limit)


@router_card.put("/{card_id}", response_model=CardResponse)
async def update_card(
    card_id: int,
    card_update: CardUpdate,
    db: Session = Depends(get_session)
) -> Card:
    """Update Card"""
    crud = CardCRUD(db)
    
    # If the series ID is updated, verify that the series exists
    if card_update.series_id:
        from knowledge_api.mapper.card_series import CardSeriesCRUD
        series_crud = CardSeriesCRUD(db)
        series = await series_crud.get_by_id(card_update.series_id)
        if not series:
            raise HTTPException(status_code=400, detail="The specified card series does not exist")
    
    card = await crud.update(card_id, card_update)
    if not card:
        raise HTTPException(status_code=404, detail="The card does not exist")
    return card


@router_card.delete("/{card_id}", response_model=bool)
async def delete_card(
    card_id: int,
    db: Session = Depends(get_session)
) -> bool:
    """Delete Cards (Soft Delete)"""
    crud = CardCRUD(db)
    success = await crud.soft_delete(card_id)
    if not success:
        raise HTTPException(status_code=404, detail="The card does not exist")
    return True


@router_card.get("/series/{series_id}/count", response_model=int)
async def count_cards_by_series(
    series_id: int,
    db: Session = Depends(get_session)
) -> int:
    """Count the number of cards in the series"""
    crud = CardCRUD(db)
    return await crud.count_by_series(series_id)


@router_card.get("/enums/rarity")
async def get_rarity_choices():
    """Get Rarity Option"""
    return RARITY_CHOICES


@router_card.get("/enums/unlock-type")
async def get_unlock_type_choices():
    """Get unlock type option"""
    return UNLOCK_TYPE_CHOICES 