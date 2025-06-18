"""Game Quest Session CRUD Operation"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json

from sqlmodel import Session, select, func, and_, or_, desc
from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination import Page

from knowledge_api.mapper.base_crud import BaseCRUD
from knowledge_api.mapper.task_game_sessions.base import (
    TaskGameSession,
    TaskGameSessionCreate,
    TaskGameSessionUpdate,
    TaskGameSessionFilter,
    TaskGameSessionStats,
    TaskGameSessionResponse
)
from knowledge_api.utils import generate_id


class TaskGameSessionCRUD(BaseCRUD[TaskGameSession, TaskGameSessionCreate, TaskGameSessionUpdate, TaskGameSessionFilter, TaskGameSessionResponse, str]):
    """Game task session CRUD operation class"""
    
    def __init__(self, db: Session):
        """Initialize CRUD operation

@Param db: database session"""
        super().__init__(db, TaskGameSession)

    async def create(self, *, session: TaskGameSessionCreate = None, obj_in: TaskGameSessionCreate = None) -> TaskGameSession:
        """Create a game session (compatible with older APIs)

@Param session: session creation model (old API)
@Param obj_in: Session Creation Model (New API)
@Return: created session"""
        create_data = session if session is not None else obj_in
        
        # Create a database model and set up all fields
        data = create_data.model_dump() if hasattr(create_data, 'model_dump') else create_data.dict()
        
        # Make sure the ID is generated correctly
        session_id = data.get('id') if hasattr(create_data, 'id') else str(generate_id())
        
        db_session = TaskGameSession(
            id=session_id,
            user_id=create_data.user_id,
            subtask_id=create_data.subtask_id,
            task_id=create_data.task_id,
            status=create_data.status,
            current_score=create_data.current_score,
            current_round=create_data.current_round,
            max_rounds=create_data.max_rounds,
            target_score=create_data.target_score,
            last_message_time=create_data.last_message_time or datetime.now(),
            summary=create_data.summary,
            create_time=datetime.now(),
            update_time=datetime.now()
        )

        # Make sure the metadata field is properly initialized
        if hasattr(create_data, 'metadata') and create_data.metadata is not None:
            db_session.metadata = create_data.metadata

        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        return db_session

    async def get_by_session_id(self, session_id: str) -> Optional[TaskGameSession]:
        """Get session by ID (backward compatible with old method name)

@Param session_id: Session ID
@Return: Session or None"""
        return await self.get_by_id(id=session_id)

    async def get_by_user_id(self, user_id: str, skip: int = 0, limit: int = 100) -> List[TaskGameSession]:
        """Get all sessions of the user

@Param user_id: User ID
@param skip: number of records skipped
@Param limit: limit the number of records
@Return: conversation list"""
        return await self.get_all(filters={"user_id": user_id}, skip=skip, limit=limit, order_by="create_time", order_desc=True)

    async def get_by_subtask_id(self, subtask_id: str, skip: int = 0, limit: int = 100) -> List[TaskGameSession]:
        """Get all sessions related to the subtask

@Param subtask_id: subtask ID
@param skip: number of records skipped
@Param limit: limit the number of records
@Return: conversation list"""
        return await self.get_all(filters={"subtask_id": subtask_id}, skip=skip, limit=limit, order_by="create_time", order_desc=True)

    async def get_active_session_by_user(self, user_id: str) -> Optional[TaskGameSession]:
        """Get the user's currently active session (status is in progress)

@Param user_id: User ID
@Return: Active Session or None"""
        statement = select(self.model).where(
            (self.model.user_id == user_id) & 
            (self.model.status == 0)  # Status 0 indicates in progress
        ).order_by(desc(self.model.create_time))
        result = self.db.exec(statement).first()
        return result

    async def get_by_user_and_subtask(self, user_id: str, subtask_id: str) -> Optional[TaskGameSession]:
        """Get session by user ID and subtask ID

@Param user_id: User ID
@Param subtask_id: subtask ID
@Return: Session or None"""
        filters = {"user_id": user_id, "subtask_id": subtask_id}
        sessions = await self.get_all(filters=filters, limit=1, order_by="create_time", order_desc=True)
        return sessions[0] if sessions else None

    async def update_session_score(self, session_id: str, score_change: int, reason: str = None) -> Optional[TaskGameSession]:
        """Update Session Score

@Param session_id: Session ID
@Param score_change: Score changes
@Param reason: change reason
@Return: Updated session or None"""
        session = await self.get_by_id(id=session_id)
        if not session:
            return None
        
        # Update score
        session.current_score += score_change
        
        # Record score changes to metadata
        if hasattr(session, 'metadata'):
            if session.metadata is None:
                session.metadata = {}
                
            if "score_changes" not in session.metadata:
                session.metadata["score_changes"] = []
                
            session.metadata["score_changes"].append({
                "time": datetime.now().isoformat(),
                "change": score_change,
                "reason": reason,
                "new_score": session.current_score
            })
        
        # Update session
        session.update_time = datetime.now()
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    async def increment_round(self, session_id: str) -> Optional[TaskGameSession]:
        """Incremental session rounds

