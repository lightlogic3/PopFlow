from typing import Any, List, Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlmodel import Session
from fastapi_pagination import Page, Params

from knowledge_api.manage.background.knowledge import world_knowledge_count
from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.roles_world import RolesWorldCRUD, RolesWorldCreate
from knowledge_api.mapper.world_knowledge.base import WorldKnowledgeResponse, WorldKnowledgeCreate, \
    WorldKnowledgeUpdate, WorldKnowledgeBulkCreate, WorldKnowledge
from knowledge_api.mapper.world_knowledge.crud import WorldKnowledgeCRUD

# Import a new RAG manager
from knowledge_api.manage.game_knowledge.services.rag_manager import RAGManager

router_world_knowledge = APIRouter(prefix="/world-knowledge", tags=["Worldview Knowledge Base"])


# Asynchronous dependency function to obtain world services from RAGManager
async def get_world_service(is_init_collection: bool = True):
    rag_manager = RAGManager()
    return await rag_manager.get_service("world", is_init_collection=is_init_collection)


async def create_relations_role(db,knowledge_in,knowledge_id):
    crud = RolesWorldCRUD(db)

    if knowledge_in.relations_role:
        # join an associated role
        for role in knowledge_in.relations_role.split(","):
            await crud.create(roles_world=RolesWorldCreate(
                world_konwledge_id=str(knowledge_id),
                role_id=role,
                world_id=knowledge_in.worlds_id,
            ))
    return crud


@router_world_knowledge.post("/", response_model=WorldKnowledgeResponse)
async def create_world_knowledge(
        knowledge_in: WorldKnowledgeCreate,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_session),
) -> Any:
    """Create worldview knowledge items"""
    crud = WorldKnowledgeCRUD(db)
    data = await crud.create(obj_in=knowledge_in)
    # Create a role binding relationship
    await create_relations_role(db,knowledge_in,data.id)
    world_service=await get_world_service()
    await world_service.add_text(data=knowledge_in.model_dump(exclude_none=True), doc_id=data.id)
    background_tasks.add_task(world_knowledge_count, db, knowledge_in.worlds_id, 1)
    
    # 确保ID是字符串类型
    if hasattr(data, 'id') and not isinstance(data.id, str):
        data.id = str(data.id)
        
    return data


@router_world_knowledge.get("/{knowledge_id}", response_model=WorldKnowledgeResponse)
async def get_world_knowledge(
        knowledge_id: str,
        db: Session = Depends(get_session)
) -> Any:
    """Acquire a single worldview knowledge item"""
    crud = WorldKnowledgeCRUD(db)
    knowledge = await crud.get(knowledge_id=knowledge_id)
    if not knowledge:
        raise HTTPException(status_code=404, detail=f"世界观知识ID {knowledge_id} 不存在")
    
    # 确保ID是字符串类型
    if hasattr(knowledge, 'id') and not isinstance(knowledge.id, str):
        knowledge.id = str(knowledge.id)
        
    return knowledge



@router_world_knowledge.get("/know_ids/{ids}", response_model= List[WorldKnowledge])
async def get_world_knowledge(
        ids: str,
        db: Session = Depends(get_session)
) -> Any:
    """Acquire a single worldview knowledge item"""
    crud = WorldKnowledgeCRUD(db)
    knowledge = await crud.get_by_ids(knowledge_ids=ids.split(","))
    return knowledge

@router_world_knowledge.get("/", response_model=List[WorldKnowledgeResponse])
async def list_world_knowledge(
        keyword: Optional[str] = None,
        worlds_id: Optional[str] = None,
        type_name: Optional[Literal["scene", "world view"]] = None,
        role_id: Optional[str] = None,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=100),
        db: Session = Depends(get_session)
) -> Any:
    """Acquire a list of worldview knowledge"""
    crud = WorldKnowledgeCRUD(db)
    return await crud.search(
        keyword=keyword,
        worlds_id=worlds_id,
        type_name=type_name,
        role_id=role_id,
        skip=skip,
        limit=limit
    )


@router_world_knowledge.get("/world/{worlds_id}", response_model=List[WorldKnowledge])
async def get_knowledge_by_world(
        worlds_id: str,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=100),
        db: Session = Depends(get_session)
) -> Any:
    """Acquire all knowledge items for a given world design"""
    crud = WorldKnowledgeCRUD(db)
    return await crud.get_by_worlds_id(worlds_id=worlds_id, skip=skip, limit=limit)

@router_world_knowledge.get("/world/{worlds_id}/paginated", response_model=Page[WorldKnowledge])
async def get_knowledge_by_world_paginated(
        worlds_id: str,
        params: Params = Depends(),
        db: Session = Depends(get_session)
) -> Any:
    """Acquire all knowledge items for a given world design (paginated version)"""
    crud = WorldKnowledgeCRUD(db)
    return await crud.get_by_worlds_id_paginated(worlds_id=worlds_id, params=params)

