from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlmodel import Session, select, func, and_, or_, desc
from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination import Page

from knowledge_api.mapper.base_crud import BaseCRUD
from .base import (
    PointRecord, PointRecordCreate, PointRecordUpdate, 
    PointRecordFilter, PointRecordResponse, PointRecordStatistics,
    PointChangeType, POINT_CHANGE_TYPE_DISPLAY
)
from knowledge_api.mapper.user_detail.crud import UserDetailCRUD
from knowledge_api.mapper.user_detail.base import UserDetailUpdate


class PointRecordCRUD(BaseCRUD[PointRecord, PointRecordCreate, PointRecordUpdate, PointRecordFilter, PointRecordResponse, int]):
    """Integral record CRUD operation class"""

    def __init__(self, db: Session):
        """Initialize integration record CRUD operation"""
        super().__init__(db, PointRecord)

    def _apply_filters(self, query, filter_data: Dict[str, Any]):
        """Apply filter conditions specific to integral records

Args:
Query: SQLModel query object
filter_data: Filter Dictionary

Returns:
Query objects to which filter criteria have been applied"""
        from sqlmodel import and_
        
        for field, value in filter_data.items():
            if value is None:
                continue
                
            if field == "min_amount":
                query = query.where(self.model.change_amount >= value)
            elif field == "max_amount":
                query = query.where(self.model.change_amount <= value)
            elif field == "start_time":
                query = query.where(self.model.create_time >= value)
            elif field == "end_time":
                query = query.where(self.model.create_time <= value)
            elif hasattr(self.model, field):
                # Handle exact matching of common fields
                query = query.where(getattr(self.model, field) == value)
                
        return query

    async def create(self, *, obj_in: PointRecordCreate, creator_id: Optional[int] = None) -> PointRecord:
        """Creating integral records (overriding base class methods, adding creator_id information)"""
        # Gets the creation data, using the default value of 0 if no creator_id is passed in (for system creation)
        create_data = obj_in.dict()
        if creator_id is not None:
            create_data["creator_id"] = creator_id
        else:
            # Set the default value of 0 to represent system creation
            create_data["creator_id"] = 0
            
        db_point_record = PointRecord(**create_data)
        self.db.add(db_point_record)
        self.db.commit()
        self.db.refresh(db_point_record)
        return db_point_record

    async def create_with_user_detail_update(
        self, 
        *, 
        obj_in: PointRecordCreate, 
        creator_id: Optional[int] = None
    ) -> PointRecord:
        """Create credit records and update user details synchronously"""
        # 1. Create a credit record
        point_record = await self.create(obj_in=obj_in, creator_id=creator_id)
        
        # 2. Synchronously update user details
        user_detail_crud = UserDetailCRUD(self.db)
        
        # Determine whether to increase or decrease the integral
        is_earned = obj_in.change_amount > 0
        
        # Update points in user details
        await user_detail_crud.update_points(
            user_id=obj_in.user_id,
            points_change=abs(obj_in.change_amount),
            is_earned=is_earned
        )
        
        return point_record

    async def get_user_point_records(
        self, 
        *, 
        user_id: int, 
        limit: int = 50,
        change_type: Optional[PointChangeType] = None
    ) -> List[PointRecordResponse]:
        """Get the user's points record"""
        query = select(self.model).where(self.model.user_id == user_id)
        
        if change_type:
            query = query.where(self.model.change_type == change_type)
        
        query = query.order_by(desc(self.model.create_time)).limit(limit)
        records = self.db.exec(query).all()
        
        # Convert to a responsive model
        return [self._to_response_model(record) for record in records]

    async def get_user_point_summary(self, *, user_id: int) -> Dict[str, Any]:
        """Get user points summary information"""
        # total revenue
        income_result = self.db.exec(
            select(func.sum(self.model.change_amount)).where(
                and_(
                    self.model.user_id == user_id,
                    self.model.change_amount > 0
                )
            )
        ).one()
        total_income = income_result or 0
        
        # total expenditure
        expense_result = self.db.exec(
            select(func.sum(self.model.change_amount)).where(
                and_(
                    self.model.user_id == user_id,
                    self.model.change_amount < 0
                )
            )
        ).one()
        total_expense = abs(expense_result or 0)
        
        # Total number of records
        total_records = self.db.exec(
            select(func.count(self.model.id)).where(self.model.user_id == user_id)
        ).one()
        
        # latest record
        latest_record = self.db.exec(
            select(self.model).where(self.model.user_id == user_id)
            .order_by(desc(self.model.create_time))
            .limit(1)
        ).first()
        
        return {
            "user_id": user_id,
            "total_income": total_income,
            "total_expense": total_expense,
            "net_change": total_income - total_expense,
            "total_records": total_records,
            "current_amount": latest_record.current_amount if latest_record else 0,
            "last_change_time": latest_record.create_time if latest_record else None
        }

    async def get_records_by_type(
        self, 
        *, 
        change_type: PointChangeType, 
        limit: int = 100,
        user_id: Optional[int] = None
    ) -> List[PointRecord]:
        """Get records by type of change"""
        query = select(self.model).where(self.model.change_type == change_type)
        
        if user_id:
            query = query.where(self.model.user_id == user_id)
        
        query = query.order_by(desc(self.model.create_time)).limit(limit)
        return self.db.exec(query).all()

    async def get_daily_statistics(
        self, 
        *, 
        start_date: datetime, 
        end_date: datetime,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get daily points stats"""
        from sqlmodel import text
        
        if user_id:
            query = text("""
                SELECT 
                    DATE(create_time) as date,
                    SUM(CASE WHEN change_amount > 0 THEN change_amount ELSE 0 END) as income,
                    SUM(CASE WHEN change_amount < 0 THEN ABS(change_amount) ELSE 0 END) as expense,
                    COUNT(id) as count
                FROM point_record 
                WHERE create_time >= :start_date 
                    AND create_time <= :end_date 
                    AND user_id = :user_id
                GROUP BY DATE(create_time)
                ORDER BY DATE(create_time)
            """)
            results = self.db.exec(query.bindparams(
                start_date=start_date,
                end_date=end_date,
                user_id=user_id
            )).all()
        else:
            query = text("""
                SELECT 
                    DATE(create_time) as date,
                    SUM(CASE WHEN change_amount > 0 THEN change_amount ELSE 0 END) as income,
                    SUM(CASE WHEN change_amount < 0 THEN ABS(change_amount) ELSE 0 END) as expense,
                    COUNT(id) as count
                FROM point_record 
                WHERE create_time >= :start_date 
                    AND create_time <= :end_date
                GROUP BY DATE(create_time)
                ORDER BY DATE(create_time)
            """)
            results = self.db.exec(query.bindparams(
                start_date=start_date,
                end_date=end_date
            )).all()
        
        return [
            {
                "date": result.date.isoformat(),
                "income": int(result.income or 0),
                "expense": int(result.expense or 0),
                "net": int((result.income or 0) - (result.expense or 0)),
                "count": result.count
            }
            for result in results
        ]

    async def get_type_distribution(
        self, 
        *, 
        user_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Obtain integral variation type distribution statistics"""
        from sqlmodel import text
        
        # Build dynamic query conditions
        where_conditions = []
        params = {}
        
        if user_id:
            where_conditions.append("user_id = :user_id")
            params["user_id"] = user_id
        if start_time:
            where_conditions.append("create_time >= :start_time")
            params["start_time"] = start_time
        if end_time:
            where_conditions.append("create_time <= :end_time")
            params["end_time"] = end_time
            
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        query = text(f"""
            SELECT 
                change_type,
                COUNT(id) as count,
                SUM(change_amount) as total_amount,
                AVG(change_amount) as avg_amount
            FROM point_record 
            {where_clause}
            GROUP BY change_type
            ORDER BY COUNT(id) DESC
        """)
        
        results = self.db.exec(query.bindparams(**params)).all()
        
        distribution = {}
        for result in results:
            distribution[result.change_type] = {
                "count": result.count,
                "total_amount": int(result.total_amount),
                "avg_amount": round(float(result.avg_amount), 2),
                "display_name": POINT_CHANGE_TYPE_DISPLAY.get(result.change_type, result.change_type)
            }
        
        return distribution

    async def get_statistics(
        self, 
        *, 
        user_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> PointRecordStatistics:
        """Get points record statistics"""
        from sqlmodel import text
        
        # Build dynamic query conditions
        where_conditions = []
        params = {}
        
        if user_id:
            where_conditions.append("user_id = :user_id")
            params["user_id"] = user_id
        if start_time:
            where_conditions.append("create_time >= :start_time")
            params["start_time"] = start_time
        if end_time:
            where_conditions.append("create_time <= :end_time")
            params["end_time"] = end_time
            
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Get all the basic statistics with a single query
        stats_query = text(f"""
            SELECT 
                COUNT(id) as total_records,
                SUM(CASE WHEN change_amount > 0 THEN change_amount ELSE 0 END) as total_income,
                SUM(CASE WHEN change_amount < 0 THEN ABS(change_amount) ELSE 0 END) as total_expense,
                AVG(ABS(change_amount)) as avg_change_amount
            FROM point_record 
            {where_clause}
        """)
        
        stats_result = self.db.exec(stats_query.bindparams(**params)).first()
        
        # Get the most common types of changes
        common_type_query = text(f"""
            SELECT change_type, COUNT(id) as count
            FROM point_record 
            {where_clause}
            GROUP BY change_type
            ORDER BY count DESC
            LIMIT 1
        """)
        
        common_type_result = self.db.exec(common_type_query.bindparams(**params)).first()
        most_common_type = common_type_result.change_type if common_type_result else ""
        
        # Get daily statistics (last 30 days)
        end_date = end_time or datetime.now()
        start_date = start_time or (end_date - timedelta(days=30))
        daily_stats = await self.get_daily_statistics(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id
        )
        
        # Get type distribution
        type_distribution = await self.get_type_distribution(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time
        )
        
        return PointRecordStatistics(
            total_records=stats_result.total_records,
            total_income=int(stats_result.total_income or 0),
            total_expense=int(stats_result.total_expense or 0),
            net_change=int((stats_result.total_income or 0) - (stats_result.total_expense or 0)),
            most_common_type=POINT_CHANGE_TYPE_DISPLAY.get(most_common_type, most_common_type),
            avg_change_amount=round(float(stats_result.avg_change_amount or 0), 2),
            daily_stats=daily_stats,
            type_distribution=type_distribution
        )

    async def batch_create_records(
        self, 
        *, 
        records: List[PointRecordCreate], 
        creator_id: Optional[int] = None
    ) -> List[PointRecord]:
        """Batch Creation of Credits"""
        created_records = []
        
        for record_data in records:
            # Use create_with_user_detail_update to ensure that user details are updated synchronously
            record = await self.create_with_user_detail_update(
                obj_in=record_data,
                creator_id=creator_id
            )
            created_records.append(record)
        
        return created_records

    async def get_all_paginated_response(self, 
                                       filters: Optional[Dict[str, Any]] = None,
                                       order_by: Optional[str] = None,
                                       order_desc: bool = True) -> Page[PointRecordResponse]:
        """Get all records (paged version) and return the response model

Args:
Filters: filter conditions, such as {"field": value}
order_by: Sort Fields
order_desc: Whether to sort in descending order

Returns:
Page [PointRecordResponse]: paging response record"""
        from fastapi_pagination import Params
        from fastapi_pagination.api import resolve_params
        from sqlmodel import func, desc
        
        # Get paging parameters
        params = resolve_params()
        
        # Create query
        query = select(self.model)
        count_query = select(func.count(self.model.id))
        
        # Apply filter conditions
        if filters:
            query = self._apply_filters(query, filters)
            count_query = self._apply_filters(count_query, filters)
        
        # app sort
        if order_by and hasattr(self.model, order_by):
            if order_desc:
                query = query.order_by(desc(getattr(self.model, order_by)))
            else:
                query = query.order_by(getattr(self.model, order_by))
        # Default sort
        elif hasattr(self.model, 'create_time'):
            query = query.order_by(desc(self.model.create_time))
        elif hasattr(self.model, 'created_at'):
            query = query.order_by(desc(self.model.created_at))
        
        # get total
        total = self.db.exec(count_query).one()
        
        # app paging
        query = query.offset((params.page - 1) * params.size).limit(params.size)
        
        # Execute Query
        items = self.db.exec(query).all()
        
        # Convert to a responsive model
        converted_items = [self._to_response_model(item) for item in items]
        
        # Manually Create Page Objects
        return Page(
            items=converted_items,
            total=total,
            page=params.page,
            size=params.size,
            pages=(total + params.size - 1) // params.size if total > 0 else 0
        )

    def _to_response_model(self, record: PointRecord) -> PointRecordResponse:
        """Convert to a responsive model"""
        # Build the data dictionary directly by hand to avoid complex judgment logic
        response_data = {
            "id": record.id,
            "user_id": record.user_id,
            "change_amount": record.change_amount,
            "current_amount": record.current_amount,
            "change_type": record.change_type,
            "related_id": record.related_id,
            "card_id": record.card_id,
            "description": record.description,
            "creator_id": record.creator_id,
            "create_time": record.create_time,
            # Add extension field
            "change_type_display": POINT_CHANGE_TYPE_DISPLAY.get(
                record.change_type, record.change_type
            ),
            "is_income": record.change_amount > 0
        }
        
        return PointRecordResponse(**response_data)

    async def get_top_earners(self, *, limit: int = 10, days: int = 30) -> List[Dict[str, Any]]:
        """Earn points to earn leaderboards (within a specified number of days)"""
        from sqlmodel import text
        start_date = datetime.now() - timedelta(days=days)
        
        query = text("""
            SELECT 
                user_id,
                SUM(change_amount) as total_earned
            FROM point_record 
            WHERE change_amount > 0 
                AND create_time >= :start_date
            GROUP BY user_id
            ORDER BY total_earned DESC
            LIMIT :limit
        """)
        
        results = self.db.exec(query.bindparams(
            start_date=start_date,
            limit=limit
        )).all()
        
        return [
            {
                "user_id": result.user_id,
                "total_earned": int(result.total_earned),
                "rank": idx + 1
            }
            for idx, result in enumerate(results)
        ]

    async def get_recent_large_transactions(
        self, 
        *, 
        min_amount: int = 1000, 
        limit: int = 20
    ) -> List[PointRecordResponse]:
        """Obtain recent large transactions"""
        from sqlmodel import text
        
        query = text("""
            SELECT * FROM point_record 
            WHERE ABS(change_amount) >= :min_amount
            ORDER BY create_time DESC
            LIMIT :limit
        """)
        
        results = self.db.exec(query.bindparams(
            min_amount=min_amount,
            limit=limit
        )).all()
        
        # Convert to a PointRecord object and then to a Response.
        records = [PointRecord(**dict(result._mapping)) for result in results]
        return [self._to_response_model(record) for record in records] 