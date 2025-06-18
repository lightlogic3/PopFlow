from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List

from knowledge_api.framework.database.database import get_session
from plugIns.dataset.mapper.sft.base import SftEntryResponse, SftEntryCreate
from plugIns.dataset.mapper.sft.crud import SftEntryCRUD

router = APIRouter(prefix="/sft", tags=["SFT数据管理"])

@router.post("/entries", response_model=SftEntryResponse)
async def create_sft_entry(
    entry: SftEntryCreate,
    db: Session = Depends(get_session)
) -> SftEntryResponse:
    """创建SFT条目"""
    crud = SftEntryCRUD(db)
    return await crud.create(sft_entry=entry)


@router.post("/batch", response_model=List[SftEntryResponse])
async def create_sft_entries_batch(
    entries: List[SftEntryCreate],
    db: Session = Depends(get_session)
) -> List[SftEntryResponse]:
    """批量创建SFT条目"""
    crud = SftEntryCRUD(db)
    return await crud.create_batch(entries=entries)


@router.get("/entries/{entry_id}", response_model=SftEntryResponse)
async def get_sft_entry(
    entry_id: int,
    db: Session = Depends(get_session)
) -> SftEntryResponse:
    """获取SFT条目"""
    crud = SftEntryCRUD(db)
    entry = await crud.get_by_id(entry_id=entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="SFT条目不存在")
    return entry


@router.get("/dataset/{dataset_id}", response_model=List[SftEntryResponse])
async def get_sft_entries_by_dataset(
    dataset_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_session)
) -> List[SftEntryResponse]:
    """获取数据集的所有SFT条目"""
    crud = SftEntryCRUD(db)
    return await crud.get_by_dataset_id(dataset_id=dataset_id, skip=skip, limit=limit)


@router.delete("/entries/{entry_id}", response_model=bool)
async def delete_sft_entry(
    entry_id: int,
    db: Session = Depends(get_session)
) -> bool:
    """删除SFT条目"""
    crud = SftEntryCRUD(db)
    success = await crud.delete(entry_id=entry_id)
    if not success:
        raise HTTPException(status_code=404, detail="SFT条目不存在")
    return True 