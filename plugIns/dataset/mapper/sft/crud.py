from sqlmodel import Session, select
from typing import Optional, List

from .base import SftEntry, SftEntryCreate

class SftEntryCRUD:
    """SFT条目CRUD操作"""

    def __init__(self, db: Session):
        self.db = db

    async def create(self, *, sft_entry: SftEntryCreate) -> SftEntry:
        """创建SFT条目"""
        db_entry = SftEntry(**sft_entry.dict())
        self.db.add(db_entry)
        self.db.commit()
        self.db.refresh(db_entry)
        return db_entry

    async def create_batch(self, *, entries: List[SftEntryCreate]) -> List[SftEntry]:
        """批量创建SFT条目"""
        db_entries = []
        for entry in entries:
            db_entry = SftEntry(**entry.dict())
            self.db.add(db_entry)
            db_entries.append(db_entry)
        
        self.db.commit()
        for entry in db_entries:
            self.db.refresh(entry)
        
        return db_entries

    async def get_by_id(self, *, entry_id: int) -> Optional[SftEntry]:
        """根据ID获取SFT条目"""
        statement = select(SftEntry).where(SftEntry.id == entry_id)
        result = self.db.exec(statement).first()
        return result

    async def get_by_dataset_id(self, *, dataset_id: int, skip: int = 0, limit: int = 100) -> List[SftEntry]:
        """根据数据集ID获取SFT条目"""
        statement = select(SftEntry).where(SftEntry.dataset_id == dataset_id).offset(skip).limit(limit)
        return self.db.exec(statement).all()

    async def delete(self, *, entry_id: int) -> bool:
        """删除SFT条目"""
        db_entry = await self.get_by_id(entry_id=entry_id)
        if not db_entry:
            return False

        self.db.delete(db_entry)
        self.db.commit()
        return True

    async def delete_by_dataset_id(self, *, dataset_id: int) -> bool:
        """根据数据集ID删除所有SFT条目"""
        entries = await self.get_by_dataset_id(dataset_id=dataset_id, limit=1000000)
        if not entries:
            return False

        for entry in entries:
            self.db.delete(entry)
        
        self.db.commit()
        return True 