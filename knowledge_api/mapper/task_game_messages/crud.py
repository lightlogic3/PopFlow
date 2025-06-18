"""Game mission message CRUD operation"""
from datetime import datetime
from typing import List, Optional, Dict, Any
import json

from sqlmodel import Session, select, func, and_, or_, desc
from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination import Page

from knowledge_api.mapper.base_crud import BaseCRUD
from knowledge_api.mapper.task_game_messages.base import (
    TaskGameMessage,
    TaskGameMessageCreate,
    TaskGameMessageUpdate,
    TaskGameMessageFilter,
    TaskGameMessageStats,
    TaskGameMessageResponse
)
from knowledge_api.utils import generate_id


class TaskGameMessageCRUD(BaseCRUD[TaskGameMessage, TaskGameMessageCreate, TaskGameMessageUpdate, TaskGameMessageFilter, TaskGameMessageResponse, int]):
    """Game mission message CRUD operation class"""
    
    def __init__(self, db: Session):
        """Initialize CRUD operation

@Param db: database session"""
        super().__init__(db, TaskGameMessage)

    async def create(self, *, message: TaskGameMessageCreate = None, obj_in: TaskGameMessageCreate = None) -> TaskGameMessage:
        """Create game messages (compatible with older APIs)

@Param message: message creation model (old API)
@Param obj_in: Message Creation Model (New API)
@Return: created message"""
        create_data = message if message is not None else obj_in

        data = create_data.model_dump() if hasattr(create_data, 'model_dump') else create_data.dict()
        data['id'] = generate_id()
        
        db_message = TaskGameMessage.model_validate(data) if hasattr(TaskGameMessage, 'model_validate') else TaskGameMessage(**data)
        db_message.create_time = datetime.now()

        self.db.add(db_message)
        self.db.commit()
        self.db.refresh(db_message)
        return db_message

    async def get_by_message_id(self, message_id: int) -> Optional[TaskGameMessage]:
        """Get message by ID (backward compatible with old method name)

@Param message_id: Message ID
@Return: Message or None"""
        return await self.get_by_id(id=message_id)

    async def get_by_session_id(self, session_id: str, skip: int = 0, limit: int = 100) -> List[TaskGameMessage]:
        """Get all messages for the session

@Param session_id: Session ID
@param skip: number of records skipped
@Param limit: limit the number of records
@return: message list"""
        return await self.get_all(filters={"session_id": session_id}, skip=skip, limit=limit)

    async def get_by_session_id_paginated(self, session_id: str) -> Page[TaskGameMessageResponse]:
        """Get all messages for the session (pagination)

@Param session_id: Session ID
@Return: list of paged messages"""
        return await self.filter_paginated(filters={"session_id": session_id})

    async def get_by_session_and_round(self, session_id: str, round_num: int) -> List[TaskGameMessage]:
        """Get messages for a specific round of the session

@Param session_id: Session ID
@Param round_num: round number
@return: message list"""
        filters = {"session_id": session_id, "round": round_num}
        return await self.get_all(filters=filters)

    async def get_by_user_id(self, user_id: str, skip: int = 0, limit: int = 100) -> List[TaskGameMessage]:
        """Get all the user's messages

@Param user_id: User ID
@param skip: number of records skipped
@Param limit: limit the number of records
@return: message list"""
        return await self.get_all(filters={"user_id": user_id}, skip=skip, limit=limit)

    async def get_latest_by_session(self, session_id: str, limit: int = 1) -> List[TaskGameMessage]:
        """Get the latest conversation news

@Param session_id: Session ID
@Param limit: limit the number of records
@return: message list"""
        statement = select(self.model).where(
            self.model.session_id == session_id
        ).order_by(desc(self.model.create_time)).limit(limit)
        results = self.db.exec(statement).all()
        return results

    async def delete_by_session_id(self, session_id: str) -> int:
        """Delete all messages from the session

@Param session_id: Session ID
@Return: Number of messages deleted"""
        # Find all messages for the session
        messages = await self.get_by_session_id(session_id=session_id, skip=0, limit=10000)
        
        if not messages:
            return 0
        
        # delete message
        count = 0
        for message in messages:
            self.db.delete(message)
            count += 1
        
        self.db.commit()
        return count
        
    async def filter_messages(self, filters: TaskGameMessageFilter, skip: int = 0, limit: int = 100) -> List[TaskGameMessage]:
        """Filter messages based on conditions

@Param filters: filter criteria
@param skip: number of records skipped
@Param limit: limit the number of records
@return: message list"""
        return await self.filter(filters=filters, skip=skip, limit=limit)

    async def filter_messages_paginated(self, filters: TaskGameMessageFilter) -> Page[TaskGameMessageResponse]:
        """Filter messages by criteria (paging)

@Param filters: filter criteria
@Return: list of paged messages"""
        return await self.filter_paginated(filters=filters)

    async def get_statistics(
        self,
        session_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> TaskGameMessageStats:
        """Get message statistics

@Param session_id: Session ID (optional)
@Param start_date: start date (optional)
@Param end_date: End date (optional)
@return: statistics"""
        # Build basic query conditions
        conditions = []
        if session_id:
            conditions.append(self.model.session_id == session_id)
        if start_date:
            conditions.append(self.model.create_time >= start_date)
        if end_date:
            conditions.append(self.model.create_time <= end_date)
        
        # Converting a conditional list to a SQLAlchemy conditional expression
        filter_condition = and_(*conditions) if conditions else True
        
        # total messages
        total_query = select(func.count()).where(filter_condition).select_from(self.model)
        total_messages = self.db.exec(total_query).first() or 0
        
        # Count messages by role
        role_query = select(self.model.role, func.count()).where(filter_condition).group_by(self.model.role)
        role_results = self.db.exec(role_query).all()
        messages_by_role = {role: count for role, count in role_results}
        
        # Count messages by round
        round_query = select(self.model.round, func.count()).where(filter_condition).group_by(self.model.round)
        round_results = self.db.exec(round_query).all()
        messages_by_round = {round_num: count for round_num, count in round_results}
        
        # change in average score
        score_query = select(func.avg(self.model.score_change)).where(
            and_(filter_condition, self.model.score_change != None)
        )
        average_score_change = self.db.exec(score_query).first() or 0.0
        
        # Total token statistics
        token_query = select(
            func.sum(self.model.input_tokens),
            func.sum(self.model.output_tokens)
        ).where(filter_condition)
        input_tokens, output_tokens = self.db.exec(token_query).first() or (0, 0)
        
        # Create and return statistics
        return TaskGameMessageStats(
            total_messages=total_messages,
            messages_by_role=messages_by_role,
            messages_by_round=messages_by_round,
            average_score_change=float(average_score_change),
            total_input_tokens=input_tokens or 0,
            total_output_tokens=output_tokens or 0
        ) 