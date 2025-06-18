from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi_pagination import Page

from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.point_record.base import (
    PointRecordCreate, PointRecordUpdate, PointRecordResponse, 
    PointRecordFilter, PointRecordStatistics, PointRecordBatchCreate,
    PointChangeType, POINT_CHANGE_TYPE_DISPLAY
)
from knowledge_api.mapper.point_record.crud import PointRecordCRUD

router_point_record = APIRouter(prefix="/point-record", tags=["Points record management"])


@router_point_record.post("/", response_model=PointRecordResponse)
async def create_point_record(
    point_record: PointRecordCreate,
    auto_update_user_detail: bool = Query(True, description="Automatically update user details"),
    db: Session = Depends(get_session)
) -> PointRecordResponse:
    """Create points record"""
    crud = PointRecordCRUD(db)
    
    try:
        if auto_update_user_detail:
            # Create credit records and update user details synchronously
            created_record = await crud.create_with_user_detail_update(obj_in=point_record)
        else:
            # Only create points records, do not update user details
            created_record = await crud.create(obj_in=point_record)
        
        return crud._to_response_model(created_record)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"创建积分记录失败: {str(e)}")


@router_point_record.post("/batch", response_model=List[PointRecordResponse])
async def batch_create_point_records(
    batch_data: PointRecordBatchCreate,
    db: Session = Depends(get_session)
) -> List[PointRecordResponse]:
    """Batch Creation of Credits"""
    crud = PointRecordCRUD(db)
    
    try:
        created_records = await crud.batch_create_records(records=batch_data.records)
        return [crud._to_response_model(record) for record in created_records]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"批量创建积分记录失败: {str(e)}")


@router_point_record.get("/{record_id}", response_model=PointRecordResponse)
async def get_point_record(
    record_id: int,
    db: Session = Depends(get_session)
) -> PointRecordResponse:
    """Get a single point record"""
    crud = PointRecordCRUD(db)
    point_record = await crud.get_by_id(id=record_id)
    if not point_record:
        raise HTTPException(status_code=404, detail="Integral record does not exist")
    
    return crud._to_response_model(point_record)


@router_point_record.get("/", response_model=Page[PointRecordResponse])
async def list_point_records(
    user_id: Optional[int] = Query(None, description="user ID"),
    change_type: Optional[PointChangeType] = Query(None, description="change type"),
    card_id: Optional[int] = Query(None, description="Associated Card ID"),
    related_id: Optional[int] = Query(None, description="Association ID"),
    min_amount: Optional[int] = Query(None, description="Minimum number of changes"),
    max_amount: Optional[int] = Query(None, description="Maximum number of changes"),
    start_time: Optional[datetime] = Query(None, description="start time"),
    end_time: Optional[datetime] = Query(None, description="end time"),
    db: Session = Depends(get_session)
) -> Page[PointRecordResponse]:
    """Get a list of points records (pagination)"""
    crud = PointRecordCRUD(db)
    
    # Build filter conditions
    filters = {}
    if user_id is not None:
        filters["user_id"] = user_id
    if change_type is not None:
        filters["change_type"] = change_type
    if card_id is not None:
        filters["card_id"] = card_id
    if related_id is not None:
        filters["related_id"] = related_id
    if min_amount is not None:
        filters["min_amount"] = min_amount
    if max_amount is not None:
        filters["max_amount"] = max_amount
    if start_time is not None:
        filters["start_time"] = start_time
    if end_time is not None:
        filters["end_time"] = end_time
    
    # Use a custom paging method to return the correct response model
    return await crud.get_all_paginated_response(
        filters=filters, 
        order_by="create_time", 
        order_desc=True
    )


@router_point_record.put("/{record_id}", response_model=PointRecordResponse)
async def update_point_record(
    record_id: int,
    point_record_update: PointRecordUpdate,
    db: Session = Depends(get_session)
) -> PointRecordResponse:
    """Update points record (only update description is allowed)"""
    crud = PointRecordCRUD(db)
    updated_record = await crud.update(id=record_id, obj_in=point_record_update)
    if not updated_record:
        raise HTTPException(status_code=404, detail="Integral record does not exist")
    
    return crud._to_response_model(updated_record)


