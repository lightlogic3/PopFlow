from sqlmodel import Session, select
from typing import Optional, List, Dict, Any

from knowledge_api.mapper.base_crud import BaseCRUD
from .base import RolesWorld, RolesWorldCreate, RolesWorldUpdate, RolesWorldResponse


class RolesWorldCRUD(BaseCRUD[RolesWorld, RolesWorldCreate, RolesWorldUpdate, Dict[str, Any], RolesWorldResponse, int]):
    """Role world associated CRUD operation"""

    def __init__(self, db: Session):
        """Initialize the character world associated CRUD operation"""
        super().__init__(db, RolesWorld)

    async def create(self, *, roles_world: RolesWorldCreate = None, obj_in: RolesWorldCreate = None) -> RolesWorld:
        """Create a character world association (override base class method, add uniqueness check)

Check:
1. Is the combination of role ID and worldview knowledge point ID unique?
2. Does the role ID and world ID exist?

Args:
roles_world: Old API mode parameters
obj_in: New API mode parameters"""
        # Use roles_world or obj_in as parameters
        create_data = roles_world if roles_world is not None else obj_in
        
        # Check for uniqueness
        query = select(self.model).where(
            self.model.role_id == create_data.role_id,
            self.model.world_konwledge_id == create_data.world_konwledge_id
        )
        existing = self.db.exec(query).first()
        if existing:
            raise ValueError("The relationship between the character and the worldview knowledge point already exists")
        
        # TODO: If you need to verify the existence of role_id and world_id, you can add logic here
        
        return await super().create(create_data)

    async def update(
            self,
            id: int,
            roles_world_update: RolesWorldUpdate
    ) -> Optional[RolesWorld]:
        """Updated role world associations (override base class method, add uniqueness check)"""
        db_roles_world = await self.get_by_id(id)
        if not db_roles_world:
            return None

        update_data = roles_world_update.dict(exclude_unset=True) if hasattr(roles_world_update, 'dict') else roles_world_update.model_dump(exclude_unset=True)
        
        # If you want to update role_id and world_konwledge_id, you need to check uniqueness
        if "role_id" in update_data or "world_konwledge_id" in update_data:
            role_id = update_data.get("role_id", db_roles_world.role_id)
            world_knowledge_id = update_data.get("world_konwledge_id", db_roles_world.world_konwledge_id)
            
            query = select(self.model).where(
                self.model.role_id == role_id,
                self.model.world_konwledge_id == world_knowledge_id,
                self.model.id != id
            )
            existing = self.db.exec(query).first()
            if existing:
                raise ValueError("The relationship between the character and the worldview knowledge point already exists")
        
        return await super().update(id, roles_world_update)
        
    async def get_by_role_id(self, *, role_id: str, skip: int = 0, limit: int = 100) -> List[RolesWorld]:
        """Get the associated worldview knowledge points according to the role ID"""
        return await self.get_all(filters={"role_id": role_id}, skip=skip, limit=limit)
        
    async def get_by_world_id(self, *, world_id: int, skip: int = 0, limit: int = 100) -> List[RolesWorld]:
        """Get a list of associated roles based on the world ID"""
        return await self.get_all(filters={"world_id": world_id}, skip=skip, limit=limit)
        
    async def get_by_world_knowledge_id(self, *, world_knowledge_id: str, skip: int = 0, limit: int = 100) -> List[RolesWorld]:
        """Get the associated role list based on the Worldview Knowledge Point ID"""
        return await self.get_all(filters={"world_konwledge_id": world_knowledge_id}, skip=skip, limit=limit)
        
    async def delete_by_role_id(self, *, role_id: str) -> bool:
        """Delete associations based on role IDs"""
        statement = select(self.model).where(self.model.role_id == role_id)
        relations = self.db.exec(statement).all()
        if not relations:
            return False
            
        for relation in relations:
            self.db.delete(relation)
        
        self.db.commit()
        return True
        
    async def delete_by_world_id(self, *, world_id: int) -> bool:
        """Delete association based on world ID"""
        statement = select(self.model).where(self.model.world_id == world_id)
        relations = self.db.exec(statement).all()
        if not relations:
            return False
            
        for relation in relations:
            self.db.delete(relation)
        
        self.db.commit()
        return True
        
    async def delete_by_world_knowledge_id(self, *, world_knowledge_id: str) -> bool:
        """Delete associations according to the Worldview Knowledge Point ID"""
        statement = select(self.model).where(self.model.world_konwledge_id == world_knowledge_id)
        relations = self.db.exec(statement).all()
        if not relations:
            return False
            
        for relation in relations:
            self.db.delete(relation)
        
        self.db.commit()
        return True 