# 数据库CRUD操作基类

这个目录包含数据库表的CRUD（创建、读取、更新、删除）操作，为了减少重复代码和提高可维护性，我们提供了一个通用的基类`BaseCRUD`。

## 特性

- 通用的CRUD操作
- 支持分页查询 (集成FastAPI-Pagination)
- 灵活的过滤条件
- 日期范围过滤
- 排序支持
- 批量删除
- 记录计数
- 兼容Pydantic v1和v2

## 使用方法

### 1. 导入基类

```python
from knowledge_api.mapper.base_crud import BaseCRUD
```

### 2. 定义您的CRUD类，继承基类

```python
# 简单版本 (不需要复杂过滤和分页)
class YourSimpleModelCRUD(BaseCRUD[YourModel, YourModelCreate, YourModelUpdate, Dict[str, Any], YourModel]):
    def __init__(self, db: Session):
        super().__init__(db, YourModel)

# 完整版本 (支持过滤和分页)
class YourModelCRUD(BaseCRUD[YourModel, YourModelCreate, YourModelUpdate, YourModelFilter, YourModelResponse]):
    def __init__(self, db: Session):
        super().__init__(db, YourModel, YourModelResponse)
```

### 3. 基类提供的通用方法

#### 基础CRUD操作

- `create(obj_in: CreateSchemaType, **kwargs) -> ModelType`: 创建记录
- `get_by_id(id: Any) -> Optional[ModelType]`: 通过ID获取记录
- `update(id: Any, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> Optional[ModelType]`: 更新记录
- `delete(id: Any) -> bool`: 删除记录

#### 列表和过滤操作

- `get_all(*, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None, order_by: Optional[str] = None, order_desc: bool = True, date_range: Optional[Dict[str, datetime]] = None, date_field: str = "created_at") -> List[ModelType]`: 获取多条记录，支持过滤、排序和分页
- `get_all_paginated(*, order_by: Optional[str] = None, order_desc: bool = True, date_field: str = "created_at") -> Page[ResponseSchemaType]`: 获取所有记录（分页版本）
- `filter_records(filter_schema: FilterSchemaType, skip: int = 0, limit: int = 100, order_by: Optional[str] = None, order_desc: bool = True, date_field: str = "created_at") -> List[ModelType]`: 过滤记录
- `filter_records_paginated(filter_schema: FilterSchemaType, order_by: Optional[str] = None, order_desc: bool = True, date_field: str = "created_at") -> Page[ResponseSchemaType]`: 过滤记录（分页版本）

#### 批量操作和统计

- `delete_many(filter_schema: FilterSchemaType) -> int`: 批量删除符合条件的记录
- `count(filter_schema: Optional[FilterSchemaType] = None) -> int`: 计算符合条件的记录数量

### 4. 类型参数说明

基类使用泛型设计，需要指定以下类型参数：

- `ModelType`: 数据库模型类
- `CreateSchemaType`: 创建记录的请求模型类
- `UpdateSchemaType`: 更新记录的请求模型类
- `FilterSchemaType`: 过滤条件模型类 (如果不需要复杂过滤，可以使用 `Dict[str, Any]`)
- `ResponseSchemaType`: 响应模型类 (用于分页响应，如果与数据库模型相同，可以直接使用 `ModelType`)

### 5. 过滤和分页示例

#### 简单过滤（使用字典）

```python
# 获取特定状态的任务
tasks = await task_crud.get_all(filters={"status": 1})

# 使用日期范围过滤
tasks = await task_crud.get_all(
    date_range={"start_date": datetime(2023, 1, 1), "end_date": datetime(2023, 12, 31)}
)
```

#### 使用过滤模型

```python
# 创建过滤对象
filter_obj = TaskGameMessageFilter(
    user_id="user123",
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31)
)

# 获取过滤后的结果
messages = await message_crud.filter_records(filter_obj)

# 获取分页结果
paginated_messages = await message_crud.filter_records_paginated(filter_obj)
```

### 6. 自定义和扩展

您可以通过以下方式扩展基类功能：

1. 重写基类方法，添加特定逻辑
2. 添加特定于模型的新方法
3. 在继承基类的同时，添加其他功能

## 示例

请参考 `example_usage.py` 文件，查看如何使用基类实现：

1. `TaskCRUD` - 简单版本实现
2. `TaskGameMessageCRUD` - 完整版本实现，展示分页和过滤功能
3. `RoleCRUD` - 展示如何重写方法

## 注意事项

