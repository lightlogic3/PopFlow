from sqlmodel import Session, select
from typing import Optional, List, Dict, Any
import uuid

from knowledge_api.mapper.base_crud import BaseCRUD
from .base import Conversation, ConversationCreate, ConversationUpdate, ConversationResponse

class ConversationCRUD(BaseCRUD[Conversation, ConversationCreate, ConversationUpdate, Dict[str, Any], ConversationResponse, int]):
    """Dialogue CRUD operation"""

    def __init__(self, db: Session):
        """Initialize dialogue CRUD operation"""
        super().__init__(db, Conversation)

    async def create(self, conversation: ConversationCreate) -> Conversation:
        """Create a conversation

Args:
Conversation: Conversation Creation Model

Returns:
Conversations: Conversations created"""
        # Make sure the message ID is unique
        if not conversation.message_id:
            conversation_dict = conversation.dict() if hasattr(conversation, 'dict') else conversation.model_dump()
            conversation_dict["message_id"] = str(uuid.uuid4())
            return await super().create(ConversationCreate(**conversation_dict))
        else:
            return await super().create(conversation)

    async def get_by_message_id(self, message_id: str) -> Optional[Conversation]:
        """Get conversation based on message ID

Args:
message_id: Message ID

Returns:
Optional [Conversation]: Conversation or None"""
        records = await self.get_all(filters={"message_id": message_id}, limit=1)
        return records[0] if records else None

    async def get_by_session_id(self, session_id: str, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """Get chat history based on session ID

Args:
session_id: Session ID
Skip: skip the number of records
Limit: limit the number of records

Returns:
List [Conversation]: Conversation list"""
        return await self.get_all(
            filters={"session_id": session_id},
            skip=skip,
            limit=limit,
            order_by="created_at",
            order_desc=False
        )

    async def get_by_conversation_id(self, conversation_id: str, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """Get chat history based on conversation session ID

Args:
conversation_id: Conversation Session ID
Skip: skip the number of records
Limit: limit the number of records

Returns:
List [Conversation]: Conversation list"""
        return await self.get_all(
            filters={"conversation_id": conversation_id},
            skip=skip,
            limit=limit,
            order_by="created_at",
            order_desc=False
        )

    async def get_conversation_tree(self, message_id: str) -> Dict[str, Any]:
        """Get the conversation tree structure - trace up from the specified message

Args:
message_id: Message ID

Returns:
Dict [str, Any]: dialog tree structure"""
        result = {}
        message = await self.get_by_message_id(message_id=message_id)
        if not message:
            return result

        try:
            result = message.dict()
        except AttributeError:
            # If you are using Pydantic v2
            result = message.model_dump()
            
        if message.parent_message_id:
            parent = await self.get_conversation_tree(message_id=message.parent_message_id)
            if parent:
                result["parent"] = parent
        return result

    async def get_by_user_id(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Conversation]:
        """Get all user conversations

Args:
user_id: User ID
Skip: skip the number of records
Limit: limit the number of records

Returns:
List [Conversation]: Conversation list"""
        return await self.get_all(
            filters={"user_id": user_id},
            skip=skip,
            limit=limit,
            order_by="created_at",
            order_desc=True
        )

    async def delete_by_session_id(self, session_id: str) -> int:
        """Delete all conversations in the conversation

Args:
session_id: Session ID

Returns:
Int: number of records deleted"""
        conversations = await self.get_by_session_id(session_id=session_id, limit=1000000)  # Set a large limit to obtain all records
        count = 0
        for conversation in conversations:
            self.db.delete(conversation)
            count += 1
        self.db.commit()
        return count

    async def get_all_conversations_by_not_syncing(self,user_id:str,role_id:str) -> List[Conversation]:
        """Get all conversations, unsynchronized
Returns:
List [Conversation]: Conversation list"""
        return await self.get_all(
            order_by="created_at",
            order_desc=True,
            filters={
                "user_id": user_id,
                "chat_role_id": role_id,
                "is_sync": 0
            }
        )

    async def update_sync_status(self, conversation_id: list[int]) -> Optional[bool]:
        """Update the synchronization status of the conversation

Args:
conversation_id: Conversation ID
is_sync: Is it synced?

Returns:
Optional [Conversation]: Updated Conversation or None"""
        statement = select(Conversation).where(Conversation.id.in_(conversation_id))
        conversations = await self.db.exec(statement)
        conversations = conversations.all()
        if not conversations:
            return None
        for conversation in conversations:
            conversation.is_sync = 1
            self.db.add(conversation)
        self.db.commit()
        return True