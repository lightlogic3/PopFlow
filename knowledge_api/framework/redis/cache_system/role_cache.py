"""Role Cache Service
Caching operations to handle role data"""
import asyncio
from typing import Dict, Optional

from knowledge_api.framework.redis.cache import RedisCache
from knowledge_api.framework.redis.config import get_redis_config
from knowledge_api.mapper.roles.crud import RoleCRUD
from knowledge_api.mapper.roles.base import Role
from knowledge_api.framework.database.database import get_db_session
from knowledge_api.utils.log_config import get_logger

logger = get_logger()

class RoleCache:
    """Role Cache Service
Manage caching operations for role data"""
    _instance = None

    def __new__(cls):
        """singleton pattern"""
        if cls._instance is None:
            cls._instance = super(RoleCache, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize cache"""
        self.redis_config = get_redis_config()
        self.enabled = True
        
        # Initialize Redis cache
        self.cache = RedisCache(
            prefix=f"{self.redis_config.KEY_PREFIX}role",
            model_class=Role
        )

    def set_enabled(self, enabled: bool):
        """Set cache switch"""
        self.enabled = enabled
    
    async def load_all(self, crud: Optional[RoleCRUD] = None):
        """Load all roles to cache

Args:
Crud: Optional RoleCRUD instance, created automatically if not provided"""
        if not self.enabled:
            return
        
        use_provided_crud = crud is not None
        try:
            # If no crud instance is passed in, create a temporary one
            if not use_provided_crud:
                with get_db_session() as session:
                    crud = RoleCRUD(session)
                    
                    # Acquire all roles
                    db_roles = await crud.get_all(limit=1000)  # Set a large limit to ensure that all roles are captured
                    
                    # Create deep copies to avoid object invalidation after the session ends
                    roles = [Role.model_validate(role.model_dump()) for role in db_roles]
                    
                    # Empty old cache
                    await self.cache.clear_prefix()
                    
                    # Process in batches to avoid creating too many connections at once
                    batch_size = 10
                    for i in range(0, len(roles), batch_size):
                        batch = roles[i:i+batch_size]
                        tasks = []
                        
                        # Create a role ID map
                        role_dict = {role.role_id: role for role in batch}
                        tasks.append(self.cache.set("all_roles", role_dict))
                        
                        # Store each role separately
                        for role in batch:
                            tasks.append(self.cache.set(role.role_id, role))
                            
                        # Perform batch caching
                        await asyncio.gather(*tasks)
                        
                        # Sleep briefly to avoid too many requests
                        await asyncio.sleep(0.05)
                        
                    logger.info(f"已加载 {len(roles)} 个角色到Redis缓存")
            else:
                # Using the provided crud instance
                # Acquire all roles
                db_roles = await crud.get_all(limit=1000)  # Set a large limit to ensure that all roles are captured
                
                # Create deep copies to avoid object invalidation after the session ends
                roles = [Role.model_validate(role.model_dump()) for role in db_roles]
                
                # Empty old cache
                await self.cache.clear_prefix()
                
                # Process in batches to avoid creating too many connections at once
                batch_size = 10
                for i in range(0, len(roles), batch_size):
                    batch = roles[i:i+batch_size]
                    tasks = []
                    
                    # Create a role ID map
                    role_dict = {role.role_id: role for role in batch}
                    tasks.append(self.cache.set("all_roles", role_dict))
                    
                    # Store each role separately
                    for role in batch:
                        tasks.append(self.cache.set(role.role_id, role))
                        
                    # Perform batch caching
                    await asyncio.gather(*tasks)
                    
                    # Sleep briefly to avoid too many requests
                    await asyncio.sleep(0.05)
                    
                logger.info(f"已加载 {len(roles)} 个角色到Redis缓存")
            
        except Exception as e:
            logger.error(f"加载角色缓存出错: {e}")

    async def get_role(self, role_id: str, crud: Optional[RoleCRUD] = None) -> Optional[Role]:
        """Get role information and load from database if not in cache

Args:
role_id: Role ID
Crud: Optional RoleCRUD instance, created automatically if not provided

Returns:
Optional [Role]: Role information, return None if not present"""
        if not self.enabled:
            return None
            
        try:
            # Get it directly from Redis
            role = await self.cache.get(role_id)
            if role:
                return role
                
            # If not, try to get it from all_roles
            all_roles = await self.cache.get("all_roles")
            if all_roles and role_id in all_roles:
                return all_roles.get(role_id)
                
            # If not in the cache, load from the database
            use_provided_crud = crud is not None
            try:
                if not use_provided_crud:
                    with get_db_session() as session:
                        crud = RoleCRUD(session)
                        
                        db_role = await crud.get_by_id(role_id=role_id)
                        
                        if db_role:
                            # Create deep copies to avoid object invalidation after the session ends
                            role = Role.model_validate(db_role.model_dump())
                            
                            # Cache to Redis
                            await self.cache.set(role_id, role)
                            
                            # Update all_roles cache
                            all_roles = await self.cache.get("all_roles") or {}
                            all_roles[role_id] = role
                            await self.cache.set("all_roles", all_roles)
                            
                            logger.info(f"已从数据库加载并缓存角色: {role_id}")
                            return role
                else:
                    # Using the provided crud instance
                    db_role = await crud.get_by_id(role_id=role_id)
                    
                    if db_role:
                        # Create deep copies to avoid object invalidation after the session ends
                        role = Role.model_validate(db_role.model_dump())
                        
                        # Cache to Redis
                        await self.cache.set(role_id, role)
                        
                        # Update all_roles cache
                        all_roles = await self.cache.get("all_roles") or {}
                        all_roles[role_id] = role
                        await self.cache.set("all_roles", all_roles)
                        
                        logger.info(f"已从数据库加载并缓存角色: {role_id}")
                        return role
            except Exception as e:
                logger.error(f"从数据库加载角色出错 (role_id={role_id}): {e}")
                    
            return None
                
        except Exception as e:
            logger.error(f"获取角色信息出错 (role_id={role_id}): {e}")
            return None
            
    async def get_all_roles(self) -> Dict[str, Role]:
        """Get all character information

Returns:
Dict [str, Role]: mapping of role ID to role information"""
        if not self.enabled:
            return {}
            
        try:
            # Get all characters from Redis
            all_roles = await self.cache.get("all_roles")
            if all_roles:
                return all_roles
                
            # If not in the cache, load from the database
            with get_db_session() as session:
                crud = RoleCRUD(session)
                db_roles = await crud.get_all(limit=1000)
                
                # Create deep copies to avoid object invalidation after the session ends
                roles = [Role.model_validate(role.model_dump()) for role in db_roles]
                
                # build map
                role_dict = {role.role_id: role for role in roles}
                
                # Cache to Redis
                await self.cache.set("all_roles", role_dict)
                
                # Cache each role individually
                for role_id, role in role_dict.items():
                    await self.cache.set(role_id, role)
                    
                logger.info(f"已从数据库加载并缓存所有角色")
                return role_dict
                
        except Exception as e:
            logger.error(f"获取所有角色信息出错: {e}")
            return {}

    async def update(self, role: Role) -> bool:
        """Update role cache

Note: This method is not responsible for updating the database, only the Redis cache

Args:
Role: The role to update
Returns:
Bool: whether the operation was successful"""
        if not self.enabled:
            return False
            
        try:
            role_id = role.role_id
            
            # Update role cache
            await self.cache.set(role_id, role)
            
            # Update all_roles cache
            all_roles = await self.cache.get("all_roles")
            if all_roles:
                all_roles[role_id] = role
                await self.cache.set("all_roles", all_roles)
                
            logger.info(f"已更新角色缓存: {role_id}")
            return True
            
        except Exception as e:
            logger.error(f"更新角色缓存出错 (role_id={role.role_id}): {e}")
            return False

    async def delete(self, role_id: str, crud: Optional[RoleCRUD] = None) -> bool:
        """Delete role cache

Args:
role_id: Role ID
Crud: Optional instance of RoleCRUD

Returns:
Bool: whether the operation was successful"""
        if not self.enabled:
            return False
            
        try:
            # Verify that the configuration has been deleted from the database
            if crud:
                db_role = await crud.get_by_id(role_id=role_id)
                if db_role:
                    logger.warning(f"要删除的角色在数据库中仍然存在: {role_id}")
            
            # Delete role cache
            await self.cache.delete(role_id)
            
            # Update all_roles cache
            all_roles = await self.cache.get("all_roles")
            if all_roles and role_id in all_roles:
                del all_roles[role_id]
                await self.cache.set("all_roles", all_roles)
                
            logger.info(f"已删除角色缓存: {role_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除角色缓存出错 (role_id={role_id}): {e}")
            return False 