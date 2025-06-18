"""Generic CRUD operation base class

This base class provides general database CRUD manipulation capabilities, supporting different models and schema types.
Subclasses simply inherit from this class and specify the corresponding model and schema types to obtain the underlying CRUD functionality."""
from typing import Generic, TypeVar, Type, List, Optional, Union, Dict, Any
from datetime import datetime
from sqlmodel import Session, select, desc, func
from fastapi_pagination.ext.sqlmodel import paginate
from fastapi_pagination import Page
from pydantic import BaseModel
from sqlmodel import SQLModel


# Define generic type variables
ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
FilterSchemaType = TypeVar("FilterSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)
IdType = TypeVar("IdType", int, str)


class BaseCRUD(Generic[ModelType, CreateSchemaType, UpdateSchemaType, FilterSchemaType, ResponseSchemaType, IdType]):
    """Generic CRUD base class

Provides common database operation methods, including create, read, update, delete, and paging queries.
Subclasses can override these methods to provide specific business logic.

Generic parameters:
ModelType: SQLModel Type
CreateSchemaType: The schema type for creating data
UpdateSchemaType: Update the schema type of the data
FilterSchemaType: The schema type of the filter condition
ResponseSchemaType: The schema type of the response data
IdType: ID type (int or str)"""
    
    def __init__(self, db: Session, model: Type[ModelType]):
        """Initialize CRUD operation

Args:
DB: database session
Model: Model class for operation"""
        self.db = db
        self.model = model
    
    async def create(self, obj_in: CreateSchemaType, **kwargs) -> ModelType:
        """Create a new record

Args:
obj_in: Creating schema instances of data
** kwargs: Additional field value that will overwrite the field with the same name in the obj_in

Returns:
ModelType: Created record"""
        # Convert input schema to dict
        obj_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in.model_dump()
        
        # Add extra kwargs
        if kwargs:
            obj_data.update(kwargs)
        
        # Create model instance
        db_obj = self.model(**obj_data)
        
        # Add to database and submit
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    async def get_by_id(self, id: IdType) -> Optional[ModelType]:
        """Get records by ID

Args:
ID: record ID

Returns:
Optional [ModelType]: Record found or None"""
        statement = select(self.model).where(self.model.id == id)
        result = self.db.exec(statement).first()
        return result
    
    async def get_all(self, 
                     skip: int = 0, 
                     limit: int = 100, 
                     filters: Optional[Dict[str, Any]] = None,
                     order_by: Optional[str] = None,
                     order_desc: bool = True) -> List[ModelType]:
        """Get all records, support filtering and sorting

Args:
Skip: skip the number of records
Limit: limit the number of records
Filters: filter conditions, such as {"field": value}
order_by: Sort Fields
order_desc: Whether to sort in descending order

Returns:
List [ModelType]: List of records"""
        # Create query
        statement = select(self.model)
        
        # Apply filter conditions
        if filters:
            statement = self._apply_filters(statement, filters)
        
        # app paging
        statement = statement.offset(skip).limit(limit)
        
        # app sort
        if order_by and hasattr(self.model, order_by):
            if order_desc:
                statement = statement.order_by(desc(getattr(self.model, order_by)))
            else:
                statement = statement.order_by(getattr(self.model, order_by))
        # Default sort
        elif hasattr(self.model, 'create_time'):
            statement = statement.order_by(desc(self.model.create_time))
        elif hasattr(self.model, 'created_at'):
            statement = statement.order_by(desc(self.model.created_at))
            
        # Execute Query
        results = self.db.exec(statement).all()
        return results
    
    async def get_all_paginated(self, 
                               filters: Optional[Dict[str, Any]] = None,
                               order_by: Optional[str] = None,
                               order_desc: bool = True) -> Page:
        """Get all records (paginated version), support filtering and sorting

Args:
Filters: filter conditions, such as {"field": value}
order_by: Sort Fields
order_desc: Whether to sort in descending order

Returns:
Page: paging records"""
        # Create query
        query = select(self.model)
        
        # Apply filter conditions
        if filters:
            query = self._apply_filters(query, filters)
        
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
            
        return paginate(self.db, query)
    
    async def update(self, id: IdType, obj_in: UpdateSchemaType) -> Optional[ModelType]:
        """update record

Args:
ID: record ID
obj_in: schema instance for updating data

Returns:
Optional [ModelType]: Updated Record or None"""
        db_obj = await self.get_by_id(id=id)
        if db_obj is None:
            return None
            
        # Get updated data to exclude unset fields
        update_data = obj_in.dict(exclude_unset=True) if hasattr(obj_in, 'dict') else obj_in.model_dump(exclude_unset=True)
        
        # Update object properties
        for key, value in update_data.items():
            setattr(db_obj, key, value)
        
        # If there are update_time fields, update automatically
        if hasattr(db_obj, 'update_time'):
            db_obj.update_time = datetime.now()
        elif hasattr(db_obj, 'updated_at'):
            db_obj.updated_at = datetime.now()
            
        # commit changes
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
    
    async def delete(self, id: IdType) -> bool:
        """delete record

Args:
ID: record ID

Returns:
Bool: successfully deleted"""
        db_obj = await self.get_by_id(id=id)
        if db_obj is None:
            return False
            
        self.db.delete(db_obj)
        self.db.commit()
        return True
    
    async def filter(self, filters: Union[FilterSchemaType, Dict[str, Any]], skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Filter records by condition

Args:
Filters: Filter conditions, which can be FilterSchemaType instances or dictionaries
Skip: skip the number of records
Limit: limit the number of records

Returns:
List [ModelType]: List of filtered records"""
        # Create query
        query = select(self.model)
        
        # Convert filter to dict
        if isinstance(filters, dict):
            filter_data = filters
        else:
            filter_data = filters.dict() if hasattr(filters, 'dict') else filters.model_dump()
        
        # Apply filter conditions
        query = self._apply_filters(query, filter_data)
        
        # app paging
        query = query.offset(skip).limit(limit)
        
        # Default sort
        if hasattr(self.model, 'create_time'):
            query = query.order_by(desc(self.model.create_time))
        elif hasattr(self.model, 'created_at'):
            query = query.order_by(desc(self.model.created_at))
            
        results = self.db.exec(query).all()
        return results
    
    async def filter_paginated(self, filters: Union[FilterSchemaType, Dict[str, Any]]) -> Page:
        """Filter records by condition (paged version)

Args:
Filters: Filter conditions, which can be FilterSchemaType instances or dictionaries

Returns:
Page: Page filtered records"""
        # Create query
        query = select(self.model)
        
        # Convert filter to dict
        if isinstance(filters, dict):
            filter_data = filters
        else:
            filter_data = filters.dict() if hasattr(filters, 'dict') else filters.model_dump()
        
        # Apply filter conditions
        query = self._apply_filters(query, filter_data)
        
        # Default sort
        if hasattr(self.model, 'create_time'):
            query = query.order_by(desc(self.model.create_time))
        elif hasattr(self.model, 'created_at'):
            query = query.order_by(desc(self.model.created_at))
            
        return paginate(self.db, query)
    
    def _apply_filters(self, query, filter_data: Dict[str, Any]):
        """Apply Filter Criteria to Queries

Subclasses should override this method to implement specific filtering logic

Args:
Query: SQLModel query object
filter_data: Filter Dictionary

Returns:
Query objects to which filter criteria have been applied"""
        # Basic implementation: Apply only exact matching conditions that are not None
        for field, value in filter_data.items():
            if value is not None and hasattr(self.model, field):
                query = query.where(getattr(self.model, field) == value)
        return query
    
    def _apply_filters_to_query(self, query, filter_data: Dict[str, Any]):
        """Apply filter criteria to SQLAlchemy query

Subclasses should override this method to implement specific filtering logic

Args:
Query: SQLAlchemy query object
filter_data: Filter Dictionary

Returns:
Query objects to which filter criteria have been applied"""
        # Basic implementation: Apply only exact matching conditions that are not None
        for field, value in filter_data.items():
            if value is not None and hasattr(self.model, field):
                query = query.filter(getattr(self.model, field) == value)
        return query
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Calculate the total number of records and support filter conditions

Args:
Filters: filter conditions, such as {"field": value}

Returns:
Int: Total number of records"""
        statement = select(func.count()).select_from(self.model)
        
        # Apply filter conditions
        if filters:
            for field, value in filters.items():
                if value is not None and hasattr(self.model, field):
                    statement = statement.where(getattr(self.model, field) == value)
                    
        result = self.db.exec(statement).one()
        return result[0] 