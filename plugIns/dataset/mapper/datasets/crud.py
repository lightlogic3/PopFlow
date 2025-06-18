from sqlmodel import Session, select
from typing import Optional, List

from .base import Dataset, DatasetCreate, DatasetUpdate

class DatasetCRUD:
    """数据集CRUD操作"""

    def __init__(self, db: Session):
        self.db = db

    async def create(self, *, dataset: DatasetCreate) -> Dataset:
        """创建数据集"""
        db_dataset = Dataset(**dataset.dict())
        self.db.add(db_dataset)
        self.db.commit()
        self.db.refresh(db_dataset)
        return db_dataset

    async def get_by_id(self, *, dataset_id: int) -> Optional[Dataset]:
        """根据ID获取数据集"""
        statement = select(Dataset).where(Dataset.id == dataset_id)
        result = self.db.exec(statement).first()
        return result

    async def get_by_type(self, *, dataset_type: str, skip: int = 0, limit: int = 100) -> List[Dataset]:
        """根据类型获取数据集"""
        statement = select(Dataset).where(Dataset.type == dataset_type).offset(skip).limit(limit)
        return self.db.exec(statement).all()

    async def get_by_tags(self, *, tags: List[str], skip: int = 0, limit: int = 100) -> List[Dataset]:
        """根据标签查询数据集"""
        query = select(Dataset)
        for tag in tags:
            query = query.where(Dataset.tags.like(f"%{tag}%"))
        query = query.offset(skip).limit(limit)
        return self.db.exec(query).all()

    async def get_all(self, *, skip: int = 0, limit: int = 100) -> List[Dataset]:
        """获取所有数据集"""
        query = select(Dataset).order_by(Dataset.created_at.desc()).offset(skip).limit(limit)
        return self.db.exec(query).all()

    async def update(
        self,
        dataset_id: int,
        dataset_update: DatasetUpdate
    ) -> Optional[Dataset]:
        """更新数据集"""
        db_dataset = await self.get_by_id(dataset_id=dataset_id)
        if not db_dataset:
            return None

        update_data = dataset_update.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_dataset, key, value)

        self.db.add(db_dataset)
        self.db.commit()
        self.db.refresh(db_dataset)
        return db_dataset

    async def delete(self, *, dataset_id: int) -> bool:
        """删除数据集"""
        db_dataset = await self.get_by_id(dataset_id=dataset_id)
        if not db_dataset:
            return False

        self.db.delete(db_dataset)
        self.db.commit()
        return True 