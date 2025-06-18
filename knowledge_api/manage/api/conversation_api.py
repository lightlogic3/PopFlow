from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Dict, Any

from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.conversations.base import ConversationResponse, ConversationCreate, Conversation, ConversationUpdate
from knowledge_api.mapper.conversations.crud import ConversationCRUD

router_conversation = APIRouter(prefix="/conversations", tags=["conversation management"])


@router_conversation.post("/", response_model=ConversationResponse)
async def create_conversation(
        conversation: ConversationCreate,
        db: Session = Depends(get_session)
) -> Conversation:
    """Create conversation message"""
    crud = ConversationCRUD(db)
    return await crud.create(conversation=conversation)


@router_conversation.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
        conversation_id: int,
        db: Session = Depends(get_session)
) -> Conversation:
    """Get a single conversation message"""
    crud = ConversationCRUD(db)
    conversation = await crud.get_by_id(id=conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation message does not exist")
    return conversation


@router_conversation.get("/message/{message_id}", response_model=ConversationResponse)
async def get_conversation_by_message_id(
        message_id: str,
        db: Session = Depends(get_session)
) -> Conversation:
    """Get conversation message according to message ID"""
    crud = ConversationCRUD(db)
    conversation = await crud.get_by_message_id(message_id=message_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation message does not exist")
    return conversation


@router_conversation.get("/session/{session_id}", response_model=List[ConversationResponse])
async def get_conversations_by_session_id(
        session_id: str,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=1000),
        db: Session = Depends(get_session)
) -> List[Conversation]:
    """Get chat history based on session ID"""
    crud = ConversationCRUD(db)
    return await crud.get_by_session_id(session_id=session_id, skip=skip, limit=limit)


@router_conversation.get("/thread/{conversation_id}", response_model=List[ConversationResponse])
async def get_conversations_by_conversation_id(
        conversation_id: str,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=1000),
        db: Session = Depends(get_session)
) -> List[Conversation]:
    """Get chat history based on conversation session ID"""
    crud = ConversationCRUD(db)
    return await crud.get_by_conversation_id(conversation_id=conversation_id, skip=skip, limit=limit)


@router_conversation.get("/tree/{message_id}", response_model=Dict[str, Any])
async def get_conversation_tree(
        message_id: str,
        db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """Get the dialog tree structure"""
    crud = ConversationCRUD(db)
    tree = await crud.get_conversation_tree(message_id=message_id)
    if not tree:
        raise HTTPException(status_code=404, detail="Conversation message does not exist")
    return tree


@router_conversation.get("/user/{user_id}", response_model=List[ConversationResponse])
async def get_conversations_by_user_id(
        user_id: str,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=1000),
        db: Session = Depends(get_session)
) -> List[Conversation]:
    """Get all user conversations"""
    crud = ConversationCRUD(db)
    return await crud.get_by_user_id(user_id=user_id, skip=skip, limit=limit)


@router_conversation.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
        conversation_id: int,
        conversation_update: ConversationUpdate,
        db: Session = Depends(get_session)
) -> Conversation:
    """Update conversation message"""
    crud = ConversationCRUD(db)
    conversation = await crud.update(id=conversation_id, obj_in=conversation_update)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation message does not exist")
    return conversation


@router_conversation.delete("/{conversation_id}", response_model=bool)
async def delete_conversation(
        conversation_id: int,
        db: Session = Depends(get_session)
) -> bool:
    """Delete conversation message"""
    crud = ConversationCRUD(db)
    success = await crud.delete(id=conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation message does not exist")
    return True


@router_conversation.delete("/session/{session_id}", response_model=int)
async def delete_conversations_by_session_id(
        session_id: str,
        db: Session = Depends(get_session)
) -> int:
    """Delete all conversations in the conversation"""
    crud = ConversationCRUD(db)
    count = await crud.delete_by_session_id(session_id=session_id)
    return count 