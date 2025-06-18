"""Redis OM Extension Module
Provides Redis object mapping capabilities to support storage and querying of structured data"""
from typing import List, Optional, Type, TypeVar, ClassVar
import json
from datetime import datetime, date
from decimal import Decimal

from pydantic import BaseModel, Field, create_model
from redis.asyncio import Redis

from knowledge_api.framework.redis import get_redis_config
from knowledge_api.framework.redis.connection import get_async_redis
from knowledge_api.utils.log_config import get_logger

logger = get_logger()
T = TypeVar('T', bound=BaseModel)

# Custom JSON encoders handle special types
class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoders handle special types"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, BaseModel):
            return obj.model_dump()
        return super().default(obj)

class RedisModel(BaseModel):
    """Redis model base class
Pydantic model that provides Redis storage and query capabilities"""
    # metadata field
    id: Optional[str] = Field(default=None, description="unique device identifier")
    created_at: Optional[datetime] = Field(default_factory=datetime.now, description="creation time")
    updated_at: Optional[datetime] = Field(default_factory=datetime.now, description="update time")
    
    # class variable
    _prefix: ClassVar[str] = "redis_model:"
    _redis_client: ClassVar[Optional[Redis]] = None
    _ttl: ClassVar[Optional[int]] = None  # Expiration time (seconds)
    
    class Config:
        """configuration"""
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat(),
            date: lambda d: d.isoformat(),
            Decimal: lambda d: str(d)
        }
    
    @classmethod
    async def _get_redis(cls) -> Redis:
        """Get the Redis client side"""
        if cls._redis_client is None:
            cls._redis_client = await get_async_redis()
        return cls._redis_client
    
    @classmethod
    def _get_key(cls, model_id: str) -> str:
        """Get the full Redis key"""
        config = get_redis_config()
        return f"{config.KEY_PREFIX}{cls._prefix}{model_id}"
    
    @classmethod
    async def get(cls: Type[T], model_id: str) -> Optional[T]:
        """Get model instance by ID

Args:
model_id: Model ID

Returns:
Optional [T]: Model instance, None if none exists"""
        redis = await cls._get_redis()
        key = cls._get_key(model_id)
        
        # Get JSON data
        data = await redis.get(key)
        if not data:
            return None
        
        # parse data
        try:
            model_data = json.loads(data)
            return cls(**model_data)
        except Exception as e:
            logger.error(f"解析模型数据出错 ({cls.__name__}:{model_id}): {e}")
            return None
    
    @classmethod
    async def find(cls: Type[T], **kwargs) -> List[T]:
        """Find model instances that match conditions

Args:
** kwargs: query conditions

Returns:
List [T]: List of matching model instances"""
        if not kwargs:
            return await cls.all()
            
        # Get all instances and filter
        instances = await cls.all()
        
        # Filter instances of matching criteria
        result = []
        for instance in instances:
            match = True
            for key, value in kwargs.items():
                if not hasattr(instance, key) or getattr(instance, key) != value:
                    match = False
                    break
            if match:
                result.append(instance)
                
        return result
    
    @classmethod
    async def all(cls: Type[T]) -> List[T]:
        """Get all model instances

Returns:
List [T]: List of all model instances"""
        redis = await cls._get_redis()
        pattern = f"{cls._get_key('')}*"
        
        # Use scan iterator to get all keys
        cursor = b"0"
        instances = []
        
        while cursor:
            cursor, keys = await redis.scan(cursor=cursor, match=pattern, count=100)
            
            if keys:
                # Get the values of all keys
                values = await redis.mget(keys)
                
                # parsing example
                for data in values:
                    if data:
                        try:
                            model_data = json.loads(data)
                            instances.append(cls(**model_data))
                        except Exception as e:
                            logger.error(f"解析模型数据出错: {e}")
                            
            if cursor == b"0":
                break
                
        return instances
    
    @classmethod
    async def delete_many(cls, model_ids: List[str]) -> int:
        """Batch removal of model instances

Args:
model_ids: List of model IDs to remove

Returns:
Int: Number of instances deleted"""
        if not model_ids:
            return 0
            
        redis = await cls._get_redis()
        keys = [cls._get_key(model_id) for model_id in model_ids]
        return await redis.delete(*keys)
    
    @classmethod
    async def delete_all(cls) -> int:
        """Delete all model instances

Returns:
Int: Number of instances deleted"""
        redis = await cls._get_redis()
        pattern = f"{cls._get_key('')}*"
        
        # Use scan iterator to get all keys
        cursor = b"0"
        deleted_count = 0
        
        while cursor:
            cursor, keys = await redis.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                deleted_count += await redis.delete(*keys)
                
            if cursor == b"0":
                break
                
        return deleted_count
    
    async def save(self) -> bool:
        """Save the model instance

Returns:
Bool: whether the operation was successful"""
        # Update timestamp
        self.updated_at = datetime.now()
        
        # Make sure there is an ID.
        if not self.id:
            self.id = f"{int(datetime.now().timestamp())}"
        
        # serialized data
        redis = await self._get_redis()
        key = self._get_key(self.id)
        
        try:
            # Handling special types with custom encoders
            data = json.dumps(self.model_dump(), cls=CustomJSONEncoder)
        except Exception as e:
            logger.error(f"模型序列化失败: {str(e)}")
            return False
        
        # Store data
        try:
            if self._ttl is not None:
                await redis.setex(key, self._ttl, data)
            else:
                await redis.set(key, data)
            return True
        except Exception as e:
            logger.error(f"保存到Redis失败: {str(e)}")
            return False
    
    async def delete(self) -> bool:
        """Delete model instance

Returns:
Bool: whether the operation was successful"""
        if not self.id:
            return False
            
        redis = await self._get_redis()
        key = self._get_key(self.id)
        deleted = await redis.delete(key)
        
        return deleted > 0
    
    @classmethod
    async def exists(cls, model_id: str) -> bool:
        """Check if the model exists

Args:
model_id: Model ID

Returns:
Bool: Does the model exist?"""
        redis = await cls._get_redis()
        key = cls._get_key(model_id)
        return await redis.exists(key) > 0


def create_redis_model(
    model_name: str,
    prefix: str = None,
    ttl: Optional[int] = None,
    **field_definitions
) -> Type[RedisModel]:
    """Dynamically create a Redis model class

Args:
model_name: Model Class Name
Prefix: Redis key prefix
TTL: expiration time (seconds)
** field_definitions: field definition

Returns:
Type [RedisModel]: Model class created"""
    # Create a model class
    model = create_model(
        model_name,
        __base__=RedisModel,
        **field_definitions
    )
    
    # Set class variables
    model._prefix = prefix or f"{model_name.lower()}:"
    model._ttl = ttl
    
    return model 