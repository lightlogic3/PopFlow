from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Any
from fastapi_pagination import Page

from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.user_card.base import UserCardResponse, UserCardCreate, UserCard, UserCardUpdate
from knowledge_api.mapper.user_card.crud import UserCardCRUD

router_user_card = APIRouter(prefix="/user_cards", tags=["User Card Management"])


@router_user_card.post("/", response_model=UserCardResponse)
async def create_user_card(
        user_card: UserCardCreate,
        db: Session = Depends(get_session)
) -> UserCard:
    """Create a user card record"""
    crud = UserCardCRUD(db)
    return await crud.create(user_card=user_card)


@router_user_card.get("/all", response_model=List[UserCardResponse])
async def list_all_user_cards(
        limit: int = Query(100, description="Maximum number of returns"),
        db: Session = Depends(get_session)
) -> List[UserCard]:
    """Get all user card records (without pagination)"""
    crud = UserCardCRUD(db)
    return await crud.get_all(limit=limit)


@router_user_card.get("/{user_card_id}", response_model=UserCardResponse)
async def get_user_card(
        user_card_id: int,
        db: Session = Depends(get_session)
) -> UserCard:
    """Get a single user card record"""
    crud = UserCardCRUD(db)
    user_card = await crud.get_by_id(user_card_id=user_card_id)
    if not user_card:
        raise HTTPException(status_code=404, detail="User card record does not exist")
    return user_card


@router_user_card.get("/", response_model=Page[UserCardResponse])
async def list_user_cards(
        db: Session = Depends(get_session)
) -> Page[UserCardResponse]:
    """Get a list of user card records (pagination)"""
    crud = UserCardCRUD(db)
    return await crud.get_all_paginated()


@router_user_card.get("/user/{user_id}", response_model=List[Any])
async def get_user_cards(
        user_id: int,
        include_card_details: bool = Query(True, description="Does it include card details?"),
        db: Session = Depends(get_session)
) -> List[Any]:
    """Get all cards of the specified user

Args:
user_id: User ID
include_card_details: Whether the card details are included, if true, the table query will be connected and the card information will be returned

Returns:
List of user cards, if include_card_details True, each record will contain card_detail fields"""
    crud = UserCardCRUD(db)
    
    if include_card_details:
        return await crud.get_by_user_id_with_card_details(user_id=user_id)
    else:
        return await crud.get_by_user_id(user_id=user_id)


@router_user_card.put("/{user_card_id}", response_model=UserCardResponse)
async def update_user_card(
        user_card_id: int,
        user_card_update: UserCardUpdate,
        db: Session = Depends(get_session)
) -> UserCard:
    """Update user card records"""
    crud = UserCardCRUD(db)
    user_card = await crud.update(user_card_id, user_card_update)
    if not user_card:
        raise HTTPException(status_code=404, detail="User card record does not exist")
    return user_card


@router_user_card.put("/favorite/{user_id}/{card_id}", response_model=UserCardResponse)
async def update_user_card_favorite(
        user_id: int,
        card_id: int, 
        is_favorite: bool,
        db: Session = Depends(get_session)
) -> UserCard:
    """Update user card collection status"""
    crud = UserCardCRUD(db)
    user_card = await crud.update_favorite(user_id, card_id, is_favorite)
    if not user_card:
        raise HTTPException(status_code=404, detail="User card record does not exist")
    return user_card


@router_user_card.put("/increment_use/{user_id}/{card_id}", response_model=UserCardResponse)
async def increment_card_use_count(
        user_id: int,
        card_id: int,
        db: Session = Depends(get_session)
) -> UserCard:
    """Increase card usage"""
    crud = UserCardCRUD(db)
    user_card = await crud.increment_use_count(user_id, card_id)
    if not user_card:
        raise HTTPException(status_code=404, detail="User card record does not exist")
    return user_card


@router_user_card.delete("/{user_card_id}", response_model=bool)
async def delete_user_card(
        user_card_id: int,
        db: Session = Depends(get_session)
) -> bool:
    """Delete user card records"""
    crud = UserCardCRUD(db)
    success = await crud.delete(user_card_id=user_card_id)
    if not success:
        raise HTTPException(status_code=404, detail="User card record does not exist")
    return True


@router_user_card.delete("/user/{user_id}/card/{card_id}", response_model=bool)
async def delete_user_card_by_ids(
        user_id: int,
        card_id: int,
        db: Session = Depends(get_session)
) -> bool:
    """Delete user card records based on user ID and card ID"""
    crud = UserCardCRUD(db)
    success = await crud.delete_by_user_and_card(user_id=user_id, card_id=card_id)
    if not success:
        raise HTTPException(status_code=404, detail="User card record does not exist")
    return True 