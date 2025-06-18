from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlmodel import Session, select, or_, and_, col
import secrets
import hashlib

from knowledge_api.mapper.base_crud import BaseCRUD
from .base import (
    SystemUser, SystemUserCreate, SystemUserUpdate, SystemUserResponse,
    SystemRole, SystemRoleCreate, SystemRoleUpdate,
    SystemMenu, SystemMenuCreate, SystemMenuUpdate,
    SystemRoleMenu, SystemRoleMenuCreate,
    SystemUserRole, SystemUserRoleCreate
)


class SystemUserCRUD(BaseCRUD[SystemUser, SystemUserCreate, SystemUserUpdate, Dict[str, Any], SystemUserResponse, int]):
    """System user CRUD operation"""

    def __init__(self, db: Session):
        """Initialize system user CRUD operation"""
        super().__init__(db, SystemUser)

    async def create(self, *, obj_in: SystemUserCreate, creator: str = "") -> SystemUser:
        """Create user (override base class method, add creator information)"""
        # Get user creation data
        user_data = obj_in.dict()
        user_data["creator"] = creator
        user_data["updater"] = creator
        
        # Manually hash passwords, consistent with update_password methods
        salt = secrets.token_hex(8)
        hashed = hashlib.sha256(f"{user_data['password']}{salt}".encode()).hexdigest()
        user_data["password"] = f"{hashed}:{salt}"
        
        # Create user
        db_user = SystemUser(**user_data)
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    async def get_by_id(self, *, id: int = None, user_id: int = None) -> Optional[SystemUser]:
        """Get users by ID (override base class method, add logical delete filter)"""
        # Use any of the ID parameters passed in
        actual_id = id if id is not None else user_id
        if actual_id is None:
            return None

        statement = select(self.model).where(
            and_(
                self.model.id == actual_id,
                self.model.deleted == False
            )
        )
        return self.db.exec(statement).first()

    async def get_by_username(self, *, username: str) -> Optional[SystemUser]:
        """Get users by username"""
        statement = select(self.model).where(
            and_(
                self.model.username == username,
                self.model.deleted == False
            )
        )
        return self.db.exec(statement).first()

    async def update(self, *, id: int, obj_in: SystemUserUpdate, updater: str = "") -> Optional[SystemUser]:
        """Update user (override base class method, add updater information)"""
        db_user = await self.get_by_id(id=id)
        if not db_user:
            return None

        update_data = obj_in.dict(exclude_unset=True)
        update_data["updater"] = updater

        for key, value in update_data.items():
            setattr(db_user, key, value)

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    async def update_password(self, *, user_id: int, new_password: str, updater: str = "") -> bool:
        """Update user password"""
        db_user = await self.get_by_id(id=user_id)
        if not db_user:
            return False

        # hashing passwords
        salt = secrets.token_hex(8)
        hashed = hashlib.sha256(f"{new_password}{salt}".encode()).hexdigest()
        db_user.password = f"{hashed}:{salt}"
        db_user.updater = updater
        db_user.update_time = datetime.now()

        self.db.add(db_user)
        self.db.commit()
        return True

    async def update_status(self, *, user_id: int, status: int, updater: str = "") -> bool:
        """Update user status"""
        db_user = await self.get_by_id(id=user_id)
        if not db_user:
            return False

        db_user.status = status
        db_user.updater = updater
        db_user.update_time = datetime.now()

        self.db.add(db_user)
        self.db.commit()
        return True

    async def update_login_time(self, *, user_id: int) -> bool:
        """Update user login time"""
        db_user = await self.get_by_id(id=user_id)
        if not db_user:
            return False

        db_user.login_date = datetime.now()
        self.db.add(db_user)
        self.db.commit()
        return True

    async def delete(self, *, id: int, updater: str = "") -> bool:
        """Delete the user (logical deletion) (override the base class method)"""
        db_user = await self.get_by_id(id=id)
        if not db_user:
            return False

        db_user.deleted = True
        db_user.updater = updater
        db_user.update_time = datetime.now()

        self.db.add(db_user)
        self.db.commit()
        return True

    async def get_all(
            self,
            *,
            skip: int = 0,
            limit: int = 100,
            username: Optional[str] = None,
            nickname: Optional[str] = None,
            mobile: Optional[str] = None,
            status: Optional[int] = None
    ) -> Tuple[List[SystemUser], int]:
        """Get a list of users, support filtering
: return: (user list, total)"""
        # Build basic query
        query = select(self.model).where(self.model.deleted == False)

        # Add filter criteria
        if username:
            query = query.where(self.model.username.like(f"%{username}%"))
        if nickname:
            query = query.where(self.model.nickname.like(f"%{nickname}%"))
        if mobile:
            query = query.where(self.model.mobile.like(f"%{mobile}%"))
        if status is not None:
            query = query.where(self.model.status == status)

        # calculate the total
        total_query = select(col(self.model.id)).select_from(self.model).where(self.model.deleted == False)
        if username:
            total_query = total_query.where(self.model.username.like(f"%{username}%"))
        if nickname:
            total_query = total_query.where(self.model.nickname.like(f"%{nickname}%"))
        if mobile:
            total_query = total_query.where(self.model.mobile.like(f"%{mobile}%"))
        if status is not None:
            total_query = total_query.where(self.model.status == status)

        total = len(self.db.exec(total_query).all())

        # paging query
        query = query.offset(skip).limit(limit).order_by(self.model.create_time.desc())
        users = self.db.exec(query).all()

        return users, total

    async def verify_password(self, *, username: str, password: str) -> Optional[SystemUser]:
        """Verify user password"""
        db_user = await self.get_by_username(username=username)
        if not db_user:
            return None

        # Check user status
        if db_user.status != 0:  # Abnormal state
            return None

        # Parse the stored password
        try:
            stored_hash, salt = db_user.password.split(":")
            input_hash = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
            if input_hash == stored_hash:
                return db_user
        except:
            pass

        return None