@Param session_id: Session ID
@Return: Updated session or None"""
        session = await self.get_by_id(id=session_id)
        if not session:
            return None
        
        # update round
        session.current_round += 1
        session.update_time = datetime.now()
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    async def complete_session(self, session_id: str, summary: str = None) -> Optional[TaskGameSession]:
        """Complete the session

@Param session_id: Session ID
@Param summary: session summary
@Return: Updated session or None"""
        session = await self.get_by_id(id=session_id)
        if not session:
            return None
        
        # Update session status to completed
        session.status = 1
        
        # If a summary is provided, update the session summary
        if summary:
            session.summary = summary
            
        session.update_time = datetime.now()
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    async def interrupt_session(self, session_id: str, reason: str = None) -> Optional[TaskGameSession]:
        """interrupt session

@Param session_id: Session ID
@Param reason: interrupt reason
@Return: Updated session or None"""
        session = await self.get_by_id(id=session_id)
        if not session:
            return None
        
        # Update session status to interrupted
        session.status = 2
        
        # Record the cause of the interruption to metadata
        if hasattr(session, 'metadata'):
            if session.metadata is None:
                session.metadata = {}
                
            session.metadata["interrupt_reason"] = reason
            session.metadata["interrupt_time"] = datetime.now().isoformat()
            
        session.update_time = datetime.now()
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    async def check_and_timeout_inactive_sessions(self, timeout_minutes: int = 30) -> int:
        """Check and timeout inactive sessions

@Param timeout_minutes: Inactivity time threshold (minutes)
@Return: Number of sessions that timed out"""
        # Calculate timeout points
        timeout_threshold = datetime.now() - timedelta(minutes=timeout_minutes)
        
        # Gets all sessions whose status is in progress and the last message time is earlier than the timeout threshold
        statement = select(self.model).where(
            (self.model.status == 0) &  # Status 0 indicates in progress
            (self.model.last_message_time < timeout_threshold)
        )
        results = self.db.exec(statement).all()
        
        # timeout session count
        timeout_count = 0
        
        # Update the state of the timeout session
        for session in results:
            session.status = 3  # Status 3 indicates timeout
            
            # Record timeout information to metadata
            if hasattr(session, 'metadata'):
                if session.metadata is None:
                    session.metadata = {}
                    
                session.metadata["timeout_time"] = datetime.now().isoformat()
                session.metadata["inactive_minutes"] = timeout_minutes
                
            session.update_time = datetime.now()
            
            self.db.add(session)
            timeout_count += 1
        
        # commit changes
        if timeout_count > 0:
            self.db.commit()
            
        return timeout_count

    async def filter_sessions(self, filters: TaskGameSessionFilter, skip: int = 0, limit: int = 100) -> List[TaskGameSession]:
        """Filter sessions based on conditions

@Param filters: filter criteria
@param skip: number of records skipped
@Param limit: limit the number of records
@Return: list of filtered sessions"""
        # Build query conditions
        conditions = []
        
        if filters.user_id:
            conditions.append(self.model.user_id == filters.user_id)
            
        if filters.subtask_id:
            conditions.append(self.model.subtask_id == filters.subtask_id)
            
        if filters.task_id:
            conditions.append(self.model.task_id == filters.task_id)
            
        if filters.status is not None:
            # Handling string type status
            if isinstance(filters.status, str):
                # Convert string state to integer
                status_mapping = {
                    "in_progress": 0,
                    "completed": 1,
                    "aborted": 2,
                    "timeout": 3
                }
                if filters.status in status_mapping:
                    conditions.append(self.model.status == status_mapping[filters.status])
                elif filters.status.isdigit():
                    # If the string can be converted to a number, it can be converted directly
                    conditions.append(self.model.status == int(filters.status))
            else:
                conditions.append(self.model.status == filters.status)
            
        if filters.start_date:
            conditions.append(self.model.create_time >= filters.start_date)
            
        if filters.end_date:
            conditions.append(self.model.create_time <= filters.end_date)
            
        if filters.min_score is not None:
            conditions.append(self.model.current_score >= filters.min_score)
            
        if filters.max_score is not None:
            conditions.append(self.model.current_score <= filters.max_score)
        
        # build query
        if conditions:
            statement = select(self.model).where(and_(*conditions))
        else:
            statement = select(self.model)
            
        # Add pagination and sorting
        statement = statement.offset(skip).limit(limit).order_by(desc(self.model.create_time))
        
        # Execute Query
        results = self.db.exec(statement).all()
        return results

    async def filter_sessions_paginated(self, filters: TaskGameSessionFilter) -> Page[TaskGameSessionResponse]:
        """Filter sessions by criteria (paging)

