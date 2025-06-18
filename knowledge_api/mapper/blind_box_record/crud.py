from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from sqlmodel import Session, select, col, func, and_, join, text

from knowledge_api.mapper.base_crud import BaseCRUD, IdType
from knowledge_api.mapper.blind_box_record.base import BlindBoxRecord, BlindBoxRecordCreate, BlindBoxRecordUpdate
from knowledge_api.mapper.card.base import Card


class BlindBoxRecordCRUD(BaseCRUD[BlindBoxRecord, BlindBoxRecordCreate, BlindBoxRecordUpdate, Dict[str, Any], BlindBoxRecord, int]):
    def __init__(self, db_session: Session):
        """Initialize blind box extraction record CRUD operation"""
        super().__init__(db_session, BlindBoxRecord)

    async def get_by_user_id(self, user_id: int, limit: int = 100) -> List[BlindBoxRecord]:
        """Get all blind box extraction records for the user"""
        stmt = select(self.model).where(col(self.model.user_id) == user_id).order_by(col(self.model.create_time).desc()).limit(limit)
        return self.db.exec(stmt).all()

    async def get_by_user_id_with_card_details(self, user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtain all blind box draw records from the user, including card details"""
        # Connect blind box record table and card table
        stmt = select(
            self.model,
            Card
        ).join(
            Card, 
            self.model.card_id == Card.id
        ).where(
            col(self.model.user_id) == user_id
        ).order_by(
            col(self.model.create_time).desc()
        ).limit(limit)
        
        results = self.db.exec(stmt).all()
        
        # Process the result, combining the data from the two tables into a dictionary
        combined_results = []
        for record, card in results:
            record_dict = record.model_dump()
            card_dict = card.model_dump()
            
            # Add card details
            record_dict["card_detail"] = card_dict
            
            combined_results.append(record_dict)
            
        return combined_results

    async def get_by_blind_box_id(self, blind_box_id: int, limit: int = 100) -> List[BlindBoxRecord]:
        """Obtain all extraction records for a specific blind box"""
        stmt = select(self.model).where(col(self.model.blind_box_id) == blind_box_id).order_by(col(self.model.create_time).desc()).limit(limit)
        return self.db.exec(stmt).all()

    async def get_by_user_and_blind_box(self, user_id: int, blind_box_id: int, limit: int = 100) -> List[BlindBoxRecord]:
        """Obtain all extraction records for a user-specific blind box"""
        stmt = select(self.model).where(
            (col(self.model.user_id) == user_id) &
            (col(self.model.blind_box_id) == blind_box_id)
        ).order_by(col(self.model.create_time).desc()).limit(limit)
        return self.db.exec(stmt).all()

    async def get_by_card_id(self, card_id: int, limit: int = 100) -> List[BlindBoxRecord]:
        """Obtain all draw records for a specific card"""
        stmt = select(self.model).where(col(self.model.card_id) == card_id).order_by(col(self.model.create_time).desc()).limit(limit)
        return self.db.exec(stmt).all()

    async def get_by_source_type(self, source_type: str, limit: int = 100) -> List[BlindBoxRecord]:
        """Get all extracted records for a specific source type"""
        stmt = select(self.model).where(col(self.model.source_type) == source_type).order_by(col(self.model.create_time).desc()).limit(limit)
        return self.db.exec(stmt).all()

    async def get_by_user_and_source_type(self, user_id: int, source_type: str, limit: int = 100) -> List[BlindBoxRecord]:
        """Get all extracted records for a user's specific source type"""
        stmt = select(self.model).where(
            (col(self.model.user_id) == user_id) &
            (col(self.model.source_type) == source_type)
        ).order_by(col(self.model.create_time).desc()).limit(limit)
        return self.db.exec(stmt).all()

    async def get_guaranteed_records(self, user_id: Optional[int] = None, limit: int = 100) -> List[BlindBoxRecord]:
        """Get the extraction record triggered by the guarantee"""
        if user_id:
            stmt = select(self.model).where(
                (col(self.model.is_guaranteed) == True) &
                (col(self.model.user_id) == user_id)
            ).order_by(col(self.model.create_time).desc()).limit(limit)
        else:
            stmt = select(self.model).where(
                col(self.model.is_guaranteed) == True
            ).order_by(col(self.model.create_time).desc()).limit(limit)
        return self.db.exec(stmt).all()

    async def get_special_rewards(self, user_id: Optional[int] = None, limit: int = 100) -> List[BlindBoxRecord]:
        """Draw records for special rewards"""
        if user_id:
            stmt = select(self.model).where(
                (col(self.model.is_special_reward) == True) &
                (col(self.model.user_id) == user_id)
            ).order_by(col(self.model.create_time).desc()).limit(limit)
        else:
            stmt = select(self.model).where(
                col(self.model.is_special_reward) == True
            ).order_by(col(self.model.create_time).desc()).limit(limit)
        return self.db.exec(stmt).all()

    async def update(self, record_id: int, record_update: BlindBoxRecordUpdate) -> Optional[BlindBoxRecord]:
        """Update blind box extraction records"""
        db_record = await self.get_by_id(record_id)
        if not db_record:
            return None
        
        update_data = record_update.dict(exclude_unset=True) if hasattr(record_update, 'dict') else record_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_record, key, value)
        
        self.db.add(db_record)
        self.db.commit()
        self.db.refresh(db_record)
        return db_record

    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Obtain user blind box extraction statistics"""
        # Get the total number of draws
        total_count_stmt = select(func.count()).select_from(self.model).where(col(self.model.user_id) == user_id)
        total_count = self.db.exec(total_count_stmt).one() or 0
        
        # Get the number of times for each source type
        source_count_stmt = select(self.model.source_type, func.count().label("count")).select_from(self.model).where(
            col(self.model.user_id) == user_id
        ).group_by(self.model.source_type)
        source_counts = {row[0]: row[1] for row in self.db.exec(source_count_stmt).all()}
        
        # Acquire the number of repetitions and points earned
        duplicate_stats_stmt = select(
            func.sum(self.model.is_duplicate).label("duplicate_count"), 
            func.sum(self.model.points_gained).label("total_points")
        ).select_from(self.model).where(col(self.model.user_id) == user_id)
        duplicate_stats = self.db.exec(duplicate_stats_stmt).first()
        duplicate_count = duplicate_stats[0] or 0
        total_points_gained = duplicate_stats[1] or 0
        
        # Get the number of guaranteed triggers
        guaranteed_count_stmt = select(func.count()).select_from(self.model).where(
            and_(col(self.model.user_id) == user_id, col(self.model.is_guaranteed) == True)
        )
        guaranteed_count = self.db.exec(guaranteed_count_stmt).one() or 0
        
        # Number of special rewards obtained
        special_count_stmt = select(func.count()).select_from(self.model).where(
            and_(col(self.model.user_id) == user_id, col(self.model.is_special_reward) == True)
        )
        special_count = self.db.exec(special_count_stmt).one() or 0
        
        # Get the number of draws for each blind box
        box_count_stmt = select(self.model.blind_box_id, func.count().label("count")).select_from(self.model).where(
            col(self.model.user_id) == user_id
        ).group_by(self.model.blind_box_id)
        box_counts = {row[0]: row[1] for row in self.db.exec(box_count_stmt).all()}
        
        return {
            "total_count": total_count,
            "source_counts": source_counts,
            "duplicate_count": duplicate_count,
            "duplicate_rate": (duplicate_count / total_count) if total_count > 0 else 0,
            "total_points_gained": total_points_gained,
            "guaranteed_count": guaranteed_count,
            "guaranteed_rate": (guaranteed_count / total_count) if total_count > 0 else 0,
            "special_count": special_count,
            "special_rate": (special_count / total_count) if total_count > 0 else 0,
            "box_counts": box_counts,
        }

    async def get_latest_records_by_user(self, user_id: int, limit: int = 10) -> List[BlindBoxRecord]:
        """Get the user's most recent extraction record"""
        stmt = select(self.model).where(col(self.model.user_id) == user_id).order_by(col(self.model.create_time).desc()).limit(limit)
        return self.db.exec(stmt).all()

    async def get_card_draw_count(self, card_id: int) -> int:
        """Get the total number of draws for a specific card"""
        stmt = select(func.count()).select_from(self.model).where(col(self.model.card_id) == card_id)
        return self.db.exec(stmt).one() or 0

    async def get_guarantee_status_by_sql(self, user_id: int, blind_box_id: int, limit: int = 120) -> Dict[str, Any]:
        """Efficiently calculate the user's guaranteed status through SQL

Args:
user_id: User ID
blind_box_id: blind box ID
Limit: Query the number of recent records (default 120)

Returns:
Dictionary containing guaranteed status information"""
        query = text("""
            WITH recent_records AS (
                SELECT 
                    id,
                    card_id,
                    is_guaranteed,
                    create_time,
                    ROW_NUMBER() OVER (ORDER BY create_time DESC) as row_num
                FROM blind_box_record 
                WHERE user_id = :user_id 
                    AND blind_box_id = :blind_box_id
                ORDER BY create_time DESC
                LIMIT :limit
            ),
            card_rarities AS (
                SELECT 
                    rr.id,
                    rr.card_id,
                    rr.is_guaranteed,
                    rr.create_time,
                    rr.row_num,
                    c.rarity
                FROM recent_records rr
                JOIN card c ON rr.card_id = c.id
            ),
            rarity_stats AS (
                SELECT 
                    rarity,
                    COUNT(*) as count,
                    MAX(CASE WHEN is_guaranteed = 1 THEN row_num ELSE NULL END) as last_guaranteed_position
                FROM card_rarities
                GROUP BY rarity
            )
            SELECT 
                (SELECT COUNT(*) FROM recent_records) as total_count,
                (SELECT JSON_OBJECTAGG(
                    CONCAT('rarity_', rarity), 
                    JSON_OBJECT(
                        'count', count,
                        'last_guaranteed_position', COALESCE(last_guaranteed_position, 999999)
                    )
                ) FROM rarity_stats) as rarity_stats,
                (SELECT create_time FROM recent_records WHERE row_num = 1) as last_draw_time
        """)
        
        result = self.db.exec(query.bindparams(
            user_id=user_id,
            blind_box_id=blind_box_id,
            limit=limit
        )).first()
        
        if not result:
            return {
                'total_count': 0,
                'rarity_stats': {},
                'last_draw_time': None
            }
        
        return {
            'total_count': result.total_count or 0,
            'rarity_stats': result.rarity_stats or {},
            'last_draw_time': result.last_draw_time
        }

    async def get_rarity_distribution_by_sql(self, user_id: int, blind_box_id: int, limit: int = 120) -> Dict[str, Any]:
        """Statistics on the rarity distribution of users through SQL

Args:
user_id: User ID
blind_box_id: blind box ID
Limit: Query the number of recent records

Returns:
rarity distribution statistics"""
        query = text("""
            WITH recent_records AS (
                SELECT 
                    bbr.card_id,
                    bbr.is_guaranteed,
                    bbr.create_time,
                    c.rarity,
                    c.name as card_name
                FROM blind_box_record bbr
                JOIN card c ON bbr.card_id = c.id
                WHERE bbr.user_id = :user_id 
                    AND bbr.blind_box_id = :blind_box_id
                ORDER BY bbr.create_time DESC
                LIMIT :limit
            )
            SELECT 
                rarity,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM recent_records), 2) as percentage,
                SUM(CASE WHEN is_guaranteed = 1 THEN 1 ELSE 0 END) as guaranteed_count,
                GROUP_CONCAT(DISTINCT card_name ORDER BY card_name) as card_names
            FROM recent_records
            GROUP BY rarity
            ORDER BY rarity
        """)
        
        results = self.db.exec(query.bindparams(
            user_id=user_id,
            blind_box_id=blind_box_id,
            limit=limit
        )).all()
        
        distribution = {}
        total_count = sum(row.count for row in results)
        
        for row in results:
            distribution[f'rarity_{row.rarity}'] = {
                'rarity': row.rarity,
                'count': row.count,
                'percentage': row.percentage,
                'guaranteed_count': row.guaranteed_count,
                'card_names': row.card_names.split(',') if row.card_names else []
            }
        
        return {
            'total_count': total_count,
            'distribution': distribution
        }

    async def calculate_next_guarantee_by_sql(self, user_id: int, blind_box_id: int, 
                                              guarantee_rules: List[Dict[str, Any]], 
                                              limit: int = 120) -> Dict[str, Any]:
        """Calculate the next guarantee information through SQL

Args:
user_id: User ID
blind_box_id: blind box ID
guarantee_rules: List of Guarantee Rules [{"count": 10, "guarantee_rarity": 2},...]
Limit: Query the number of recent records

Returns:
Next guarantee information"""
        # Build a dynamic guaranteed rule query
        rule_cases = []
        for rule in guarantee_rules:
            interval = rule['count']
            rarity = rule['guarantee_rarity']
            rule_cases.append(f"""
                WHEN {rarity} THEN 
                    CASE 
                        WHEN total_count % {interval} = 0 AND total_count > 0 THEN {interval}
                        ELSE {interval} - (total_count % {interval})
                    END
            """)
        
        rule_cases_sql = '\n'.join(rule_cases)
        
        query = text(f"""
            WITH total_draws AS (
                SELECT COUNT(*) as total_count
                FROM blind_box_record 
                WHERE user_id = :user_id 
                    AND blind_box_id = :blind_box_id
            )
            SELECT 
                td.total_count,
                CASE 
                    {rule_cases_sql}
                    ELSE NULL
                END as next_guarantee_2,
                CASE 
                    {rule_cases_sql.replace('WHEN 2 THEN', 'WHEN 3 THEN')}
                    ELSE NULL
                END as next_guarantee_3,
                CASE 
                    {rule_cases_sql.replace('WHEN 2 THEN', 'WHEN 4 THEN')}
                    ELSE NULL
                END as next_guarantee_4,
                CASE 
                    {rule_cases_sql.replace('WHEN 2 THEN', 'WHEN 5 THEN')}
                    ELSE NULL
                END as next_guarantee_5
            FROM total_draws td
        """)
        
        result = self.db.exec(query.bindparams(
            user_id=user_id,
            blind_box_id=blind_box_id
        )).first()
        
        if not result:
            return {'total_count': 0, 'next_guarantees': {}}
        
        next_guarantees = {}
        for rule in guarantee_rules:
            rarity = rule['guarantee_rarity']
            attr_name = f'next_guarantee_{rarity}'
            if hasattr(result, attr_name):
                next_guarantees[f'rarity_{rarity}'] = {
                    'rarity': rarity,
                    'interval': rule['count'],
                    'next_guarantee_in': getattr(result, attr_name),
                    'description': rule.get('description', f'稀有度{rarity}保底')
                }
        
        return {
            'total_count': result.total_count,
            'next_guarantees': next_guarantees
        }

    async def get_recent_draws_for_algorithm(self, user_id: int, blind_box_id: int, limit: int = 120) -> List[Dict[str, Any]]:
        """Get the most recently extracted records for algorithm calculations (optimized version)

Args:
user_id: User ID
blind_box_id: blind box ID
Limit: Limit on number of records

Returns:
Formatted list of extracted records"""
        query = text("""
            SELECT 
                bbr.card_id,
                bbr.is_guaranteed,
                bbr.create_time,
                c.rarity,
                c.name as card_name
            FROM blind_box_record bbr
            JOIN card c ON bbr.card_id = c.id
            WHERE bbr.user_id = :user_id 
                AND bbr.blind_box_id = :blind_box_id
            ORDER BY bbr.create_time DESC
            LIMIT :limit
        """)
        
        results = self.db.exec(query.bindparams(
            user_id=user_id,
            blind_box_id=blind_box_id,
            limit=limit
        )).all()
        
        return [
            {
                "card_id": row.card_id,
                "rarity": row.rarity,
                "is_guaranteed": bool(row.is_guaranteed),
                "create_time": row.create_time.isoformat() if row.create_time else None,
                "card_name": row.card_name
            }
            for row in results
        ]

    async def get_guarantee_trigger_history(self, user_id: int, blind_box_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get guaranteed trigger history

Args:
user_id: User ID
blind_box_id: blind box ID
Limit: Limit on number of records

Returns:
Guaranteed trigger history"""
        query = text("""
            WITH numbered_records AS (
                SELECT 
                    bbr.id,
                    bbr.card_id,
                    bbr.is_guaranteed,
                    bbr.create_time,
                    c.rarity,
                    c.name as card_name,
                    ROW_NUMBER() OVER (ORDER BY bbr.create_time ASC) as draw_sequence
                FROM blind_box_record bbr
                JOIN card c ON bbr.card_id = c.id
                WHERE bbr.user_id = :user_id 
                    AND bbr.blind_box_id = :blind_box_id
                ORDER BY bbr.create_time ASC
            )
            SELECT 
                draw_sequence,
                card_id,
                card_name,
                rarity,
                is_guaranteed,
                create_time
            FROM numbered_records
            WHERE is_guaranteed = 1
            ORDER BY create_time DESC
            LIMIT :limit
        """)
        
        results = self.db.exec(query.bindparams(
            user_id=user_id,
            blind_box_id=blind_box_id,
            limit=limit
        )).all()
        
        return [
            {
                "draw_sequence": row.draw_sequence,
                "card_id": row.card_id,
                "card_name": row.card_name,
                "rarity": row.rarity,
                "is_guaranteed": bool(row.is_guaranteed),
                "create_time": row.create_time.isoformat() if row.create_time else None
            }
            for row in results
        ]

    async def get_algorithm_statistics(self, user_id: int, blind_box_id: int) -> Dict[str, Any]:
        """Obtain comprehensive statistical information related to the algorithm

Args:
user_id: User ID
blind_box_id: blind box ID

Returns:
Comprehensive statistical information"""
        query = text("""
            WITH draw_stats AS (
                SELECT 
                    COUNT(*) as total_draws,
                    SUM(CASE WHEN bbr.is_guaranteed = 1 THEN 1 ELSE 0 END) as total_guarantees,
                    MIN(bbr.create_time) as first_draw_time,
                    MAX(bbr.create_time) as last_draw_time
                FROM blind_box_record bbr
                WHERE bbr.user_id = :user_id 
                    AND bbr.blind_box_id = :blind_box_id
            ),
            rarity_stats AS (
                SELECT 
                    c.rarity,
                    COUNT(*) as count,
                    SUM(CASE WHEN bbr.is_guaranteed = 1 THEN 1 ELSE 0 END) as guaranteed_count,
                    ROUND(COUNT(*) * 100.0 / (SELECT total_draws FROM draw_stats), 2) as percentage
                FROM blind_box_record bbr
                JOIN card c ON bbr.card_id = c.id
                WHERE bbr.user_id = :user_id 
                    AND bbr.blind_box_id = :blind_box_id
                GROUP BY c.rarity
            )
            SELECT 
                ds.total_draws,
                ds.total_guarantees,
                ds.first_draw_time,
                ds.last_draw_time,
                ROUND(ds.total_guarantees * 100.0 / NULLIF(ds.total_draws, 0), 2) as guarantee_rate,
                (
                    SELECT JSON_OBJECTAGG(
                        CONCAT('rarity_', rarity),
                        JSON_OBJECT(
                            'count', count,
                            'guaranteed_count', guaranteed_count,
                            'percentage', percentage
                        )
                    )
                    FROM rarity_stats
                ) as rarity_distribution
            FROM draw_stats ds
        """)
        
        result = self.db.exec(query.bindparams(
            user_id=user_id,
            blind_box_id=blind_box_id
        )).first()
        
        if not result or result.total_draws == 0:
            return {
                'total_draws': 0,
                'total_guarantees': 0,
                'guarantee_rate': 0.0,
                'first_draw_time': None,
                'last_draw_time': None,
                'rarity_distribution': {}
            }
        
        return {
            'total_draws': result.total_draws,
            'total_guarantees': result.total_guarantees,
            'guarantee_rate': result.guarantee_rate or 0.0,
            'first_draw_time': result.first_draw_time.isoformat() if result.first_draw_time else None,
            'last_draw_time': result.last_draw_time.isoformat() if result.last_draw_time else None,
            'rarity_distribution': result.rarity_distribution or {}
        } 