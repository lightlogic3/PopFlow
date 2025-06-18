from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List

from knowledge_api.framework.database.database import get_session
from plugIns.dataset.mapper.dpo.base import DpoEntryResponse, DpoEntryCreate
from plugIns.dataset.mapper.dpo.crud import DpoEntryCRUD

router = APIRouter(prefix="/dpo", tags=["DPO数据管理"])

@router.post("/entries", response_model=DpoEntryResponse)
async def create_dpo_entry(
    entry: DpoEntryCreate,
    db: Session = Depends(get_session)
) -> DpoEntryResponse:
    """创建DPO条目"""
    crud = DpoEntryCRUD(db)
    return await crud.create(dpo_entry=entry)


@router.post("/batch", response_model=List[DpoEntryResponse])
async def create_dpo_entries_batch(
    entries: List[DpoEntryCreate],
    db: Session = Depends(get_session)
) -> List[DpoEntryResponse]:
    """批量创建DPO条目"""
    crud = DpoEntryCRUD(db)
    return await crud.create_batch(entries=entries)


@router.get("/entries/{entry_id}", response_model=DpoEntryResponse)
async def get_dpo_entry(
    entry_id: int,
    db: Session = Depends(get_session)
) -> DpoEntryResponse:
    """获取DPO条目"""
    crud = DpoEntryCRUD(db)
    entry = await crud.get_by_id(entry_id=entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="DPO条目不存在")
    return entry


@router.get("/dataset/{dataset_id}", response_model=List[DpoEntryResponse])
async def get_dpo_entries_by_dataset(
    dataset_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_session)
) -> List[DpoEntryResponse]:
    """获取数据集的所有DPO条目"""
    crud = DpoEntryCRUD(db)
    return await crud.get_by_dataset_id(dataset_id=dataset_id, skip=skip, limit=limit)


@router.delete("/entries/{entry_id}", response_model=bool)
async def delete_dpo_entry(
    entry_id: int,
    db: Session = Depends(get_session)
) -> bool:
    """删除DPO条目"""
    crud = DpoEntryCRUD(db)
    success = await crud.delete(entry_id=entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="DPO条目不存在")
    return True 