class SystemRoleCRUD(BaseCRUD[SystemRole, SystemRoleCreate, SystemRoleUpdate, Dict[str, Any], SystemRole, int]):
    """System Role CRUD Operation"""

    def __init__(self, db: Session):
        """Initialize system role CRUD operation"""
        super().__init__(db, SystemRole)

    async def create(self, *, obj_in: SystemRoleCreate, creator: str = "") -> SystemRole:
        """Create role (override base class method, add creator information)"""
        db_role = SystemRole(
            **obj_in.dict(),
            creator=creator,
            updater=creator
        )
        self.db.add(db_role)
        self.db.commit()
        self.db.refresh(db_role)
        return db_role

    async def get_by_code(self, *, code: str) -> Optional[SystemRole]:
        """Get a role based on the role code"""
        statement = select(self.model).where(
            and_(
                self.model.code == code,
                self.model.deleted == False
            )
        )
        return self.db.exec(statement).first()

    async def update(self, *, id: int, obj_in: SystemRoleUpdate, updater: str = "") -> Optional[SystemRole]:
        """Update roles (override base class methods, add updater information)"""
        db_role = await self.get_by_id(id=id)
        if not db_role:
            return None

        update_data = obj_in.dict(exclude_unset=True)
        update_data["updater"] = updater

        for key, value in update_data.items():
            setattr(db_role, key, value)

        self.db.add(db_role)
        self.db.commit()
        self.db.refresh(db_role)
        return db_role

    async def delete(self, *, id: int, updater: str = "") -> bool:
        """Delete roles (logical deletion) (override base class methods)"""
        db_role = await self.get_by_id(id=id)
        if not db_role:
            return False

        db_role.deleted = True
        db_role.updater = updater
        db_role.update_time = datetime.now()

        self.db.add(db_role)
        self.db.commit()
        return True

    async def get_all(
            self,
            *,
            skip: int = 0,
            limit: int = 100,
            name: Optional[str] = None,
            code: Optional[str] = None,
            status: Optional[int] = None
    ) -> Tuple[List[SystemRole], int]:
        """Get a list of roles, support filtering
: return: (character list, total)"""
        # Build basic query
        query = select(self.model).where(self.model.deleted == False)

        # Add filter criteria
        if name:
            query = query.where(self.model.name.like(f"%{name}%"))
        if code:
            query = query.where(self.model.code.like(f"%{code}%"))
        if status is not None:
            query = query.where(self.model.status == status)

        # calculate the total
        total_query = select(col(self.model.id)).select_from(self.model).where(self.model.deleted == False)
        if name:
            total_query = total_query.where(self.model.name.like(f"%{name}%"))
        if code:
            total_query = total_query.where(self.model.code.like(f"%{code}%"))
        if status is not None:
            total_query = total_query.where(self.model.status == status)

        total = len(self.db.exec(total_query).all())

        # paging query
        query = query.offset(skip).limit(limit).order_by(self.model.create_time)
        roles = self.db.exec(query).all()

        return roles, total

    async def get_roles_by_user_id(self, *, user_id: int) -> List[SystemRole]:
        """Get all the roles of the user"""
        # Use a connection query to get the user's role
        query = select(self.model).join(
            SystemUserRole,
            and_(
                SystemUserRole.role_id == self.model.id,
                SystemUserRole.user_id == user_id
            )
        ).where(self.model.deleted == False)

        roles = self.db.exec(query).all()
        return roles


