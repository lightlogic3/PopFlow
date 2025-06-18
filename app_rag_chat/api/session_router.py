# api/chat_router.py
from typing import List

from fastapi import APIRouter, Depends, Query
from langchain_core.chat_sessions import ChatSession

from knowledge_api.mapper.chat_session.base import SessionResponse, SessionCreate
from knowledge_api.mapper.chat_session.crud import SessionCRUD
from knowledge_api.mapper.conversations.base import Conversation, ConversationResponse
from knowledge_api.mapper.conversations.crud import ConversationCRUD
from knowledge_api.framework.database.database import get_session
from sqlmodel import Session

session_router = APIRouter(prefix="/session", tags=["session"])


@session_router.get("/get_history/{session_id}", response_model=List[ConversationResponse])
async def get_conversations_by_session_id(
        session_id: str,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=1000),
        db: Session = Depends(get_session)
) -> List[Conversation]:
    """Get chat history based on session ID"""
    crud = ConversationCRUD(db)
    return crud.get_by_session_id(session_id=session_id, skip=skip, limit=limit)


@session_router.post("/create_session", response_model=SessionResponse)
async def create_session(
        session: SessionCreate,
        db: Session = Depends(get_session)
) -> ChatSession:
    """Create a session"""
    crud = SessionCRUD(db)
    return crud.create(session=session)

