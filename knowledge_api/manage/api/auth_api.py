from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session
from typing import List, Dict, Any
from datetime import datetime

from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.system.base import (
    UserLoginRequest, UserLoginResponse, SystemUserResponse, SystemUserCreate
)
from knowledge_api.mapper.system.crud import (
    SystemUserCRUD, SystemRoleCRUD, SystemMenuCRUD
)
from knowledge_api.mapper.point_record.base import PointRecordCreate, PointChangeType
from knowledge_api.mapper.point_record.crud import PointRecordCRUD
from knowledge_api.mapper.user_detail.base import UserDetailCreate
from knowledge_api.mapper.user_detail.crud import UserDetailCRUD
from knowledge_api.framework.auth.jwt_utils import JWTUtils
from knowledge_api.framework.auth.auth_decorator import skip_auth, get_current_user

router_auth = APIRouter(prefix="/auth", tags=["certification"])

@router_auth.post("/register", response_model=UserLoginResponse)
@skip_auth()
async def register(
    user_create: SystemUserCreate,
    db: Session = Depends(get_session)
):
    """user registration"""
    # Create user
    user_crud = SystemUserCRUD(db)
    
    # Check if the username already exists
    existing_user = await user_crud.get_by_username(username=user_create.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Create a user (the validator of the SystemUser model automatically hashes the password)
    new_user = await user_crud.create(obj_in=user_create)
    
    # Assign a default role (usually a normal user role)
    role_crud = SystemRoleCRUD(db)
    default_role = await role_crud.get_by_code(code="user")  # Suppose there is a normal user role with code "user"
    if default_role:
        await role_crud.assign_role_to_user(user_id=new_user.id, role_id=default_role.id)
    
    # Create user details
    user_detail_crud = UserDetailCRUD(db)
    user_detail = UserDetailCreate(
        user_id=new_user.id,
        total_points=100,  # Initial gift of 100 points
        available_points=100,
        consumed_points=0,
        login_count=1,  # Registration counts as one login
        challenge_count=0,
        challenge_success_count=0,
        card_count=0,
        blind_box_opened_count=0,
        last_active_time=datetime.now(),
    )
    await user_detail_crud.create(obj_in=user_detail)
    
    # Add points record
    point_record_crud = PointRecordCRUD(db)
    point_record = PointRecordCreate(
        user_id=new_user.id,
        change_amount=100,  # Give away 100 points
        current_amount=100,
        change_type=PointChangeType.REGISTER,  # sign-up bonus
        description="sign-up bonus",
    )
    await point_record_crud.create(obj_in=point_record)
    
    # Get user role
    roles = await role_crud.get_roles_by_user_id(user_id=new_user.id)
    role_codes = [role.code for role in roles]
    
    # Get user permissions
    permissions = []
    menu_crud = SystemMenuCRUD(db)
    for role in roles:
        menus = await menu_crud.get_menus_by_role_id(role_id=role.id)
        for menu in menus:
            if menu.permission and menu.permission not in permissions:
                permissions.append(menu.permission)
    
    # Build user information
    user_info = {
        "id": new_user.id,
        "username": new_user.username,
        "nickname": new_user.nickname,
        "email": new_user.email,
        "mobile": new_user.mobile,
        "sex": new_user.sex,
        "avatar": new_user.avatar,
        "status": new_user.status,
        "remark": new_user.remark,
    }
    
    # Create a session
    from knowledge_api.framework.auth.token_util import TokenUtil
    session = await TokenUtil.create_user_session(
        user_id=new_user.id,
        username=new_user.username,
        roles=role_codes,
        permissions=permissions,
        user_info=user_info
    )
    
    # Generate JWT Token
    token = JWTUtils.create_access_token(
        user_id=new_user.id,
        username=new_user.username,
        session_id=session.session_id
    )
    
    # build response
    user_response = SystemUserResponse(
        id=new_user.id,
        username=new_user.username,
        nickname=new_user.nickname,
        email=new_user.email,
        mobile=new_user.mobile,
        sex=new_user.sex,
        avatar=new_user.avatar,
        status=new_user.status,
        remark=new_user.remark,
        create_time=new_user.create_time,
        update_time=new_user.update_time,
        login_date=new_user.login_date
    )
    
    return UserLoginResponse(token=token, user_info=user_response)


@router_auth.post("/login", response_model=UserLoginResponse)
@skip_auth()
async def login(
    login_data: UserLoginRequest,
    db: Session = Depends(get_session)
):
    """user login"""
    # Verify username password
    user_crud = SystemUserCRUD(db)
    user = await user_crud.verify_password(
        username=login_data.username,
        password=login_data.password
    )
    
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    # Get user role
    role_crud = SystemRoleCRUD(db)
    roles = await role_crud.get_roles_by_user_id(user_id=user.id)
    role_codes = [role.code for role in roles]
    
    # Get user permissions
    permissions = []
    menu_crud = SystemMenuCRUD(db)
    for role in roles:
        menus = await menu_crud.get_menus_by_role_id(role_id=role.id)
        for menu in menus:
            if menu.permission and menu.permission not in permissions:
                permissions.append(menu.permission)
    
    # Build user information
    user_info = {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "email": user.email,
        "mobile": user.mobile,
        "sex": user.sex,
        "avatar": user.avatar,
        "status": user.status,
        "remark": user.remark,
    }
    
    # Create a session
    from knowledge_api.framework.auth.token_util import TokenUtil
    session = await TokenUtil.create_user_session(
        user_id=user.id,
        username=user.username,
        roles=role_codes,
        permissions=permissions,
        user_info=user_info
    )
    
    # Generating JWT tokens - using the new parameter format
    token = JWTUtils.create_access_token(
        user_id=user.id,
        username=user.username,
        session_id=session.session_id
    )
    
    # Update login time
    await user_crud.update_login_time(user_id=user.id)
    
    # build response
    user_response = SystemUserResponse(
        id=user.id,
        username=user.username,
        nickname=user.nickname,
        email=user.email,
        mobile=user.mobile,
        sex=user.sex,
        avatar=user.avatar,
        status=user.status,
        remark=user.remark,
        create_time=user.create_time,
        update_time=user.update_time,
        login_date=user.login_date
    )
    
    return UserLoginResponse(token=token, user_info=user_response)


@router_auth.post("/logout")
async def logout(request: Request):
    """user logout"""
    # Get Token
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return {"code": 200, "message": "Logout successful"}
        
    token = auth_header.replace("Bearer ", "")
    
    # Using TokenUtil to invalidate a token (delete a session)
    from knowledge_api.framework.auth.token_util import TokenUtil
    success = await TokenUtil.invalidate_token(token)
    
    return {"code": 200, "message": "Logout successful"}


@router_auth.get("/refresh")
async def refresh_token(request: Request):
    """refresh token"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="unauthorized")
    
    token = auth_header.replace("Bearer ", "")
    
    try:
        # Parse the token to obtain the session ID
        token_data = JWTUtils.decode_token(token)
        session_id = token_data.get("session_id")
        
        if not session_id:
            raise HTTPException(status_code=401, detail="Invalid token format")
            
        # Get user session
        from knowledge_api.framework.auth.token_util import TokenUtil
        session = await TokenUtil.get_session(token)
        
        if not session:
            raise HTTPException(status_code=401, detail="The session has expired or does not exist")
            
        # Refresh the token (keep the same session ID)
        new_token = JWTUtils.refresh_token(token)
        
        # Update session expiration time
        await TokenUtil.refresh_session(token)
        
        return {"token": new_token}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"刷新令牌失败: {str(e)}")


@router_auth.get("/user/info", response_model=Dict[str, Any])
async def get_user_info(
    request: Request,
    db: Session = Depends(get_session)
):
    """Get current user information"""
    user_data = await get_current_user(request)
    user_id = user_data.get("user_id")
    
    # Acquire user information
    user_crud = SystemUserCRUD(db)
    user = await user_crud.get_by_id(user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User does not exist")
    
    # Get user role
    role_crud = SystemRoleCRUD(db)
    roles = await role_crud.get_roles_by_user_id(user_id=user_id)
    role_info = [{"id": role.id, "name": role.name, "code": role.code} for role in roles]
    
    # Get user details
    user_detail_crud = UserDetailCRUD(db)
    user_detail = await user_detail_crud.get_user_detail_with_rates(user_id=user_id)
    
    # build response
    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "email": user.email,
            "mobile": user.mobile,
            "sex": user.sex,
            "avatar": user.avatar,
            "status": user.status,
            "remark": user.remark,
            "login_date": user.login_date
        },
        "roles": role_info,
        "permissions": user_data.get("permissions", []),
        "user_detail": user_detail if user_detail else None
    }


@router_auth.get("/user/menu", response_model=List[Dict[str, Any]])
async def get_user_menu(
    request: Request,
    db: Session = Depends(get_session)
):
    """Get the current user menu"""
    user_data = await get_current_user(request)
    user_id = user_data.get("user_id")
    
    # Get user role
    role_crud = SystemRoleCRUD(db)
    roles = await role_crud.get_roles_by_user_id(user_id=user_id)
    
    # Get character menu
    menu_crud = SystemMenuCRUD(db)
    all_menus = []
    
    # Super admin role owns all menus
    is_admin = any(role.code == "admin" for role in roles)
    if is_admin:
        return await menu_crud.get_all_menus_tree(status=0)  # Get only normal menus
    
    # Normal user gets the corresponding role menu
    menu_ids = set()
    for role in roles:
        role_menus = await menu_crud.get_menus_by_role_id(role_id=role.id)
        for menu in role_menus:
            if menu.status == 0 and menu.visible:  # Get only normal and visible menus
                menu_ids.add(menu.id)
                all_menus.append(menu)
    
    # Get the parent menu of all menus
    parent_ids = set()
    for menu in all_menus:
        if menu.parent_id != 0:
            parent_ids.add(menu.parent_id)
    
    # Get parent menu information
    for parent_id in parent_ids:
        if parent_id not in menu_ids:
            parent_menu = await menu_crud.get_by_id(id=parent_id)
            if parent_menu and parent_menu.status == 0:
                all_menus.append(parent_menu)
    
    # Build menu tree
    return menu_crud._build_menu_tree(all_menus)


# Add routes compatible with legacy APIs
@router_auth.get("/api/user/info", response_model=Dict[str, Any])
async def api_get_user_info(
    request: Request,
    db: Session = Depends(get_session)
):
    """Get current user information (compatible with older APIs)"""
    return await get_user_info(request, db) 