import json
import random
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException
from sqlmodel import Session

from card_game.server.card_service import CardService
from knowledge_api.framework.blind_box.blind_box_algorithm import BlindBoxEngine
from knowledge_api.mapper.blind_box.crud import BlindBoxCRUD
from knowledge_api.mapper.blind_box_record.base import BlindBoxRecordCreate
from knowledge_api.mapper.blind_box_record.crud import BlindBoxRecordCRUD
from knowledge_api.mapper.card import CardCRUD, Card
from knowledge_api.mapper.card.base import CardAlg
from knowledge_api.mapper.card_usage_record.crud import CardUsageRecordCRUD
from knowledge_api.mapper.limited_card_stats.crud import LimitedCardStatsCRUD
from knowledge_api.mapper.point_record import PointRecordCRUD
from knowledge_api.mapper.user_blind_box_stats.crud import UserBlindBoxStatsCRUD
from knowledge_api.mapper.user_blind_box_stats.base import UserBlindBoxStatsCreate, UserBlindBoxStatsUpdate
from knowledge_api.mapper.user_card.base import UserCardCreate
from knowledge_api.mapper.user_card.crud import UserCardCRUD
from knowledge_api.mapper.user_detail import UserDetailCRUD
from knowledge_api.utils.log_config import get_logger

logger = get_logger()


