"""Card series API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Optional
from fastapi_pagination import Page

from knowledge_api.framework.database.database import get_session
from knowledge_api.framework.utils.param_utils import build_filters
from knowledge_api.mapper.card_series import (
    CardSeries, 
    CardSeriesCreate, 
    CardSeriesUpdate, 
    CardSeriesFilter, 
    CardSeriesResponse,
    CardSeriesCRUD
)

router_card_series = APIRouter(prefix="/card-series", tags=["Card series management"])


@router_card_series.post("/", response_model=CardSeriesResponse)
async def create_card_series(
    series: CardSeriesCreate,
    db: Session = Depends(get_session)
) -> CardSeries:
    """Create a card series"""
    crud = CardSeriesCRUD(db)
    
    # Check if the encoding already exists
    existing_series = await crud.get_by_code(series.code)
    if existing_series:
        raise HTTPException(status_code=400, detail="The serial code already exists")
    
    return await crud.create(series)


@router_card_series.get("/{series_id}", response_model=CardSeriesResponse)
async def get_card_series(
    series_id: int,
    db: Session = Depends(get_session)
) -> CardSeries:
    """Acquire a single card series"""
    crud = CardSeriesCRUD(db)
    series = await crud.get_by_id(series_id)
    if not series:
        raise HTTPException(status_code=404, detail="The card series does not exist")
    return series


@router_card_series.get("/", response_model=Page[CardSeriesResponse])
async def list_card_series(
    name: Optional[str] = Query(None, description="Series name"),
    code: Optional[str] = Query(None, description="serial coding"),
    status: Optional[str] = Query(None, description="state"),
    db: Session = Depends(get_session)
) -> Page[CardSeriesResponse]:
    """Get a list of card series (pagination)"""
    crud = CardSeriesCRUD(db)
    
    # Build filter conditions
    filters = build_filters(name=name, code=code, status=status)
    
    return await crud.get_all_paginated(filters=filters, order_by="sort_order")


@router_card_series.get("/active/list", response_model=List[CardSeriesResponse])
async def get_active_card_series(
    skip: int = Query(0, description="skip record count"),
    limit: int = Query(100, description="Limit the number of records"),
    db: Session = Depends(get_session)
) -> List[CardSeries]:
    """Get a list of enabled card series"""
    crud = CardSeriesCRUD(db)
    return await crud.get_active_series(skip=skip, limit=limit)


@router_card_series.put("/{series_id}", response_model=CardSeriesResponse)
async def update_card_series(
    series_id: int,
    series_update: CardSeriesUpdate,
    db: Session = Depends(get_session)
) -> CardSeries:
    """Update Card Series"""
    crud = CardSeriesCRUD(db)
    
    # If updating the encoding, check for duplicates
    if series_update.code:
        existing_series = await crud.get_by_code(series_update.code)
        if existing_series and existing_series.id != series_id:
            raise HTTPException(status_code=400, detail="The serial code already exists")
    
    series = await crud.update(series_id, series_update)
    if not series:
        raise HTTPException(status_code=404, detail="The card series does not exist")
    return series


@router_card_series.delete("/{series_id}", response_model=bool)
async def delete_card_series(
    series_id: int,
    db: Session = Depends(get_session)
) -> bool:
    """Delete Card Series (Soft Delete)"""
    crud = CardSeriesCRUD(db)
    
    # Check if there are any cards under the series.
    from knowledge_api.mapper.card import CardCRUD
    card_crud = CardCRUD(db)
    card_count = await card_crud.count_by_series(series_id)
    if card_count > 0:
        raise HTTPException(status_code=400, detail="There are also cards under this series that cannot be deleted.")
    
    success = await crud.soft_delete(series_id)
    if not success:
        raise HTTPException(status_code=404, detail="The card series does not exist")
    return True


@router_card_series.get("/code/{code}", response_model=CardSeriesResponse)
async def get_card_series_by_code(
    code: str,
    db: Session = Depends(get_session)
) -> CardSeries:
    """Obtain a card series through code"""
    crud = CardSeriesCRUD(db)
    series = await crud.get_by_code(code)
    if not series:
        raise HTTPException(status_code=404, detail="The card series does not exist")
    return series 