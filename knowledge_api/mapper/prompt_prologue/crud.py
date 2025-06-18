from sqlmodel import Session, select
from typing import Optional, List, Dict, Any

from knowledge_api.mapper.base_crud import BaseCRUD
from .base import PromptPrologue, PromptPrologueCreate, PromptPrologueUpdate, PromptPrologueResponse


class PromptPrologueCRUD(BaseCRUD[PromptPrologue, PromptPrologueCreate, PromptPrologueUpdate, Dict[str, Any], PromptPrologueResponse, int]):
    """Cue word opening statement CRUD operation"""

    def __init__(self, db: Session):
        """Initialize prompt word opener CRUD operation"""
        super().__init__(db, PromptPrologue)

    async def create(self, *, prompt_prologue: PromptPrologueCreate = None, obj_in: PromptPrologueCreate = None) -> PromptPrologue:
        """Create a prompt opening statement (compatible with older API calls)

Args:
prompt_prologue: Parameters of the old API way
obj_in: Parameters for the new API approach

Returns:
PromptPrologue: Created prompt word openers"""
        # Use prompt_prologue or obj_in as parameters
        create_data = prompt_prologue if prompt_prologue is not None else obj_in
        return await super().create(create_data)

    async def get_by_prompt_id(self, *, prompt_id: int) -> List[PromptPrologue]:
        """Get the opening statement according to the prompt ID"""
        return await self.get_all(filters={"prompt_id": prompt_id})

    async def delete_by_prompt_id(self, *, prompt_id: int) -> bool:
        """Delete all relevant opening remarks according to the prompt ID"""
        statement = select(self.model).where(self.model.prompt_id == prompt_id)
        results = self.db.exec(statement).all()
        
        if not results:
            return False
        
        for item in results:
            self.db.delete(item)
            
        self.db.commit()
        return True
