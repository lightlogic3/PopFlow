"""Game task message API interface"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from fastapi_pagination import Page

from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.task_game_messages.base import (
    TaskGameMessage,
    TaskGameMessageCreate,
    TaskGameMessageUpdate,
    TaskGameMessageResponse,
    TaskGameMessageFilter,
    TaskGameMessageStats
)
from knowledge_api.mapper.task_game_messages.crud import TaskGameMessageCRUD

# Create route
task_game_messages_router = APIRouter(prefix="/task-game-messages", tags=["Game mission message"])

@task_game_messages_router.post("/", response_model=TaskGameMessageResponse)
async def create_message(
    message: TaskGameMessageCreate,
    db: Session = Depends(get_session)
) -> TaskGameMessage:
    """Create a new game message

Args:
Message: Message data
DB: database session

Returns:
TaskGameMessage: created message"""
    crud = TaskGameMessageCRUD(db)
    return await crud.create(message=message)


@task_game_messages_router.get("/{message_id}", response_model=TaskGameMessageResponse)
async def get_message(
    message_id: int,
    db: Session = Depends(get_session)
) -> TaskGameMessage:
    """Get a single message

Args:
message_id: Message ID
DB: database session

Returns:
TaskGameMessage: messages found"""
    crud = TaskGameMessageCRUD(db)
    message = await crud.get_by_id(message_id=message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message does not exist")
    return message


@task_game_messages_router.get("/", response_model=Page[TaskGameMessageResponse])
async def list_messages(
    db: Session = Depends(get_session)
) -> Page[TaskGameMessageResponse]:
    """Get a list of messages (pagination)

Args:
DB: database session

Returns:
Page [TaskGameMessageResponse]: list of paged messages"""
    crud = TaskGameMessageCRUD(db)
    return await crud.get_all_paginated()


@task_game_messages_router.get("/session/{session_id}", response_model=Page[TaskGameMessageResponse])
async def get_messages_by_session(
    session_id: str,
    db: Session = Depends(get_session)
) -> Page[TaskGameMessageResponse]:
    """Get all messages for the session (pagination)

Args:
session_id: Session ID
DB: database session

Returns:
Page [TaskGameMessageResponse]: list of paged messages"""
    crud = TaskGameMessageCRUD(db)
    return await crud.get_by_session_id_paginated(session_id=session_id)


@task_game_messages_router.get("/session/{session_id}/round/{round_num}", response_model=List[TaskGameMessageResponse])
async def get_messages_by_round(
    session_id: str,
    round_num: int,
    db: Session = Depends(get_session)
) -> List[TaskGameMessage]:
    """Get messages for a specific round of the session

Args:
session_id: Session ID
round_num: round number
DB: database session

Returns:
List [TaskGameMessageResponse]: Message list"""
    crud = TaskGameMessageCRUD(db)
    return await crud.get_by_session_and_round(session_id=session_id, round_num=round_num)


@task_game_messages_router.get("/session/{session_id}/latest", response_model=List[TaskGameMessageResponse])
async def get_latest_messages(
    session_id: str,
    limit: int = Query(1, ge=1, le=50),
    db: Session = Depends(get_session)
) -> List[TaskGameMessage]:
    """Get the latest conversation news

Args:
session_id: Session ID
Limit: Limit the number of messages
DB: database session

Returns:
List [TaskGameMessageResponse]: Message list"""
    crud = TaskGameMessageCRUD(db)
    return await crud.get_latest_by_session(session_id=session_id, limit=limit)


@task_game_messages_router.post("/filter", response_model=Page[TaskGameMessageResponse])
async def filter_messages(
    filters: TaskGameMessageFilter,
    db: Session = Depends(get_session)
) -> Page[TaskGameMessageResponse]:
    """Filter messages by criteria (paging)

Args:
Filters: filter criteria
DB: database session

Returns:
Page [TaskGameMessageResponse]: A list of filtered messages"""
    crud = TaskGameMessageCRUD(db)
    return await crud.filter_messages_paginated(filters=filters)


@task_game_messages_router.put("/{message_id}", response_model=TaskGameMessageResponse)
async def update_message(
    message_id: int,
    message_update: TaskGameMessageUpdate,
    db: Session = Depends(get_session)
) -> TaskGameMessage:
    """update message

Args:
message_id: Message ID
message_update: Update Data
DB: database session

Returns:
TaskGameMessage: Updated message"""
    crud = TaskGameMessageCRUD(db)
    updated_message = await crud.update(message_id=message_id, message_update=message_update)
    if not updated_message:
        raise HTTPException(status_code=404, detail="Message does not exist")
    return updated_message


@task_game_messages_router.delete("/{message_id}", response_model=bool)
async def delete_message(
    message_id: int,
    db: Session = Depends(get_session)
) -> bool:
    """delete message

Args:
message_id: Message ID
DB: database session

Returns:
Bool: successfully deleted"""
    crud = TaskGameMessageCRUD(db)
    success = await crud.delete(message_id=message_id)
    if not success:
        raise HTTPException(status_code=404, detail="Message does not exist")
    return True


@task_game_messages_router.delete("/session/{session_id}", response_model=int)
async def delete_session_messages(
    session_id: str,
    db: Session = Depends(get_session)
) -> int:
    """Delete all messages from the session

Args:
session_id: Session ID
DB: database session

Returns:
Int: number of messages deleted"""
    crud = TaskGameMessageCRUD(db)
    return await crud.delete_by_session_id(session_id=session_id)


@task_game_messages_router.get("/statistics/summary", response_model=TaskGameMessageStats)
async def get_statistics(
    session_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_session)
) -> TaskGameMessageStats:
    """Get message statistics

Args:
session_id: Session ID (optional)
start_date: Start Date
end_date: End date
DB: database session

Returns:
TaskGameMessageStats: Statistics"""
    crud = TaskGameMessageCRUD(db)
    return await crud.get_statistics(
        session_id=session_id,
        start_date=start_date,
        end_date=end_date
    ) 