from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Optional, Dict, Any

from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.roles.crud import RoleCRUD
from knowledge_api.mapper.roles_world.base import RolesWorldResponse, RolesWorldCreate, RolesWorld, RolesWorldUpdate
from knowledge_api.mapper.roles_world.crud import RolesWorldCRUD
from knowledge_api.mapper.world_knowledge.crud import WorldKnowledgeCRUD

router_roles_world = APIRouter(prefix="/roles-world", tags=["Role Worldview Association Management"])


@router_roles_world.post("/", response_model=RolesWorldResponse)
async def create_roles_world(
        roles_world: RolesWorldCreate,
        db: Session = Depends(get_session)
) -> RolesWorld:
    """Create a relationship between characters and worldview knowledge points"""
    try:
        crud = RolesWorldCRUD(db)
        return await crud.create(roles_world=roles_world)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router_roles_world.get("/{id}", response_model=RolesWorldResponse)
async def get_roles_world(
        id: int,
        db: Session = Depends(get_session)
) -> RolesWorld:
    """Get a single character to associate with worldview knowledge points"""
    crud = RolesWorldCRUD(db)
    roles_world = await crud.get_by_id(id=id)
    if not roles_world:
        raise HTTPException(status_code=404, detail="There is no relationship between roles and worldview knowledge points")
    return roles_world


@router_roles_world.get("/", response_model=List[RolesWorldResponse])
async def list_roles_worlds(
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=100),
        role_id: Optional[str] = Query(None, description="Role ID"),
        world_id: Optional[int] = Query(None, description="World ID"),
        world_konwledge_id: Optional[str] = Query(None, description="World view knowledge point ID"),
        db: Session = Depends(get_session)
) -> List[RolesWorld]:
    """Obtain a list of roles and worldview knowledge points"""
    crud = RolesWorldCRUD(db)
    filters: Dict[str, Any] = {}
    if role_id:
        filters["role_id"] = role_id
    if world_id:
        filters["world_id"] = world_id
    if world_konwledge_id:
        filters["world_konwledge_id"] = world_konwledge_id
    return await crud.get_all(skip=skip, limit=limit, filters=filters)


@router_roles_world.get("/role/{role_id}", response_model=List[RolesWorldResponse])
async def list_roles_worlds_by_role(
        role_id: str,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=100),
        db: Session = Depends(get_session)
) -> List[RolesWorld]:
    """Get a list of associated worldview knowledge points based on the role ID"""
    crud = RolesWorldCRUD(db)
    return await crud.get_by_role_id(role_id=role_id, skip=skip, limit=limit)


@router_roles_world.get("/role/{role_id}/with-details", response_model=Dict[str, Any])
async def list_roles_worlds_by_role_with_details(
        role_id: str,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=100),
        db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """Get a list of associated worldview knowledge points according to the role ID, and include the details of the knowledge points

Return format:
{
"Relations": [list of associated records],
"world_knowledge": {
"knowledge_id1": Knowledge point details 1,
"knowledge_id2": Knowledge point details 2,
So...
},
"Worlds": {
"world_id1": world view details 1,
"world_id2": world view details 2,
So...
}
}"""
    # Get associated record
    roles_world_crud = RolesWorldCRUD(db)
    relations = await roles_world_crud.get_by_role_id(role_id=role_id, skip=skip, limit=limit)

    if not relations:
        return {
            "relations": [],
            "world_knowledge": {},
            "worlds": {}
        }

    # Extract all knowledge point IDs
    knowledge_ids = [relation.world_konwledge_id for relation in relations]

    # Batch acquisition of knowledge point details
    world_knowledge_crud = WorldKnowledgeCRUD(db)
    knowledge_details = await world_knowledge_crud.get_by_ids(knowledge_ids)

    # Return in dictionary format
    knowledge_dict = {detail.id: detail for detail in knowledge_details}

    # Extract all world IDs and deduplicate
    world_ids = list(set(relation.world_id for relation in relations))

    # Get world view details (if the backend provides this feature)
    worlds_dict = {}

    return {
        "relations": relations,
        "world_knowledge": knowledge_dict,
        "worlds": worlds_dict
    }


@router_roles_world.get("/world/{world_id}", response_model=List[RolesWorldResponse])
async def list_roles_worlds_by_world(
        world_id: str,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=100),
        db: Session = Depends(get_session)
) -> List[RolesWorld]:
    """Get a list of associated roles based on the world ID"""
    crud = RolesWorldCRUD(db)
    return await crud.get_by_world_id(world_id=world_id, skip=skip, limit=limit)


@router_roles_world.get("/world-knowledge/{world_knowledge_id}", response_model=List[RolesWorldResponse])
async def list_roles_worlds_by_world_knowledge(
        world_knowledge_id: str,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=100),
        db: Session = Depends(get_session)
) -> List[RolesWorld]:
    """Get the associated role list based on the Worldview Knowledge Point ID"""
    crud = RolesWorldCRUD(db)
    return await crud.get_by_world_knowledge_id(world_knowledge_id=world_knowledge_id, skip=skip, limit=limit)


