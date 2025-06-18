from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Optional
from fastapi_pagination import Page

from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.user_detail.base import (
    UserDetailCreate, UserDetailUpdate, UserDetailResponse, 
    UserDetailFilter, UserDetailStatistics
)
from knowledge_api.mapper.user_detail.crud import UserDetailCRUD

router_user_detail = APIRouter(prefix="/user-detail", tags=["user details management"])


@router_user_detail.post("/", response_model=UserDetailResponse)
async def create_user_detail(
    user_detail: UserDetailCreate,
    db: Session = Depends(get_session)
) -> UserDetailResponse:
    """Create user details"""
    crud = UserDetailCRUD(db)
    
    # Check if user details already exist
    existing_detail = await crud.get_by_user_id(user_id=user_detail.user_id)
    if existing_detail:
        raise HTTPException(status_code=400, detail="The details of this user already exist")
    
    created_detail = await crud.create(obj_in=user_detail)
    # Get a response with calculated fields
    return await crud.get_user_detail_with_rates(user_id=created_detail.user_id)


@router_user_detail.get("/{detail_id}", response_model=UserDetailResponse)
async def get_user_detail(
    detail_id: int,
    db: Session = Depends(get_session)
) -> UserDetailResponse:
    """Get individual user details"""
    crud = UserDetailCRUD(db)
    user_detail = await crud.get_by_user_id(user_id=detail_id)
    if not user_detail:
        raise HTTPException(status_code=404, detail="User details do not exist")
    
    # Get a response with calculated fields
    return await crud.get_user_detail_with_rates(user_id=user_detail.user_id)


@router_user_detail.get("/by-user/{user_id}", response_model=UserDetailResponse)
async def get_user_detail_by_user_id(
    user_id: int,
    db: Session = Depends(get_session)
) -> UserDetailResponse:
    """Get user details based on user ID"""
    crud = UserDetailCRUD(db)
    user_detail_response = await crud.get_user_detail_with_rates(user_id=user_id)
    if not user_detail_response:
        raise HTTPException(status_code=404, detail="User details do not exist")
    
    return user_detail_response


@router_user_detail.get("/", response_model=Page[UserDetailResponse])
async def list_user_details(
    user_id: Optional[int] = Query(None, description="user ID"),
    min_total_points: Optional[int] = Query(None, description="minimum total integral"),
    max_total_points: Optional[int] = Query(None, description="Maximum Total Points"),
    min_login_count: Optional[int] = Query(None, description="minimum login count"),
    min_challenge_count: Optional[int] = Query(None, description="Minimum number of challenges"),
    db: Session = Depends(get_session)
) -> Page[UserDetailResponse]:
    """Get a list of user details (pagination)"""
    crud = UserDetailCRUD(db)
    
    # Build filter conditions
    filters = {}
    if user_id is not None:
        filters["user_id"] = user_id
    if min_total_points is not None:
        filters["min_total_points"] = min_total_points
    if max_total_points is not None:
        filters["max_total_points"] = max_total_points
    if min_login_count is not None:
        filters["min_login_count"] = min_login_count
    if min_challenge_count is not None:
        filters["min_challenge_count"] = min_challenge_count
    
    return await crud.get_all_paginated(filters=filters, order_by="total_points", order_desc=True)


@router_user_detail.put("/{detail_id}", response_model=UserDetailResponse)
async def update_user_detail(
    detail_id: int,
    user_detail_update: UserDetailUpdate,
    db: Session = Depends(get_session)
) -> UserDetailResponse:
    """Update user details"""
    crud = UserDetailCRUD(db)
    updated_detail = await crud.update(id=detail_id, obj_in=user_detail_update)
    if not updated_detail:
        raise HTTPException(status_code=404, detail="User details do not exist")
    
    # Get a response with calculated fields
    return await crud.get_user_detail_with_rates(user_id=updated_detail.user_id)


@router_user_detail.put("/by-user/{user_id}", response_model=UserDetailResponse)
async def update_user_detail_by_user_id(
    user_id: int,
    user_detail_update: UserDetailUpdate,
    db: Session = Depends(get_session)
) -> UserDetailResponse:
    """Update user details based on user ID"""
    crud = UserDetailCRUD(db)
    updated_detail = await crud.update_by_user_id(user_id=user_id, obj_in=user_detail_update)
    if not updated_detail:
        raise HTTPException(status_code=404, detail="User details do not exist")
    
    # Get a response with calculated fields
    return await crud.get_user_detail_with_rates(user_id=user_id)


