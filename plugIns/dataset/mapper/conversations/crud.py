from sqlmodel import Session, select
from typing import Optional, List, Dict
import uuid

from .base import ConversationEntry, ConversationEntryCreate, ConversationBatchCreate

class ConversationEntryCRUD:
    """对话条目CRUD操作"""

    def __init__(self, db: Session):
        self.db = db

    async def create(self, *, conversation_entry: ConversationEntryCreate) -> ConversationEntry:
        """创建对话条目"""
        db_entry = ConversationEntry(**conversation_entry.dict())
        self.db.add(db_entry)
        self.db.commit()
        self.db.refresh(db_entry)
        return db_entry

    async def create_batch(self, *, batch: ConversationBatchCreate) -> List[ConversationEntry]:
        """批量创建对话条目"""
        conversation_id = batch.conversation_id or str(uuid.uuid4())
        db_entries = []
        
        for i, message in enumerate(batch.messages):
            message_dict = message.dict()
            message_dict["dataset_id"] = batch.dataset_id
            message_dict["conversation_id"] = conversation_id
            message_dict["sequence_order"] = i
            
            db_entry = ConversationEntry(**message_dict)
            self.db.add(db_entry)
            db_entries.append(db_entry)
        
        self.db.commit()
        for entry in db_entries:
            self.db.refresh(entry)
        
        return db_entries

    async def get_by_id(self, *, entry_id: int) -> Optional[ConversationEntry]:
        """根据ID获取对话条目"""
        statement = select(ConversationEntry).where(ConversationEntry.id == entry_id)
        result = self.db.exec(statement).first()
        return result

    async def get_by_conversation_id(self, *, conversation_id: str) -> List[ConversationEntry]:
        """根据对话ID获取所有条目"""
        statement = select(ConversationEntry).where(
            ConversationEntry.conversation_id == conversation_id
        ).order_by(ConversationEntry.sequence_order)
        
        return self.db.exec(statement).all()

    async def get_by_dataset_id(self, *, dataset_id: int, skip: int = 0, limit: int = 100) -> List[str]:
        """根据数据集ID获取对话ID列表"""
        statement = select(ConversationEntry.conversation_id).where(
            ConversationEntry.dataset_id == dataset_id
        ).distinct().offset(skip).limit(limit)
        
        results = self.db.exec(statement).all()
        return results

    async def get_conversations_by_dataset_id(
        self, *, dataset_id: int, skip: int = 0, limit: int = 100
    ) -> Dict[str, List[ConversationEntry]]:
        """根据数据集ID获取对话数据，按conversation_id分组"""
        conversation_ids = await self.get_by_dataset_id(dataset_id=dataset_id, skip=skip, limit=limit)
        
        result = {}
        for conv_id in conversation_ids:
            entries = await self.get_by_conversation_id(conversation_id=conv_id)
            result[conv_id] = entries
        
        return result

    async def delete_by_conversation_id(self, *, conversation_id: str) -> bool:
        """根据对话ID删除所有条目"""
        entries = await self.get_by_conversation_id(conversation_id=conversation_id)
        if not entries:
            return False

        for entry in entries:
            self.db.delete(entry)
        
        self.db.commit()
        return True

    async def delete_by_dataset_id(self, *, dataset_id: int) -> bool:
        """根据数据集ID删除所有对话条目"""
        conversation_ids = await self.get_by_dataset_id(dataset_id=dataset_id, limit=1000000)
        if not conversation_ids:
            return False

        success = True
        for conv_id in conversation_ids:
            result = await self.delete_by_conversation_id(conversation_id=conv_id)
            success = success and result
        
        return success 