class SystemMenuCRUD(BaseCRUD[SystemMenu, SystemMenuCreate, SystemMenuUpdate, Dict[str, Any], SystemMenu, int]):
    """System menu CRUD operation"""

    def __init__(self, db: Session):
        """Initialize system menu CRUD operation"""
        super().__init__(db, SystemMenu)

    async def create(self, *, obj_in: SystemMenuCreate, creator: str = "") -> SystemMenu:
        """Create menu (override base class method, add creator information)"""
        db_menu = SystemMenu(
            **obj_in.dict(),
            creator=creator,
            updater=creator
        )
        self.db.add(db_menu)
        self.db.commit()
        self.db.refresh(db_menu)
        return db_menu

    async def update(self, *, id: int, obj_in: SystemMenuUpdate, updater: str = "") -> Optional[SystemMenu]:
        """Update menu (override base class method, add updater information)"""
        db_menu = await self.get_by_id(id=id)
        if not db_menu:
            return None

        update_data = obj_in.dict(exclude_unset=True)
        update_data["updater"] = updater

        # Special handling: visible may be of type bool and needs to be converted to 0/1
        if "visible" in update_data and update_data["visible"] is not None:
            update_data["visible"] = 1 if update_data["visible"] else 0

        for key, value in update_data.items():
            setattr(db_menu, key, value)

        self.db.add(db_menu)
        self.db.commit()
        self.db.refresh(db_menu)
        return db_menu

    async def delete(self, *, id: int, updater: str = "") -> bool:
        """Delete menu (logical delete) (override base class method)"""
        # Check if there is a submenu
        if await self.has_children(menu_id=id):
            raise ValueError("There is a submenu that cannot be deleted.")

        db_menu = await self.get_by_id(id=id)
        if not db_menu:
            return False

        db_menu.deleted = True
        db_menu.updater = updater
        db_menu.update_time = datetime.now()

        self.db.add(db_menu)
        self.db.commit()
        return True

    async def has_children(self, *, menu_id: int) -> bool:
        """Check if the menu has submenus"""
        statement = select(self.model).where(
            and_(
                self.model.parent_id == menu_id,
                self.model.deleted == False
            )
        )
        result = self.db.exec(statement).first()
        return result is not None

    async def get_all(
            self,
            *,
            skip: int = 0,
            limit: int = 100,
            name: Optional[str] = None,
            status: Optional[int] = None
    ) -> Tuple[List[SystemMenu], int]:
        """Get menu list, support filtering
: return: (menu list, total)"""
        # Build basic query
        query = select(self.model).where(self.model.deleted == False)

        # Add filter criteria
        if name:
            query = query.where(self.model.name.like(f"%{name}%"))
        if status is not None:
            query = query.where(self.model.status == status)

        # calculate the total
        total_query = select(col(self.model.id)).select_from(self.model).where(self.model.deleted == False)
        if name:
            total_query = total_query.where(self.model.name.like(f"%{name}%"))
        if status is not None:
            total_query = total_query.where(self.model.status == status)

        total = len(self.db.exec(total_query).all())

        # paging query
        query = query.offset(skip).limit(limit).order_by(self.model.sort)
        menus = self.db.exec(query).all()

        return menus, total

    async def get_menus_by_role_id(self, *, role_id: int) -> List[SystemMenu]:
        """Get the character's menu list"""
        query = select(self.model).join(
            SystemRoleMenu,
            SystemRoleMenu.menu_id == self.model.id
        ).where(
            and_(
                SystemRoleMenu.role_id == role_id,
                self.model.deleted == False,
                self.model.status == 0  # Normal state
            )
        )

        return self.db.exec(query).all()

    async def get_all_menus_tree(self, *, status: Optional[int] = None) -> List[Dict]:
        """Get all menu tree structures"""
        # query condition
        conditions = [self.model.deleted == False]
        if status is not None:
            conditions.append(self.model.status == status)

        # Get all menus
        statement = select(self.model).where(and_(*conditions))
        menus = self.db.exec(statement).all()

        # Build a tree structure
        return self._build_menu_tree(menus)

    async def get_user_menus_tree(self, *, username: str, status: Optional[int] = None) -> List[Dict]:
        """Get the user's menu tree structure

Parameter:
Username: username
Status: Menu status filter

Return:
menu tree structure"""
        # Acquire users
        user_crud = SystemUserCRUD(self.db)
        user = await user_crud.get_by_username(username=username)
        if not user:
            return []

        # Get user role
        role_crud = SystemRoleCRUD(self.db)
        roles = await role_crud.get_roles_by_user_id(user_id=user.id)

        # No role, no permission.
        if not roles:
            return []

        # query condition
        conditions = [self.model.deleted == False]
        if status is not None:
            conditions.append(self.model.status == status)

        # Get a list of role IDs
        role_ids = [role.id for role in roles]

        # Query all menu permissions for users
        statement = select(self.model).join(
            SystemRoleMenu,
            SystemRoleMenu.menu_id == self.model.id
        ).where(
            and_(
                SystemRoleMenu.role_id.in_(role_ids),
                *conditions
            )
        ).distinct()

        menus = self.db.exec(statement).all()

        # Build a tree structure
        return self._build_menu_tree(menus)

    def _build_menu_tree(self, menus: List[SystemMenu], parent_id: int = 0) -> List[Dict]:
        """Build menu tree structure

Parameter:
Menus: menu list
parent_id: Parent Menu ID

Return:
tree-structured menu list"""
        result = []
        for menu in menus:
            if menu.parent_id == parent_id:
                menu_dict = {
                    "id": menu.id,
                    "name": menu.name,
                    "permission": menu.permission,
                    "type": menu.type,
                    "sort": menu.sort,
                    "parent_id": menu.parent_id,
                    "path": menu.path,
                    "icon": menu.icon,
                    "component": menu.component,
                    "component_name": menu.component_name,
                    "status": menu.status,
                    "visible": menu.visible,
                    "keep_alive": menu.keep_alive,
                    "always_show": menu.always_show,
                    "create_time": menu.create_time.isoformat() if menu.create_time else None,
                    "update_time": menu.update_time.isoformat() if menu.update_time else None,
                    "meta": {
                        "title": menu.name,
                        "icon": menu.icon,
                        "noCache": not menu.keep_alive,
                        "hidden": menu.visible != 0
                    },
                    "children": self._build_menu_tree(menus, menu.id)
                }
                result.append(menu_dict)
        return result


