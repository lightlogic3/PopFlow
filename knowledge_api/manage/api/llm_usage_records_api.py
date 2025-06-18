"""The LLM model uses the record API interface"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlmodel import Session
from fastapi_pagination import Page

from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.llm_usage_records.base import (
    LLMUsageRecord,
    LLMUsageRecordCreate,
    LLMUsageRecordUpdate,
    LLMUsageRecordResponse,
    LLMUsageRecordFilter,
    LLMUsageRecordStats
)
from knowledge_api.mapper.llm_usage_records.crud import LLMUsageRecordCRUD

# Create route
llm_usage_records_router = APIRouter(prefix="/llm-usage-records", tags=["LLM usage record"])

@llm_usage_records_router.post("/", response_model=LLMUsageRecordResponse)
async def create_usage_record(
    record: LLMUsageRecordCreate,
    db: Session = Depends(get_session)
) -> LLMUsageRecord:
    """Create a new LLM usage record

Args:
Record: record data
DB: database session

Returns:
LLMUsageRecord: created record"""
    crud = LLMUsageRecordCRUD(db)
    return await crud.create(record=record)


@llm_usage_records_router.post("/from-response", response_model=LLMUsageRecordResponse)
async def create_from_response(
    response_data: Dict[str, Any] = Body(...),
    vendor_type: str = Body(...),
    model_id: str = Body(...),
    application_scenario: Optional[str] = Body(None),
    related_record_id: Optional[str] = Body(None),
    db: Session = Depends(get_session)
) -> LLMUsageRecord:
    """Create usage records from LLM response data

Args:
response_data: LLM Response Data
vendor_type: Supplier Type
model_id: Model ID
application_scenario: Application Scenarios
related_record_id: Associated Record ID
DB: database session

Returns:
LLMUsageRecord: created record"""
    crud = LLMUsageRecordCRUD(db)
    return await crud.create_from_response(
        response_data=response_data,
        vendor_type=vendor_type,
        model_id=model_id,
        application_scenario=application_scenario,
        related_record_id=related_record_id
    )


@llm_usage_records_router.get("/{record_id}", response_model=LLMUsageRecordResponse)
async def get_usage_record(
    record_id: int,
    db: Session = Depends(get_session)
) -> LLMUsageRecord:
    """Get a single usage record

Args:
record_id: Record ID
DB: database session

Returns:
LLMUsageRecord: Records found"""
    crud = LLMUsageRecordCRUD(db)
    record = await crud.get_by_id(record_id=record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Usage record does not exist")
    return record


@llm_usage_records_router.get("/request/{request_id}", response_model=LLMUsageRecordResponse)
async def get_by_request_id(
    request_id: str,
    db: Session = Depends(get_session)
) -> LLMUsageRecord:
    """Obtain usage records according to the request ID

Args:
request_id: Request ID
DB: database session

Returns:
LLMUsageRecord: Records found"""
    crud = LLMUsageRecordCRUD(db)
    record = await crud.get_by_request_id(request_id=request_id)
    if not record:
        raise HTTPException(status_code=404, detail="Usage record does not exist")
    return record


@llm_usage_records_router.get("/", response_model=Page[LLMUsageRecordResponse])
async def list_usage_records(
    db: Session = Depends(get_session)
) -> Page[LLMUsageRecordResponse]:
    """Get a list of usage records (pagination)

Args:
DB: database session

Returns:
Page [LLMUsageRecordResponse]: list of paging records"""
    crud = LLMUsageRecordCRUD(db)
    return await crud.get_all_paginated()


@llm_usage_records_router.post("/filter", response_model=Page[LLMUsageRecordResponse])
async def filter_usage_records(
    filters: LLMUsageRecordFilter,
    db: Session = Depends(get_session)
) -> Page[LLMUsageRecordResponse]:
    """Filter usage records by condition (paging)

Args:
Filters: filter criteria
DB: database session

Returns:
Page [LLMUsageRecordResponse]: List of filtered records"""
    crud = LLMUsageRecordCRUD(db)
    return await crud.filter_records_paginated(filters=filters)


@llm_usage_records_router.put("/{record_id}", response_model=LLMUsageRecordResponse)
async def update_usage_record(
    record_id: int,
    record_update: LLMUsageRecordUpdate,
    db: Session = Depends(get_session)
) -> LLMUsageRecord:
    """Update usage record

Args:
record_id: Record ID
record_update: Update Data
DB: database session

Returns:
LLMUsageRecord: updated record"""
    crud = LLMUsageRecordCRUD(db)
    updated_record = await crud.update(record_id=record_id, record_update=record_update)
    if not updated_record:
        raise HTTPException(status_code=404, detail="Usage record does not exist")
    return updated_record


@llm_usage_records_router.delete("/{record_id}", response_model=bool)
async def delete_usage_record(
    record_id: int,
    db: Session = Depends(get_session)
) -> bool:
    """Delete usage record

Args:
record_id: Record ID
DB: database session

Returns:
Bool: successfully deleted"""
    crud = LLMUsageRecordCRUD(db)
    success = await crud.delete(id=record_id)
    if not success:
        raise HTTPException(status_code=404, detail="Usage record does not exist")
    return True


@llm_usage_records_router.get("/statistics/summary", response_model=LLMUsageRecordStats)
async def get_statistics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    vendor_type: Optional[str] = Query(None),
    model_id: Optional[str] = Query(None),
    application_scenario: Optional[str] = Query(None),
    db: Session = Depends(get_session)
) -> LLMUsageRecordStats:
    """Get statistics

Args:
start_date: Start Date
end_date: End date
vendor_type: Supplier Type
model_id: Model ID
application_scenario: Application Scenarios
DB: database session

Returns:
LLMUsageRecordStats: Statistics"""
    crud = LLMUsageRecordCRUD(db)
    return await crud.get_statistics(
        start_date=start_date,
        end_date=end_date,
        vendor_type=vendor_type,
        model_id=model_id,
        application_scenario=application_scenario
    )


@llm_usage_records_router.get("/statistics/daily", response_model=Dict[str, Dict])
async def get_daily_statistics(
    days: int = Query(default=30, ge=1, le=365),
    vendor_type: Optional[str] = Query(None),
    model_id: Optional[str] = Query(None),
    db: Session = Depends(get_session)
) -> Dict[str, Dict]:
    """Acquire daily statistics

Args:
Days: The number of days counted
vendor_type: Supplier Type
model_id: Model ID
DB: database session

Returns:
Dict [str, Dict]: Daily statistics"""
    crud = LLMUsageRecordCRUD(db)
    return await crud.get_daily_statistics(
        days=days,
        vendor_type=vendor_type,
        model_id=model_id
    ) 