- 基类使用泛型参数，确保类型提示正确
- 创建模型和过滤模型应继承自 `BaseModel`
- 基类兼容Pydantic v1和v2版本
- 默认情况下，分页功能依赖于FastAPI-Pagination库
- 日期范围过滤默认字段名为`created_at`，可以通过`date_field`参数自定义

# CRUD基类使用指南

## 简介

`BaseCRUD`类为数据库操作提供了一个通用框架，可以大幅减少重复代码，使CRUD操作更加简洁。

## 基本用法

假设你已经有了一个模型`User`和相应的schema类`UserCreate`, `UserUpdate`, `UserFilter`, `UserResponse`，以下是如何使用`BaseCRUD`类的示例：

```python
from knowledge_api.mapper.base_crud import BaseCRUD
from knowledge_api.mapper.users.base import User, UserCreate, UserUpdate, UserFilter, UserResponse

class UserCRUD(BaseCRUD[User, UserCreate, UserUpdate, UserFilter, UserResponse, int]):
    """用户CRUD操作类"""
    
    def __init__(self, db: Session):
        """初始化用户CRUD"""
        super().__init__(db, User)
        
    # 可以添加User特有的方法
    async def get_by_email(self, email: str) -> Optional[User]:
        """通过邮箱获取用户"""
        statement = select(self.model).where(self.model.email == email)
        result = self.db.exec(statement).first()
        return result
        
    # 覆写基类方法，添加特定的业务逻辑
    async def create(self, obj_in: UserCreate) -> User:
        """创建用户，添加密码加密等逻辑"""
        # 自定义处理，如密码加密
        hashed_password = hash_password(obj_in.password)
        
        # 创建数据字典
        obj_data = obj_in.dict()
        obj_data["hashed_password"] = hashed_password
        del obj_data["password"]
        
        # 调用父类方法完成实际创建
        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj
```

## 如何重构现有的CRUD类

将现有的CRUD类重构为使用`BaseCRUD`基类的步骤：

1. 让CRUD类继承`BaseCRUD`并提供正确的泛型参数
2. 在`__init__`方法中调用`super().__init__(db, 模型类)`
3. 移除已被基类实现的通用方法
4. 保留并可能重写特定业务逻辑的方法

例如，重构`LLMUsageRecordCRUD`类：

```python
from knowledge_api.mapper.base_crud import BaseCRUD
from knowledge_api.mapper.llm_usage_records.base import (
    LLMUsageRecord, 
    LLMUsageRecordCreate, 
    LLMUsageRecordUpdate, 
    LLMUsageRecordFilter, 
    LLMUsageRecordStats
)

class LLMUsageRecordCRUD(BaseCRUD[LLMUsageRecord, LLMUsageRecordCreate, LLMUsageRecordUpdate, LLMUsageRecordFilter, LLMUsageRecord, int]):
    """LLM模型使用记录CRUD操作"""
    
    def __init__(self, db: Session):
        """初始化数据库会话"""
        super().__init__(db, LLMUsageRecord)
    
    # 保留特有方法
    async def create_from_response(
        self, 
        response_data: Dict[str, Any], 
        vendor_type: str,
        model_id: str,
        application_scenario: Optional[str] = None,
        related_record_id: Optional[str] = None
    ) -> LLMUsageRecord:
        # 原有实现...
        
    # 重写filter方法以实现特定的过滤逻辑
    def _apply_filters_to_query(self, query, filter_data: Dict[str, Any]):
        """应用LLM使用记录的特定过滤逻辑"""
        if "vendor_type" in filter_data and filter_data["vendor_type"]:
            query = query.filter(self.model.vendor_type == filter_data["vendor_type"])
        
        if "start_date" in filter_data and filter_data["start_date"]:
            query = query.filter(self.model.created_at >= filter_data["start_date"])
            
        # 其他过滤条件...
        return query
```

## 支持的基本操作

`BaseCRUD`提供以下基本操作：

- `create`: 创建新记录
- `get_by_id`: 通过ID获取记录
- `get_all`: 获取所有记录(带分页)
- `get_all_paginated`: 获取分页记录
- `update`: 更新记录
- `delete`: 删除记录
- `filter`: 根据条件过滤记录
- `filter_paginated`: 根据条件分页过滤记录
- `count`: 计算记录总数

## 注意事项

- 为支持多种主键类型，`get_by_id`、`update`、`delete`方法中的`id`参数类型为`IdType`(int或str)
- 基类会自动处理`create_time`/`update_time`或`created_at`/`updated_at`字段
- 过滤方法需要在子类中重写`_apply_filters`和`_apply_filters_to_query`方法以实现特定业务逻辑 