class SystemRoleMenuCRUD(
    BaseCRUD[SystemRoleMenu, SystemRoleMenuCreate, SystemRoleMenu, Dict[str, Any], SystemRoleMenu, int]):
    """System Role Menu Associated CRUD Action"""

    def __init__(self, db: Session):
        """Initialize system role menu associated CRUD operation"""
        super().__init__(db, SystemRoleMenu)

    async def create(self, *, obj_in: SystemRoleMenuCreate, creator: str = "") -> SystemRoleMenu:
        """Create role menu associations (override base class method, add creator information)"""
        db_role_menu = SystemRoleMenu(
            **obj_in.dict(),
            creator=creator,
            updater=creator
        )
        self.db.add(db_role_menu)
        self.db.commit()
        self.db.refresh(db_role_menu)
        return db_role_menu

    async def delete_by_role_id(self, *, role_id: int) -> bool:
        """Delete all associated menus by role ID"""
        statement = select(self.model).where(
            and_(
                self.model.role_id == role_id,
                self.model.deleted == False
            )
        )
        results = self.db.exec(statement).all()

        if not results:
            return False

        for result in results:
            result.deleted = True
            result.update_time = datetime.now()
            self.db.add(result)

        self.db.commit()
        return True

    async def delete_role_menu_by_ids(self, *, role_id: int, menu_ids: List[int]) -> bool:
        """Delete associations based on a list of role IDs and menu IDs"""
        statement = select(self.model).where(
            and_(
                self.model.role_id == role_id,
                self.model.menu_id.in_(menu_ids),
                self.model.deleted == False
            )
        )
        results = self.db.exec(statement).all()

        if not results:
            return False

        for result in results:
            result.deleted = True
            result.update_time = datetime.now()
            self.db.add(result)

        self.db.commit()
        return True

    async def update_role_menus(self, *, role_id: int, add_menu_ids: List[int], remove_menu_ids: List[int],
                                operator: str = "") -> bool:
        """Update the role menu (add new menu permissions, remove existing menu permissions)"""
        # Add new menu permissions
        if add_menu_ids:
            for menu_id in add_menu_ids:
                db_role_menu = SystemRoleMenu(
                    role_id=role_id,
                    menu_id=menu_id,
                    creator=operator,
                    updater=operator
                )
                self.db.add(db_role_menu)

        # Delete existing menu permissions
        if remove_menu_ids:
            await self.delete_role_menu_by_ids(role_id=role_id, menu_ids=remove_menu_ids)

        if add_menu_ids or remove_menu_ids:
            self.db.commit()
            return True

        return False

    async def assign_role_menus(self, *, role_id: int, menu_ids: List[int], creator: str = "") -> bool:
        """Assign menu permissions to roles (delete all existing permissions before adding new ones)"""
        # Delete all existing menu permissions for the role
        await self.delete_by_role_id(role_id=role_id)

        # Add new menu permissions
        for menu_id in menu_ids:
            db_role_menu = SystemRoleMenu(
                role_id=role_id,
                menu_id=menu_id,
                creator=creator,
                updater=creator
            )
            self.db.add(db_role_menu)

        self.db.commit()
        return True


