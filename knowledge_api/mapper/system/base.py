from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Column, BLOB
from sqlalchemy import Integer, Boolean
from pydantic import validator
import secrets
import hashlib


class BaseModel(SQLModel):
    """Base model with common fields"""
    creator: Optional[str] = Field(default="", description="creator")
    create_time: datetime = Field(default_factory=datetime.now, description="creation time")
    updater: Optional[str] = Field(default="", description="Updater")
    update_time: datetime = Field(
        default_factory=datetime.now,
        sa_column_kwargs={"onupdate": datetime.now},
        description="update time"
    )
    deleted: bool = Field(default=False, description="Whether to delete")


# user model
class SystemUserBase(SQLModel):
    """System User Base Model"""
    username: str = Field(..., max_length=30, description="user account")
    nickname: str = Field(..., max_length=30, description="user nickname")
    remark: Optional[str] = Field(None, max_length=500, description="Remarks")
    email: Optional[str] = Field("", max_length=50, description="user email")
    mobile: Optional[str] = Field("", max_length=11, description="Mobile number")
    sex: Optional[int] = Field(0, description="User gender (0 unknown 1 male 2 female)")
    avatar: Optional[str] = Field("", max_length=512, description="avatar address")
    status: int = Field(0, description="Account Status (0 Normal 1 Deactivated)")


class SystemUser(SystemUserBase, BaseModel, table=True):
    """System User Database Model"""
    __tablename__ = "system_users"

    id: Optional[int] = Field(default=None, primary_key=True)
    password: str = Field(..., max_length=100, description="password")
    login_date: Optional[datetime] = Field(None, description="Last login time")
    
    @validator('password', pre=True)
    def hash_password(cls, v):
        """Hashing before password storage"""
        if len(v) < 60:  # If it's not a hashed password
            salt = secrets.token_hex(8)
            hashed = hashlib.sha256(f"{v}{salt}".encode()).hexdigest()
            return f"{hashed}:{salt}"
        return v


class SystemUserCreate(SystemUserBase):
    """Create a user request model"""
    password: str = Field(..., min_length=6, max_length=20, description="password")


class SystemUserUpdate(SQLModel):
    """Update the user request model"""
    nickname: Optional[str] = Field(None, max_length=30)
    remark: Optional[str] = Field(None, max_length=500)
    email: Optional[str] = Field(None, max_length=50)
    mobile: Optional[str] = Field(None, max_length=11)
    sex: Optional[int] = None
    avatar: Optional[str] = Field(None, max_length=512)
    status: Optional[int] = None


class SystemUserResponse(SystemUserBase):
    """user response model"""
    id: int
    create_time: datetime
    update_time: datetime
    login_date: Optional[datetime]


class UserLoginRequest(SQLModel):
    """user login request model"""
    username: str = Field(..., description="user name")
    password: str = Field(..., description="password")


class UserLoginResponse(SQLModel):
    """user login response model"""
    token: str = Field(..., description="JWT Token")
    user_info: SystemUserResponse = Field(..., description="user information")


# role model
class SystemRoleBase(SQLModel):
    """System Role Foundation Model"""
    name: str = Field(..., max_length=30, description="role name")
    code: str = Field(..., max_length=100, description="Role permission string")
    sort: int = Field(..., description="display order")
    data_scope: int = Field(1, description="Data range (1 All data permissions 2 Custom data permissions)")
    status: int = Field(..., description="Role Status (0 Normal 1 Deactivated)")
    type: int = Field(..., description="character type")
    remark: Optional[str] = Field(None, max_length=500, description="Remarks")


class SystemRole(SystemRoleBase, BaseModel, table=True):
    """System Role Database Model"""
    __tablename__ = "system_role"

    id: Optional[int] = Field(default=None, primary_key=True)


class SystemRoleCreate(SystemRoleBase):
    """Create a role request model"""
    pass


class SystemRoleUpdate(SQLModel):
    """Update the role request model"""
    name: Optional[str] = Field(None, max_length=30)
    code: Optional[str] = Field(None, max_length=100)
    sort: Optional[int] = None
    data_scope: Optional[int] = None
    status: Optional[int] = None
    type: Optional[int] = None
    remark: Optional[str] = Field(None, max_length=500)


