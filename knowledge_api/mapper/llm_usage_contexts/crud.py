"""LLM uses database operations that record contextual data"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, and_
from sqlalchemy import desc

from knowledge_api.mapper.base_crud import BaseCRUD
from knowledge_api.mapper.llm_usage_contexts.base import (
    LLMUsageContext,
    LLMUsageContextCreate,
    LLMUsageContextUpdate,
    LLMUsageContextResponse
)


class LLMUsageContextCRUD(BaseCRUD[LLMUsageContext, LLMUsageContextCreate, LLMUsageContextUpdate, Dict[str, Any], LLMUsageContextResponse, int]):
    """LLM uses record context data CRUD operations"""
    
    def __init__(self, db: Session):
        """Initialize LLM using record context data CRUD operations

Args:
DB: database session"""
        super().__init__(db, LLMUsageContext)
    
    # Backwards compatible with primitive API call methods
    async def get_by_id(self, id=None, context_id=None) -> Optional[LLMUsageContext]:
        """Get context record by ID

Args:
ID: record ID
context_id: Record ID (compatible with old API)

Returns:
Optional [LLMUsageContext]: Found Record or None"""
        # Using context_id as Alternative Parameters
        _id = id if id is not None else context_id
        return await super().get_by_id(_id)
    
    async def create_from_messages(
        self, 
        record_id: int,
        messages: List[Dict[str, Any]],
        additional_data: Optional[Dict[str, Any]] = None
    ) -> LLMUsageContext:
        """Create a contextual record from a message list

Args:
record_id: Associated LLM Usage Record ID
Messages: Message List
additional_data: Additional data

Returns:
LLMUsageContext: record created"""
        # Extracting system_prompt and user_prompt
        system_prompt = None
        user_prompt = None
        
        if messages:
            # Find the first system message as system_prompt
            for msg in messages:
                if not isinstance(msg,dict):
                    msg=msg.to_dict()
                if msg.get("role") == "system":
                    system_prompt = msg.get("content")
                    break
            
            # Find the last user message as user_prompt
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    user_prompt = msg.get("content")
                    break
        
        # Create record
        context = LLMUsageContextCreate(
            record_id=record_id,
            messages=messages,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            additional_data=additional_data
        )
        
        return await self.create(context)
    
    async def get_by_record_id(self, record_id: int) -> Optional[LLMUsageContext]:
        """Obtain context records using record ID according to LLM

Args:
record_id: LLM Usage Record ID

Returns:
Optional [LLMUsageContext]: Found Record or None"""
        records = await self.get_all(filters={"record_id": record_id}, limit=1)
        return records[0] if records else None
    
    async def delete_by_record_id(self, record_id: int) -> bool:
        """Delete contextual records using record IDs based on LLM

Args:
record_id: LLM Usage Record ID

Returns:
Bool: successfully deleted"""
        db_context = await self.get_by_record_id(record_id)
        if not db_context:
            return False
        
        return await self.delete(db_context.id) 