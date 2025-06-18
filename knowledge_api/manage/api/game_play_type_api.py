from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List

from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.game_play_type.base import GamePlayTypeResponse, GamePlayTypeCreate, GamePlayType, \
    GamePlayTypeUpdate
from knowledge_api.mapper.game_play_type.crud import GamePlayTypeCRUD
from knowledge_api.mapper.game_character_relations.base import GameCharacterRelationUpdate
from knowledge_api.mapper.game_character_relations.crud import GameCharacterRelationCRUD
from knowledge_api.mapper.roles.crud import RoleCRUD

router_game_play_type = APIRouter(prefix="/game_play_types", tags=["Game Type Management"])


@router_game_play_type.post("/", response_model=GamePlayTypeResponse)
async def create_game_play_type(
        game_play_type: GamePlayTypeCreate,
        db: Session = Depends(get_session)
) -> GamePlayType:
    """Create a game type"""
    # 1. Create the game type first
    crud = GamePlayTypeCRUD(db)
    db_game_play_type = await crud.create(obj_in=game_play_type)
    
    # 2. If there is a role association, create a role association
    if game_play_type.role_relations and len(game_play_type.role_relations) > 0:
        # Verify that the role exists
        role_crud = RoleCRUD(db)
        for relation in game_play_type.role_relations:
            role = await role_crud.get_by_id(role_id=relation["role_id"])
            if not role:
                # Roll back game type creation, throw exception
                await crud.delete(game_play_type_id=db_game_play_type.id)
                raise HTTPException(status_code=404, detail=f"角色 {relation['role_id']} 不存在")
        
        # Create role associations
        relation_crud = GameCharacterRelationCRUD(db)
        await relation_crud.bulk_create(game_id=db_game_play_type.id, relations=game_play_type.role_relations)
    
    return db_game_play_type


@router_game_play_type.get("/{game_play_type_id}", response_model=GamePlayTypeResponse)
async def get_game_play_type(
        game_play_type_id: int,
        db: Session = Depends(get_session)
) -> GamePlayType:
    """Get a single game type"""
    crud = GamePlayTypeCRUD(db)
    game_play_type = await crud.get_by_id(id=game_play_type_id)
    if not game_play_type:
        raise HTTPException(status_code=404, detail="The game type does not exist")
    return game_play_type


@router_game_play_type.get("/", response_model=List[GamePlayTypeResponse])
async def list_game_play_types(
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=100),
        db: Session = Depends(get_session)
) -> List[GamePlayType]:
    """Get a list of game types"""
    crud = GamePlayTypeCRUD(db)
    return await crud.get_all(skip=skip, limit=limit)


@router_game_play_type.put("/{game_play_type_id}", response_model=GamePlayTypeResponse)
async def update_game_play_type(
        game_play_type_id: int,
        game_play_type_update: GamePlayTypeUpdate,
        db: Session = Depends(get_session)
) -> GamePlayType:
    """Update game type"""
    crud = GamePlayTypeCRUD(db)
    
    # If there is a role association update
    if game_play_type_update.role_relations and len(game_play_type_update.role_relations) > 0:
        # Verify that the game type exists
        existing_game_play_type = await crud.get_by_id(id=game_play_type_id)
        if not existing_game_play_type:
            raise HTTPException(status_code=404, detail="The game type does not exist")
            
        # Verify that the role exists
        role_crud = RoleCRUD(db)
        for relation in game_play_type_update.role_relations:
            role = await role_crud.get_by_id(role_id=relation["role_id"])
            if not role:
                raise HTTPException(status_code=404, detail=f"角色 {relation['role_id']} 不存在")
        
        # Delete old relationships
        relation_crud = GameCharacterRelationCRUD(db)
        await relation_crud.delete_by_game_id(game_id=game_play_type_id)
        
        # Create a new relationship
        await relation_crud.bulk_create(game_id=game_play_type_id, relations=game_play_type_update.role_relations)
        
        # Remove role_relations field from updated data
        role_relations = game_play_type_update.role_relations
        game_play_type_update_dict = game_play_type_update.dict(exclude={"role_relations"})
        game_play_type_update = GamePlayTypeUpdate(**game_play_type_update_dict)
    
    # Update game type data
    game_play_type = await crud.update(game_play_type_id, game_play_type_update)
    if not game_play_type:
        raise HTTPException(status_code=404, detail="The game type does not exist")
    return game_play_type


@router_game_play_type.delete("/{game_play_type_id}", response_model=bool)
async def delete_game_play_type(
        game_play_type_id: int,
        db: Session = Depends(get_session)
) -> bool:
    """Delete game type"""
    # First, remove the relationship between the game type and the character
    relation_crud = GameCharacterRelationCRUD(db)
    await relation_crud.delete_by_game_id(game_id=game_play_type_id)
    
    # Then delete the game type
    crud = GamePlayTypeCRUD(db)
    success = await crud.delete(id=game_play_type_id)
    if not success:
        raise HTTPException(status_code=404, detail="The game type does not exist")
    return True


@router_game_play_type.get("/get_by_game_type_info/{game_type}", response_model=GamePlayType)
async def get_game_play_type_info(game_type: str,
                                  db: Session = Depends(get_session)):
    """Get game type information through game type code"""
    crud = GamePlayTypeCRUD(db)
    return await crud.get_by_game_play_type(game_play_type=game_type)


@router_game_play_type.get("/{game_play_type_id}/relations", response_model=List[dict])
async def get_game_play_type_relations(
        game_play_type_id: int,
        db: Session = Depends(get_session)
) -> List[dict]:
    """Get character associations for game types"""
    # First check if the game type exists
    game_play_type_crud = GamePlayTypeCRUD(db)
    game_play_type = await game_play_type_crud.get_by_id(id=game_play_type_id)
    if not game_play_type:
        raise HTTPException(status_code=404, detail="The game type does not exist")
    
    # Get character associations for game types
    relation_crud = GameCharacterRelationCRUD(db)
    relations = await relation_crud.get_by_game_id(game_id=game_play_type_id)
    
    # Get role details
    role_crud = RoleCRUD(db)
    result = []
    for relation in relations:
        role = await role_crud.get_by_id(role_id=relation.role_id)
        if role:
            result.append({
                "relation_id": relation.id,
                "game_id": relation.game_id,
                "role_id": relation.role_id,
                "role_name": role.name,
                "image_url": role.image_url if hasattr(role, "image_url") else None,
                "llm_provider": relation.llm_provider,
                "llm_model": relation.llm_model,
                "voice": relation.voice,
                "character_setting": relation.character_setting
            })
    
    return result


@router_game_play_type.put("/relations/{relation_id}", response_model=dict)
async def update_game_play_type_relation(
        relation_id: int,
        relation_update: GameCharacterRelationUpdate,
        db: Session = Depends(get_session)
) -> dict:
    """Update Game Type Character Association"""
    relation_crud = GameCharacterRelationCRUD(db)
    relation = await relation_crud.update(relation_id, relation_update)
    if not relation:
        raise HTTPException(status_code=404, detail="Game character associations do not exist")
    
    # Get role details
    role_crud = RoleCRUD(db)
    role = await role_crud.get_by_id(role_id=relation.role_id)
    if not role:
        raise HTTPException(status_code=404, detail="Character does not exist")
    
    return {
        "relation_id": relation.id,
        "game_id": relation.game_id,
        "role_id": relation.role_id,
        "role_name": role.name,
        "image_url": role.image_url if hasattr(role, "image_url") else None,
        "llm_provider": relation.llm_provider,
        "llm_model": relation.llm_model,
        "voice": relation.voice,
        "character_setting": relation.character_setting
    }
