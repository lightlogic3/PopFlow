from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Dict, Any, Optional
from fastapi_pagination import Page

from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.card_usage_record.base import CardUsageRecordResponse, CardUsageRecordCreate, CardUsageRecord, CardUsageRecordUpdate
from knowledge_api.mapper.card_usage_record.crud import CardUsageRecordCRUD

router_card_usage_record = APIRouter(prefix="/card_usage_records", tags=["Card usage record management"])


@router_card_usage_record.post("/", response_model=CardUsageRecordResponse)
async def create_card_usage_record(
        record: CardUsageRecordCreate,
        db: Session = Depends(get_session)
) -> CardUsageRecord:
    """Create a card usage record"""
    crud = CardUsageRecordCRUD(db)
    return await crud.create(record=record)


@router_card_usage_record.get("/all", response_model=List[CardUsageRecordResponse])
async def list_all_card_usage_records(
        limit: int = Query(100, description="Maximum number of returns"),
        db: Session = Depends(get_session)
) -> List[CardUsageRecord]:
    """Get all card usage records (without pagination)"""
    crud = CardUsageRecordCRUD(db)
    return await crud.get_all(limit=limit)


@router_card_usage_record.get("/{record_id}", response_model=CardUsageRecordResponse)
async def get_card_usage_record(
        record_id: int,
        db: Session = Depends(get_session)
) -> CardUsageRecord:
    """Get a single card usage record"""
    crud = CardUsageRecordCRUD(db)
    record = await crud.get_by_id(record_id=record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Card usage record does not exist")
    return record


@router_card_usage_record.get("/", response_model=Page[CardUsageRecordResponse])
async def list_card_usage_records(
        db: Session = Depends(get_session)
) -> Page[CardUsageRecordResponse]:
    """Get the card usage record list (pagination)"""
    crud = CardUsageRecordCRUD(db)
    return await crud.get_all_paginated()


@router_card_usage_record.get("/user/{user_id}", response_model=List[CardUsageRecordResponse])
async def get_user_card_usage_records(
        user_id: int,
        limit: int = Query(100, description="Maximum number of returns"),
        db: Session = Depends(get_session)
) -> List[CardUsageRecord]:
    """Get all the user's card usage records"""
    crud = CardUsageRecordCRUD(db)
    return await crud.get_by_user_id(user_id=user_id, limit=limit)


@router_card_usage_record.get("/card/{card_id}", response_model=List[CardUsageRecordResponse])
async def get_card_usage_records(
        card_id: int,
        limit: int = Query(100, description="Maximum number of returns"),
        db: Session = Depends(get_session)
) -> List[CardUsageRecord]:
    """Obtain all usage records for a specific card"""
    crud = CardUsageRecordCRUD(db)
    return await crud.get_by_card_id(card_id=card_id, limit=limit)


@router_card_usage_record.get("/user/{user_id}/card/{card_id}", response_model=List[CardUsageRecordResponse])
async def get_user_card_specific_usage_records(
        user_id: int,
        card_id: int,
        limit: int = Query(100, description="Maximum number of returns"),
        db: Session = Depends(get_session)
) -> List[CardUsageRecord]:
    """Obtain all usage records for a user's specific card"""
    crud = CardUsageRecordCRUD(db)
    return await crud.get_by_user_and_card(user_id=user_id, card_id=card_id, limit=limit)


@router_card_usage_record.get("/type/{usage_type}", response_model=List[CardUsageRecordResponse])
async def get_usage_type_records(
        usage_type: str,
        limit: int = Query(100, description="Maximum number of returns"),
        db: Session = Depends(get_session)
) -> List[CardUsageRecord]:
    """Get all records for a specific usage type"""
    crud = CardUsageRecordCRUD(db)
    return await crud.get_by_usage_type(usage_type=usage_type, limit=limit)


@router_card_usage_record.get("/user/{user_id}/type/{usage_type}", response_model=List[Any])
async def get_user_usage_type_records(
        user_id: int,
        usage_type: str,
        include_card_details: bool = Query(True, description="Does it include card details?"),
        limit: int = Query(100, description="Maximum number of returns"),
        db: Session = Depends(get_session)
) -> List[Any]:
    """Get all usage records for a user's specific type

Args:
user_id: User ID
usage_type: Types of use
include_card_details: Whether the card details are included, if true, the table query will be connected and the card information will be returned
Limit: Maximum number of returns

Returns:
A list of user-specific usage records, each containing card_detail fields if include_card_details True"""
    crud = CardUsageRecordCRUD(db)
    
    if include_card_details:
        return await crud.get_by_user_and_type_with_card_details(user_id=user_id, usage_type=usage_type, limit=limit)
    else:
        return await crud.get_by_user_and_type(user_id=user_id, usage_type=usage_type, limit=limit)


@router_card_usage_record.get("/user/{user_id}/stats", response_model=Dict[str, Any])
async def get_user_usage_statistics(
        user_id: int,
        db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """Obtain user card usage statistics"""
    crud = CardUsageRecordCRUD(db)
    return await crud.get_user_usage_stats(user_id=user_id)


@router_card_usage_record.put("/{record_id}", response_model=CardUsageRecordResponse)
async def update_card_usage_record(
        record_id: int,
        record_update: CardUsageRecordUpdate,
        db: Session = Depends(get_session)
) -> CardUsageRecord:
    """Update card usage record"""
    crud = CardUsageRecordCRUD(db)
    record = await crud.update(record_id, record_update)
    if not record:
        raise HTTPException(status_code=404, detail="Card usage record does not exist")
    return record


@router_card_usage_record.put("/{record_id}/end", response_model=CardUsageRecordResponse)
async def end_card_usage(
        record_id: int,
        end_time: Optional[datetime] = None,
        db: Session = Depends(get_session)
) -> CardUsageRecord:
    """End card use (update end time)"""
    crud = CardUsageRecordCRUD(db)
    record = await crud.update_end_time(record_id, end_time)
    if not record:
        raise HTTPException(status_code=404, detail="Card usage record does not exist")
    return record


@router_card_usage_record.put("/{record_id}/points", response_model=CardUsageRecordResponse)
async def update_record_points(
        record_id: int,
        points_earned: int,
        db: Session = Depends(get_session)
) -> CardUsageRecord:
    """Update Card Use Earned Points"""
    crud = CardUsageRecordCRUD(db)
    record = await crud.update_points_earned(record_id, points_earned)
    if not record:
        raise HTTPException(status_code=404, detail="Card usage record does not exist")
    return record


@router_card_usage_record.delete("/{record_id}", response_model=bool)
async def delete_card_usage_record(
        record_id: int,
        db: Session = Depends(get_session)
) -> bool:
    """Delete card usage record"""
    crud = CardUsageRecordCRUD(db)
    success = await crud.delete(record_id=record_id)
    if not success:
        raise HTTPException(status_code=404, detail="Card usage record does not exist")
    return True 