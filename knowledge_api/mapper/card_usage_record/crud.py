from datetime import datetime
from typing import List, Optional, Dict, Any, Union

from sqlmodel import Session, select, col, func

from knowledge_api.mapper.base_crud import BaseCRUD, IdType
from knowledge_api.mapper.card_usage_record.base import CardUsageRecord, CardUsageRecordCreate, CardUsageRecordUpdate
from knowledge_api.mapper.card.base import Card


class CardUsageRecordCRUD(
    BaseCRUD[CardUsageRecord, CardUsageRecordCreate, CardUsageRecordUpdate, Dict[str, Any], CardUsageRecord, int]):
    def __init__(self, db_session: Session):
        """Initialize card usage record CRUD operation"""
        super().__init__(db_session, CardUsageRecord)

    async def get_by_user_id(self, user_id: int, limit: int = 100) -> List[CardUsageRecord]:
        """Get all the user's card usage records"""
        stmt = select(self.model).where(col(self.model.user_id) == user_id).order_by(
            col(self.model.create_time).desc()).limit(limit)
        return self.db.exec(stmt).all()

    async def get_by_card_id(self, card_id: int, limit: int = 100) -> List[CardUsageRecord]:
        """Obtain all usage records for a specific card"""
        stmt = select(self.model).where(col(self.model.card_id) == card_id).order_by(
            col(self.model.create_time).desc()).limit(limit)
        return self.db.exec(stmt).all()

    async def get_by_user_and_card(self, user_id: int, card_id: int, limit: int = 100) -> List[CardUsageRecord]:
        """Obtain all usage records for a user's specific card"""
        stmt = select(self.model).where(
            (col(self.model.user_id) == user_id) &
            (col(self.model.card_id) == card_id)
        ).order_by(col(self.model.create_time).desc()).limit(limit)
        return self.db.exec(stmt).all()

    async def get_by_usage_type(self, usage_type: str, limit: int = 100) -> List[CardUsageRecord]:
        """Get all records for a specific usage type"""
        stmt = select(self.model).where(col(self.model.usage_type) == usage_type).order_by(
            col(self.model.create_time).desc()).limit(limit)
        return self.db.exec(stmt).all()

    async def get_by_user_and_type(self, user_id: int, usage_type: str, limit: int = 100) -> List[CardUsageRecord]:
        """Get all usage records for a user's specific type"""
        stmt = select(self.model).where(
            (col(self.model.user_id) == user_id) &
            (col(self.model.usage_type) == usage_type)
        ).order_by(col(self.model.create_time).desc()).limit(limit)
        return self.db.exec(stmt).all()

    async def get_by_user_and_type_with_card_details(self, user_id: int, usage_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtain all usage records for a user's specific type, including card details"""
        # Connect the card usage record table and the card table
        stmt = select(
            self.model,
            Card
        ).join(
            Card, 
            self.model.card_id == Card.id
        ).where(
            (col(self.model.user_id) == user_id) &
            (col(self.model.usage_type) == usage_type)
        ).order_by(col(self.model.create_time).desc()).limit(limit)
        
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

    async def update(self, record_id: int, record_update: CardUsageRecordUpdate) -> Optional[CardUsageRecord]:
        """Update card usage record"""
        db_record = await self.get_by_id(record_id)
        if not db_record:
            return None

        update_data = record_update.dict(exclude_unset=True) if hasattr(record_update,
                                                                        'dict') else record_update.model_dump(
            exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_record, key, value)

        self.db.add(db_record)
        self.db.commit()
        self.db.refresh(db_record)
        return db_record

    async def update_end_time(self, record_id: int, end_time: datetime = None) -> Optional[CardUsageRecord]:
        """Update end time"""
        if end_time is None:
            end_time = datetime.now()

        db_record = await self.get_by_id(record_id)
        if not db_record:
            return None

        db_record.end_time = end_time
        self.db.add(db_record)
        self.db.commit()
        self.db.refresh(db_record)
        return db_record

    async def update_points_earned(self, record_id: int, points_earned: int) -> Optional[CardUsageRecord]:
        """Update earned points"""
        db_record = await self.get_by_id(record_id)
        if not db_record:
            return None

        db_record.points_earned = points_earned
        self.db.add(db_record)
        self.db.commit()
        self.db.refresh(db_record)
        return db_record

    async def update_game_status(self, related_id: str, game_status: int, user_id: int) -> Optional[CardUsageRecord]:
        """Update game status

Args:
related_id: Record ID
game_status: game status, 0 default status, 1 win, 2 lose
user_id: User ID

Returns:
The updated record, returning None if the record does not exist"""
        db_record = await self.get_by_id_user_id(related_id, user_id)
        if not db_record:
            return None

        db_record.game_status = game_status
        self.db.add(db_record)
        self.db.commit()
        self.db.refresh(db_record)
        return db_record

    async def update_blind_box_id(self, record_id: int, blind_box_id: int) -> Optional[CardUsageRecord]:
        """Update the obtained blind box ID.

Args:
record_id: Record ID
blind_box_id: blind box ID, -1 means no blind box was obtained

Returns:
The updated record, returning None if the record does not exist"""
        db_record = await self.get_by_id(record_id)
        if not db_record:
            return None

        db_record.blind_box_id = blind_box_id
        self.db.add(db_record)
        self.db.commit()
        self.db.refresh(db_record)
        return db_record

    async def update_blind_box_record_id(self, record_id: int, blind_box_record_id: int) -> Optional[CardUsageRecord]:
        """Update blind box record ID

Args:
record_id: Record ID
blind_box_record_id: Open blind box record ID

Returns:
The updated record, returning None if the record does not exist"""
        db_record = await self.get_by_id(record_id)
        if not db_record:
            return None

        db_record.blind_box_record_id = blind_box_record_id
        self.db.add(db_record)
        self.db.commit()
        self.db.refresh(db_record)
        return db_record

    async def update_game_status_bind_box(self, related_id: str,
                                          game_status: int,
                                          blind_box_id: int,
                                          user_id: int,
                                          blind_box_record_id: Optional[int] = None,
                                          points_earned:int=0,
                                          ) -> \
            Optional[
                CardUsageRecord]:
        """Update game status and blind box ID

Args:
related_id: Record ID
game_status: game status, 0 default status, 1 win, 2 lose
blind_box_id: blind box ID, -1 means no blind box was obtained
user_id: User ID
blind_box_record_id: Open blind box record ID, default is None
points_earned: Points earned, default is 0

Returns:
The updated record, returning None if the record does not exist"""
        db_record = await self.get_by_id_user_id(related_id, user_id)
        if not db_record:
            return None

        db_record.game_status = game_status
        db_record.blind_box_id = blind_box_id
        db_record.points_earned = points_earned
        if blind_box_record_id is not None:
            db_record.blind_box_record_id = blind_box_record_id
        db_record.end_time = datetime.now()
        self.db.add(db_record)
        self.db.commit()
        self.db.refresh(db_record)
        return db_record

    async def get_user_usage_stats(self, user_id: int) -> Dict[str, Any]:
        """Obtain user card usage statistics"""
        # Get total usage
        total_count_stmt = select(func.count()).select_from(self.model).where(col(self.model.user_id) == user_id)
        total_count = self.db.exec(total_count_stmt).one() or 0

        # Get the number of times for each usage type
        type_count_stmt = select(self.model.usage_type, func.count().label("count")).select_from(self.model).where(
            col(self.model.user_id) == user_id
        ).group_by(self.model.usage_type)
        type_counts = {row[0]: row[1] for row in self.db.exec(type_count_stmt).all()}

        # Get the total points earned
        total_points_stmt = select(func.sum(self.model.points_earned)).select_from(self.model).where(
            (col(self.model.user_id) == user_id) &
            (col(self.model.points_earned) != None)
        )
        total_points = self.db.exec(total_points_stmt).one() or 0

        # Get the number of times each card is used
        card_count_stmt = select(self.model.card_id, func.count().label("count")).select_from(self.model).where(
            col(self.model.user_id) == user_id
        ).group_by(self.model.card_id)
        card_counts = {row[0]: row[1] for row in self.db.exec(card_count_stmt).all()}

        return {
            "total_count": total_count,
            "type_counts": type_counts,
            "total_points": total_points,
            "card_counts": card_counts,
        }

    async def get_by_related_id(self, related_id: Union[str, int], limit: int = 1) -> List[CardUsageRecord]:
        """Obtain card usage records through relevant IDs

Args:
related_id: Related ID (like session ID, etc.)
Limit: Returns the maximum number of records

Returns:
List of eligible card usage records"""
        stmt = select(self.model).where(col(self.model.related_id) == related_id).order_by(
            col(self.model.create_time).desc()).limit(limit)
        return self.db.exec(stmt).all()

    async def update_game_status_by_related_id(self, related_id: Union[str, int], game_status: int) -> List[
        CardUsageRecord]:
        """Update game status with relevant ID

Args:
related_id: Related ID (e.g. Session ID, Challenge ID, etc.)
game_status: game status, 0 default status, 1 win, 2 lose

Returns:
Updated record list"""
        records = await self.get_by_related_id(related_id)
        updated_records = []

        for record in records:
            record.game_status = game_status
            self.db.add(record)
            updated_records.append(record)

        if updated_records:
            self.db.commit()
            for record in updated_records:
                self.db.refresh(record)

        return updated_records

    async def update_blind_box_by_related_id(self, related_id: Union[str, int], blind_box_id: int) -> List[
        CardUsageRecord]:
        """Update blind box ID with relevant ID

Args:
related_id: Related ID (e.g. Session ID, Challenge ID, etc.)
blind_box_id: blind box ID, -1 means no blind box was obtained

Returns:
Updated record list"""
        records = await self.get_by_related_id(related_id)
        updated_records = []

        for record in records:
            record.blind_box_id = blind_box_id
            self.db.add(record)
            updated_records.append(record)

        if updated_records:
            self.db.commit()
            for record in updated_records:
                self.db.refresh(record)

        return updated_records

    async def get_by_id_user_id(self, related_id: str, user_id: int) -> Optional[CardUsageRecord]:
        """Obtain card usage records by record ID and user ID

Args:
related_id: Related ID (e.g. Session ID, Challenge ID, etc.)
user_id: User ID

Returns:
The latest card usage record that meets the conditions, returning None if it does not exist"""
        stmt = select(self.model).where(
            (col(self.model.related_id) == related_id) &
            (col(self.model.user_id) == user_id)
        ).order_by(col(self.model.create_time).desc()).limit(1)
        result = self.db.exec(stmt).first()
        return result

    async def get_victory_records_by_user(self, user_id: int, limit: int = 20, offset: int = 0) -> List[CardUsageRecord]:
        """Get a list of user victories

Args:
user_id: User ID
Limit: limit the number of records returned
Offset: Offset

Returns:
List of user victorious challenge records"""
        stmt = select(self.model).where(
            (self.model.user_id == user_id) &
            (self.model.game_status == 1)  # The victory status is 1.
        ).order_by(
            self.model.create_time.desc()
        ).offset(offset).limit(limit)
        
        return self.db.exec(stmt).all()
    
    async def count_victory_records_by_user(self, user_id: int) -> int:
        """Count the number of challenges won by users

Args:
user_id: User ID

Returns:
Number of challenges won by users"""
        from sqlmodel import func
        
        stmt = select(func.count()).where(
            (self.model.user_id == user_id) &
            (self.model.game_status == 1)  # The victory status is 1.
        )
        
        return self.db.exec(stmt).one()
