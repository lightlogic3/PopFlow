"""Card Game - User Points Recording API"""
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlmodel import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from knowledge_api.framework.database.database import get_session
from knowledge_api.framework.auth.token_util import TokenUtil
from knowledge_api.mapper.point_record.crud import PointRecordCRUD
from knowledge_api.mapper.point_record.base import PointRecordResponse, PointChangeType
from card_game.server.user_point_service import UserPointService

router_user_point = APIRouter(prefix="/user-points", tags=["Card Game - User Points"])


@router_user_point.get("/list", response_model=List[Dict[str, Any]])
async def get_user_point_records_list(
    limit: int = Query(50, description="Return number of records", ge=1, le=100),
    authorization: str = Header(..., description="User Authentication Token"),
    db: Session = Depends(get_session)
) -> List[Dict[str, Any]]:
    """Get a list of user points changes (simplified version)

- Returns all types of points change records for users
- Contains basic change information and card information (if there are associated cards)"""
    # Get the current user ID
    user_id = TokenUtil.get_user_id(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized, please log in first")

    # Use the user points service to obtain user points records
    service = UserPointService(db)
    return await service.get_user_point_records(user_id=user_id, limit=limit)


@router_user_point.get("/summary", response_model=Dict[str, Any])
async def get_user_point_summary(
    authorization: str = Header(..., description="User Authentication Token"),
    db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """Get user points summary statistics

- Returns users' available points, total revenue, total expenses, and recent records
- Provide an overview of points usage"""
    # Get the current user ID
    user_id = TokenUtil.get_user_id(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized, please log in first")
    
    # Use the user points service to obtain points summary
    service = UserPointService(db)
    return await service.get_point_summary(user_id=user_id)


@router_user_point.get("/available", response_model=Dict[str, int])
async def get_user_available_points(
    authorization: str = Header(..., description="User Authentication Token"),
    db: Session = Depends(get_session)
) -> Dict[str, int]:
    """Acquire User Available Points

- Returns the number of points currently available to the user"""
    # Get the current user ID
    user_id = TokenUtil.get_user_id(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized, please log in first")
    
    # Use the user points service to obtain user available points
    service = UserPointService(db)
    available_points = await service.get_user_available_points(user_id=user_id)
    
    return {"available_points": available_points} 