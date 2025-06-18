from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Dict

from knowledge_api.framework.database.database import get_session
from plugIns.dataset.mapper.conversations.base import ConversationEntryResponse, ConversationEntryCreate, ConversationBatchCreate
from plugIns.dataset.mapper.conversations.crud import ConversationEntryCRUD

router = APIRouter(prefix="/conversations", tags=["对话数据管理"])

@router.post("/entries", response_model=ConversationEntryResponse)
async def create_conversation_entry(
    entry: ConversationEntryCreate,
    db: Session = Depends(get_session)
) -> ConversationEntryResponse:
    """创建对话条目"""
    crud = ConversationEntryCRUD(db)
    return await crud.create(conversation_entry=entry)


@router.post("/batch", response_model=List[ConversationEntryResponse])
async def create_conversation_batch(
    batch: ConversationBatchCreate,
    db: Session = Depends(get_session)
) -> List[ConversationEntryResponse]:
    """批量创建对话条目"""
    crud = ConversationEntryCRUD(db)
    return await crud.create_batch(batch=batch)


@router.get("/entries/{entry_id}", response_model=ConversationEntryResponse)
async def get_conversation_entry(
    entry_id: int,
    db: Session = Depends(get_session)
) -> ConversationEntryResponse:
    """获取对话条目"""
    crud = ConversationEntryCRUD(db)
    entry = await crud.get_by_id(entry_id=entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="对话条目不存在")
    return entry


@router.get("/conversation/{conversation_id}", response_model=List[ConversationEntryResponse])
async def get_conversation_by_id(
    conversation_id: str,
    db: Session = Depends(get_session)
) -> List[ConversationEntryResponse]:
    """获取完整对话"""
    crud = ConversationEntryCRUD(db)
    entries = await crud.get_by_conversation_id(conversation_id=conversation_id)
    if not entries:
        raise HTTPException(status_code=404, detail="对话不存在")
    return entries


@router.get("/dataset/{dataset_id}/ids", response_model=List[str])
async def get_conversation_ids_by_dataset(
    dataset_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_session)
) -> List[str]:
    """获取数据集中的对话ID列表"""
    crud = ConversationEntryCRUD(db)
    return await crud.get_by_dataset_id(dataset_id=dataset_id, skip=skip, limit=limit)


@router.get("/dataset/{dataset_id}", response_model=Dict[str, List[ConversationEntryResponse]])
async def get_conversations_by_dataset(
    dataset_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_session)
) -> Dict[str, List[ConversationEntryResponse]]:
    """获取数据集中的所有对话"""
    crud = ConversationEntryCRUD(db)
    return await crud.get_conversations_by_dataset_id(dataset_id=dataset_id, skip=skip, limit=limit)


@router.delete("/conversation/{conversation_id}", response_model=bool)
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_session)
) -> bool:
    """删除完整对话"""
    crud = ConversationEntryCRUD(db)
    success = await crud.delete_by_conversation_id(conversation_id=conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="对话不存在")
    return True 