@router_point_record.delete("/{record_id}", response_model=bool)
async def delete_point_record(
    record_id: int,
    db: Session = Depends(get_session)
) -> bool:
    """Delete the points record (operate with caution)"""
    crud = PointRecordCRUD(db)
    success = await crud.delete(id=record_id)
    if not success:
        raise HTTPException(status_code=404, detail="Integral record does not exist")
    return True


# user related interface
@router_point_record.get("/user/{user_id}/records", response_model=List[PointRecordResponse])
async def get_user_point_records(
    user_id: int,
    limit: int = Query(50, description="number of records", ge=1, le=500),
    change_type: Optional[PointChangeType] = Query(None, description="change type"),
    db: Session = Depends(get_session)
) -> List[PointRecordResponse]:
    """Get the user's points record"""
    crud = PointRecordCRUD(db)
    return await crud.get_user_point_records(
        user_id=user_id, 
        limit=limit, 
        change_type=change_type
    )


@router_point_record.get("/user/{user_id}/summary")
async def get_user_point_summary(
    user_id: int,
    db: Session = Depends(get_session)
):
    """Get user points summary information"""
    crud = PointRecordCRUD(db)
    return await crud.get_user_point_summary(user_id=user_id)


# statistical correlation interface
@router_point_record.get("/statistics/overview", response_model=PointRecordStatistics)
async def get_point_record_statistics(
    user_id: Optional[int] = Query(None, description="User ID (optional, global statistics if not passed)"),
    start_time: Optional[datetime] = Query(None, description="start time"),
    end_time: Optional[datetime] = Query(None, description="end time"),
    db: Session = Depends(get_session)
) -> PointRecordStatistics:
    """Get points record statistics"""
    crud = PointRecordCRUD(db)
    return await crud.get_statistics(
        user_id=user_id,
        start_time=start_time,
        end_time=end_time
    )


@router_point_record.get("/statistics/daily")
async def get_daily_statistics(
    start_date: datetime = Query(..., description="Start Date"),
    end_date: datetime = Query(..., description="end date"),
    user_id: Optional[int] = Query(None, description="User ID (optional)"),
    db: Session = Depends(get_session)
):
    """Get daily points stats"""
    crud = PointRecordCRUD(db)
    return await crud.get_daily_statistics(
        start_date=start_date,
        end_date=end_date,
        user_id=user_id
    )


@router_point_record.get("/statistics/type-distribution")
async def get_type_distribution(
    user_id: Optional[int] = Query(None, description="User ID (optional)"),
    start_time: Optional[datetime] = Query(None, description="start time"),
    end_time: Optional[datetime] = Query(None, description="end time"),
    db: Session = Depends(get_session)
):
    """Obtain integral variation type distribution statistics"""
    crud = PointRecordCRUD(db)
    return await crud.get_type_distribution(
        user_id=user_id,
        start_time=start_time,
        end_time=end_time
    )


@router_point_record.get("/statistics/top-earners")
async def get_top_earners(
    limit: int = Query(10, description="number of leaderboards", ge=1, le=100),
    days: int = Query(30, description="statistical days", ge=1, le=365),
    db: Session = Depends(get_session)
):
    """Get points to earn leaderboards"""
    crud = PointRecordCRUD(db)
    return await crud.get_top_earners(limit=limit, days=days)


@router_point_record.get("/statistics/large-transactions", response_model=List[PointRecordResponse])
async def get_large_transactions(
    min_amount: int = Query(1000, description="minimum amount", ge=1),
    limit: int = Query(20, description="number of records", ge=1, le=100),
    db: Session = Depends(get_session)
) -> List[PointRecordResponse]:
    """Obtain recent large transactions"""
    crud = PointRecordCRUD(db)
    return await crud.get_recent_large_transactions(
        min_amount=min_amount,
        limit=limit
    )


