"""Blind Box Management API"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_pagination import Page, paginate
from sqlmodel import Session

from knowledge_api.framework.database.database import get_session
from knowledge_api.framework.utils.param_utils import build_filters
from knowledge_api.mapper.blind_box.base import (
    BlindBoxCreate,
    BlindBoxUpdate, 
    BlindBoxResponse,
    BlindBoxFilter,
    GUARANTEE_RARITY_CHOICES
)
from knowledge_api.mapper.blind_box.crud import BlindBoxCRUD

router = APIRouter(prefix="/blind-box", tags=["blind box management"])
@router.get("/choices/guarantee-rarity", summary="Get guaranteed rarity selection")
async def get_guarantee_rarity_choices():
    """Get the guaranteed rarity selection list"""
    return [
        {"value": key, "label": value}
        for key, value in GUARANTEE_RARITY_CHOICES.items()
    ]

# @Router.get ("/all", response_model = List [BlindBoxResponse], summary = "Get a list of all blind boxes")
# async def get_all_blind_boxes(
#     db: Session = Depends(get_session)
# ):
#     """Get a list of all blind boxes (without pagination)"""
#     crud = BlindBoxCRUD(db)
#     Return await crud.get_all (limit = 1000) #Set a larger limit to get all blind boxes


@router.post("/", response_model=BlindBoxResponse, summary="Create a blind box")
async def create_blind_box(
    blind_box_in: BlindBoxCreate,
    db: Session = Depends(get_session)
):
    """Create a new blind box"""
    crud = BlindBoxCRUD(db)
    return await crud.create(blind_box_in, creator_id=1)  # TODO: Get user ID from authentication information

@router.get("/", response_model=Page[BlindBoxResponse], summary="Get a list of blind boxes")
async def get_blind_boxes(
    name: Optional[str] = Query(None, description="Blind box name"),
    status: Optional[str] = Query(None, description="state"),
    guarantee_rarity: Optional[str] = Query(None, description="guaranteed rarity"),
    page: int = Query(1, description="page number", ge=1),
    size: int = Query(20, description="page size", ge=1, le=100),
    db: Session = Depends(get_session)
):
    """Get blind box paging list"""
    crud = BlindBoxCRUD(db)
    
    # Build filter parameters
    filters = build_filters(
        name=name,
        status=status, 
        guarantee_rarity=guarantee_rarity
    )
    
    # Get paging data
    return await crud.filter_paginated(filters)

@router.get("/{blind_box_id}", response_model=BlindBoxResponse, summary="Get the blind box details.")
async def get_blind_box(
    blind_box_id: int,
    db: Session = Depends(get_session)
):
    """Get the blind box details according to the ID."""
    crud = BlindBoxCRUD(db)
    blind_box = await crud.get_by_id(blind_box_id)
    
    if not blind_box:
        raise HTTPException(status_code=404, detail="The blind box does not exist.")
    
    return blind_box

@router.put("/{blind_box_id}", response_model=BlindBoxResponse, summary="Update blind box")
async def update_blind_box(
    blind_box_id: int,
    blind_box_in: BlindBoxUpdate,
    db: Session = Depends(get_session)
):
    """Update blind box information"""
    crud = BlindBoxCRUD(db)
    blind_box = await crud.update(blind_box_id, blind_box_in, updater_id=1)  # TODO: Get user ID from authentication information
    
    if not blind_box:
        raise HTTPException(status_code=404, detail="The blind box does not exist.")
    
    return blind_box

@router.delete("/{blind_box_id}", summary="Remove blind box")
async def delete_blind_box(
    blind_box_id: int,
    db: Session = Depends(get_session)
):
    """soft delete blind box"""
    crud = BlindBoxCRUD(db)
    success = await crud.soft_delete(blind_box_id, updater_id=1)  # TODO: Get user ID from authentication information
    
    if not success:
        raise HTTPException(status_code=404, detail="The blind box does not exist.")
    
    return {"message": "Blind box deleted successfully"}

@router.get("/active/list", response_model=List[BlindBoxResponse], summary="Get a list of enabled blind boxes")
async def get_active_blind_boxes(
    skip: int = Query(0, description="skip record count", ge=0),
    limit: int = Query(100, description="Limit the number of records", ge=1, le=1000),
    db: Session = Depends(get_session)
):
    """Get a list of enabled blind boxes"""
    crud = BlindBoxCRUD(db)
    return await crud.get_active_blind_boxes(skip=skip, limit=limit)

