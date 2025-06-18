from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session
from typing import List, Dict, Any, Optional

from knowledge_api.framework.database.database import get_session
from knowledge_api.mapper.user_blind_box_stats.base import (
    UserBlindBoxStatsCreate, 
    UserBlindBoxStatsUpdate, 
    UserBlindBoxStats
)
from knowledge_api.mapper.user_blind_box_stats.crud import UserBlindBoxStatsCRUD
from knowledge_api.mapper.blind_box.crud import BlindBoxCRUD
from datetime import datetime

router_user_blind_box_stats = APIRouter(prefix="/user_blind_box_stats", tags=["User blind box statistical management"])


@router_user_blind_box_stats.post("/", response_model=UserBlindBoxStats)
async def create_user_blind_box_stats(
    stats_in: UserBlindBoxStatsCreate,
    db: Session = Depends(get_session)
) -> UserBlindBoxStats:
    """Create user blind box statistics"""
    crud = UserBlindBoxStatsCRUD(db)
    return await crud.create(obj_in=stats_in)


@router_user_blind_box_stats.get("/{stats_id}", response_model=UserBlindBoxStats)
async def get_user_blind_box_stats(
    stats_id: int,
    db: Session = Depends(get_session)
) -> UserBlindBoxStats:
    """Obtain user blind box statistics"""
    crud = UserBlindBoxStatsCRUD(db)
    stats = await crud.get_by_id(id=stats_id)
    if not stats:
        raise HTTPException(status_code=404, detail="The user blind box statistical record does not exist")
    return stats


@router_user_blind_box_stats.get("/user/{user_id}", response_model=List[UserBlindBoxStats])
async def get_user_all_blind_box_stats(
    user_id: int,
    db: Session = Depends(get_session)
) -> List[UserBlindBoxStats]:
    """Obtain all user blind box statistics"""
    crud = UserBlindBoxStatsCRUD(db)
    return await crud.get_multi_by_user(user_id=user_id)


@router_user_blind_box_stats.get("/user/{user_id}/box/{blind_box_id}", response_model=Dict[str, Any])
async def get_user_specific_blind_box_stats(
    user_id: int,
    blind_box_id: int,
    db: Session = Depends(get_session)
) -> Dict[str, Any]:
    """Obtain statistical information and guarantee probability for user-specific blind boxes"""
    crud = UserBlindBoxStatsCRUD(db)
    blind_box_crud = BlindBoxCRUD(db)
    
    stats = await crud.get_by_user_and_box(user_id=user_id, blind_box_id=blind_box_id)
    if not stats:
        # Create a default record if it doesn't exist
        stats_create = UserBlindBoxStatsCreate(
            user_id=user_id,
            blind_box_id=blind_box_id,
            total_count=0,
            current_count=0,
            creator_id=user_id
        )
        stats = await crud.create(obj_in=stats_create)
    
    # Get the blind box guarantee rule
    blind_box = await blind_box_crud.get_by_id(id=blind_box_id)
    probability_info = {"guarantee_rules": None, "next_guarantee": None}
    
    if blind_box and blind_box.probability_rules:
        import json
        try:
            probability_rules = json.loads(blind_box.probability_rules)
            guarantee_rule = probability_rules.get("guarantee_rule", {})
            
            if guarantee_rule.get("enabled", False):
                probability_info["guarantee_rules"] = guarantee_rule.get("rules", [])
                
                # Calculate the remaining number of times to trigger the guarantee next time and the corresponding rarity
                current_count = stats.current_count
                next_guarantee = None
                
                for rule in guarantee_rule.get("rules", []):
                    rule_count = rule.get("count", 0)
                    if current_count < rule_count:
                        remaining = rule_count - current_count
                        rarity = rule.get("guarantee_rarity", 0)
                        if next_guarantee is None or remaining < next_guarantee["remaining"]:
                            next_guarantee = {
                                "remaining": remaining,
                                "rarity": rarity,
                                "description": rule.get("description", f"{rule_count}抽必出")
                            }
                
                probability_info["next_guarantee"] = next_guarantee
        except Exception as e:
            probability_info["error"] = str(e)
    
    # build response
    response = {
        "data": stats,
        "probability_info": probability_info
    }
    
    return response


@router_user_blind_box_stats.put("/{stats_id}", response_model=UserBlindBoxStats)
async def update_user_blind_box_stats(
    stats_id: int,
    stats_update: UserBlindBoxStatsUpdate,
    db: Session = Depends(get_session)
) -> UserBlindBoxStats:
    """Update user blind box statistics"""
    crud = UserBlindBoxStatsCRUD(db)
    stats = await crud.update_by_id(id=stats_id, obj_in=stats_update)
    if not stats:
        raise HTTPException(status_code=404, detail="The user blind box statistical record does not exist")
    return stats


@router_user_blind_box_stats.put("/user/{user_id}/box/{blind_box_id}/increment", response_model=UserBlindBoxStats)
async def increment_draw_count(
    user_id: int,
    blind_box_id: int,
    db: Session = Depends(get_session)
) -> UserBlindBoxStats:
    """Increase the number of blind box extraction and guarantee count"""
    crud = UserBlindBoxStatsCRUD(db)
    stats = await crud.get_by_user_and_box(user_id=user_id, blind_box_id=blind_box_id)
    
    if not stats:
        # Create a default record if it doesn't exist
        stats_create = UserBlindBoxStatsCreate(
            user_id=user_id,
            blind_box_id=blind_box_id,
            total_count=1,
            current_count=1,
            creator_id=user_id
        )
        return await crud.create(obj_in=stats_create)
    else:
        # Update existing records
        update_data = UserBlindBoxStatsUpdate(
            total_count=stats.total_count + 1,
            current_count=stats.current_count + 1
        )
        return await crud.update(stats.id, update_data)


