from typing import Dict, Any, List, Optional, Tuple
from fastapi import HTTPException

from sqlmodel import Session
from knowledge_api.mapper.card_usage_record.crud import CardUsageRecordCRUD
from knowledge_api.mapper.blind_box_record.crud import BlindBoxRecordCRUD
from knowledge_api.mapper.user_card.crud import UserCardCRUD
from knowledge_api.mapper.card.crud import CardCRUD
from knowledge_api.mapper.blind_box.crud import BlindBoxCRUD
from knowledge_api.mapper.point_record.crud import PointRecordCRUD
from knowledge_api.mapper.user_detail.crud import UserDetailCRUD


class RewardService:
    """incentive service"""

    def __init__(self, db: Session):
        """Initialize the reward service"""
        self.db = db
        self.card_usage_record_crud = CardUsageRecordCRUD(self.db)
        self.blind_box_record_crud = BlindBoxRecordCRUD(self.db)
        self.user_card_crud = UserCardCRUD(self.db)
        self.card_crud = CardCRUD(self.db)
        self.blind_box_crud = BlindBoxCRUD(self.db)
        self.point_record_crud = PointRecordCRUD(self.db)
        self.user_detail_crud = UserDetailCRUD(self.db)

    async def get_challenge_reward(self, user_id: int, challenge_id: str) -> Dict[str, Any]:
        """Get a list of challenge rewards

Args:
user_id: User ID
challenge_id: Challenge ID

Returns:
reward information dictionary"""
        # 1. Query the challenge record
        usage_record = await self.card_usage_record_crud.get_by_id_user_id(user_id=user_id, related_id=challenge_id)
        
        if not usage_record:
            raise HTTPException(status_code=404, detail="No challenge record found")
            
        # 2. Check if the game status is a win (1)
        if usage_record.game_status != 1:
            raise HTTPException(status_code=400, detail="The challenge has not been won and cannot be rewarded")
            
        # 3. Initialize the reward list
        rewards = []
        total_points = 0
        
        # 4. Points Reward
        if usage_record.points_earned and usage_record.points_earned > 0:
            point_reward = {
                "type": "points",
                "amount": usage_record.points_earned,
                "message": f"获得{usage_record.points_earned}积分"
            }
            rewards.append(point_reward)
            total_points += usage_record.points_earned
            
        # 5. Blind Box Reward
        blind_box_reward = None
        if usage_record.blind_box_id and usage_record.blind_box_id > 0:
            # 5.1 Obtaining blind box information
            blind_box = await self.blind_box_crud.get_by_id(usage_record.blind_box_id)
            if not blind_box:
                raise HTTPException(status_code=404, detail="No blind box information found.")
                
            # 5.2 Obtain all cards associated with the blind box
            blind_box_cards = await self.blind_box_crud.get_blind_box_cards(usage_record.blind_box_id)
            
            # 5.3 Obtaining blind box extraction records
            blind_box_record = None
            card_detail = None
            is_duplicate = False
            points_gained = 0
            
            if usage_record.blind_box_record_id:
                blind_box_record = await self.blind_box_record_crud.get_by_id(usage_record.blind_box_record_id)
                
                if blind_box_record:
                    # Get the details of the drawn card
                    card_detail = await self.card_crud.get_by_id(blind_box_record.card_id)
                    is_duplicate = blind_box_record.is_duplicate
                    points_gained = blind_box_record.points_gained or 0
                    
                    if points_gained > 0:
                        total_points += points_gained
            
            # Building a blind box reward object
            blind_box_reward = {
                "type": "blind_box",
                "blind_box": {
                    "id": blind_box.id,
                    "name": blind_box.name,
                    "description": blind_box.description,
                    "image_url": blind_box.image_url,
                    "cards": [
                        {
                            "id": card.id,
                            "name": card.name,
                            "rarity": card.rarity,
                            "image_url": card.image_url
                        } for card in blind_box_cards
                    ]
                },
                "drawn_card": card_detail and {
                    "id": card_detail.id,
                    "name": card_detail.name,
                    "rarity": card_detail.rarity,
                    "image_url": card_detail.image_url,
                    "description": card_detail.description
                },
                "is_duplicate": is_duplicate,
                "points_gained": points_gained,
                "message": f"获得重复卡片【{card_detail.name if card_detail else ''}】，转化为{points_gained}积分" if is_duplicate else f"获得新卡片【{card_detail.name if card_detail else ''}】"
            }
            rewards.append(blind_box_reward)
        
        # 6. Build returns results
        return {
            "rewards": rewards,
            "total_points": total_points,
            "message": f"共获得{total_points}积分" + ("和一个盲盒" if blind_box_reward else "")
        }

    async def get_challenge_rewards_history(self, user_id: int, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """Get a list of user challenge rewards history

Args:
user_id: User ID
Limit: Number of records per page
Offset: Offset

Returns:
Historical reward list and paging information"""
        # 1. Query the user's winning challenge record
        records = await self.card_usage_record_crud.get_victory_records_by_user(
            user_id=user_id, 
            limit=limit, 
            offset=offset
        )
        
        # Get the total number of records
        total_count = await self.card_usage_record_crud.count_victory_records_by_user(user_id=user_id)
        
        # 2. Process each record to obtain relevant reward information
        rewards_history = []
        
        for record in records:
            # Basic information
            reward_info = {
                "challenge_id": record.related_id,
                "card_id": record.card_id,
                "challenge_time": record.start_time,
                "completed_time": record.end_time,
                "points_earned": record.points_earned or 0,
                "rewards": []
            }
            
            # Get card information
            card = await self.card_crud.get_by_id(record.card_id)
            if card:
                reward_info["card_info"] = {
                    "id": card.id,
                    "name": card.name,
                    "rarity": card.rarity,
                    "image_url": card.image_url
                }
            
            # Add bonus points
            if record.points_earned and record.points_earned > 0:
                reward_info["rewards"].append({
                    "type": "points",
                    "amount": record.points_earned,
                    "message": f"获得{record.points_earned}积分"
                })
            
            # Add blind box rewards
            if record.blind_box_id and record.blind_box_id > 0:
                blind_box_reward = {
                    "type": "blind_box",
                    "blind_box_id": record.blind_box_id,
                    "drawn_card": None,
                    "is_duplicate": False,
                    "points_gained": 0
                }
                
                # Get blind box information
                blind_box = await self.blind_box_crud.get_by_id(record.blind_box_id)
                if blind_box:
                    blind_box_reward["blind_box_name"] = blind_box.name
                
                # Obtain blind box extraction records
                if record.blind_box_record_id:
                    blind_box_record = await self.blind_box_record_crud.get_by_id(record.blind_box_record_id)
                    
                    if blind_box_record:
                        blind_box_reward["is_duplicate"] = blind_box_record.is_duplicate
                        blind_box_reward["points_gained"] = blind_box_record.points_gained or 0
                        
                        # Get the details of the drawn card
                        card_detail = await self.card_crud.get_by_id(blind_box_record.card_id)
                        if card_detail:
                            blind_box_reward["drawn_card"] = {
                                "id": card_detail.id,
                                "name": card_detail.name,
                                "rarity": card_detail.rarity,
                                "image_url": card_detail.image_url
                            }
                            
                            # Add bonus message
                            if blind_box_reward["is_duplicate"]:
                                blind_box_reward["message"] = f"获得重复卡片【{card_detail.name}】，转化为{blind_box_reward['points_gained']}积分"
                            else:
                                blind_box_reward["message"] = f"获得新卡片【{card_detail.name}】"
                
                reward_info["rewards"].append(blind_box_reward)
            
            # Calculate the total integral
            total_points = reward_info["points_earned"]
            for reward in reward_info["rewards"]:
                if reward["type"] == "blind_box" and reward["is_duplicate"] and reward["points_gained"]:
                    total_points += reward["points_gained"]
            
            reward_info["total_points"] = total_points
            rewards_history.append(reward_info)
        
        # 3. Build the return result
        return {
            "items": rewards_history,
            "total": total_count,
            "limit": limit,
            "offset": offset
        }