# query interface by type
@router_point_record.get("/by-type/{change_type}", response_model=List[PointRecordResponse])
async def get_records_by_type(
    change_type: PointChangeType,
    limit: int = Query(100, description="number of records", ge=1, le=500),
    user_id: Optional[int] = Query(None, description="User ID (optional)"),
    db: Session = Depends(get_session)
) -> List[PointRecordResponse]:
    """Get records by type of change"""
    crud = PointRecordCRUD(db)
    records = await crud.get_records_by_type(
        change_type=change_type,
        limit=limit,
        user_id=user_id
    )
    return [crud._to_response_model(record) for record in records]


# Get all available change types
@router_point_record.get("/types/all")
async def get_all_change_types():
    """Get all points change types"""
    return {
        "types": [
            {
                "code": change_type.value,
                "display_name": display_name,
                "description": f"{display_name}相关的积分变动"
            }
            for change_type, display_name in POINT_CHANGE_TYPE_DISPLAY.items()
        ]
    }


# Easy interface for integral operation
@router_point_record.post("/quick-actions/reward", response_model=PointRecordResponse)
async def quick_reward_points(
    user_id: int,
    amount: int = Query(..., description="Number of Reward Points", gt=0),
    change_type: PointChangeType = Query(PointChangeType.SYSTEM_REWARD, description="Reward type"),
    description: Optional[str] = Query(None, description="reward description"),
    related_id: Optional[int] = Query(None, description="Association ID"),
    card_id: Optional[int] = Query(None, description="Associated Card ID"),
    db: Session = Depends(get_session)
) -> PointRecordResponse:
    """Quick Rewards Points"""
    crud = PointRecordCRUD(db)
    
    # Acquire the user's current points (from the user details module)
    from knowledge_api.mapper.user_detail.crud import UserDetailCRUD
    user_detail_crud = UserDetailCRUD(db)
    user_detail = await user_detail_crud.get_by_user_id(user_id=user_id)
    current_amount = (user_detail.total_points if user_detail else 0) + amount
    
    # Create points record
    point_record = PointRecordCreate(
        user_id=user_id,
        change_amount=amount,
        current_amount=current_amount,
        change_type=change_type,
        description=description,
        related_id=related_id,
        card_id=card_id
    )
    
    try:
        created_record = await crud.create_with_user_detail_update(obj_in=point_record)
        return crud._to_response_model(created_record)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"奖励积分失败: {str(e)}")


@router_point_record.post("/quick-actions/deduct", response_model=PointRecordResponse)
async def quick_deduct_points(
    user_id: int,
    amount: int = Query(..., description="Deduct the number of points", gt=0),
    change_type: PointChangeType = Query(PointChangeType.SHOP_PURCHASE, description="Deduction type"),
    description: Optional[str] = Query(None, description="Deduction description"),
    related_id: Optional[int] = Query(None, description="Association ID"),
    card_id: Optional[int] = Query(None, description="Associated Card ID"),
    db: Session = Depends(get_session)
) -> PointRecordResponse:
    """Quick deduction of points"""
    crud = PointRecordCRUD(db)
    
    # Acquire the user's current points (from the user details module)
    from knowledge_api.mapper.user_detail.crud import UserDetailCRUD
    user_detail_crud = UserDetailCRUD(db)
    user_detail = await user_detail_crud.get_by_user_id(user_id=user_id)
    
    if not user_detail or user_detail.available_points < amount:
        raise HTTPException(status_code=400, detail="Insufficient user points")
    
    current_amount = user_detail.total_points - amount
    
    # Create a points record (negative numbers represent deductions)
    point_record = PointRecordCreate(
        user_id=user_id,
        change_amount=-amount,
        current_amount=current_amount,
        change_type=change_type,
        description=description,
        related_id=related_id,
        card_id=card_id
    )
    
    try:
        created_record = await crud.create_with_user_detail_update(obj_in=point_record)
        return crud._to_response_model(created_record)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"扣除积分失败: {str(e)}") 