@Param filters: filter criteria
@Return: list of paging sessions"""
        # Build query conditions
        conditions = []
        
        if filters.user_id:
            conditions.append(self.model.user_id == filters.user_id)
            
        if filters.subtask_id:
            conditions.append(self.model.subtask_id == filters.subtask_id)
            
        if filters.task_id:
            conditions.append(self.model.task_id == filters.task_id)
            
        if filters.status is not None:
            # Handling string type status
            if isinstance(filters.status, str):
                # Convert string state to integer
                status_mapping = {
                    "in_progress": 0,
                    "completed": 1,
                    "aborted": 2,
                    "timeout": 3
                }
                if filters.status in status_mapping:
                    conditions.append(self.model.status == status_mapping[filters.status])
                elif filters.status.isdigit():
                    # If the string can be converted to a number, it can be converted directly
                    conditions.append(self.model.status == int(filters.status))
            else:
                conditions.append(self.model.status == filters.status)
            
        if filters.start_date:
            conditions.append(self.model.create_time >= filters.start_date)
            
        if filters.end_date:
            conditions.append(self.model.create_time <= filters.end_date)
            
        if filters.min_score is not None:
            conditions.append(self.model.current_score >= filters.min_score)
            
        if filters.max_score is not None:
            conditions.append(self.model.current_score <= filters.max_score)
        
        # build query
        if conditions:
            statement = select(self.model).where(and_(*conditions))
        else:
            statement = select(self.model)
            
        # Add sort
        statement = statement.order_by(desc(self.model.create_time))
        
        # Execute a paged query
        return paginate(self.db, statement)

    async def get_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> TaskGameSessionStats:
        """Get session statistics

@Param start_date: start date (optional)
@Param end_date: End date (optional)
@Param user_id: User ID (optional)
@Param task_id: Task ID (optional)
@return: statistics"""
        # Build basic query conditions
        conditions = []
        if start_date:
            conditions.append(self.model.create_time >= start_date)
        if end_date:
            conditions.append(self.model.create_time <= end_date)
        if user_id:
            conditions.append(self.model.user_id == user_id)
        if task_id:
            conditions.append(self.model.task_id == task_id)
        
        # Converting a conditional list to a SQLAlchemy conditional expression
        filter_condition = and_(*conditions) if conditions else True
        
        # total session count
        total_query = select(func.count()).where(filter_condition).select_from(self.model)
        total_sessions = self.db.exec(total_query).first() or 0
        
        # Count sessions by state
        completed_query = select(func.count()).where(and_(filter_condition, self.model.status == 1)).select_from(self.model)
        completed_sessions = self.db.exec(completed_query).first() or 0
        
        interrupted_query = select(func.count()).where(and_(filter_condition, self.model.status == 2)).select_from(self.model)
        interrupted_sessions = self.db.exec(interrupted_query).first() or 0
        
        timeout_query = select(func.count()).where(and_(filter_condition, self.model.status == 3)).select_from(self.model)
        timed_out_sessions = self.db.exec(timeout_query).first() or 0
        
        in_progress_query = select(func.count()).where(and_(filter_condition, self.model.status == 0)).select_from(self.model)
        in_progress_sessions = self.db.exec(in_progress_query).first() or 0
        
        # average score
        score_query = select(func.avg(self.model.current_score)).where(filter_condition)
        average_score = self.db.exec(score_query).first() or 0.0
        
        # average round
        rounds_query = select(func.avg(self.model.current_round)).where(filter_condition)
        average_rounds = self.db.exec(rounds_query).first() or 0.0
        
        # Number of sessions grouped by task
        task_query = select(self.model.task_id, func.count()).where(filter_condition).group_by(self.model.task_id)
        task_results = self.db.exec(task_query).all()
        sessions_by_task = {task_id: count for task_id, count in task_results}
        
        # Number of sessions grouped by state
        status_query = select(self.model.status, func.count()).where(filter_condition).group_by(self.model.status)
        status_results = self.db.exec(status_query).all()
        sessions_by_status = {status: count for status, count in status_results}
        
        # Create and return statistics
        return TaskGameSessionStats(
            total_sessions=total_sessions,
            completed_sessions=completed_sessions,
            interrupted_sessions=interrupted_sessions,
            timed_out_sessions=timed_out_sessions,
            in_progress_sessions=in_progress_sessions,
            average_score=float(average_score),
            average_rounds=float(average_rounds),
            sessions_by_task=sessions_by_task,
            sessions_by_status=sessions_by_status
        ) 