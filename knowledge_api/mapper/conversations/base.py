from datetime import datetime
from typing import Optional, Literal
from sqlmodel import SQLModel, Field, JSON


class ConversationBase(SQLModel):
    """dialogue base model"""
    user_id: str = Field(..., max_length=64, description="User ID or identifier")
    session_id: Optional[str] = Field(None, max_length=64, description="Session ID")
    chat_role_id: Optional[str] = Field(None, max_length=255, description="Dialogue Role _id")
    conversation_id: str = Field(..., max_length=64, description="Conversation ID, associated with multiple rounds of the same conversation")
    message_id: str = Field(..., max_length=64, description="Message ID, a unique identifier for each message")
    parent_message_id: Optional[str] = Field(None, max_length=64, description="Parent message ID, used to represent the dialog tree structure")
    role: str = Field(..., description="Message roles: user, assistant")
    content: str = Field(..., description="message content")
    prompt_tokens: Optional[int] = Field(None, description="Number of token for prompt word")
    completion_tokens: Optional[int] = Field(None, description="Number of tokens replied")
    total_tokens: Optional[int] = Field(None, description="Total number of tokens")
    model_name: Optional[str] = Field(None, max_length=64, description="Model name used")
    is_sync: Optional[int] = Field(0, description="Whether it has been synchronized to the vector database, 0 means not synchronized, 1 means synchronized" )


class Conversation(ConversationBase, table=True):
    """dialog database model"""
    __tablename__ = "llm_conversations"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now, description="creation time")


class ConversationCreate(ConversationBase):
    """Create a conversation request model"""
    pass


class ConversationUpdate(SQLModel):
    """Update the conversation request model"""
    content: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class ConversationResponse(ConversationBase):
    """conversation response model"""
    id: int
    created_at: datetime 