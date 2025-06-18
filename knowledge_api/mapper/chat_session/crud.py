from sqlmodel import Session, select
from typing import Optional, List, Dict, Any
import uuid

from knowledge_api.mapper.base_crud import BaseCRUD
from .base import Session as ChatSession, SessionCreate, SessionUpdate, SessionResponse

class SessionCRUD(BaseCRUD[ChatSession, SessionCreate, SessionUpdate, Dict[str, Any], SessionResponse, str]):
    """Session CRUD operation"""

    def __init__(self, db: Session):
        """Initialize session CRUD operation"""
        super().__init__(db, ChatSession)

    async def get_by_id(self, id: str) -> Optional[ChatSession]:
        """Get session by ID

Args:
ID: Session ID

Returns:
Optional [ChatSession]: Found Session or None"""
        statement = select(self.model).where(self.model.session_id == id)
        result = self.db.exec(statement).first()
        return result

    async def create(self, session: SessionCreate) -> ChatSession:
        """Create a session, add a session ID

Args:
Session: session creation model

Returns:
ChatSession: Created session"""
        # Use UUID as session ID
        return await super().create(session, session_id=str(uuid.uuid4()))

    async def get_by_user_id(self, user_id: str, skip: int = 0, limit: int = 100) -> List[ChatSession]:
        """Get all sessions of the user

Args:
user_id: User ID
Skip: skip the number of records
Limit: limit the number of records

Returns:
List [ChatSession]: List of sessions"""
        return await self.get_all(
            filters={"user_id": user_id},
            skip=skip,
            limit=limit,
            order_by="last_message_time",
            order_desc=True
        )

    async def get_all(self, 
                     skip: int = 0, 
                     limit: int = 100,
                     filters: Optional[Dict[str, Any]] = None,
                     order_by: Optional[str] = None,
                     order_desc: bool = True,
                     user_id: str = None) -> List[ChatSession]:
        """Get all sessions

Args:
Skip: skip the number of records
Limit: limit the number of records
Filters: filter conditions, such as {"field": value}
order_by: Sort Fields
order_desc: Whether to sort in descending order
user_id: User ID filter (for backward compatibility)

Returns:
List [ChatSession]: List of sessions"""
        # Handling user_id parameters (for backward compatibility)
        actual_filters = filters or {}
        if user_id:
            actual_filters["user_id"] = user_id
            
        # If no sort field is specified, the default sort is by last message time
        actual_order_by = order_by or "last_message_time"
            
        return await super().get_all(
            filters=actual_filters,
            skip=skip,
            limit=limit,
            order_by=actual_order_by,
            order_desc=order_desc
        )

    async def delete(self, session_id: str) -> bool:
        """Delete session (soft delete, set state to deleted)

Args:
session_id: Session ID

Returns:
Bool: successfully deleted"""
        db_session = await self.get_by_id(session_id)
        if not db_session:
            return False

        db_session.session_status = "deleted"
        self.db.add(db_session)
        self.db.commit()
        return True

    async def permanently_delete(self, session_id: str) -> bool:
        """Permanently delete a session

Args:
session_id: Session ID

Returns:
Bool: successfully deleted"""
        return await super().delete(session_id) 