import random
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime

from knowledge_api.mapper.card.base import CardBase, CardAlg
from sqlmodel import Field


class BlindBoxEngine:
    """Blind Box Drawing Engine"""

    def __init__(self, random_seed: Optional[int] = None):
        """Initialize the blind box engine

Args:
random_seed: Random seeds, used for test when results are reproduced"""
        self.random = random.Random(random_seed)
        self.db_crud = None  # Database CRUD instance, requires external injection

    def set_db_crud(self, crud_instance):
        """Setting up a database CRUD instance

Args:
crud_instance: BlindBoxRecordCRUD instance"""
        self.db_crud = crud_instance

    def draw_card(self,
                  blind_box_id: int,
                  user_id: int,
                  cards: List[CardAlg],
                  probability_rules: Dict[str, Any],
                  draw_records: List[Dict[str, Any]],
                  sold_out_card_ids: List[int] = None) -> Tuple[CardAlg, bool]:
        """Draw Cards

Args:
blind_box_id: blind box ID
user_id: User ID
Cards: List of all cards under the blind box
probability_rules: Probability Rules
draw_records: Extract a list of records (used to calculate guaranteed status)
sold_out_card_ids: List of sold out card IDs

Returns:
(Whether the drawn card triggers the guarantee)"""

        # 1. Filter out sold-out cards
        available_cards = self._filter_available_cards(cards, sold_out_card_ids or [])

        if not available_cards:
            raise ValueError("No cards to draw")

        # 2. Calculate guaranteed status based on extracted records
        user_stats = self._calculate_guarantee_status_from_records(
            draw_records, probability_rules
        )
        print(f"[DEBUG] 基于抽取记录计算的用户统计: {user_stats}")

        # 3. Check the guarantee mechanism
        print(f"[DEBUG] 开始检查保底，当前抽取记录数量: {len(draw_records)}")
        is_guaranteed, guaranteed_rarity = self._check_guarantee_optimized(
            probability_rules, user_stats
        )

        # 4. If the guarantee is triggered, filter the cards corresponding to the rarity
        if is_guaranteed:
            print(f"[DEBUG] 触发保底，保底稀有度: {guaranteed_rarity}")
            eligible_cards = [card for card in available_cards if card.rarity >= guaranteed_rarity]
            if not eligible_cards:
                print(f"[DEBUG] 没有稀有度>={guaranteed_rarity}的卡牌，使用所有可用卡牌")
                eligible_cards = available_cards  # If there is no card corresponding to rarity, choose from the available cards
            else:
                print(f"[DEBUG] 筛选出{len(eligible_cards)}张稀有度>={guaranteed_rarity}的卡牌")
        else:
            print(f"[DEBUG] 未触发保底，使用正常概率")
            eligible_cards = available_cards

        # 5. Calculate probabilities based on weights and extract them
        selected_card = self._weighted_random_select(eligible_cards, probability_rules)

        print(f"[DEBUG] 抽中卡牌: {selected_card.name}(ID:{selected_card.id}, 稀有度:{selected_card.rarity}), 保底:{is_guaranteed}")
        return selected_card, is_guaranteed

    def _filter_available_cards(self,
                                cards: List[CardAlg],
                                sold_out_card_ids: List[int]) -> List[CardAlg]:
        """Filter available cards (excluding sold-out cards)"""
        return [card for card in cards if card.id not in sold_out_card_ids]

    def _calculate_guarantee_status_from_records(self, 
                                                 draw_records: List[Dict[str, Any]], 
                                                 probability_rules: Dict[str, Any]) -> Dict[str, Any]:
        """Recalculate the guaranteed state according to the extraction records

Args:
draw_records: Extract a list of records, each record contains:
- card_id: Card ID
- rarity: Card rarity
- is_guaranteed: Is it a guaranteed trigger?
- create_time: Extraction time
probability_rules: Probability Rules

Returns:
Calculated user statistics"""
        guarantee_rule = probability_rules.get('guarantee_rule', {})
        if not guarantee_rule.get('enabled', False):
            return {'current_count': len(draw_records), 'total_count': len(draw_records)}

        rules = guarantee_rule.get('rules', [])
        total_count = len(draw_records)
        
        # Dynamic processing of all guarantee rules
        guarantee_status = {}
        
        for rule in rules:
            rarity = rule['guarantee_rarity']
            interval = rule['count']
            
            # Calculate the number of times from the next guarantee (based on the total number of draws)
            remainder = total_count % interval
            
            if remainder == 0 and total_count > 0:
                # Just completed one cycle (the guarantee has just been triggered), and the next guarantee needs a complete interval.
                remaining_for_next = interval
            else:
                # In the middle of the cycle, calculate the number of times the distance is guaranteed next time
                remaining_for_next = interval - remainder
            
            guarantee_status[f'rarity_{rarity}_total_count'] = total_count
            guarantee_status[f'rarity_{rarity}_next_guarantee'] = remaining_for_next
            guarantee_status[f'rarity_{rarity}_interval'] = interval
            guarantee_status[f'rarity_{rarity}_description'] = rule.get('description', f'稀有度{rarity}保底')
        
        return {
            'current_count': total_count,
            'total_count': total_count,
            'guarantee_status': guarantee_status,
            'last_guaranteed_time': None
        }

    def _check_guarantee_optimized(self,
                                   probability_rules: Dict[str, Any],
                                   user_stats: Dict[str, Any]) -> Tuple[bool, int]:
        """Guarantee mechanism inspection

Guaranteed logic:
- Rare every 10 draws (10th, 20th, 30th, 40th, etc.)
- Epic every 50 draws (50th, 100th, 150th, etc.)
- Legends will be drawn every 100 draws (100th, 200th, 300th, etc.)
- Judging based on the total number of draws, rather than the number of times from the last high rarity"""
        
        guarantee_rule = probability_rules.get('guarantee_rule', {})
        if not guarantee_rule.get('enabled', False):
            return False, 0

        # Use detailed guarantee status
        guarantee_status = user_stats.get('guarantee_status', {})
        return self._check_guarantee_with_detailed_status(guarantee_rule, guarantee_status)

    def _check_guarantee_with_detailed_status(self,
                                              guarantee_rule: Dict[str, Any],
                                              guarantee_status: Dict[str, Any]) -> Tuple[bool, int]:
        """Guaranteed inspection based on detailed status"""
        
        rules = guarantee_rule.get('rules', [])
        # Dynamic sorting rules by rarity (from high to low), priority is given to checking high rarity guarantees
        rules_sorted = sorted(rules, key=lambda x: x['guarantee_rarity'], reverse=True)
        
        print(f"[DEBUG] 检查保底状态: {guarantee_status}")
        print(f"[DEBUG] 保底规则排序（按稀有度从高到低）: {[(r['guarantee_rarity'], r['count']) for r in rules_sorted]}")
        
        for rule in rules_sorted:
            rarity = rule['guarantee_rarity']
            interval = rule['count']
            
            total_count_key = f'rarity_{rarity}_total_count'
            
            total_count = guarantee_status.get(total_count_key, 0)
            
            print(f"[DEBUG] 稀有度{rarity}: 总抽取{total_count}次, 间隔{interval}")
            
            # Check if the guarantee conditions are met: the upcoming extraction happens to be the guarantee point
            if (total_count + 1) % interval == 0:
                print(f"[DEBUG] 触发保底! 稀有度{rarity}, 原因: (total_count + 1) % interval == 0, {total_count + 1} % {interval} == 0")
                return True, rarity
        
        print(f"[DEBUG] 未触发保底")
        return False, 0

    def get_next_guarantee_info(self,
                                draw_records: List[Dict[str, Any]],
                                probability_rules: Dict[str, Any]) -> Dict[str, Any]:
        """Get the next guarantee information.

Returns:
A dictionary containing information on the next guarantee for each rarity"""
        user_stats = self._calculate_guarantee_status_from_records(draw_records, probability_rules)
        guarantee_status = user_stats.get('guarantee_status', {})
        
        guarantee_rule = probability_rules.get('guarantee_rule', {})
        rules = guarantee_rule.get('rules', [])
        
        next_guarantee_info = {}
        total_count = len(draw_records)
        
        # Dynamic processing of all guarantee rules
        for rule in rules:
            rarity = rule['guarantee_rarity']
            interval = rule['count']
            
            # Calculate how many more times it will take for the next guarantee
            remainder = total_count % interval
            
            if remainder == 0 and total_count > 0:
                # Just completed one cycle (the guarantee has just been triggered), and the next guarantee needs a complete interval.
                remaining_for_next = interval
            else:
                # In the middle of the cycle, calculate the number of times the distance is guaranteed next time
                remaining_for_next = interval - remainder
            
            next_guarantee_info[f'rarity_{rarity}'] = {
                'rarity': rarity,
                'interval': interval,
                'total_count': total_count,
                'next_guarantee_in': remaining_for_next,
                'description': rule.get('description', f'稀有度{rarity}保底')
            }
        
        return next_guarantee_info

    def _weighted_random_select(self,
                                cards: List[CardAlg],
                                probability_rules: Dict[str, Any]) -> CardAlg:
        """Randomly select cards according to weight"""

        # Calculate the actual weight of each card
        weighted_cards = []
        total_weight = 0

        weight_calculation = probability_rules.get('weight_calculation', {})
        rarity_multiplier = weight_calculation.get('rarity_multiplier', {})
        
        # Acquire all possible rarities for dynamic processing
        available_rarities = set(card.rarity for card in cards)
        print(f"[DEBUG] 可用卡牌稀有度: {sorted(available_rarities)}")
        print(f"[DEBUG] 配置的稀有度倍率: {rarity_multiplier}")

        for card in cards:
            # Get the rarity magnification dynamically, use the default value of 1.0 if not configured
            multiplier = rarity_multiplier.get(str(card.rarity), 1.0)
            actual_weight = card.weight * multiplier

            weighted_cards.append((card, actual_weight))
            total_weight += actual_weight
            
            print(f"[DEBUG] 卡牌{card.name}(稀有度{card.rarity}): 基础权重{card.weight} × 倍率{multiplier} = 实际权重{actual_weight}")

        print(f"[DEBUG] 总权重: {total_weight}")

        # Random selection
        random_value = self.random.uniform(0, total_weight)
        current_weight = 0

        for card, weight in weighted_cards:
            current_weight += weight
            if random_value <= current_weight:
                return card

        # If something unexpected happens, return the last card
        return weighted_cards[-1][0]

    def calculate_probability_display(self,
                                      cards: List[CardAlg],
                                      probability_rules: Dict[str, Any]) -> Dict[int, float]:
        """Calculate and display the draw probability of each card (for front-end display)"""

        total_weight = 0
        card_weights = {}
        rarity_multiplier = probability_rules.get('weight_calculation', {}).get('rarity_multiplier', {})

        # Calculate the total weight
        for card in cards:
            multiplier = rarity_multiplier.get(str(card.rarity), 1.0)
            actual_weight = card.weight * multiplier
            card_weights[card.id] = actual_weight
            total_weight += actual_weight

        # Calculate probability
        probabilities = {}
        for card_id, weight in card_weights.items():
            probabilities[card_id] = (weight / total_weight) * 100  # Convert to percentage

        return probabilities

    def validate_probability_rules(self, probability_rules: Dict[str, Any], cards: List[CardAlg]) -> Dict[str, Any]:
        """Verify and optimize probabilistic rule configurations

Args:
probability_rules: Probability Rules
Cards: Card List

Returns:
Validation results and recommendations"""
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'suggestions': []
        }
        
        # 1. Verify the guarantee rules
        guarantee_rule = probability_rules.get('guarantee_rule', {})
        if guarantee_rule.get('enabled', False):
            rules = guarantee_rule.get('rules', [])
            
            # Acquire all rarities in the card
            card_rarities = set(card.rarity for card in cards)
            
            # Acquire the rarity in the guaranteed rule
            guarantee_rarities = set(rule['guarantee_rarity'] for rule in rules)
            
            # Check if the guaranteed rarity exists in the card
            for rarity in guarantee_rarities:
                matching_cards = [card for card in cards if card.rarity >= rarity]
                if not matching_cards:
                    validation_result['errors'].append(
                        f"保底稀有度{rarity}没有对应的卡牌（稀有度>={rarity}）"
                    )
                    validation_result['is_valid'] = False
            
            # Check the rationality of the guarantee interval
            for rule in rules:
                if rule['count'] <= 0:
                    validation_result['errors'].append(
                        f"保底间隔不能小于等于0: {rule}"
                    )
                    validation_result['is_valid'] = False
        
        # 2. Verify weight configuration
        weight_calculation = probability_rules.get('weight_calculation', {})
        rarity_multiplier = weight_calculation.get('rarity_multiplier', {})
        
        # Gets the actual rarity present in the card
        card_rarities = set(card.rarity for card in cards)
        configured_rarities = set(int(k) for k in rarity_multiplier.keys() if k.isdigit())
        
        # Check for missing rarity configurations
        missing_rarities = card_rarities - configured_rarities
        if missing_rarities:
            validation_result['warnings'].append(
                f"以下稀有度缺少权重倍率配置，将使用默认值1.0: {sorted(missing_rarities)}"
            )
        
        # Check for redundant rarity configurations
        extra_rarities = configured_rarities - card_rarities
        if extra_rarities:
            validation_result['suggestions'].append(
                f"以下稀有度配置了权重倍率但卡牌中不存在: {sorted(extra_rarities)}"
            )
        
        # 3. Check the rationality of the weight allocation
        for rarity_str, multiplier in rarity_multiplier.items():
            if not isinstance(multiplier, (int, float)) or multiplier < 0:
                validation_result['errors'].append(
                    f"稀有度{rarity_str}的权重倍率无效: {multiplier}，必须是非负数"
                )
                validation_result['is_valid'] = False
        
        return validation_result

    def generate_dynamic_probability_rules(self, 
                                           cards: List[CardAlg],
                                           guarantee_intervals: Dict[int, int] = None,
                                           rarity_weights: Dict[int, float] = None) -> Dict[str, Any]:
        """Dynamically generate probability rules based on card data

Args:
Cards: Card List
guarantee_intervals: Custom Guaranteed Interval {Rarity: Number of Intervals}
rarity_weights: Custom Rarity Weight {Rarity: Weight Magnification}

Returns:
Dynamically Generated Probability Rules"""
        # Acquire all existing rarities in the card
        available_rarities = sorted(set(card.rarity for card in cards))
        
        print(f"[INFO] 检测到的稀有度: {available_rarities}")
        
        # Default guaranteed interval policy
        default_intervals = {
            1: None,  # Ordinary card has no guarantee.
            2: 10,    # Rare Card 10 Draw Guaranteed
            3: 30,    # Epic Card 30 Draw Guarantee  
            4: 100,   # Legend Card 100 draw guarantee
            5: 500,   # Emperor Card 500 draw guarantee
            6: 1000,  # Myth Card 1000 draw guarantee
            7: 2000,  # Supreme Card 2000 draw guarantee
        }
        
        # Default weight magnification strategy (the higher the rarity, the lower the weight)
        default_weights = {
            1: 1.0,     # regular card
            2: 0.4,     # Rare Card
            3: 0.08,    # Epic Card
            4: 0.01,    # Legend Card
            5: 0.001,   # Emperor Card
            6: 0.0001,  # Myth Card
            7: 0.00001, # Supreme Card
        }
        
        # Use custom configuration or default configuration
        intervals = guarantee_intervals or {}
        weights = rarity_weights or {}
        
        # Generate guaranteed rules
        guarantee_rules = []
        rarity_names = {
            1: "ordinary", 2: "rare", 3: "epic", 4: "legend", 
            5: "Emperor", 6: "myth", 7: "Supreme"
        }
        
        for rarity in available_rarities:
            if rarity == 1:  # Ordinary cards are usually not guaranteed.
                continue
                
            interval = intervals.get(rarity, default_intervals.get(rarity))
            if interval:
                rule = {
                    "count": interval,
                    "guarantee_rarity": rarity,
                    "description": f"{interval}抽必出{rarity_names.get(rarity, f'稀有度{rarity}')}"
                }
                guarantee_rules.append(rule)
        
        # generation weight magnification configuration
        rarity_multiplier = {}
        for rarity in available_rarities:
            weight = weights.get(rarity, default_weights.get(rarity, 1.0))
            rarity_multiplier[str(rarity)] = weight
        
        # Building a complete probability rule
        probability_rules = {
            "probability_type": "weight_based",
            "guarantee_rule": {
                "enabled": len(guarantee_rules) > 0,
                "type": "progressive",
                "rules": guarantee_rules
            },
            "weight_calculation": {
                "method": "card_weight",
                "rarity_multiplier": rarity_multiplier
            }
        }
        
        print(f"[INFO] 生成的保底规则: {len(guarantee_rules)}条")
        for rule in guarantee_rules:
            print(f"  - {rule['description']}")
        
        print(f"[INFO] 生成的权重倍率: {rarity_multiplier}")
        
        return probability_rules

    async def draw_card_with_sql_optimization(self,
                                              blind_box_id: int,
                                              user_id: int,
                                              cards: List[CardAlg],
                                              probability_rules: Dict[str, Any],
                                              sold_out_card_ids: Optional[List[int]] = None) -> Tuple[CardAlg, bool]:
        """Drawing methods optimized using SQL

Args:
blind_box_id: blind box ID
user_id: User ID
Cards: List of cards that can be drawn
probability_rules: Probability Rules
sold_out_card_ids: List of sold out card IDs

Returns:
(The selected card, whether it is guaranteed to trigger)"""
        if not self.db_crud:
            raise ValueError("The database CRUD instance is not set, please call the set_db_crud () method first")

        # Phase 1: Data Preprocessing
        available_cards = self._filter_available_cards(cards, sold_out_card_ids)
        if not available_cards:
            raise ValueError("No cards available")

        # Phase 2: Efficient access to extracted records and guaranteed state through SQL
        draw_records = await self.db_crud.get_recent_draws_for_algorithm(
            user_id=user_id,
            blind_box_id=blind_box_id,
            limit=120
        )

        # The third stage: guarantee judgment
        guarantee_rule = probability_rules.get('guarantee_rule', {})
        is_guaranteed = False
        guarantee_rarity = 0

        if guarantee_rule.get('enabled', False):
            user_stats = self._calculate_guarantee_status_from_records(draw_records, probability_rules)
            guarantee_status = user_stats.get('guarantee_status', {})
            is_guaranteed, guarantee_rarity = self._check_guarantee_with_detailed_status(guarantee_rule, guarantee_status)

        # Stage 4: Card Pool Screening
        if is_guaranteed:
            candidate_cards = [card for card in available_cards if card.rarity >= guarantee_rarity]
            if not candidate_cards:
                candidate_cards = available_cards
                is_guaranteed = False
                print(f"[WARNING] 没有满足保底稀有度{guarantee_rarity}的卡牌，使用全部卡牌池")
        else:
            candidate_cards = available_cards

        # The fifth stage: random weight selection
        selected_card = self._weighted_random_select(candidate_cards, probability_rules)

        return selected_card, is_guaranteed

    async def get_next_guarantee_info_sql(self,
                                          user_id: int,
                                          blind_box_id: int,
                                          probability_rules: Dict[str, Any]) -> Dict[str, Any]:
        """Use SQL optimization to get the next guarantee information

Args:
user_id: User ID
blind_box_id: blind box ID
probability_rules: Probability Rules

Returns:
Next guarantee information"""
        if not self.db_crud:
            raise ValueError("Database CRUD instance not set up")

        guarantee_rule = probability_rules.get('guarantee_rule', {})
        if not guarantee_rule.get('enabled', False):
            return {}

        rules = guarantee_rule.get('rules', [])
        return await self.db_crud.calculate_next_guarantee_by_sql(
            user_id=user_id,
            blind_box_id=blind_box_id,
            guarantee_rules=rules
        )

    async def get_user_draw_statistics_sql(self,
                                           user_id: int,
                                           blind_box_id: int) -> Dict[str, Any]:
        """Using SQL optimization to obtain user extraction statistics

Args:
user_id: User ID
blind_box_id: blind box ID

Returns:
User Extraction Statistics"""
        if not self.db_crud:
            raise ValueError("Database CRUD instance not set up")

        # Acquire comprehensive statistical information
        algorithm_stats = await self.db_crud.get_algorithm_statistics(user_id, blind_box_id)
        
        # Obtain the rarity distribution
        rarity_distribution = await self.db_crud.get_rarity_distribution_by_sql(user_id, blind_box_id)
        
        # Get Guaranteed Trigger History
        guarantee_history = await self.db_crud.get_guarantee_trigger_history(user_id, blind_box_id)
        
        return {
            'basic_stats': algorithm_stats,
            'rarity_distribution': rarity_distribution,
            'guarantee_history': guarantee_history
        }

    async def validate_guarantee_mechanism_sql(self,
                                               user_id: int,
                                               blind_box_id: int,
                                               probability_rules: Dict[str, Any]) -> Dict[str, Any]:
        """Verify the correctness of the guarantee mechanism using SQL

Args:
user_id: User ID
blind_box_id: blind box ID
probability_rules: Probability Rules

Returns:
validation result"""
        if not self.db_crud:
            raise ValueError("Database CRUD instance not set up")

        guarantee_rule = probability_rules.get('guarantee_rule', {})
        if not guarantee_rule.get('enabled', False):
            return {'is_valid': True, 'message': 'The guarantee mechanism is not enabled'}

        rules = guarantee_rule.get('rules', [])
        
        # Get Guaranteed Trigger History
        guarantee_history = await self.db_crud.get_guarantee_trigger_history(user_id, blind_box_id, limit=100)
        
        # Get the total number of draws
        stats = await self.db_crud.get_algorithm_statistics(user_id, blind_box_id)
        total_draws = stats['total_draws']
        
        validation_results = []
        
        for rule in rules:
            interval = rule['count']
            rarity = rule['guarantee_rarity']
            
            # Calculate the expected number of guarantees
            expected_guarantees = total_draws // interval
            
            # Calculate the actual guarantee number (this rarity and above)
            actual_guarantees = len([
                h for h in guarantee_history 
                if h['rarity'] >= rarity
            ])
            
            # Verify key guarantee points
            key_points = [i * interval for i in range(1, (total_draws // interval) + 1)]
            missed_guarantees = []
            
            for point in key_points:
                # Check if there is a guaranteed trigger at this point.
                point_guarantees = [
                    h for h in guarantee_history 
                    if h['draw_sequence'] == point and h['rarity'] >= rarity
                ]
                if not point_guarantees:
                    missed_guarantees.append(point)
            
            validation_results.append({
                'rule': rule,
                'expected_guarantees': expected_guarantees,
                'actual_guarantees': actual_guarantees,
                'is_valid': actual_guarantees >= expected_guarantees and len(missed_guarantees) == 0,
                'missed_points': missed_guarantees
            })
        
        overall_valid = all(result['is_valid'] for result in validation_results)
        
        return {
            'is_valid': overall_valid,
            'total_draws': total_draws,
            'validation_details': validation_results,
            'message': 'The guarantee mechanism has passed the verification.' if overall_valid else 'There is a problem with the guarantee mechanism'
        }

