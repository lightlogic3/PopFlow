from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Optional

from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.relationship_level.base import RelationshipLevelResponse, RelationshipLevelCreate, \
    RelationshipLevelUpdate
from knowledge_api.mapper.relationship_level.crud import RelationshipLevelCRUD
from knowledge_api.framework.exception.custom_exceptions import BusinessException

router_relationship_level = APIRouter(prefix="/relationship-levels", tags=["relationship hierarchy management"])

@router_relationship_level.post("/", response_model=RelationshipLevelResponse)
async def create_relationship_level(
    relationship_level: RelationshipLevelCreate,
    db: Session = Depends(get_session)
) -> RelationshipLevelResponse:
    """Create relationship hierarchy"""
    crud = RelationshipLevelCRUD(db)
    return await crud.create(obj_in=relationship_level)


@router_relationship_level.get("/role/{role_id}")
async def get_relationship_level_by_role(
    role_id: str,
    db: Session = Depends(get_session)
) :
    """Get relationship level based on role ID"""
    crud = RelationshipLevelCRUD(db)
    relationship_level = await crud.get_by_role_id(role_id=role_id)
    if not relationship_level:
        return []
    return relationship_level

@router_relationship_level.get("/name/{relationship_name}", response_model=RelationshipLevelResponse)
async def get_relationship_level_by_name(
    relationship_name: str,
    db: Session = Depends(get_session)
) -> RelationshipLevelResponse:
    """Get relationship rank by relationship name"""
    crud = RelationshipLevelCRUD(db)
    relationship_level = await crud.get_by_relationship_name(relationship_name=relationship_name)
    if not relationship_level:
        raise BusinessException(business_code=4000, detail="Relationship hierarchy does not exist")
    return relationship_level

@router_relationship_level.get("/", response_model=List[RelationshipLevelResponse])
async def list_relationship_levels(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    status: Optional[int] = Query(default=None, description="Status: 1-enabled, 0-disabled"),
    relationship_name: Optional[str] = Query(default=None, description="relationship name"),
    db: Session = Depends(get_session)
) -> List[RelationshipLevelResponse]:
    """Get a list of relationship levels"""
    crud = RelationshipLevelCRUD(db)
    return await crud.get_all(
        skip=skip,
        limit=limit,
        status=status,
        relationship_name=relationship_name
    )

@router_relationship_level.put("/{relationship_level_id}", response_model=RelationshipLevelResponse)
async def update_relationship_level(
    relationship_level_id: int,
    relationship_level_update: RelationshipLevelUpdate,
    db: Session = Depends(get_session)
) -> RelationshipLevelResponse:
    """Update relationship level"""
    crud = RelationshipLevelCRUD(db)
    relationship_level = await crud.update(relationship_level_id, relationship_level_update)
    if not relationship_level:
        raise HTTPException(status_code=404, detail="Relationship hierarchy does not exist")
    return relationship_level

@router_relationship_level.delete("/{relationship_level_id}", response_model=bool)
async def delete_relationship_level(
    relationship_level_id: int,
    db: Session = Depends(get_session)
) -> bool:
    """Delete relationship level"""
    crud = RelationshipLevelCRUD(db)
    success = await crud.delete(relationship_level_id=relationship_level_id)
    if not success:
        raise HTTPException(status_code=404, detail="Relationship hierarchy does not exist")
    return True



@router_relationship_level.get("/{relationship_level_id}", response_model=RelationshipLevelResponse)
async def get_relationship_level(
    relationship_level_id: int,
    db: Session = Depends(get_session)
) -> RelationshipLevelResponse:
    """Get a single relationship level"""
    crud = RelationshipLevelCRUD(db)
    relationship_level = await crud.get_by_id(relationship_level_id=relationship_level_id)
    if not relationship_level:
        raise HTTPException(status_code=404, detail="Relationship hierarchy does not exist")
    return relationship_level