"""Blind Box Card Association Management API"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.blind_box.base import (
    BlindBoxCardCreate,
    BlindBoxCardUpdate,
    BlindBoxCardResponse
)
from knowledge_api.mapper.blind_box.crud import BlindBoxCardCRUD

router = APIRouter(prefix="/blind-box-card", tags=["Blind Box Card Association"])

@router.post("/", response_model=BlindBoxCardResponse, summary="Create a blind box card association")
async def create_blind_box_card(
    card_in: BlindBoxCardCreate,
    db: Session = Depends(get_session)
):
    """Create a blind box card association"""
    crud = BlindBoxCardCRUD(db)
    return await crud.create(card_in, creator_id=1)  # TODO: Get user ID from authentication information

@router.get("/blind-box/{blind_box_id}", response_model=List[BlindBoxCardResponse], summary="Obtain the associated card of the blind box")
async def get_blind_box_cards(
    blind_box_id: int,
    db: Session = Depends(get_session)
):
    """Get the associated card list according to the blind box ID"""
    crud = BlindBoxCardCRUD(db)
    return await crud.get_cards_by_blind_box(blind_box_id)

@router.get("/blind-box/{blind_box_id}/card-status", summary="Get the bound and unbound cards of the blind box")
async def get_blind_box_card_status(
    blind_box_id: int,
    name: Optional[str] = Query(None, description="Card Name Search"),
    rarity: Optional[int] = Query(None, description="rarity screening"),
    page: int = Query(1, description="page number", ge=1),
    size: int = Query(12, description="page size", ge=1, le=100),
    db: Session = Depends(get_session)
):
    """Get the bound and unbound cards of the blind box

Return:
{
"bound_cards": [List of Bound Cards],
"unbound_cards": {
"Items": [List of unbound cards],
"Total": Total number of unbound cards
}
}"""
    crud = BlindBoxCardCRUD(db)
    return await crud.get_card_binding_status(
        blind_box_id=blind_box_id, 
        name=name,
        rarity=rarity,
        page=page,
        size=size
    )

@router.put("/{card_id}", response_model=BlindBoxCardResponse, summary="Update blind box card association")
async def update_blind_box_card(
    card_id: int,
    card_in: BlindBoxCardUpdate,
    db: Session = Depends(get_session)
):
    """Update blind box card related information"""
    crud = BlindBoxCardCRUD(db)
    card = await crud.update(card_id, card_in)  # TODO: Get user ID from authentication information
    
    if not card:
        raise HTTPException(status_code=404, detail="Associated record does not exist")
    
    return card

@router.delete("/{card_id}", summary="Delete blind box card association")
async def delete_blind_box_card(
    card_id: int,
    db: Session = Depends(get_session)
):
    """Delete blind box card association"""
    crud = BlindBoxCardCRUD(db)
    success = await crud.delete(card_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Associated record does not exist")
    
    return {"message": "Association deletion successful"}

@router.delete("/blind-box/{blind_box_id}/card/{card_id}", summary="Delete the specified blind box card association")
async def delete_blind_box_card_relation(
    blind_box_id: int,
    card_id: int,
    db: Session = Depends(get_session)
):
    """Delete the association between the specified blind box and the card"""
    crud = BlindBoxCardCRUD(db)
    success = await crud.delete_by_blind_box_and_card(blind_box_id, card_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Associated record does not exist")
    
    return {"message": "Association deletion successful"}

@router.post("/blind-box/{blind_box_id}/batch", response_model=List[BlindBoxCardResponse], summary="Batch creation of blind box card associations")
async def batch_create_blind_box_cards(
    blind_box_id: int,
    card_configs: List[Dict[str, Any]],
    db: Session = Depends(get_session)
):
    """Batch creation of blind box card associations

card_configs format:
[
{
"card_id": 1,
"Probability": 10.5,
"Weight": 100,
"is_special_reward": 0
}
]"""
    crud = BlindBoxCardCRUD(db)
    return await crud.batch_create_cards(blind_box_id, card_configs, creator_id=1)

@router.delete("/blind-box/{blind_box_id}/clear", summary="Empty Blind Box Card Association")
async def clear_blind_box_cards(
    blind_box_id: int,
    db: Session = Depends(get_session)
):
    """Empty all card associations of the specified blind box"""
    crud = BlindBoxCardCRUD(db)
    success = await crud.clear_blind_box_cards(blind_box_id)
    
    return {"message": f"盲盒 {blind_box_id} 的卡牌关联已清空", "success": success} 