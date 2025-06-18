from sqlmodel import Session, select
from typing import Optional, List, Dict, Any
import uuid

from knowledge_api.mapper.base_crud import BaseCRUD, IdType
from .base import Role, RoleCreate, RoleUpdate, RoleResponse
from ...utils import generate_id


class RoleCRUD(BaseCRUD[Role, RoleCreate, RoleUpdate, Dict[str, Any], RoleResponse, str]):
    """Role CRUD operation"""

    def __init__(self, db: Session):
        """Initialize character CRUD operation"""
        super().__init__(db, Role)

    async def create(self, *, role: RoleCreate = None, obj_in: RoleCreate = None) -> Role:
        """Create roles (override base class methods, add UUID generation)

Args:
Role: old API mode parameters
obj_in: New API mode parameters"""
        # Use role or obj_in as parameters
        create_data = role if role is not None else obj_in
        
        db_role = Role(id=str(generate_id()), **create_data.dict() if hasattr(create_data, 'dict') else create_data.model_dump())
        self.db.add(db_role)
        self.db.commit()
        self.db.refresh(db_role)
        return db_role

    async def update(self, role_id: str, role_update: RoleUpdate) -> Optional[Role]:
        """update role"""
        db_role = await self.get_by_id(role_id=role_id)
        if not db_role:
            return None

        for key, value in role_update.dict().items():
            setattr(db_role, key, value)

        self.db.add(db_role)
        self.db.commit()
        self.db.refresh(db_role)
        return db_role
    async def get_by_id(self, *, role_id: str) -> Optional[Role]:
        """Acquire roles based on role_id"""
        statement = select(self.model).where(self.model.role_id == role_id)
        result = self.db.exec(statement).first()
        return result

    async def get_by_main_id(self, *, id: str) -> Optional[Role]:
        """Get role by id"""
        return await super().get_by_id(id)

    async def get_by_ids(self, *, role_ids: List[str]) -> List[Role]:
        """Get roles in batches based on ID list"""
        if not role_ids:
            return []

        statement = select(self.model).where(self.model.role_id.in_(role_ids))
        return self.db.exec(statement).all()

    async def increment_knowledge_count(self, *, role_id: str, count: int) -> Optional[Role]:
        """Increase character knowledge_count count"""
        db_role = await self.get_by_id(role_id=role_id)
        if not db_role:
            return None

        db_role.knowledge_count += count
        
        self.db.add(db_role)
        self.db.commit()
        self.db.refresh(db_role)
        return db_role

    async def delete(self, role_id: IdType) -> bool:
        """delete role"""
        from ..character_prompt_config.crud import CharacterPromptConfigCRUD
        from ..relationship_level.crud import RelationshipLevelCRUD
        from ..role_knowledge.crud import RoleKnowledgeCRUD
        from ..role_tasks import RoleTaskCRUD
        from ..roles_world import RolesWorldCRUD
        from ...manage.game_knowledge import RAGManager
        db_role = await self.get_by_id(role_id=role_id)
        if not db_role:
            return False
        # Delete Role Description
        character_prompt=CharacterPromptConfigCRUD(self.db)
        await character_prompt.delete_by_role_id(role_id=db_role.role_id)

        # Delete role relationships
        relation=RelationshipLevelCRUD(self.db)
        await relation.delete_by_role_id(role_id=db_role.role_id)

        # Delete Knowledge Base
        role_know = RoleKnowledgeCRUD(self.db)
        ids=await role_know.delete_by_role_id(role_id=db_role.role_id)
        rag_manager = RAGManager()
        role_service = await rag_manager.get_service("role", is_init_collection=True)
        await role_service.delete_by_ids(ids)

        # Delete worldview association
        roles_world=RolesWorldCRUD(self.db)
        await roles_world.delete_by_role_id(role_id=db_role.role_id)

        # Delete joint memory

        # Task task main task
        main_task=RoleTaskCRUD(self.db)
        await main_task.delete_by_role_id(role_id=db_role.role_id)

        self.db.delete(db_role)
        self.db.commit()
        return True