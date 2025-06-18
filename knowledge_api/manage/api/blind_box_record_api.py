from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Dict, Any, Optional
from fastapi_pagination import Page

from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.blind_box_record.base import BlindBoxRecordResponse, BlindBoxRecordCreate, BlindBoxRecord, BlindBoxRecordUpdate
from knowledge_api.mapper.blind_box_record.crud import BlindBoxRecordCRUD

router_blind_box_record = APIRouter(prefix="/blind_box_records", tags=["Blind Box Extraction Record Management"])


@router_blind_box_record.post("/", response_model=BlindBoxRecordResponse)
async def create_blind_box_record(
        record: BlindBoxRecordCreate,
        db: Session = Depends(get_session)
) -> BlindBoxRecord:
    """Create blind box extraction record"""
    crud = BlindBoxRecordCRUD(db)
    return await crud.create(record=record)


@router_blind_box_record.get("/all", response_model=List[BlindBoxRecordResponse])
async def list_all_blind_box_records(
        limit: int = Query(100, description="Maximum number of returns"),
        db: Session = Depends(get_session)
) -> List[BlindBoxRecord]:
    """Get all blind box extraction records (without paging)"""
    crud = BlindBoxRecordCRUD(db)
    return await crud.get_all(limit=limit)


@router_blind_box_record.get("/{record_id}", response_model=BlindBoxRecordResponse)
async def get_blind_box_record(
        record_id: int,
        db: Session = Depends(get_session)
) -> BlindBoxRecord:
    """Get a single blind box extraction record"""
    crud = BlindBoxRecordCRUD(db)
    record = await crud.get_by_id(record_id=record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Blind box extraction record does not exist")
    return record


@router_blind_box_record.get("/", response_model=Page[BlindBoxRecordResponse])
async def list_blind_box_records(
        db: Session = Depends(get_session)
) -> Page[BlindBoxRecordResponse]:
    """Get a list of blind box extracted records (paging)"""
    crud = BlindBoxRecordCRUD(db)
    return await crud.get_all_paginated()


@router_blind_box_record.get("/user/{user_id}", response_model=List[Any])
async def get_user_blind_box_records(
        user_id: int,
        limit: int = Query(100, description="Maximum number of returns"),
        include_card_details: bool = Query(True, description="Does it include card details?"),
        db: Session = Depends(get_session)
) -> List[Any]:
    """Get all blind box extraction records for the user

Args:
user_id: User ID
Limit: Maximum number of returns
include_card_details: Whether the card details are included, if true, the table query will be connected and the card information will be returned

Returns:
The blind box extracts a list of records, and if include_card_details True, each record contains card_detail fields"""
    crud = BlindBoxRecordCRUD(db)
    
    if include_card_details:
        return await crud.get_by_user_id_with_card_details(user_id=user_id, limit=limit)
    else:
        return await crud.get_by_user_id(user_id=user_id, limit=limit)


@router_blind_box_record.get("/box/{box_id}", response_model=List[BlindBoxRecordResponse])
async def get_box_records(
        box_id: int,
        limit: int = Query(100, description="Maximum number of returns"),
        db: Session = Depends(get_session)
) -> List[BlindBoxRecord]:
    """Obtain all extraction records for a specific blind box"""
    crud = BlindBoxRecordCRUD(db)
    return await crud.get_by_blind_box_id(blind_box_id=box_id, limit=limit)


@router_blind_box_record.get("/user/{user_id}/box/{box_id}", response_model=List[BlindBoxRecordResponse])
async def get_user_box_records(
        user_id: int,
        box_id: int,
        limit: int = Query(100, description="Maximum number of returns"),
        db: Session = Depends(get_session)
) -> List[BlindBoxRecord]:
    """Obtain all extraction records for a user-specific blind box"""
    crud = BlindBoxRecordCRUD(db)
    return await crud.get_by_user_and_blind_box(user_id=user_id, blind_box_id=box_id, limit=limit)


@router_blind_box_record.get("/card/{card_id}", response_model=List[BlindBoxRecordResponse])
async def get_card_draw_records(
        card_id: int,
        limit: int = Query(100, description="Maximum number of returns"),
        db: Session = Depends(get_session)
) -> List[BlindBoxRecord]:
    """Obtain all draw records for a specific card"""
    crud = BlindBoxRecordCRUD(db)
    return await crud.get_by_card_id(card_id=card_id, limit=limit)


@router_blind_box_record.get("/source/{source_type}", response_model=List[BlindBoxRecordResponse])
async def get_source_type_records(
        source_type: str,
        limit: int = Query(100, description="Maximum number of returns"),
        db: Session = Depends(get_session)
) -> List[BlindBoxRecord]:
    """Get all extracted records for a specific source type"""
    crud = BlindBoxRecordCRUD(db)
    return await crud.get_by_source_type(source_type=source_type, limit=limit)


@router_blind_box_record.get("/user/{user_id}/source/{source_type}", response_model=List[BlindBoxRecordResponse])
async def get_user_source_records(
        user_id: int,
        source_type: str,
        limit: int = Query(100, description="Maximum number of returns"),
        db: Session = Depends(get_session)
) -> List[BlindBoxRecord]:
    """Get all extracted records for a user's specific source type"""
    crud = BlindBoxRecordCRUD(db)
    return await crud.get_by_user_and_source_type(user_id=user_id, source_type=source_type, limit=limit)


@router_blind_box_record.get("/guaranteed", response_model=List[BlindBoxRecordResponse])
async def get_guaranteed_records(
        user_id: Optional[int] = Query(None, description="User ID, optional"),
        limit: int = Query(100, description="Maximum number of returns"),
        db: Session = Depends(get_session)
) -> List[BlindBoxRecord]:
    """Get the extraction record triggered by the guarantee"""
    crud = BlindBoxRecordCRUD(db)
    return await crud.get_guaranteed_records(user_id=user_id, limit=limit)


@router_blind_box_record.get("/special", response_model=List[BlindBoxRecordResponse])
async def get_special_reward_records(
        user_id: Optional[int] = Query(None, description="User ID, optional"),
        limit: int = Query(100, description="Maximum number of returns"),
        db: Session = Depends(get_session)
) -> List[BlindBoxRecord]:
    """Draw records for special rewards"""
    crud = BlindBoxRecordCRUD(db)
    return await crud.get_special_rewards(user_id=user_id, limit=limit)


@router_blind_box_record.get("/user/{user_id}/stats", response_model=Dict[str, Any])
async def get_user_stats(
        user_id: int,
        db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """Obtain user blind box extraction statistics"""
    crud = BlindBoxRecordCRUD(db)
    return await crud.get_user_stats(user_id=user_id)


@router_blind_box_record.get("/user/{user_id}/latest", response_model=List[BlindBoxRecordResponse])
async def get_user_latest_records(
        user_id: int,
        limit: int = Query(10, description="Return number of records"),
        db: Session = Depends(get_session)
) -> List[BlindBoxRecord]:
    """Get the user's most recent extraction record"""
    crud = BlindBoxRecordCRUD(db)
    return await crud.get_latest_records_by_user(user_id=user_id, limit=limit)


@router_blind_box_record.get("/card/{card_id}/count", response_model=int)
async def get_card_draw_count(
        card_id: int,
        db: Session = Depends(get_session)
) -> int:
    """Get the total number of draws for a specific card"""
    crud = BlindBoxRecordCRUD(db)
    return await crud.get_card_draw_count(card_id=card_id)


@router_blind_box_record.put("/{record_id}", response_model=BlindBoxRecordResponse)
async def update_blind_box_record(
        record_id: int,
        record_update: BlindBoxRecordUpdate,
        db: Session = Depends(get_session)
) -> BlindBoxRecord:
    """Update blind box extraction records"""
    crud = BlindBoxRecordCRUD(db)
    record = await crud.update(record_id, record_update)
    if not record:
        raise HTTPException(status_code=404, detail="Blind box extraction record does not exist")
    return record


@router_blind_box_record.delete("/{record_id}", response_model=bool)
async def delete_blind_box_record(
        record_id: int,
        db: Session = Depends(get_session)
) -> bool:
    """Delete blind box extraction records"""
    crud = BlindBoxRecordCRUD(db)
    success = await crud.delete(record_id=record_id)
    if not success:
        raise HTTPException(status_code=404, detail="Blind box extraction record does not exist")
    return True 