"""The LLM model uses recorded database operations"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple, Union, TYPE_CHECKING

from sqlmodel import Session, select, func, and_, or_
from sqlalchemy import desc
from fastapi_pagination.ext.sqlalchemy import paginate

from knowledge_api.mapper.base_crud import BaseCRUD
from knowledge_api.mapper.llm_usage_records.base import (
    LLMUsageRecord,
    LLMUsageRecordCreate,
    LLMUsageRecordUpdate,
    LLMUsageRecordFilter,
    LLMUsageRecordStats,
    LLMUsageRecordResponse
)

if TYPE_CHECKING:
    from knowledge_api.mapper.llm_usage_records.base import LLMUsageRecordFilter


class LLMUsageRecordCRUD(BaseCRUD[LLMUsageRecord, LLMUsageRecordCreate, LLMUsageRecordUpdate, LLMUsageRecordFilter, LLMUsageRecordResponse, int]):
    """The LLM model uses recorded CRUD operations"""
    
    def __init__(self, db: Session):
        """Initialize the LLM model using record CRUD operations"""
        super().__init__(db, LLMUsageRecord)
    
    # Backwards compatible with primitive API call methods
    async def get_by_id(self, id=None, record_id=None) -> Optional[LLMUsageRecord]:
        """Get records by ID

Args:
ID: record ID
record_id: Record ID (compatible with old API)

Returns:
Optional [LLMUsageRecord]: Found record or None"""
        # Using record_id as Alternative Parameters
        _id = id if id is not None else record_id
        return await super().get_by_id(_id)
    
    async def create_from_response(
        self, 
        response_data: Dict[str, Any], 
        vendor_type: str,
        model_id: str,
        application_scenario: Optional[str] = None,
        related_record_id: Optional[str] = None
    ) -> LLMUsageRecord:
        """Create usage records from LLM response data

Args:
response_data: LLM Response Data
vendor_type: Supplier Type
model_id: Model ID
application_scenario: Application Scenarios
related_record_id: Associated Record ID

Returns:
LLMUsageRecord: created record"""
        # Handling common LLM response formats
        content = response_data.get("content", "")
        input_tokens = response_data.get("input_tokens", 0)
        output_tokens = response_data.get("output_tokens", 0)
        total_tokens = response_data.get("total_tokens", input_tokens + output_tokens)
        role = response_data.get("role", "assistant")
        finish_reason = response_data.get("finish_reason", "stop")
        elapsed_time = response_data.get("elapsed_time", 0.0)
        request_id = response_data.get("id", None)
        total_price = response_data.get("total_price", Decimal("0.00000000"))
        
        # Create record
        record = LLMUsageRecordCreate(
            request_id=request_id,
            vendor_type=vendor_type,
            model_id=model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            application_scenario=application_scenario,
            content=content,
            role=role,
            finish_reason=finish_reason,
            elapsed_time=elapsed_time,
            related_record_id=related_record_id,
            total_price=total_price
        )
        
        return await self.create(record)
    
    async def get_by_request_id(self, request_id: str) -> Optional[LLMUsageRecord]:
        """Get records by request ID

Args:
request_id: Request ID

Returns:
Optional [LLMUsageRecord]: Found record or None"""
        records = await self.get_all(filters={"request_id": request_id}, limit=1)
        return records[0] if records else None
    
    def _apply_filters_to_query(self, query, filter_data: Dict[str, Any]):
        """Apply Filter Criteria to Queries

Args:
Query: Query object
filter_data: Filter Criteria