@router_roles_world.put("/{id}", response_model=RolesWorldResponse)
async def update_roles_world(
        id: int,
        roles_world_update: RolesWorldUpdate,
        db: Session = Depends(get_session)
) -> RolesWorld:
    """Update the relationship between roles and worldview knowledge points"""
    try:
        crud = RolesWorldCRUD(db)
        roles_world = await crud.update(id, roles_world_update)
        if not roles_world:
            raise HTTPException(status_code=404, detail="There is no relationship between roles and worldview knowledge points")
        return roles_world
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router_roles_world.delete("/{id}", response_model=bool)
async def delete_roles_world(
        id: int,
        db: Session = Depends(get_session)
) -> bool:
    """Delete the relationship between the character and the world view knowledge point"""
    crud = RolesWorldCRUD(db)
    success = await crud.delete(id=id)
    if not success:
        raise HTTPException(status_code=404, detail="There is no relationship between roles and worldview knowledge points")
    return True


@router_roles_world.delete("/role/{role_id}", response_model=bool)
async def delete_roles_world_by_role(
        role_id: str,
        db: Session = Depends(get_session)
) -> bool:
    """Delete associations based on role IDs"""
    crud = RolesWorldCRUD(db)
    success = await crud.delete_by_role_id(role_id=role_id)
    if not success:
        raise HTTPException(status_code=404, detail="No relationship found for the corresponding role")
    return True


@router_roles_world.delete("/world/{world_id}", response_model=bool)
async def delete_roles_world_by_world(
        world_id: int,
        db: Session = Depends(get_session)
) -> bool:
    """Delete association based on world ID"""
    crud = RolesWorldCRUD(db)
    success = await crud.delete_by_world_id(world_id=world_id)
    if not success:
        raise HTTPException(status_code=404, detail="No correlation found for the world")
    return True


@router_roles_world.delete("/world-knowledge/{world_knowledge_id}", response_model=bool)
async def delete_roles_world_by_world_knowledge(
        world_knowledge_id: str,
        db: Session = Depends(get_session)
) -> bool:
    """Delete associations according to the Worldview Knowledge Point ID"""
    crud = RolesWorldCRUD(db)
    success = await crud.delete_by_world_knowledge_id(world_knowledge_id=world_knowledge_id)
    if not success:
        raise HTTPException(status_code=404, detail="No correlation was found corresponding to the knowledge points of the world view")
    return True


@router_roles_world.get("/world/{world_id}/roles", response_model=Dict[str, Any])
async def get_roles_by_world_id(
        world_id: str,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=100),
        db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """Gets a list of role details associated with the specified worldview and deduplicates

Return format:
{
"Total": total,
"Roles": [
{
"Id": "Role ID",
"Name": "character name",
"Avatar": "Character avatar",
... Other character information
},
So...
]
}"""
    # Get associated record
    roles_world_crud = RolesWorldCRUD(db)
    relations = await roles_world_crud.get_by_world_id(world_id=world_id)

    if not relations:
        return {
            "total": 0,
            "roles": []
        }

    # Extract the role ID and deduplicate
    role_ids = list(set(relation.role_id for relation in relations))
    total = len(role_ids)

    # Get the role ID of the current page
    page_role_ids = role_ids[skip:skip + limit]

    # Get role details in bulk
    role_crud = RoleCRUD(db)
    roles = await role_crud.get_by_ids(role_ids=page_role_ids)

    return {
        "total": total,
        "roles": roles
    }


@router_roles_world.get("/world-knowledge/{world_knowledge_id}/roles", response_model=Dict[str, Any])
async def get_roles_by_world_knowledge_id(
        world_knowledge_id: str,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=100),
        db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """Gets a list of role details associated with a specified worldview knowledge point and deduplicates

Return format:
{
"Total": total,
"Roles": [
{
"Id": "character ID",
"Name": "character name",
"Avatar": "Character avatar",
... Other character information
},
So...
]
}"""
    # Get associated record
    roles_world_crud = RolesWorldCRUD(db)
    relations = await roles_world_crud.get_by_world_knowledge_id(world_knowledge_id=world_knowledge_id)

    if not relations:
        return {
            "total": 0,
            "roles": []
        }

    # Extract the role ID and deduplicate
    role_ids = list(set(relation.role_id for relation in relations))
    total = len(role_ids)

    # Get the role ID of the current page
    page_role_ids = role_ids[skip:skip + limit]

    # Get role details in bulk
    role_crud = RoleCRUD(db)
    roles = await role_crud.get_by_ids(role_ids=page_role_ids)
    back_list = []
    for role in roles:
        for relation in relations:
            if role.role_id == relation.role_id:
                item=role.model_dump()
                item["relation_id"] = relation.id
                back_list.append(item)

    return {
        "total": total,
        "roles": back_list
    }
