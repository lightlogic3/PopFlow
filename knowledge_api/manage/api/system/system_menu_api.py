from fastapi import APIRouter, Depends, HTTPException, Request, Query, Path
from sqlmodel import Session
from typing import Dict, Any, List, Optional

from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.system.base import (
    SystemMenuCreate, SystemMenuUpdate, SystemMenuResponse
)
from knowledge_api.mapper.system.crud import SystemMenuCRUD
from knowledge_api.framework.auth.auth_decorator import require_permissions, get_current_user

# Create route
router_system_menu = APIRouter(prefix="/system/menus", tags=["menu management"])


@router_system_menu.post("/", response_model=SystemMenuResponse)
@require_permissions(["system:menu:add"])
async def create_menu(
    menu_create: SystemMenuCreate,
    request: Request,
    db: Session = Depends(get_session)
):
    """Create menu"""
    creator = request.state.token_data.get("username", "")
    
    # Create menu
    menu_crud = SystemMenuCRUD(db)
    menu = await menu_crud.create(obj_in=menu_create, creator=creator)
    
    return menu


@router_system_menu.get("/", response_model=Dict[str, Any])
@require_permissions(["system:menu:list"])
async def list_menus(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    name: str = Query(None),
    status: int = Query(None),
    db: Session = Depends(get_session)
):
    """Get menu list"""
    menu_crud = SystemMenuCRUD(db)
    menus, total = await menu_crud.get_all(
        skip=skip,
        limit=limit,
        name=name,
        status=status
    )
    
    return {
        "items": menus,
        "total": total
    }


@router_system_menu.get("/tree", response_model=List[Dict[str, Any]])
@require_permissions(["system:menu:list"])
async def get_menu_tree(
    request: Request,
    status: Optional[int] = Query(None),
    db: Session = Depends(get_session)
):
    """Get menu tree"""
    menu_crud = SystemMenuCRUD(db)
    menu_tree = await menu_crud.get_all_menus_tree(status=status)
    
    return menu_tree


@router_system_menu.get("/{menu_id}", response_model=SystemMenuResponse)
@require_permissions(["system:menu:query"])
async def get_menu(
    request: Request,
    menu_id: int = Path(..., title="Menu ID"),
    db: Session = Depends(get_session)
):
    """Get menu by ID"""
    menu_crud = SystemMenuCRUD(db)
    menu = await menu_crud.get_by_id(id=menu_id)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu does not exist")
    
    return menu


@router_system_menu.put("/{menu_id}", response_model=SystemMenuResponse)
@require_permissions(["system:menu:edit"])
async def update_menu(
    request: Request,
    menu_data: Dict[str, Any],  # Use Dict [str, Any] instead of using Pydantic models directly
    menu_id: int = Path(..., title="Menu ID"),
    db: Session = Depends(get_session)
):
    """Update menu"""
    updater = request.state.token_data.get("username", "")
    
    # log request data
    print(f"更新菜单 - 菜单ID: {menu_id}")
    print(f"请求体数据: {menu_data}")
    
    # query menu
    menu_crud = SystemMenuCRUD(db)
    db_menu = await menu_crud.get_by_id(id=menu_id)
    if not db_menu:
        raise HTTPException(status_code=404, detail="Menu does not exist")
    
    # Transforming request volume data into a model
    from pydantic import parse_obj_as
    try:
        menu_update = parse_obj_as(SystemMenuUpdate, menu_data)
    except Exception as e:
        print(f"解析菜单更新数据失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"数据格式错误: {str(e)}")
    
    # Update menu
    menu = await menu_crud.update(id=menu_id, obj_in=menu_update, updater=updater)
    if not menu:
        raise HTTPException(status_code=404, detail="Menu update failed")
    
    return menu


@router_system_menu.delete("/{menu_id}", response_model=Dict[str, Any])
@require_permissions(["system:menu:remove"])
async def delete_menu(
    request: Request,
    menu_id: int = Path(..., title="Menu ID"),
    db: Session = Depends(get_session)
):
    """Delete menu"""
    updater = request.state.token_data.get("username", "")
    
    menu_crud = SystemMenuCRUD(db)
    success = await menu_crud.delete(id=menu_id, updater=updater)
    if not success:
        raise HTTPException(status_code=404, detail="Menu does not exist or submenus exist")
    
    return {"code": 200, "message": "Deleted successfully"}


@router_system_menu.get("/user/routes", response_model=List[Dict[str, Any]])
async def get_user_menus(
    request: Request,
    db: Session = Depends(get_session)
):
    """Get menu routing permissions for the current user"""
    # Get user information from the token
    token_data = await get_current_user(request)
    username = token_data.get("username", "")
    is_admin = token_data.get("is_admin", False)
    
    # Get the user's menu permissions
    menu_crud = SystemMenuCRUD(db)
    
    # If you are an administrator, return to all visible menus
    if is_admin:
        menu_tree = await menu_crud.get_all_menus_tree(status=0)  # Get only normal menus
    else:
        # Gets menu permissions owned by the user role
        menu_tree = await menu_crud.get_user_menus_tree(username=username, status=0)
    
    return menu_tree


@router_system_menu.put("/{menu_id}/test", response_model=Dict[str, Any])
async def test_update_menu(
    request: Request,
    menu_data: Dict[str, Any],
    menu_id: int = Path(..., title="Menu ID"),
    db: Session = Depends(get_session)
):
    """Test the update menu function and print the full request data"""
    print(f"测试更新菜单 - 菜单ID: {menu_id}")
    print(f"请求体原始数据: {menu_data}")
    
    # Extracting visible fields
    visible = menu_data.get("visible")
    print(f"visible字段值: {visible}, 类型: {type(visible)}")
    
    # Query the current menu
    menu_crud = SystemMenuCRUD(db)
    menu = await menu_crud.get_by_id(id=menu_id)
    if not menu:
        return {"code": 404, "message": "Menu does not exist"}
    
    # Attempt to create an updated model
    try:
        from pydantic import parse_obj_as
        # Directly transform the request body into an update model
        menu_update = parse_obj_as(SystemMenuUpdate, menu_data)
        print(f"解析后的更新模型: {menu_update}")
        print(f"更新模型中的visible: {menu_update.visible}")
        print(f"字段是否被设置: {menu_update.__fields_set__}")
    except Exception as e:
        print(f"解析失败: {str(e)}")
        return {"code": 400, "message": f"数据格式错误: {str(e)}"}
    
    # Return to test results
    return {
        "code": 200, 
        "message": "Test completed",
        "current_visible": menu.visible,
        "request_visible": visible,
        "fields_set": list(menu_update.__fields_set__) if hasattr(menu_update, "__fields_set__") else []
    } 