@router_world_knowledge.get("/world_ids/{ids}", response_model=List[WorldKnowledgeResponse])
async def get_knowledge_by_world(
        ids: str,
        db: Session = Depends(get_session)
) -> Any:
    """Acquire all knowledge items for a given world design"""
    crud = WorldKnowledgeCRUD(db)
    return await crud.get_by_worlds_ids(worlds_ids=ids.split(","))
@router_world_knowledge.get("/type/{type_name}", response_model=List[WorldKnowledgeResponse])
async def get_knowledge_by_type(
        type_name: Literal["scene", "world view"],
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=100),
        db: Session = Depends(get_session)
) -> Any:
    """Gets all knowledge items of the specified type"""
    crud = WorldKnowledgeCRUD(db)
    return await crud.get_by_type(type_name=type_name, skip=skip, limit=limit)


@router_world_knowledge.get("/role/{role_id}", response_model=List[WorldKnowledgeResponse])
async def get_knowledge_by_role(
        role_id: str,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=100),
        db: Session = Depends(get_session)
) -> Any:
    """Gets the world view knowledge item associated with the specified role"""
    crud = WorldKnowledgeCRUD(db)
    return await crud.get_by_relations_role(role_id=role_id, skip=skip, limit=limit)


@router_world_knowledge.put("/{knowledge_id}", response_model=WorldKnowledgeResponse)
async def update_world_knowledge(
        knowledge_id: str,
        knowledge_in: WorldKnowledgeUpdate,
        db: Session = Depends(get_session)
) -> Any:
    """Update worldview knowledge items"""
    crud = WorldKnowledgeCRUD(db)
    knowledge = await crud.update(knowledge_id=knowledge_id, obj_in=knowledge_in)
    if not knowledge:
        raise HTTPException(status_code=404, detail=f"世界观知识ID {knowledge_id} 不存在")
    crud = RolesWorldCRUD(db)
    # Delete the original first, and then bind the new one.
    await crud.delete_by_world_knowledge_id(world_knowledge_id=str(knowledge_id))
    # Create a role binding relationship
    await create_relations_role(db,knowledge_in,knowledge_id)
    world_service = await get_world_service()
    # Update documents in vector store
    await world_service.update_text(knowledge_in.model_dump(exclude_none=True), doc_id=knowledge_id)
    
    # 确保ID是字符串类型
    if hasattr(knowledge, 'id') and not isinstance(knowledge.id, str):
        knowledge.id = str(knowledge.id)
        
    return knowledge


@router_world_knowledge.post("/bulk", response_model=List[WorldKnowledgeResponse])
async def bulk_create_world_knowledge(
        knowledge_in: WorldKnowledgeBulkCreate,
        db: Session = Depends(get_session),
) -> Any:
    """Batch creation of worldview knowledge items"""
    crud = WorldKnowledgeCRUD(db)
    created_items = await crud.bulk_create(objs_in=knowledge_in.items)

    # Batch Add to Vector Store
    for i, item in enumerate(created_items):
        item_data = knowledge_in.items[i].model_dump(exclude_none=True)
        world_service = await get_world_service()
        await world_service.add_text(data=item_data, doc_id=item.id)
        
        # 确保ID是字符串类型
        if hasattr(item, 'id') and not isinstance(item.id, str):
            item.id = str(item.id)

    return created_items


@router_world_knowledge.delete("/{knowledge_id}", response_model=bool)
async def delete_world_knowledge(
        knowledge_id: str,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_session),
) -> Any:
    """Delete Worldview Knowledge Entry"""
    crud = WorldKnowledgeCRUD(db)
    success, world_id = await crud.delete(knowledge_id=knowledge_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"世界观知识ID {knowledge_id} 不存在")
    crud = RolesWorldCRUD(db)
    # Delete the original first, and then bind the new one.
    await crud.delete_by_world_knowledge_id(world_knowledge_id=str(knowledge_id))
    # Delete the corresponding content in the vector database
    world_service = await get_world_service()
    await world_service.delete_by_ids([str(knowledge_id)])
    background_tasks.add_task(world_knowledge_count, db, world_id, -1)
    return True


@router_world_knowledge.get("/count/world/{worlds_id}", response_model=int)
async def count_knowledge_by_world(
        worlds_id: str,
        db: Session = Depends(get_session)
) -> Any:
    """Count the number of knowledge items for a given world design"""
    crud = WorldKnowledgeCRUD(db)
    return await crud.count_by_worlds_id(worlds_id=worlds_id)
