from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List

from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.chat_session.base import SessionResponse, SessionCreate, Session as ChatSession, SessionUpdate
from knowledge_api.mapper.chat_session.crud import SessionCRUD

router_session = APIRouter(prefix="/sessions", tags=["session management"])


@router_session.post("/", response_model=SessionResponse)
async def create_session(
        session: SessionCreate,
        db: Session = Depends(get_session)
) -> ChatSession:
    """Create a session"""
    session.type_session = "admin"
    crud = SessionCRUD(db)
    return await crud.create(session=session)


@router_session.get("/user/{user_id}", response_model=List[SessionResponse])
async def list_user_sessions(
        user_id: str,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=100),
        db: Session = Depends(get_session)
) -> List[ChatSession]:
    """Get the user's session list"""
    crud = SessionCRUD(db)
    return await crud.get_by_user_id(user_id=user_id, skip=skip, limit=limit)


@router_session.get("/get_list_admin", response_model=List[SessionResponse])
async def list_sessions(
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=100),
        db: Session = Depends(get_session)
) -> List[ChatSession]:
    """Get a list of all conversations"""
    crud = SessionCRUD(db)
    return await crud.get_all(user_id="admin", skip=skip, limit=limit)


@router_session.get("/get_list_user", response_model=List[SessionResponse])
async def get_sessions_user_list(
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=100),
        db: Session = Depends(get_session)
) -> List[ChatSession]:
    """Get a list of all conversations"""
    crud = SessionCRUD(db)
    return await crud.get_all(skip=skip, limit=limit)


@router_session.put("/{session_id}", response_model=SessionResponse)
async def update_session(
        session_id: str,
        session_update: SessionUpdate,
        db: Session = Depends(get_session)
) -> ChatSession:
    """Update session"""
    crud = SessionCRUD(db)
    session = await crud.update(id=session_id, obj_in=session_update)
    if not session:
        raise HTTPException(status_code=404, detail="Session does not exist")
    return session


@router_session.delete("/{session_id}", response_model=bool)
async def delete_session(
        session_id: str,
        db: Session = Depends(get_session)
) -> bool:
    """Delete session (soft delete)"""
    crud = SessionCRUD(db)
    success = await crud.delete(session_id=session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session does not exist")
    return True


@router_session.delete("/{session_id}/permanent", response_model=bool)
async def permanently_delete_session(
        session_id: str,
        db: Session = Depends(get_session)
) -> bool:
    """Permanently delete a session"""
    crud = SessionCRUD(db)
    success = await crud.permanently_delete(session_id=session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session does not exist")
    return True


@router_session.get("/get_session/{session_id}", response_model=SessionResponse)
async def get_session(
        session_id: str,
        db: Session = Depends(get_session)
) -> ChatSession:
    """Get a single session"""
    crud = SessionCRUD(db)
    session = await crud.get_by_id(id=session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session does not exist")
    return session
