from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlmodel import Session

from knowledge_api.manage.background.knowledge import role_knowledge_count
from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.role_knowledge.base import RoleKnowledgeResponse, RoleKnowledgeCreate, RoleKnowledgeUpdate, \
    RoleKnowledgeBulkCreate
from knowledge_api.mapper.role_knowledge.crud import RoleKnowledgeCRUD

# Import a new RAG manager
from knowledge_api.manage.game_knowledge.services.rag_manager import RAGManager

router_role_knowledge = APIRouter(prefix="/role-knowledge", tags=["Role Knowledge Base"])


async def get_role_servie():
    rag_manager = RAGManager()
    role_service=await rag_manager.get_service("role", is_init_collection=True)
    return role_service

@router_role_knowledge.post("/", response_model=RoleKnowledgeResponse)
async def create_role_knowledge(
        knowledge_in: RoleKnowledgeCreate,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_session),
) -> Any:
    """Create a character knowledge entry"""
    if knowledge_in.type=="join":
        knowledge_in.role_id="share"
    crud = RoleKnowledgeCRUD(db)
    data = await crud.create(obj_in=knowledge_in)
    background_tasks.add_task(role_knowledge_count, db, data.role_id, 1)
    role_service=await get_role_servie()
    await role_service.add_text(knowledge_in.model_dump(exclude_none=True), doc_id=data.id)
    
    # 确保ID是字符串类型
    if hasattr(data, 'id') and not isinstance(data.id, str):
        data.id = str(data.id)
        
    return data


@router_role_knowledge.get("/{knowledge_id}", response_model=RoleKnowledgeResponse)
async def get_role_knowledge(
        knowledge_id: str,
        db: Session = Depends(get_session)
) -> Any:
    """Get a single role knowledge item"""
    crud = RoleKnowledgeCRUD(db)
    knowledge = await crud.get(knowledge_id=knowledge_id)
    if not knowledge:
        raise HTTPException(status_code=404, detail=f"角色知识ID {knowledge_id} 不存在")
    
    # 确保ID是字符串类型
    if hasattr(knowledge, 'id') and not isinstance(knowledge.id, str):
        knowledge.id = str(knowledge.id)
        
    return knowledge


@router_role_knowledge.get("/", response_model=List[RoleKnowledgeResponse])
async def list_role_knowledge(
        keyword: Optional[str] = None,
        role_id: Optional[str] = None,
        type_name: Optional[str] = None,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=100),
        db: Session = Depends(get_session)
) -> Any:
    """Acquire character knowledge list"""
    crud = RoleKnowledgeCRUD(db)
    return await crud.search(
        keyword=keyword,
        role_id=role_id,
        type_name=type_name,
        skip=skip,
        limit=limit
    )


@router_role_knowledge.get("/role/{role_id}", response_model=List[RoleKnowledgeResponse])
async def get_knowledge_by_role(
        role_id: str,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=100),
        db: Session = Depends(get_session)
) -> Any:
    """Gets all knowledge items for the specified role"""
    crud = RoleKnowledgeCRUD(db)
    return await crud.get_by_role_id(role_id=role_id, skip=skip, limit=limit)


@router_role_knowledge.get("/role/share/{role_id}", response_model=List[RoleKnowledgeResponse])
async def get_knowledge_by_share_join(
        role_id: str,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=100),
        db: Session = Depends(get_session)
) -> Any:
    """Gets all knowledge items for the specified role"""
    crud = RoleKnowledgeCRUD(db)
    return await crud.get_by_role_share_id(role_id=role_id, skip=skip, limit=limit)

@router_role_knowledge.get("/type/{type_name}", response_model=List[RoleKnowledgeResponse])
async def get_knowledge_by_type(
        type_name: str,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=100),
        db: Session = Depends(get_session)
) -> Any:
    """Gets all knowledge items of the specified type"""
    crud = RoleKnowledgeCRUD(db)
    return await crud.get_by_type(type_name=type_name, skip=skip, limit=limit)


@router_role_knowledge.put("/{knowledge_id}", response_model=RoleKnowledgeResponse)
async def update_role_knowledge(
        knowledge_id: str,
        knowledge_in: RoleKnowledgeUpdate,
        db: Session = Depends(get_session),
) -> Any:
    """Update character knowledge items"""
    crud = RoleKnowledgeCRUD(db)
    knowledge = await crud.update(knowledge_id=knowledge_id, obj_in=knowledge_in)
    if not knowledge:
        raise HTTPException(status_code=404, detail=f"角色知识ID {knowledge_id} 不存在")
    role_service=await get_role_servie()
    # Update documents in vector store
    await role_service.update_text(knowledge_in.model_dump(exclude_none=True), doc_id=knowledge_id)

    # 确保ID是字符串类型
    if hasattr(knowledge, 'id') and not isinstance(knowledge.id, str):
        knowledge.id = str(knowledge.id)
        
    return knowledge


@router_role_knowledge.post("/bulk", response_model=List[RoleKnowledgeResponse])
async def bulk_create_role_knowledge(
        knowledge_in: RoleKnowledgeBulkCreate,
        db: Session = Depends(get_session)
) -> Any:
    """Batch creation of character knowledge items"""
    crud = RoleKnowledgeCRUD(db)
    created_items = await crud.bulk_create(objs_in=knowledge_in.items)

    # Batch Add to Vector Store
    for i, item in enumerate(created_items):
        item_data = knowledge_in.items[i].model_dump(exclude_none=True)
        role_service = await get_role_servie()
        await role_service.add_text(item_data, doc_id=item.id)
        
        # 确保ID是字符串类型
        if hasattr(item, 'id') and not isinstance(item.id, str):
            item.id = str(item.id)

    return created_items


@router_role_knowledge.delete("/{knowledge_id}", response_model=bool)
async def delete_role_knowledge(
        knowledge_id: str,
        background_tasks: BackgroundTasks,
        db: Session = Depends(get_session)
) -> Any:
    """Delete character knowledge entry"""
    crud = RoleKnowledgeCRUD(db)
    success,role_id = await crud.delete(knowledge_id=knowledge_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"角色知识ID {knowledge_id} 不存在")
    role_service=await get_role_servie()
    await role_service.delete_by_ids([str(knowledge_id)])
    background_tasks.add_task(role_knowledge_count, db, role_id, -1)
    return True


@router_role_knowledge.get("/count/role/{role_id}", response_model=int)
async def count_knowledge_by_role(
        role_id: str,
        db: Session = Depends(get_session)
) -> Any:
    """Count the number of knowledge items for a given role"""
    crud = RoleKnowledgeCRUD(db)
    return await crud.count_by_role_id(role_id=role_id)
