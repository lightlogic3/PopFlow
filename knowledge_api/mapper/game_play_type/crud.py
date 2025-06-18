from sqlmodel import Session, select
from typing import List, Optional, Dict, Any

from knowledge_api.mapper.base_crud import BaseCRUD
from knowledge_api.mapper.game_play_type.base import (
    GamePlayType, 
    GamePlayTypeCreate, 
    GamePlayTypeUpdate,
    GamePlayTypeResponse
)


class GamePlayTypeCRUD(BaseCRUD[GamePlayType, GamePlayTypeCreate, GamePlayTypeUpdate, Dict[str, Any], GamePlayTypeResponse, int]):
    """Game Type CRUD Operation Class

Provide game type creation, read, update, delete and query functions"""
    def __init__(self, db: Session):
        """Initialize game type CRUD operation

Args:
DB: database session"""
        super().__init__(db, GamePlayType)
        
    async def get_by_game_play_type(self, game_play_type: str) -> Optional[GamePlayType]:
        """Get game type by game_play_type

Args:
game_play_type: Business ID corresponding to the code path

Returns:
Optional [GamePlayType]: Game Type Object or None"""
        records = await self.get_all(filters={"game_play_type": game_play_type}, limit=1)
        return records[0] if records else None
        
    async def get_active_types(self) -> List[GamePlayType]:
        """Get all enabled game types

Returns:
List [GamePlayType]: List of game types enabled"""
        return await self.get_all(filters={"status": 1}) 