@router_user_detail.delete("/{detail_id}", response_model=bool)
async def delete_user_detail(
    detail_id: int,
    db: Session = Depends(get_session)
) -> bool:
    """Delete user details"""
    crud = UserDetailCRUD(db)
    success = await crud.delete(id=detail_id)
    if not success:
        raise HTTPException(status_code=404, detail="User details do not exist")
    return True


# statistical correlation interface
@router_user_detail.get("/statistics/overview", response_model=UserDetailStatistics)
async def get_user_detail_statistics(
    db: Session = Depends(get_session)
) -> UserDetailStatistics:
    """Get user details statistics"""
    crud = UserDetailCRUD(db)
    return await crud.get_statistics()


@router_user_detail.get("/ranking/points", response_model=List[UserDetailResponse])
async def get_points_ranking(
    limit: int = Query(10, description="number of leaderboards", ge=1, le=100),
    db: Session = Depends(get_session)
) -> List[UserDetailResponse]:
    """Get points leaderboard"""
    crud = UserDetailCRUD(db)
    top_users = await crud.get_top_users_by_points(limit=limit)
    
    # Convert to responsive format
    result = []
    for user in top_users:
        response = await crud.get_user_detail_with_rates(user_id=user.user_id)
        if response:
            result.append(response)
    
    return result


@router_user_detail.get("/ranking/challenges", response_model=List[UserDetailResponse])
async def get_challenges_ranking(
    limit: int = Query(10, description="number of leaderboards", ge=1, le=100),
    db: Session = Depends(get_session)
) -> List[UserDetailResponse]:
    """Get the challenge leaderboard"""
    crud = UserDetailCRUD(db)
    top_users = await crud.get_top_users_by_challenges(limit=limit)
    
    # Convert to responsive format
    result = []
    for user in top_users:
        response = await crud.get_user_detail_with_rates(user_id=user.user_id)
        if response:
            result.append(response)
    
    return result


@router_user_detail.get("/ranking/active", response_model=List[UserDetailResponse])
async def get_active_ranking(
    limit: int = Query(10, description="number of leaderboards", ge=1, le=100),
    db: Session = Depends(get_session)
) -> List[UserDetailResponse]:
    """Get the most active users list"""
    crud = UserDetailCRUD(db)
    top_users = await crud.get_most_active_users(limit=limit)
    
    # Convert to responsive format
    result = []
    for user in top_users:
        response = await crud.get_user_detail_with_rates(user_id=user.user_id)
        if response:
            result.append(response)
    
    return result


# Game behavior update interface
@router_user_detail.post("/actions/login/{user_id}", response_model=bool)
async def update_login_count(
    user_id: int,
    db: Session = Depends(get_session)
) -> bool:
    """Update user logins"""
    crud = UserDetailCRUD(db)
    return await crud.update_login_count(user_id=user_id)


@router_user_detail.post("/actions/challenge/{user_id}", response_model=bool)
async def update_challenge_stats(
    user_id: int,
    success: bool = Query(False, description="Was the challenge successful?"),
    db: Session = Depends(get_session)
) -> bool:
    """Update user challenge statistics"""
    crud = UserDetailCRUD(db)
    return await crud.update_challenge_stats(user_id=user_id, success=success)


@router_user_detail.post("/actions/points/{user_id}", response_model=bool)
async def update_points(
    user_id: int,
    points_change: int = Query(..., description="number of integral changes"),
    is_earned: bool = Query(True, description="Whether to obtain points (False is consumption points)"),
    db: Session = Depends(get_session)
) -> bool:
    """Update user points"""
    if points_change <= 0:
        raise HTTPException(status_code=400, detail="The number of integral changes must be greater than 0.")
    
    crud = UserDetailCRUD(db)
    success = await crud.update_points(user_id=user_id, points_change=points_change, is_earned=is_earned)
    if not success and not is_earned:
        raise HTTPException(status_code=400, detail="Insufficient user points")
    
    return success


@router_user_detail.post("/actions/cards/{user_id}", response_model=bool)
async def update_card_count(
    user_id: int,
    count_change: int = Query(..., description="Number of cards changes"),
    db: Session = Depends(get_session)
) -> bool:
    """Update the number of user cards"""
    crud = UserDetailCRUD(db)
    return await crud.update_card_count(user_id=user_id, count_change=count_change)


@router_user_detail.post("/actions/blind-box/{user_id}", response_model=bool)
async def update_blind_box_count(
    user_id: int,
    db: Session = Depends(get_session)
) -> bool:
    """Update the number of times the user opens the blind box"""
    crud = UserDetailCRUD(db)
    return await crud.update_blind_box_count(user_id=user_id) 