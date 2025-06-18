"""Game task session API interface"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from fastapi_pagination import Page

from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.task_game_sessions.base import (
    TaskGameSession,
    TaskGameSessionCreate,
    TaskGameSessionUpdate,
    TaskGameSessionResponse,
    TaskGameSessionFilter,
    TaskGameSessionStats
)
from knowledge_api.mapper.task_game_sessions.crud import TaskGameSessionCRUD

# Create route
task_game_sessions_router = APIRouter(prefix="/task-game-sessions", tags=["Game Quest Session"])


@task_game_sessions_router.post("/filter", response_model=Page[TaskGameSessionResponse])
async def filter_sessions(
        filters: TaskGameSessionFilter,
        db: Session = Depends(get_session)
) -> Page[TaskGameSessionResponse]:
    """Filter sessions by criteria (paging)

Args:
Filters: filter criteria
DB: database session

Returns:
Page [TaskGameSessionResponse]: list of filtered sessions after paging"""
    crud = TaskGameSessionCRUD(db)
    return await crud.filter_sessions_paginated(filters=filters)


@task_game_sessions_router.get("/statistics/summary", response_model=TaskGameSessionStats)
async def get_statistics(
        user_id: Optional[str] = Query(None),
        start_date: Optional[datetime] = Query(None),
        end_date: Optional[datetime] = Query(None),
        db: Session = Depends(get_session)
) -> TaskGameSessionStats:
    """Get session statistics

Args:
user_id: User ID
start_date: Start Date
end_date: End date
DB: database session

Returns:
TaskGameSessionStats: Statistics"""
    crud = TaskGameSessionCRUD(db)
    return await crud.get_statistics(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date
    )
@task_game_sessions_router.post("/", response_model=TaskGameSessionResponse)
async def create_session(
    session_data: TaskGameSessionCreate,
    db: Session = Depends(get_session)
) -> TaskGameSession:
    """Create a new game session

Args:
session_data: Session Data
DB: database session

Returns:
TaskGameSession: created session"""
    crud = TaskGameSessionCRUD(db)
    return await crud.create(session=session_data)


@task_game_sessions_router.get("/{session_id}", response_model=TaskGameSessionResponse)
async def get_session(
    session_id: str,
    db: Session = Depends(get_session)
) -> TaskGameSession:
    """Get a single session

Args:
session_id: Session ID
DB: database session

Returns:
TaskGameSession: session found"""
    crud = TaskGameSessionCRUD(db)
    session = await crud.get_by_id(id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session does not exist")
    return session


@task_game_sessions_router.get("/", response_model=Page[TaskGameSessionResponse])
async def list_sessions(
    db: Session = Depends(get_session)
) -> Page[TaskGameSessionResponse]:
    """Get a list of sessions (pagination)

Args:
DB: database session

Returns:
Page [TaskGameSessionResponse]: list of paging sessions"""
    crud = TaskGameSessionCRUD(db)
    return await crud.get_all_paginated()


@task_game_sessions_router.get("/user/{user_id}", response_model=Page[TaskGameSessionResponse])
async def get_sessions_by_user(
    user_id: str,
    db: Session = Depends(get_session)
) -> Page[TaskGameSessionResponse]:
    """Get all the user's sessions (pagination)

Args:
user_id: User ID
DB: database session

Returns:
Page [TaskGameSessionResponse]: list of paging sessions"""
    crud = TaskGameSessionCRUD(db)
    return await crud.filter_sessions_paginated(filters=TaskGameSessionFilter(user_id=user_id))



@task_game_sessions_router.put("/{session_id}", response_model=TaskGameSessionResponse)
async def update_session(
    session_id: str,
    session_update: TaskGameSessionUpdate,
    db: Session = Depends(get_session)
) -> TaskGameSession:
    """Update session

Args:
session_id: Session ID
session_update: Update Data
DB: database session

Returns:
TaskGameSession: Updated session"""
    crud = TaskGameSessionCRUD(db)
    updated_session = await crud.update(id=session_id, obj_in=session_update)
    if not updated_session:
        raise HTTPException(status_code=404, detail="Session does not exist")
    return updated_session


@task_game_sessions_router.delete("/{session_id}", response_model=bool)
async def delete_session(
    session_id: str,
    db: Session = Depends(get_session)
) -> bool:
    """Delete session

Args:
session_id: Session ID
DB: database session

Returns:
Bool: successfully deleted"""
    crud = TaskGameSessionCRUD(db)
    success = await crud.delete(id=session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session does not exist")
    return True


