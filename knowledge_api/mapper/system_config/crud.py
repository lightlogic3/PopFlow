import json

from sqlmodel import Session, select, or_
from typing import Optional, List, Dict, Any

from knowledge_api.mapper.base_crud import BaseCRUD
from .base import SystemConfig, SystemConfigCreate, SystemConfigUpdate, SystemConfigResponse


class SystemConfigCRUD(BaseCRUD[SystemConfig, SystemConfigCreate, SystemConfigUpdate, Dict[str, Any], SystemConfigResponse, int]):
    """System configuration CRUD operation"""

    def __init__(self, db: Session):
        """Initialize system configuration CRUD operation"""
        super().__init__(db, SystemConfig)

    async def get_by_key(self, *, config_key: str) -> Optional[SystemConfig]:
        """Get the configuration through the configuration key"""
        statement = select(self.model).where(self.model.config_key == config_key)
        result = self.db.exec(statement).first()
        return result

    async def get_multiple_by_keys(self, *, config_keys: List[str]) -> List[SystemConfig]:
        """Get configuration list by multiple configuration keys"""
        statement = select(self.model).where(self.model.config_key.in_(config_keys))
        results = self.db.exec(statement).all()
        return results

    async def search(self, *,
                     keyword: Optional[str] = None,
                     skip: int = 0,
                     limit: int = 100) -> List[SystemConfig]:
        """search configuration"""
        query = select(self.model)

        # Add search criteria
        if keyword:
            query = query.where(
                or_(
                    self.model.config_key.contains(keyword),
                    self.model.description.contains(keyword),
                    self.model.config_value.contains(keyword)
                )
            )

        # paging
        query = query.offset(skip).limit(limit)

        # Execute Query
        results = self.db.exec(query)
        return results.all()

    async def update(
            self,
            id: int,
            obj_in: SystemConfigUpdate
    ) -> Optional[SystemConfig]:
        """Update system configuration (override base class methods, add special handling)"""
        db_obj = await self.get_by_id(id=id)
        if not db_obj:
            return None

        if hasattr(obj_in, 'item_type'):
            # Ak, sk, the input content is empty, backfill
            if obj_in.item_type == 'json_object' and db_obj.item_type == "json_object":
                try:
                    data = json.loads(obj_in.config_value)
                    data_db = json.loads(db_obj.config_value)
                    for key, value in data.items():
                        if key in ["ak", "sk"] and not data[key]:
                            data[key] = data_db.get(key)
                        if "token" in key and not data[key]:
                            data[key] = data_db.get(key)
                    obj_in.config_value = json.dumps(data)
                except:
                    pass
        
        update_data = obj_in.model_dump() if hasattr(obj_in, 'model_dump') else obj_in.dict(exclude_unset=True)
        for key, value in update_data.items():
            # Skip null values and do not update the database
            if value is None or (isinstance(value, str) and value.strip() == ""):
                continue
            setattr(db_obj, key, value)

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    async def update_by_key(
            self,
            config_key: str,
            obj_in: SystemConfigUpdate
    ) -> Optional[SystemConfig]:
        """Update system configuration via configuration key"""
        db_obj = await self.get_by_key(config_key=config_key)
        if not db_obj:
            return None

        update_data = obj_in.model_dump() if hasattr(obj_in, 'model_dump') else obj_in.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_obj, key, value)

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    async def create_or_update(self, *, obj_in: SystemConfigCreate) -> SystemConfig:
        """Create or update configuration (based on key name)"""
        # Find an existing configuration
        existing = await self.get_by_key(config_key=obj_in.config_key)

        if existing:
            # If it exists, update it
            update_data = SystemConfigUpdate(**obj_in.dict())
            return await self.update(id=existing.id, obj_in=update_data)
        else:
            # If it doesn't exist, create it
            return await super().create(obj_in=obj_in)

    async def bulk_create_or_update(self, *, objs_in: List[SystemConfigCreate]) -> List[SystemConfig]:
        """Batch creation or update of configurations"""
        results = []

        for obj_in in objs_in:
            result = await self.create_or_update(obj_in=obj_in)
            results.append(result)

        return results

    async def delete_by_key(self, *, config_key: str) -> bool:
        """Delete configuration via configuration key"""
        db_obj = await self.get_by_key(config_key=config_key)
        if not db_obj:
            return False

        self.db.delete(db_obj)
        self.db.commit()
        return True

    async def get_all_as_dict(self) -> Dict[str, Any]:
        """Get all configurations as a dictionary (key-value pairs)"""
        configs = await self.get_all()
        return {config.config_key: config.config_value for config in configs}
