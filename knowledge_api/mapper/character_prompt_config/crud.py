# crud.py
from sqlmodel import Session, select
from typing import Optional, List, Dict, Any
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import paginate

from knowledge_api.mapper.base_crud import BaseCRUD
from knowledge_api.mapper.character_prompt_config.base import (
    CharacterPromptConfig,
    CharacterPromptConfigCreate,
    CharacterPromptConfigUpdate,
    CharacterPromptConfigResponse
)
from runtime import ExecutionTimer


class CharacterPromptConfigCRUD(BaseCRUD[CharacterPromptConfig, CharacterPromptConfigCreate, CharacterPromptConfigUpdate, Dict[str, Any], CharacterPromptConfigResponse, int]):
    """Role prompt word configuration CRUD operation"""

    def __init__(self, db: Session):
        """Initialize Role Hint Configure CRUD Operation"""
        super().__init__(db, CharacterPromptConfig)

    async def get_by_id(self, id: int = None, config_id: int = None) -> Optional[CharacterPromptConfig]:
        """Get prompt word configuration by ID

Args:
Id: Configuration ID (parameter name compatible with base class)
config_id: Configuration ID (parameter name used by the original code)

Returns:
Optional [CharacterPromptConfig]: Found cue word configuration or None"""
        # Use any of the ID parameters passed in
        actual_id = id if id is not None else config_id
        if actual_id is None:
            return None
            
        # Call base class method
        return await super().get_by_id(actual_id)

    async def get_by_role_id(self, role_id: str) -> List[CharacterPromptConfig]:
        """Get prompt word configuration based on role ID

Args:
role_id: Role ID

Returns:
List [CharacterPromptConfig]: Prompt word configuration list"""
        return await self.get_all(filters={"role_id": role_id})

    async def get_all_cache(self) -> List[CharacterPromptConfig]:
        """Get all configurations (no pagination)

Returns:
List [CharacterPromptConfig]: All prompt word configurations"""
        return await self.get_all(limit=10000)

    async def get_all(self, 
                     *,
                     role_ids: List[str] = None, 
                     types: list[str] = None, 
                     skip: int = 0, 
                     limit: int = 100,
                     filters: Optional[Dict[str, Any]] = None,
                     order_by: Optional[str] = None,
                     order_desc: bool = True) -> List[CharacterPromptConfig]:
        """Get all prompt word configurations

Args:
role_ids: Role ID list for filtering
Types: List of types for filtering
Skip: skip the number of records
Limit: limit the number of records
Filters: filter conditions, such as {"field": value}
order_by: Sort Fields
order_desc: Whether to sort in descending order

Returns:
List [CharacterPromptConfig]: Prompt word configuration list"""
        if role_ids:
            # Use a custom query to obtain the configuration for a specific role ID
            statement = select(CharacterPromptConfig).where(CharacterPromptConfig.role_id.in_(role_ids))
            if skip >= 0:
                statement = statement.offset(skip).limit(limit)
            return self.db.exec(statement).all()
        elif types:
            # Use a custom query to obtain a specific type of configuration
            statement = select(CharacterPromptConfig).where(CharacterPromptConfig.type.in_(types))
            if skip >= 0:
                statement = statement.offset(skip).limit(limit)
            return self.db.exec(statement).all()
        else:
            # Use base class methods to handle simple filtering and sorting
            return await super().get_all(
                skip=skip, 
                limit=limit, 
                filters=filters, 
                order_by=order_by, 
                order_desc=order_desc
            )

    def get_nearest_prompt(self, role_id: str, current_level: float) -> Optional[CharacterPromptConfig]:
        """Get the most recent prompt word configuration

Args:
role_id: Role ID
current_level: Current level

Returns:
Optional [CharacterPromptConfig]: Configuration found or default"""
        timer = ExecutionTimer("Time to check the relational database:")
        timer.start()
        
        query = select(CharacterPromptConfig).where(
            CharacterPromptConfig.role_id == role_id,
            CharacterPromptConfig.level <= current_level,
            CharacterPromptConfig.status == 1
        ).order_by(CharacterPromptConfig.level.desc()).limit(1)

        result = self.db.exec(query).first()
        timer.stop()
        
        if result:
            return result

        # If not found, return to default configuration
        return CharacterPromptConfig(role_id=role_id, level=current_level, status=1, prompt_text="")

    async def get_special_prompts(self, role_ids: List[str]) -> List[CharacterPromptConfig]:
        """Get special prompt word configuration

Args:
role_ids: List of character IDs for special hints

Returns:
List [CharacterPromptConfig]: List of eligible prompt word configurations"""
        if not role_ids:
            return []

        # build query
        query = select(CharacterPromptConfig).where(
            CharacterPromptConfig.role_id.in_(role_ids),
            CharacterPromptConfig.status == 1
        )

        # Execute Query
        results = self.db.exec(query).all()

        # Organize results in order of incoming role_ids
        result_dict = {config.role_id: config for config in results}
        ordered_results = []

        for role_id in role_ids:
            if role_id in result_dict:
                ordered_results.append(result_dict[role_id])

        return ordered_results

    async def get_all_paginated(self, 
                               *,
                               role_ids: List[str] = None, 
                               types: List[str] = None,
                               filters: Optional[Dict[str, Any]] = None,
                               order_by: Optional[str] = None,
                               order_desc: bool = True) -> Page[CharacterPromptConfig]:
        """Get a list of prompt word configurations for pagination

Args:
role_ids: Role ID list for filtering
Types: List of types for filtering
Filters: Other Filters
order_by: Sort Fields
order_desc: Whether to sort in descending order

Returns:
Page [CharacterPromptConfig]: Tip word configuration list for pagination"""
        from fastapi_pagination import Params
        from fastapi_pagination.api import resolve_params
        from sqlmodel import func
        
        # Get paging parameters
        params = resolve_params()
        
        # Build basic query
        statement = select(CharacterPromptConfig)
        count_statement = select(func.count(CharacterPromptConfig.id))
        
        # Apply filter conditions
        where_conditions = []
        
        if role_ids:
            where_conditions.append(CharacterPromptConfig.role_id.in_(role_ids))
        
        if types:
            where_conditions.append(CharacterPromptConfig.type.in_(types))
            
        if filters:
            for field, value in filters.items():
                if hasattr(CharacterPromptConfig, field):
                    column = getattr(CharacterPromptConfig, field)
                    if isinstance(value, list):
                        where_conditions.append(column.in_(value))
                    else:
                        where_conditions.append(column == value)
        
        # Apply WHERE conditions
        if where_conditions:
            for condition in where_conditions:
                statement = statement.where(condition)
                count_statement = count_statement.where(condition)
        
        # app sort
        if order_by and hasattr(CharacterPromptConfig, order_by):
            column = getattr(CharacterPromptConfig, order_by)
            if order_desc:
                statement = statement.order_by(column.desc())
            else:
                statement = statement.order_by(column)
        
        # get total
        total = self.db.exec(count_statement).one()
        
        # app paging
        statement = statement.offset((params.page - 1) * params.size).limit(params.size)
        
        # Execute Query
        items = self.db.exec(statement).all()
        
        # Manually Create Page Objects
        return Page[CharacterPromptConfig](
            items=items,
            total=total,
            page=params.page,
            size=params.size,
            pages=(total + params.size - 1) // params.size if total > 0 else 0
        )

    async def delete_by_role_id(self, role_id):
        """Removes the prompt word configuration for the specified role ID

Args:
role_id: Role ID

Returns:
Bool: successfully deleted"""
        # build query
        query = select(CharacterPromptConfig).where(CharacterPromptConfig.role_id == role_id)
        # Execute the query and delete it
        result = self.db.exec(query).all()
        for item in result:
            self.db.delete(item)
        self.db.commit()
        return True