class SystemRoleResponse(SystemRoleBase):
    """Role Response Model"""
    id: int
    create_time: datetime
    update_time: datetime


# menu model
class SystemMenuBase(SQLModel):
    """System menu base model"""
    name: str = Field(..., max_length=50, description="Menu name")
    permission: str = Field("", max_length=100, description="permission identifier")
    type: int = Field(..., description="menu type")
    sort: int = Field(0, description="display order")
    parent_id: int = Field(0, description="Parent Menu ID")
    path: Optional[str] = Field("", max_length=200, description="routing address")
    icon: Optional[str] = Field("#", max_length = 100, description =" menu icon ")
    component: Optional[str] = Field(None, max_length=255, description="component path")
    component_name: Optional[str] = Field(None, max_length=255, description="component name")
    status: int = Field(0, description="Menu Status")
    visible: int = Field(0, description="Is it visible?")
    keep_alive: bool = Field(True, description="Whether to cache")
    meta: Optional[str] = Field(None, max_length=500, description="Additional field")
    always_show: bool = Field(True, description="Is it always displayed?")


class SystemMenu(SystemMenuBase, BaseModel, table=True):
    """System menu database model"""
    __tablename__ = "system_menu"

    id: Optional[int] = Field(default=None, primary_key=True)


class SystemMenuCreate(SystemMenuBase):
    """Create a menu request model"""
    pass


class SystemMenuUpdate(SQLModel):
    """Update menu request model"""
    name: Optional[str] = Field(None, max_length=50)
    permission: Optional[str] = Field(None, max_length=100)
    type: Optional[int] = None
    sort: Optional[int] = None
    parent_id: Optional[int] = None
    path: Optional[str] = Field(None, max_length=200)
    icon: Optional[str] = Field(None, max_length=100)
    component: Optional[str] = Field(None, max_length=255)
    component_name: Optional[str] = Field(None, max_length=255)
    status: Optional[int] = None
    visible: Optional[bool] = None
    keep_alive: Optional[bool] = None
    meta: Optional[str] = Field(None, max_length=500)
    always_show: Optional[bool] = None


class SystemMenuResponse(SystemMenuBase):
    """menu response model"""
    id: int
    create_time: datetime
    update_time: datetime


# Role menu association model
class SystemRoleMenuBase(SQLModel):
    """System Role Menu Association Base Model"""
    role_id: int = Field(..., description="Role ID")
    menu_id: int = Field(..., description="Menu ID")


class SystemRoleMenu(SystemRoleMenuBase, BaseModel, table=True):
    """System Role Menu Associated Database Model"""
    __tablename__ = "system_role_menu"

    id: Optional[int] = Field(default=None, primary_key=True)


class SystemRoleMenuCreate(SystemRoleMenuBase):
    """Create a role menu association request model"""
    pass


class SystemRoleMenuUpdate(SQLModel):
    """Update the role menu association request model"""
    role_id: Optional[int] = None
    menu_id: Optional[int] = None


class SystemRoleMenuResponse(SystemRoleMenuBase):
    """Role menu association response model"""
    id: int
    create_time: datetime
    update_time: datetime


# user role association model
class SystemUserRoleBase(SQLModel):
    """System User Role Association Basic Model"""
    user_id: int = Field(..., description="user ID")
    role_id: int = Field(..., description="Role ID")


class SystemUserRole(SystemUserRoleBase, BaseModel, table=True):
    """System User Role Associated Database Model"""
    __tablename__ = "system_user_role"

    id: Optional[int] = Field(default=None, primary_key=True)


class SystemUserRoleCreate(SystemUserRoleBase):
    """Create a user role association request model"""
    pass


class SystemUserRoleUpdate(SQLModel):
    """Update the user role association request model"""
    user_id: Optional[int] = None
    role_id: Optional[int] = None


class SystemUserRoleResponse(SystemUserRoleBase):
    """user role association response model"""
    id: int
    create_time: datetime
    update_time: datetime 