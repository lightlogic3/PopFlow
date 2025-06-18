from sqlmodel import Session, select
from typing import Optional, List, Dict, Any
from datetime import datetime

from knowledge_api.mapper.base_crud import BaseCRUD
from .base import AudioTimbre, AudioTimbreCreate, AudioTimbreUpdate, AudioTimbreResponse


class AudioTimbreCRUD(BaseCRUD[AudioTimbre, AudioTimbreCreate, AudioTimbreUpdate, Dict[str, Any], AudioTimbreResponse, int]):
    """Tone CRUD operation

Inherited from BaseCRUD, the following methods are automatically provided:
- create: create timbre
- get_by_id: Get sound by ID
- get_all: Get all sounds
- update: update tone
- delete: delete timbre
- filter: filter sounds according to conditions
- filter_paginated: Paging Filter Tones
- count: get total number of sounds"""

    def __init__(self, db: Session):
        """Initialize tone CRUD operation"""
        super().__init__(db, AudioTimbre)

    async def get_by_speaker_id(self, speaker_id: str) -> Optional[AudioTimbre]:
        """Get timbre according to sound ID

Args:
speaker_id: Sound ID

Returns:
Optional [AudioTimbre]: Found timbre or None"""
        records = await self.get_all(filters={"speaker_id": speaker_id}, limit=1)
        return records[0] if records else None
    
    async def get_by_state(self, state: str, skip: int = 0, limit: int = 100) -> List[AudioTimbre]:
        """Get a list of sounds by status

Args:
State: status value
Skip: skip the number of records
Limit: limit the number of records

Returns:
List [AudioTimbre]: list of sounds"""
        # Use get_all methods of the base class and apply filter conditions
        return await self.get_all(filters={"state": state}, skip=skip, limit=limit) 