Returns:
Query objects with filter conditions applied"""
        if "vendor_type" in filter_data and filter_data["vendor_type"]:
            query = query.filter(self.model.vendor_type == filter_data["vendor_type"])
        
        if "model_id" in filter_data and filter_data["model_id"]:
            query = query.filter(self.model.model_id == filter_data["model_id"])
        
        if "application_scenario" in filter_data and filter_data["application_scenario"]:
            query = query.filter(self.model.application_scenario == filter_data["application_scenario"])
        
        if "related_record_id" in filter_data and filter_data["related_record_id"]:
            query = query.filter(self.model.related_record_id == filter_data["related_record_id"])
        
        if "start_date" in filter_data and filter_data["start_date"]:
            query = query.filter(self.model.created_at >= filter_data["start_date"])
        
        if "end_date" in filter_data and filter_data["end_date"]:
            # Add a day so that end_date contains all records for the day
            end_date = filter_data["end_date"] + timedelta(days=1)
            query = query.filter(self.model.created_at < end_date)
        
        if "min_tokens" in filter_data and filter_data["min_tokens"]:
            query = query.filter(self.model.total_tokens >= filter_data["min_tokens"])
        
        if "max_tokens" in filter_data and filter_data["max_tokens"]:
            query = query.filter(self.model.total_tokens <= filter_data["max_tokens"])
            
        return query
    
    async def filter_records_paginated(self, filters: LLMUsageRecordFilter):
        """Filter records by condition (paged version)

Args:
Filters: filter criteria

Returns:
Records after paging filter"""
        return await self.filter_paginated(filters)
    
    async def get_statistics(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        vendor_type: Optional[str] = None,
        model_id: Optional[str] = None,
        application_scenario: Optional[str] = None
    ) -> LLMUsageRecordStats:
        """Get usage statistics

Args:
start_date: Start Date
end_date: End date
vendor_type: Supplier Type
model_id: Model ID
application_scenario: Application Scenarios

Returns:
LLMUsageRecordStats: Statistics"""
        # Build query conditions
        conditions = []
        if start_date:
            conditions.append(LLMUsageRecord.created_at >= start_date)
        if end_date:
            # Add a day so that end_date contains all records for the day
            end_date = end_date + timedelta(days=1)
            conditions.append(LLMUsageRecord.created_at < end_date)
        if vendor_type:
            conditions.append(LLMUsageRecord.vendor_type == vendor_type)
        if model_id:
            conditions.append(LLMUsageRecord.model_id == model_id)
        if application_scenario:
            conditions.append(LLMUsageRecord.application_scenario == application_scenario)
            
        # Basic Statistical Query
        if conditions:
            where_clause = and_(*conditions)
            base_query = select(
                func.count().label("total_records"),
                func.sum(LLMUsageRecord.input_tokens).label("total_input_tokens"),
                func.sum(LLMUsageRecord.output_tokens).label("total_output_tokens"),
                func.sum(LLMUsageRecord.total_tokens).label("total_tokens"),
                func.sum(LLMUsageRecord.total_price).label("total_price"),
                func.avg(LLMUsageRecord.elapsed_time).label("average_elapsed_time")
            ).where(where_clause)
        else:
            base_query = select(
                func.count().label("total_records"),
                func.sum(LLMUsageRecord.input_tokens).label("total_input_tokens"),
                func.sum(LLMUsageRecord.output_tokens).label("total_output_tokens"),
                func.sum(LLMUsageRecord.total_tokens).label("total_tokens"),
                func.sum(LLMUsageRecord.total_price).label("total_price"),
                func.avg(LLMUsageRecord.elapsed_time).label("average_elapsed_time")
            )
            
        base_result = self.db.exec(base_query).one()
        
        # Group statistics by model
        if conditions:
            model_query = select(
                LLMUsageRecord.model_id,
                func.count().label("count"),
                func.sum(LLMUsageRecord.total_tokens).label("total_tokens"),
                func.sum(LLMUsageRecord.total_price).label("total_price")
            ).where(where_clause).group_by(LLMUsageRecord.model_id)
        else:
            model_query = select(
                LLMUsageRecord.model_id,
                func.count().label("count"),
                func.sum(LLMUsageRecord.total_tokens).label("total_tokens"),
                func.sum(LLMUsageRecord.total_price).label("total_price")
            ).group_by(LLMUsageRecord.model_id)
            
        model_results = self.db.exec(model_query).all()
        records_by_model = {}
        for m in model_results:
            records_by_model[m.model_id] = {
                "count": m.count,
                "total_tokens": m.total_tokens or 0,
                "total_price": float(m.total_price or 0)
            }
            
        # Group statistics by supplier
        if conditions:
            vendor_query = select(
                LLMUsageRecord.vendor_type,
                func.count().label("count"),
                func.sum(LLMUsageRecord.total_tokens).label("total_tokens"),
                func.sum(LLMUsageRecord.total_price).label("total_price")
            ).where(where_clause).group_by(LLMUsageRecord.vendor_type)
        else:
            vendor_query = select(
                LLMUsageRecord.vendor_type,
                func.count().label("count"),
                func.sum(LLMUsageRecord.total_tokens).label("total_tokens"),
                func.sum(LLMUsageRecord.total_price).label("total_price")
            ).group_by(LLMUsageRecord.vendor_type)
            
        vendor_results = self.db.exec(vendor_query).all()
        records_by_vendor = {}
        for v in vendor_results:
            records_by_vendor[v.vendor_type] = {
                "count": v.count,
                "total_tokens": v.total_tokens or 0,
                "total_price": float(v.total_price or 0)
            }
            
        # Construct statistical results
        stats = LLMUsageRecordStats(
            total_records=base_result.total_records or 0,
            total_input_tokens=base_result.total_input_tokens or 0,
            total_output_tokens=base_result.total_output_tokens or 0,
            total_tokens=base_result.total_tokens or 0,
            total_price=base_result.total_price or Decimal("0.00000000"),
            average_elapsed_time=base_result.average_elapsed_time or 0.0,
            records_by_model=records_by_model,
            records_by_vendor=records_by_vendor
        )
        
        return stats
    
    async def get_daily_statistics(
        self,
        days: int = 30,
        vendor_type: Optional[str] = None,
        model_id: Optional[str] = None
    ) -> Dict[str, Dict]:
        """Acquire daily statistics