@router_user_blind_box_stats.put("/user/{user_id}/box/{blind_box_id}/trigger-guaranteed", response_model=UserBlindBoxStats)
async def trigger_guaranteed(
    user_id: int,
    blind_box_id: int,
    db: Session = Depends(get_session)
) -> UserBlindBoxStats:
    """Trigger guarantee, reset guarantee count and record guarantee time"""
    crud = UserBlindBoxStatsCRUD(db)
    stats = await crud.get_by_user_and_box(user_id=user_id, blind_box_id=blind_box_id)
    
    if not stats:
        # Create a default record if it doesn't exist
        stats_create = UserBlindBoxStatsCreate(
            user_id=user_id,
            blind_box_id=blind_box_id,
            total_count=0,
            current_count=0,
            last_guaranteed_time=datetime.now(),
            creator_id=user_id
        )
        return await crud.create(obj_in=stats_create)
    else:
        # Update existing records
        update_data = UserBlindBoxStatsUpdate(
            current_count=0,  # Reset guaranteed count
            last_guaranteed_time=datetime.now()  # Record the guarantee time
        )
        return await crud.update(stats.id, update_data)


@router_user_blind_box_stats.put("/user/{user_id}/box/{blind_box_id}/reset-pity", response_model=UserBlindBoxStats)
async def reset_pity_counter(
    user_id: int,
    blind_box_id: int,
    new_count: int = Query(0, description="New guaranteed count value"),
    db: Session = Depends(get_session)
) -> UserBlindBoxStats:
    """Manual reset user blind box guaranteed bottom count"""
    crud = UserBlindBoxStatsCRUD(db)
    stats = await crud.get_by_user_and_box(user_id=user_id, blind_box_id=blind_box_id)
    
    if not stats:
        # Create a default record if it doesn't exist
        stats_create = UserBlindBoxStatsCreate(
            user_id=user_id,
            blind_box_id=blind_box_id,
            total_count=0,
            current_count=new_count,
            creator_id=user_id
        )
        return await crud.create(obj_in=stats_create)
    else:
        # Update existing records
        update_data = UserBlindBoxStatsUpdate(
            current_count=new_count
        )
        return await crud.update(stats.id, update_data)


@router_user_blind_box_stats.delete("/{stats_id}", response_model=bool)
async def delete_user_blind_box_stats(
    stats_id: int,
    db: Session = Depends(get_session)
) -> bool:
    """Delete user blind box statistics"""
    crud = UserBlindBoxStatsCRUD(db)
    success = await crud.delete(id=stats_id)
    if not success:
        raise HTTPException(status_code=404, detail="The user blind box statistical record does not exist")
    return True


@router_user_blind_box_stats.get("/user/{user_id}/all_stats", response_model=Dict[str, List[Dict[str, Any]]])
async def get_user_all_blind_box_stats_with_detail(
    user_id: int,
    db: Session = Depends(get_session)
) -> Dict[str, List[Dict[str, Any]]]:
    """Get all blind box statistics for the user, including probability information and blind box name"""
    user_stats_crud = UserBlindBoxStatsCRUD(db)
    blind_box_crud = BlindBoxCRUD(db)
    
    # Get all blind box statistics for users
    user_stats = await user_stats_crud.get_multi_by_user(user_id=user_id)
    
    result_data = []
    
    # Get detailed and probability information for each blind box
    for stat in user_stats:
        blind_box_id = stat.blind_box_id
        blind_box = await blind_box_crud.get_by_id(id=blind_box_id)
        
        # Get the blind box name
        blind_box_name = blind_box.name if blind_box else f"盲盒 #{blind_box_id}"
        
        # Obtain guaranteed rules
        probability_info = {"guarantee_rules": None, "next_guarantee": None}
        
        if blind_box and blind_box.probability_rules:
            import json
            try:
                probability_rules = json.loads(blind_box.probability_rules)
                guarantee_rule = probability_rules.get("guarantee_rule", {})
                
                if guarantee_rule.get("enabled", False):
                    probability_info["guarantee_rules"] = guarantee_rule.get("rules", [])
                    
                    # Calculate the remaining number of times to trigger the guarantee next time and the corresponding rarity
                    current_count = stat.current_count
                    next_guarantee = None
                    
                    for rule in guarantee_rule.get("rules", []):
                        rule_count = rule.get("count", 0)
                        if current_count < rule_count:
                            remaining = rule_count - current_count
                            rarity = rule.get("guarantee_rarity", 0)
                            if next_guarantee is None or remaining < next_guarantee["remaining"]:
                                next_guarantee = {
                                    "remaining": remaining,
                                    "rarity": rarity,
                                    "description": rule.get("description", f"{rule_count}抽必出")
                                }
                    
                    probability_info["next_guarantee"] = next_guarantee
            except Exception as e:
                probability_info["error"] = str(e)
        
        # build result
        result_data.append({
            "stats": stat,
            "blind_box_name": blind_box_name,
            "probability_info": probability_info
        })
    
    return {"data": result_data} 