from sqlmodel import Session, select
from typing import List, Optional, Dict, Any

from knowledge_api.mapper.base_crud import BaseCRUD
from knowledge_api.mapper.game_character_relations.base import (
    GameCharacterRelation, 
    GameCharacterRelationCreate, 
    GameCharacterRelationUpdate,
    GameCharacterRelationResponse
)


class GameCharacterRelationCRUD(BaseCRUD[GameCharacterRelation, GameCharacterRelationCreate, GameCharacterRelationUpdate, Dict[str, Any], GameCharacterRelationResponse, int]):
    """Game character association CRUD operation class"""
    def __init__(self, db: Session):
        """Initialize the game character association CRUD operation

Args:
DB: database session"""
        super().__init__(db, GameCharacterRelation)

    async def bulk_create(self, game_id: int, relations: List[dict]) -> List[GameCharacterRelation]:
        """Batch creation of game character associations

Args:
game_id: Game ID
Relations: Role association list, each element contains role_id, optional llm_provider, llm_model, voice, character_setting

Returns:
List [GameCharacterRelation]: A list of game character associations created"""
        created_relations = []
        for relation in relations:
            db_relation = GameCharacterRelation(
                game_id=game_id,
                role_id=relation["role_id"],
                llm_provider=relation.get("llm_provider"),
                llm_model=relation.get("llm_model"),
                voice=relation.get("voice"),
                character_setting=relation.get("character_setting")
            )
            self.db.add(db_relation)
            created_relations.append(db_relation)
        
        self.db.commit()
        for relation in created_relations:
            self.db.refresh(relation)
        
        return created_relations

    async def get_by_game_id(self, game_id: int) -> List[GameCharacterRelation]:
        """Get all character associations by game ID

Args:
game_id: Game ID

Returns:
List [GameCharacterRelation]: Game character association list"""
        return await self.get_all(filters={"game_id": game_id})

    async def get_by_role_id(self, role_id: str) -> List[GameCharacterRelation]:
        """Get all game associations by character ID

Args:
role_id: Role ID

Returns:
List [GameCharacterRelation]: Game character association list"""
        return await self.get_all(filters={"role_id": role_id})
    
    async def get_by_game_and_role(self, game_id: int, role_id: str) -> Optional[GameCharacterRelation]:
        """Get associations through game ID and character ID

Args:
game_id: Game ID
role_id: Role ID

Returns:
Optional [GameCharacterRelation]: Game character association or None"""
        records = await self.get_all(filters={"game_id": game_id, "role_id": role_id}, limit=1)
        return records[0] if records else None

    async def get_by_llm_provider(self, llm_provider: str) -> List[GameCharacterRelation]:
        """Get all connections through large model providers

Args:
llm_provider: Large Model Provider

Returns:
List [GameCharacterRelation]: Game character association list"""
        return await self.get_all(filters={"llm_provider": llm_provider})

    async def get_by_llm_model(self, llm_model: str) -> List[GameCharacterRelation]:
        """Get all the connections through the large model

Args:
llm_model: Large Model

Returns:
List [GameCharacterRelation]: Game character association list"""
        return await self.get_all(filters={"llm_model": llm_model})

    async def delete_by_game_id(self, game_id: int) -> bool:
        """Delete all character associations by game ID

Args:
game_id: Game ID

Returns:
Bool: successfully deleted"""
        relations = await self.get_by_game_id(game_id)
        if not relations:
            return False
            
        for relation in relations:
            self.db.delete(relation)
        
        self.db.commit()
        return True

    async def delete_by_role_id(self, role_id: str) -> bool:
        """Delete all game associations by character ID

Args:
role_id: Role ID

Returns:
Bool: successfully deleted"""
        relations = await self.get_by_role_id(role_id)
        if not relations:
            return False
            
        for relation in relations:
            self.db.delete(relation)
        
        self.db.commit()
        return True 