Args:
Days: statistical days
vendor_type: Supplier Type
model_id: Model ID

Returns:
Dict [str, Dict]: Statistics grouped by date"""
        # Calculate start date
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Build query conditions
        conditions = [LLMUsageRecord.created_at >= start_date, LLMUsageRecord.created_at <= end_date]
        if vendor_type:
            conditions.append(LLMUsageRecord.vendor_type == vendor_type)
        if model_id:
            conditions.append(LLMUsageRecord.model_id == model_id)
            
        # Group statistics by date
        if self.db.bind.dialect.name == 'sqlite':
            # SQLite date formatting
            date_func = func.strftime("%Y-%m-%d", LLMUsageRecord.created_at)
        elif self.db.bind.dialect.name == 'postgresql':
            # PostgreSQL date formatting
            date_func = func.to_char(LLMUsageRecord.created_at, "YYYY-MM-DD")
        else:
            # Date formatting for MySQL and other databases
            date_func = func.date_format(LLMUsageRecord.created_at, "%Y-%m-%d")
            
        # Query daily statistics
        query = select(
            date_func.label("date"),
            func.count().label("count"),
            func.sum(LLMUsageRecord.input_tokens).label("input_tokens"),
            func.sum(LLMUsageRecord.output_tokens).label("output_tokens"),
            func.sum(LLMUsageRecord.total_tokens).label("total_tokens"),
            func.sum(LLMUsageRecord.total_price).label("total_price"),
            func.avg(LLMUsageRecord.elapsed_time).label("avg_elapsed_time")
        ).where(and_(*conditions)).group_by(date_func).order_by(date_func)
        
        results = self.db.exec(query).all()
        
        # Construct statistical results
        stats_by_date = {}
        for r in results:
            stats_by_date[r.date] = {
                "count": r.count,
                "input_tokens": r.input_tokens or 0,
                "output_tokens": r.output_tokens or 0,
                "total_tokens": r.total_tokens or 0,
                "total_price": float(r.total_price or 0),
                "avg_elapsed_time": r.avg_elapsed_time or 0.0
            }
            
        return stats_by_date 