class CardChallengeService:
    def __init__(self, db: Session):
        """Initialize Card Challenge Service
: Param db: database session"""
        self.db = db
        self.user_detail_crud = UserDetailCRUD(self.db)
        self.card_usage_record_crud = CardUsageRecordCRUD(self.db)
        self.point_record_crud = PointRecordCRUD(self.db)
        # Card List
        self.card_crud = CardCRUD(db)
        self.card_service = CardService(db)

        # blind box
        self.blind_box_crud = BlindBoxCRUD(db)
        self.blind_box_engine = BlindBoxEngine()
        # Inject database CRUD instances into the blind box engine, enabling SQL optimization
        self.blind_box_engine.set_db_crud(BlindBoxRecordCRUD(db))
        self.blind_box_record_crud = BlindBoxRecordCRUD(db)
        self.user_card_crud = UserCardCRUD(db)
        # user blind box statistics
        self.user_blind_box_stats_crud = UserBlindBoxStatsCRUD(db)
        # Limited Card Statistics
        self.limited_card_stats_crud = LimitedCardStatsCRUD(db)

    async def challenge_successful(self, user_id: int, record_id: str) -> Dict[str, Any]:
        """Check if the challenge was successful
: Param user_id: session id
: Param record_id: record ID
: return: whether it was successful"""
        #  Update challenge statistics to success (user details data synchronization), sync success records
        await self.user_detail_crud.update_challenge_stats(
            user_id=user_id,
            success=True
        )
        # Query Challenge Records
        usage_records = await self.card_usage_record_crud.get_by_id_user_id(user_id=user_id, related_id=record_id)

        # Check the challenge card information.
        card_info = await self.card_crud.get_by_id(usage_records.card_id)
        # Earn victory points
        await self.card_service.reward_challenge_points(user_id=user_id,
                                                        card_id=card_info.id,
                                                        points=card_info.victory_points
                                                        )
        # Handling blind box drops
        blind_box_result = await self.bind_box_drop(card_info, user_id=user_id)

        # Update the game status of the card usage record to win (1), blind box ID, and blind box record ID
        await self.card_usage_record_crud.update_game_status_bind_box(
            related_id=record_id, 
            game_status=1,
            blind_box_id=blind_box_result["blind_box_id"], 
            user_id=user_id,
            points_earned=card_info.victory_points,
            blind_box_record_id=blind_box_result.get("blind_box_record_id")
        )
        
        # Build returns results
        result = {
            "blind_box_id": blind_box_result["blind_box_id"],
            "victory_points": card_info.victory_points,
        }
        
        # If there is a blind box record, add relevant information.
        if blind_box_result.get("blind_box_record_id"):
            result["blind_box_record_id"] = blind_box_result["blind_box_record_id"]
            result["card_id"] = blind_box_result.get("card_id")
            result["is_duplicate"] = blind_box_result.get("is_duplicate")
            result["duplicate_points"] = blind_box_result.get("duplicate_points", 0)
            
        return result

    # Blind box drop logic processing
    async def bind_box_drop(self, card_info: Card, user_id: int) -> Dict[str, Any]:
        """Handling blind box drop logic
: Param card_info: Card Information
: Param user_id: user ID
: Return: drop information dictionary, including blind box ID and blind box record ID"""
        result = {
            "blind_box_id": -1,
            "blind_box_record_id": None
        }
        
        try:
            # Get card information
            if card_info and card_info.box_drop_rate:
                # Determine whether to get the blind box according to the drop probability
                if random.random() * 100 <= card_info.box_drop_rate:  # Convert to percentage probability
                    # Get the blind box! Record the blind box ID
                    blind_box_id = card_info.blind_box_id or -1
                    if blind_box_id > 0:
                        # Execute blind box logic
                        draw_result = await self.draw_blind_box(
                            user_id=user_id,
                            blind_box_id=blind_box_id)
                        
                        # Update returns results
                        result["blind_box_id"] = blind_box_id
                        result["blind_box_record_id"] = draw_result.get("blind_box_record_id")
                        result.update(draw_result)
        except Exception as e:
            # Log errors without interrupting the process
            import traceback
            traceback.print_exc()
            logger.error(f"盲盒掉落判断失败: {str(e)}")
        
        return result

    async def fail_challenge(self, user_id: int, record_id: str) -> None:
        """Handling challenge failure logic
: Param user_id: user ID
: Param record_id: record ID"""
        # Update challenge statistics as failures (user details data synchronization)
        await self.user_detail_crud.update_challenge_stats(
            user_id=user_id,
            success=False
        )
        # Update the game status of the card usage record to Failed (2)
        await self.card_usage_record_crud.update_game_status(related_id=record_id, game_status=2,user_id=user_id)

    async def draw_blind_box(self, user_id: int, blind_box_id: int) -> Dict[str, Any]:
        """Extracting blind boxes (using SQL optimized version)
: Param user_id: user ID
: Param blind_box_id: blind box ID
: return: extraction result"""
        # 1. Verify whether the blind box ID is valid.
        if blind_box_id <= 0:
            raise ValueError("Invalid blind box ID")

        # 2. Obtain blind box card information
        blind_box = await self.blind_box_crud.get_by_id(blind_box_id)
        if not blind_box:
            raise ValueError("No corresponding blind box card information found.")

        # 3. Get the list of cards in the blind box
        cards: List[CardAlg] = await self.blind_box_crud.get_blind_box_cards(blind_box_id)
        if not cards:
            raise ValueError("There are no extractable cards in the blind box")
            
        # 4. Get a list of sold-out limited cards
        sold_out_card_ids = await self.limited_card_stats_crud.get_sold_out_card_ids()

        # 5. Analyze probability rules
        probability_rules = json.loads(blind_box.probability_rules)

        # 6. Using SQL-optimized card drawing algorithms
        try:
            selected_card, is_guaranteed = await self.blind_box_engine.draw_card_with_sql_optimization(
                blind_box_id=blind_box_id,
                user_id=user_id,
                cards=cards,
                probability_rules=probability_rules,
                sold_out_card_ids=sold_out_card_ids
            )
        except Exception as e:
            # If the SQL optimization version fails, revert to the original version
            logger.warning(f"SQL优化抽卡失败，回退到原版本: {str(e)}")
            user_stats = await self.get_user_blind_box_stats_sql_optimized(user_id, blind_box_id)
            selected_card, is_guaranteed = self.blind_box_engine.draw_card(
                blind_box_id=blind_box_id,
                user_id=user_id,
                cards=cards,
                probability_rules=probability_rules,
                user_stats=user_stats,
                sold_out_card_ids=sold_out_card_ids
            )

        # 7. Update user draw card statistics (retain the original logic to ensure compatibility)
        await self.update_user_blind_box_stats(user_id, blind_box_id, is_guaranteed)
        
        # 8. Handling limit card logic
        await self.process_limited_card(selected_card, user_id)

        # 9. Process card acquisition logic
        is_duplicate, duplicate_points = await self.process_card_acquisition(
            user_id=user_id,
            card_id=selected_card.id,
            obtain_type="blind_box"
        )

        # 10. Record blind box extraction records
        blind_box_record = BlindBoxRecordCreate(
            user_id=user_id,
            blind_box_id=blind_box_id,
            card_id=selected_card.id,
            is_duplicate=is_duplicate,
            points_gained=duplicate_points if is_duplicate else None,
            is_guaranteed=is_guaranteed,
            is_special_reward=False,  # Can be set as needed
            source_type="reward",  # Reward type
            source_id=blind_box_id,
            creator_id=user_id
        )
        blind_box_record_obj = await self.blind_box_record_crud.create(blind_box_record)
        
        # Returns the record ID for the caller to save
        return {
            "blind_box_record_id": blind_box_record_obj.id,
            "card_id": selected_card.id,
            "is_duplicate": is_duplicate,
            "duplicate_points": duplicate_points if is_duplicate else 0
        }

    async def get_user_blind_box_stats_sql_optimized(self, user_id: int, blind_box_id: int) -> Dict[str, Any]:
        """Obtain user blind box statistics using SQL optimization (for fallback scenarios)

: Param user_id: user ID
: Param blind_box_id: blind box ID
: return: user blind box statistical dictionary"""
        try:
            # Use SQL to directly count the last 120 records
            recent_records = await self.blind_box_record_crud.get_recent_draws_for_algorithm(
                user_id=user_id,
                blind_box_id=blind_box_id,
                limit=120
            )
            
            total_count = len(recent_records)
            
            # Calculate the current number of consecutive uninsured times
            current_count = 0
            last_guaranteed_time = None
            
            for record in recent_records:
                if record.get('is_guaranteed', False):
                    last_guaranteed_time = record.get('create_time')
                    break
                current_count += 1
            
            return {
                "current_count": current_count,
                "total_count": total_count,
                "last_guaranteed_time": last_guaranteed_time
            }
            
        except Exception as e:
            # Log when an error occurs and revert to the original method
            logger.error(f"SQL优化统计失败，回退到原方法: {str(e)}")
            return await self.get_user_blind_box_stats(user_id, blind_box_id)

    async def get_user_blind_box_stats(self, user_id: int, blind_box_id: int) -> Dict[str, Any]:
        """Obtain user blind box statistics and create them if they don't exist (original method, maintaining compatibility)

: Param user_id: user ID
: Param blind_box_id: blind box ID
: return: user blind box statistical dictionary"""
        try:
            # Query user blind box statistics
            stats = await self.user_blind_box_stats_crud.get_by_user_and_box(user_id, blind_box_id)
            
            if not stats:
                # Create a new statistical record if it does not exist
                new_stats = UserBlindBoxStatsCreate(
                    user_id=user_id,
                    blind_box_id=blind_box_id,
                    total_count=0,
                    current_count=0,
                    creator_id=user_id
                )
                stats = await self.user_blind_box_stats_crud.create(new_stats)
            
            # Returns the dictionary format, matching the algorithm interface
            return {
                "current_count": stats.current_count,
                "total_count": stats.total_count,
                "last_guaranteed_time": stats.last_guaranteed_time
            }
            
        except Exception as e:
            # Log on error and return empty statistics
            logger.error(f"获取用户盲盒统计失败: {str(e)}")
            return {
                "current_count": 0,
                "total_count": 0,
                "last_guaranteed_time": None
            }

    async def get_user_draw_statistics(self, user_id: int, blind_box_id: int) -> Dict[str, Any]:
        """Get user extraction statistics (new method, optimized using SQL)

: Param user_id: user ID
: Param blind_box_id: blind box ID
: return: Detailed extraction statistics"""
        try:
            # Statistical methods optimized using SQL
            statistics = await self.blind_box_engine.get_user_draw_statistics_sql(user_id, blind_box_id)
            return statistics
        except Exception as e:
            logger.error(f"获取用户抽取统计失败: {str(e)}")
            return {
                'basic_stats': {
                    'total_draws': 0,
                    'total_guarantees': 0,
                    'guarantee_rate': 0.0,
                    'first_draw_time': None,
                    'last_draw_time': None,
                    'rarity_distribution': {}
                },
                'rarity_distribution': {'total_count': 0, 'distribution': {}},
                'guarantee_history': []
            }

    async def get_next_guarantee_info(self, user_id: int, blind_box_id: int) -> Dict[str, Any]:
        """Get the next guarantee information (new method, use SQL optimization)

: Param user_id: user ID
: Param blind_box_id: blind box ID
: return: next guarantee information"""
        try:
            # Obtain the blind box probability rule
            blind_box = await self.blind_box_crud.get_by_id(blind_box_id)
            if not blind_box:
                return {}
            
            probability_rules = json.loads(blind_box.probability_rules)
            
            # Use SQL optimization to obtain guaranteed information
            guarantee_info = await self.blind_box_engine.get_next_guarantee_info_sql(
                user_id=user_id,
                blind_box_id=blind_box_id,
                probability_rules=probability_rules
            )
            
            return guarantee_info
            
        except Exception as e:
            logger.error(f"获取保底信息失败: {str(e)}")
            return {}

    async def validate_guarantee_mechanism(self, user_id: int, blind_box_id: int) -> Dict[str, Any]:
        """Verify the correctness of the guarantee mechanism (new method for debugging and monitoring)

: Param user_id: user ID
: Param blind_box_id: blind box ID
: return: verification result"""
        try:
            # Obtain the blind box probability rule
            blind_box = await self.blind_box_crud.get_by_id(blind_box_id)
            if not blind_box:
                return {'is_valid': False, 'message': 'The blind box does not exist.'}
            
            probability_rules = json.loads(blind_box.probability_rules)
            
            # Validation methods optimized using SQL
            validation_result = await self.blind_box_engine.validate_guarantee_mechanism_sql(
                user_id=user_id,
                blind_box_id=blind_box_id,
                probability_rules=probability_rules
            )
            
            return validation_result
            
        except Exception as e:
            logger.error(f"验证保底机制失败: {str(e)}")
            return {'is_valid': False, 'message': f'验证失败: {str(e)}'}

    async def get_algorithm_performance_comparison(self, user_id: int, blind_box_id: int) -> Dict[str, Any]:
        """Performance comparison before and after SQL optimization (new method for performance monitoring)

: Param user_id: user ID
: Param blind_box_id: blind box ID
: return: performance comparison results"""
        import time
        
        try:
            # Test original method performance
            start_time = time.time()
            original_stats = await self.get_user_blind_box_stats(user_id, blind_box_id)
            original_time = time.time() - start_time
            
            # Testing the performance of SQL optimization methods
            start_time = time.time()
            optimized_stats = await self.get_user_blind_box_stats_sql_optimized(user_id, blind_box_id)
            optimized_time = time.time() - start_time
            
            # Test detailed statistical performance
            start_time = time.time()
            detailed_stats = await self.get_user_draw_statistics(user_id, blind_box_id)
            detailed_time = time.time() - start_time
            
            return {
                'performance': {
                    'original_method_time': round(original_time * 1000, 2),  # millisecond
                    'optimized_method_time': round(optimized_time * 1000, 2),  # millisecond
                    'detailed_stats_time': round(detailed_time * 1000, 2),  # millisecond
                    'performance_improvement': round((original_time - optimized_time) / original_time * 100, 2) if original_time > 0 else 0  # percentage
                },
                'data_comparison': {
                    'original_stats': original_stats,
                    'optimized_stats': optimized_stats,
                    'data_consistency': original_stats == optimized_stats
                },
                'detailed_stats_sample': {
                    'total_draws': detailed_stats.get('basic_stats', {}).get('total_draws', 0),
                    'guarantee_rate': detailed_stats.get('basic_stats', {}).get('guarantee_rate', 0),
                    'rarity_count': len(detailed_stats.get('rarity_distribution', {}).get('distribution', {}))
                }
            }
            
        except Exception as e:
            logger.error(f"性能比较失败: {str(e)}")
            return {'error': str(e)}

    async def update_user_blind_box_stats(self, user_id: int, blind_box_id: int, is_guaranteed: bool) -> None:
        """Update user blind box statistics

: Param user_id: user ID
: Param blind_box_id: blind box ID
: Param is_guaranteed: whether to trigger the guarantee"""
        try:
            # Query user blind box statistics
            stats = await self.user_blind_box_stats_crud.get_by_user_and_box(user_id, blind_box_id)
            
            if not stats:
                # Create a new statistical record if it does not exist
                new_stats = UserBlindBoxStatsCreate(
                    user_id=user_id,
                    blind_box_id=blind_box_id,
                    total_count=1,
                    current_count=1 if not is_guaranteed else 0,
                    last_guaranteed_time=datetime.now() if is_guaranteed else None,
                    creator_id=user_id
                )
                await self.user_blind_box_stats_crud.create(new_stats)
            else:
                # Existence update statistics
                update_data = {
                    "total_count": stats.total_count + 1,
                }
                
                if is_guaranteed:
                    # Trigger guarantee, reset count and record guarantee time
                    update_data["current_count"] = 0
                    update_data["last_guaranteed_time"] = datetime.now()
                else:
                    # Guarantee not triggered, increase count
                    update_data["current_count"] = stats.current_count + 1
                
                update_stats = UserBlindBoxStatsUpdate(**update_data)
                await self.user_blind_box_stats_crud.update_by_user_and_box(
                    user_id, blind_box_id, update_stats, user_id
                )
                
        except Exception as e:
            # Log when errors occur but do not interrupt the process
            logger.error(f"更新用户盲盒统计失败: {str(e)}")

    async def process_card_acquisition(self, user_id: int, card_id: int, obtain_type: str):
        """Process card acquisition logic
Add a new card, user_card, if the user_card card already exists, convert the repeated card to points. And indicate in the response body how many points the repeated card is converted to.
: Param user_id: user ID
: Param card_id: Card ID
: Param obtain_type: Obtain type (such as blind box, challenge, etc.)
: return: whether to repeat the acquisition, repeat the points"""
        # Check if the user already has the card
        existing_user_card = await self.user_card_crud.get_by_user_and_card(user_id, card_id)

        if existing_user_card:
            # Card repeats, converted to points
            card_info = await self.card_crud.get_by_id(card_id)
            if not card_info:
                raise HTTPException(status_code=404, detail=f"未找到ID为{card_id}的卡牌")

            duplicate_points = card_info.duplicate_points

            # Record integral changes
            if duplicate_points > 0:
                await self.card_service.reward_challenge_points(
                    user_id=user_id,
                    card_id=card_id,
                    points=duplicate_points
                )
            return True, duplicate_points
        else:
            # New card, added to user card list
            try:
                user_card = UserCardCreate(
                    user_id=user_id,
                    card_id=card_id,
                    obtain_type=obtain_type,
                    obtain_time=datetime.now(),
                    use_count=0,
                    is_favorite=False,
                    creator_id=user_id
                )
                await self.user_card_crud.create(user_card)
                return False, 0
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"添加用户卡牌失败: {str(e)}")

    async def process_limited_card(self, card: CardAlg, user_id: int) -> None:
        """Handling limited card logic
: param card: drawn card
: Param user_id: user ID"""
        try:
            # Check if it is a qualified card (is_limited is an integer in the database, 1 means a qualified card)
            if not hasattr(card, "is_limited") or card.is_limited != 1 or not hasattr(card, "limited_count") or not card.limited_count:
                return
                
            # Initialize qualification card statistics (if not present)
            existing_stats = await self.limited_card_stats_crud.get_by_card_id(card.id)
            
            if not existing_stats:
                # If no record exists, create a new record
                await self.limited_card_stats_crud.initialize_limited_card(
                    card_id=card.id,
                    limited_count=card.limited_count,
                    creator_id=user_id
                )
                
            # Update card draw status
            await self.limited_card_stats_crud.update_card_drawn(
                card_id=card.id,
                drawn_count=1,
                updater_id=user_id
            )
            
        except Exception as e:
            # Log errors without interrupting the process
            logger.error(f"处理限定卡片失败: {str(e)}")
            
    async def initialize_limited_cards(self, blind_box_id: int, creator_id: int) -> None:
        """Initialize all qualified card statistics in the blind box
Suitable for creating a blind box for the first time or adding a new limited card

: Param blind_box_id: blind box ID
: Param creator_id: creator ID"""
        try:
            # Acquire all cards in the blind box
            cards = await self.blind_box_crud.get_blind_box_cards(blind_box_id)
            
            # Filter out qualified cards (is_limited is an integer in the database, 1 means a qualified card)
            limited_cards = [card for card in cards 
                            if hasattr(card, "is_limited") and card.is_limited == 1 
                            and hasattr(card, "limited_count") and card.limited_count]
            
            # Create statistical records for each limited card
            for card in limited_cards:
                existing = await self.limited_card_stats_crud.get_by_card_id(card.id)
                if not existing:
                    await self.limited_card_stats_crud.initialize_limited_card(
                        card_id=card.id,
                        limited_count=card.limited_count,
                        creator_id=creator_id
                    )
                    logger.info(f"已初始化限定卡{card.id}({card.name})的统计记录，限定数量: {card.limited_count}")
                    
        except Exception as e:
            logger.error(f"初始化限定卡片统计失败: {str(e)}")