class SystemUserRoleCRUD(
    BaseCRUD[SystemUserRole, SystemUserRoleCreate, SystemUserRole, Dict[str, Any], SystemUserRole, int]):
    """System user role association CRUD operation"""

    def __init__(self, db: Session):
        """Initialize the system user role association CRUD operation"""
        super().__init__(db, SystemUserRole)

    async def create(self, *, obj_in: SystemUserRoleCreate, creator: str = "") -> SystemUserRole:
        """Create user role associations (override base class method, add creator information)"""
        db_user_role = SystemUserRole(
            **obj_in.dict(),
            creator=creator,
            updater=creator
        )
        self.db.add(db_user_role)
        self.db.commit()
        self.db.refresh(db_user_role)
        return db_user_role

    async def delete_by_user_id(self, *, user_id: int) -> bool:
        """Delete all role associations by user ID"""
        statement = select(self.model).where(
            and_(
                self.model.user_id == user_id,
                self.model.deleted == False
            )
        )
        results = self.db.exec(statement).all()

        if not results:
            return False

        for result in results:
            result.deleted = True
            result.update_time = datetime.now()
            self.db.add(result)

        self.db.commit()
        return True

    async def assign_user_roles(self, *, user_id: int, role_ids: List[int], creator: str = "") -> bool:
        """Assign roles to users (delete all existing associations before adding new ones)"""
        # Delete all existing roles for users
        await self.delete_by_user_id(user_id=user_id)

        # Add a new role association
        for role_id in role_ids:
            db_user_role = SystemUserRole(
                user_id=user_id,
                role_id=role_id,
                creator=creator,
                updater=creator
            )
            self.db.add(db_user_role)

        self.db.commit()
        return True 