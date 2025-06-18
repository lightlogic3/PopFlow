# api/chat_models.py
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field


class ChatRole(str, Enum):
    """chat role enumeration"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class MemoryType(str, Enum):
    """memory type enumeration"""
    BUFFER_WINDOW = "buffer_window"  # Window buffer memory
    SUMMARY = "summary"  # Abstract memory
    ENTITY = "entity"  # Entity Memory
    KNOWLEDGE_GRAPH = "knowledge_graph"  # Knowledge Graph Memory


class Message(BaseModel):
    """chat message model"""
    role: ChatRole
    content: str


class ChatHistory(BaseModel):
    """chat history model"""
    messages: List[Message] = []


class ChatInput(BaseModel):
    """chat input model"""
    way: str = Field("half", description="Half-stream output, all, full-stream output")
    message: str = Field(..., description="user message")
    role_id: str = Field(..., description="role unique identifier")
    level: float = Field(..., description="character level")
    user_level: float = Field(..., description="user level")
    session_id: Optional[str] = Field(None, description="Session ID, create a new session for null")
    stream: Optional[bool] = Field(False, description="Whether to use streaming responses")
    top_k: Optional[int] = Field(3, description="Number of similar documents retrieved")
    temperature: Optional[float] = Field(0.7, description="generation temperature")
    template_type: Optional[str] = Field("chat", description="Cue word template type")
    include_sources: Optional[bool] = Field(True, description="Whether to include the source in the response")
    user_id: Optional[str] = Field("test", description="user ID")
    user_name:str=Field(...,description="user name")
    relationship_level:int=Field(1,description="relationship hierarchy")
    # Is long-term memory switched on?
    long_term_memory: Optional[bool] = Field(default=False, description="Is long-term memory switched on?")
    # memory level
    memory_level: Optional[int] = Field(default=6, description="Memory level, 6 is dialogue memory, 7 is memory 0, and 10 is dialogue memory")


class ChatResponse(BaseModel):
    """chat response model"""
    message: str = Field(..., description="Assistant reply")
    session_id: str = Field(..., description="Session ID")
    sources: Optional[List[Dict[str, Any]]] = Field(None, description="source document")
    contexts: Optional[List[str]] = Field(None, description="retrieved context")


class SessionInput(BaseModel):
    """conversation input model"""
    session_id: str = Field(..., description="Session ID")
    memory_type: Optional[MemoryType] = Field(None, description="Memory type")
    system_message: Optional[str] = Field(None, description="System message")


class SessionResponse(BaseModel):
    """conversation response model"""
    session_id: str = Field(..., description="Session ID")
    memory_type: str = Field(..., description="Memory type")
    history: Optional[List[Message]] = Field(None, description="chat history")
    created_at: str = Field(..., description="creation time")
    message_count: int = Field(..., description="number of messages")


class UserInfo(BaseModel):
    role_id: str = Field(..., description="user role ID")
    level: float = Field(..., description="Role Level")
    user_level: float = Field(..., description="user level")
    user_id: str = Field(..., description="user ID")
    user: str = Field(..., description="user name")
    relationship_level: int = Field(..., description="relationship hierarchy")
    # Is long-term memory switched on?
    long_term_memory: Optional[bool] = Field(default=False, description="Is long-term memory switched on?")
    # memory level
    memory_level: Optional[int] = Field(default=6, description="Memory level, 6 is dialogue memory, 7 is memory 0, and 10 is dialogue memory")
