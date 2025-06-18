"""user details caching service
Caching operations for handling user details data"""
import asyncio
from typing import Dict, Optional, List, Any

from knowledge_api.framework.redis.cache import RedisCache
from knowledge_api.framework.redis.config import get_redis_config
from knowledge_api.mapper.user_detail.crud import UserDetailCRUD
from knowledge_api.mapper.user_detail.base import UserDetail, UserDetailResponse
from knowledge_api.framework.database.database import get_db_session
from knowledge_api.utils.log_config import get_logger

logger = get_logger()

class UserDetailCache:
    """user details caching service
Manage cache operations for user details data"""
    _instance = None

    def __new__(cls):
        """singleton pattern"""
        if cls._instance is None:
            cls._instance = super(UserDetailCache, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize cache"""
        self.redis_config = get_redis_config()
        self.enabled = True
        
        # Initialize Redis cache
        self.cache = RedisCache(
            prefix=f"{self.redis_config.KEY_PREFIX}user_detail",
            model_class=UserDetail,
            default_ttl=3600  # 1 hour expires
        )

        # Statistics cache (long TTL)
        self.stats_cache = RedisCache(
            prefix=f"{self.redis_config.KEY_PREFIX}user_detail_stats",
            default_ttl=1800  # 30 minutes expires
        )

    def set_enabled(self, enabled: bool):
        """Set cache switch"""
        self.enabled = enabled

    async def get_by_user_id(self, user_id: int) -> Optional[UserDetail]:
        """Get user details by user ID (with cache)"""
        if not self.enabled:
            return None

        cache_key = f"user:{user_id}"
        
        try:
            # Try to get from cache
            cached_detail = await self.cache.get(cache_key)
            if cached_detail:
                logger.debug(f"从缓存获取用户详情: user_id={user_id}")
                return cached_detail

            # Cache miss, fetched from database
            async with get_db_session() as db:
                crud = UserDetailCRUD(db)
                user_detail = await crud.get_by_user_id(user_id=user_id)
                
                if user_detail:
                    # cache
                    await self.cache.set(cache_key, user_detail)
                    logger.debug(f"用户详情已缓存: user_id={user_id}")
                
                return user_detail

        except Exception as e:
            logger.error(f"获取用户详情缓存失败: user_id={user_id}, error={e}")
            return None

    async def update(self, user_detail: UserDetail):
        """Update user details cache"""
        if not self.enabled:
            return

        cache_key = f"user:{user_detail.user_id}"
        
        try:
            await self.cache.set(cache_key, user_detail)
            logger.debug(f"用户详情缓存已更新: user_id={user_detail.user_id}")

            # Clear the relevant statistics cache
            await self.clear_statistics_cache()
            
        except Exception as e:
            logger.error(f"更新用户详情缓存失败: user_id={user_detail.user_id}, error={e}")

    async def delete_by_user_id(self, user_id: int):
        """Delete user details cache"""
        if not self.enabled:
            return

        cache_key = f"user:{user_id}"
        
        try:
            await self.cache.delete(cache_key)
            logger.debug(f"用户详情缓存已删除: user_id={user_id}")

            # Clear the relevant statistics cache
            await self.clear_statistics_cache()
            
        except Exception as e:
            logger.error(f"删除用户详情缓存失败: user_id={user_id}, error={e}")

    async def get_statistics(self) -> Optional[Dict]:
        """Get user details statistics (with cache)"""
        if not self.enabled:
            return None

        cache_key = "statistics"
        
        try:
            # Try to get from cache
            cached_stats = await self.stats_cache.get(cache_key)
            if cached_stats:
                logger.debug("Get user details statistics from cache")
                return cached_stats

            # Cache miss, fetched from database
            async with get_db_session() as db:
                crud = UserDetailCRUD(db)
                stats = await crud.get_statistics()
                
                if stats:
                    # Convert to dictionary and cache
                    stats_dict = stats.dict() if hasattr(stats, 'dict') else stats.model_dump()
                    await self.stats_cache.set(cache_key, stats_dict)
                    logger.debug("User details statistics are cached")
                    return stats_dict
                
                return None

        except Exception as e:
            logger.error(f"获取用户详情统计缓存失败: error={e}")
            return None

    async def get_ranking(self, ranking_type: str, limit: int = 10) -> Optional[List[Dict]]:
        """Get leaderboard data (with cache)"""
        if not self.enabled:
            return None

        cache_key = f"ranking:{ranking_type}:{limit}"
        
        try:
            # Try to get from cache
            cached_ranking = await self.stats_cache.get(cache_key)
            if cached_ranking:
                logger.debug(f"从缓存获取排行榜数据: type={ranking_type}")
                return cached_ranking

            # Cache miss, fetched from database
            async with get_db_session() as db:
                crud = UserDetailCRUD(db)
                
                if ranking_type == "points":
                    ranking_data = await crud.get_top_users_by_points(limit=limit)
                elif ranking_type == "challenges":
                    ranking_data = await crud.get_top_users_by_challenges(limit=limit)
                elif ranking_type == "active":
                    ranking_data = await crud.get_most_active_users(limit=limit)
                else:
                    return None
                
                if ranking_data:
                    # Convert to dictionary list and cache
                    ranking_list = []
                    for item in ranking_data:
                        item_dict = item.dict() if hasattr(item, 'dict') else item.model_dump()
                        ranking_list.append(item_dict)
                    
                    await self.stats_cache.set(cache_key, ranking_list)
                    logger.debug(f"排行榜数据已缓存: type={ranking_type}")
                    return ranking_list
                
                return []

        except Exception as e:
            logger.error(f"获取排行榜缓存失败: type={ranking_type}, error={e}")
            return None

    async def clear_user_cache(self, user_id: int):
        """Clear the cache for a specific user"""
        await self.delete_by_user_id(user_id)

    async def clear_statistics_cache(self):
        """Clear statistics related cache"""
        if not self.enabled:
            return

        try:
            # Clear statistics cache
            await self.stats_cache.delete("statistics")
            
            # Clear all leaderboard caches
            await self.stats_cache.clear_prefix("ranking:")
            
            logger.debug("User details statistics cache cleared")
            
        except Exception as e:
            logger.error(f"清除统计缓存失败: error={e}")

    async def invalidate_cache_on_update(self, user_id: int):
        """invalidate correlation cache when data is updated"""
        # Clear user details cache
        await self.clear_user_cache(user_id)
        
        # Clear the statistics cache (as changes in user data can affect statistics)
        await self.clear_statistics_cache()

    async def warm_up_cache(self, user_ids: List[int]):
        """Warm up cache - bulk load details of frequently used users"""
        if not self.enabled:
            return

        try:
            async with get_db_session() as db:
                crud = UserDetailCRUD(db)
                
                for user_id in user_ids:
                    cache_key = f"user:{user_id}"
                    
                    # Check if the cache already exists
                    if not await self.cache.exists(cache_key):
                        user_detail = await crud.get_by_user_id(user_id=user_id)
                        if user_detail:
                            await self.cache.set(cache_key, user_detail)
                
                logger.info(f"用户详情缓存预热完成: {len(user_ids)} 个用户")
                
        except Exception as e:
            logger.error(f"缓存预热失败: error={e}")

    async def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information"""
        if not self.enabled:
            return {"enabled": False}

        try:
            # Get all user details cached
            user_caches = await self.cache.get_all("user:")
            
            # Get all statistics cached
            stats_caches = await self.stats_cache.get_all()
            
            return {
                "enabled": True,
                "user_detail_count": len(user_caches),
                "statistics_cache_count": len(stats_caches),
                "cache_prefix": self.cache.prefix,
                "stats_cache_prefix": self.stats_cache.prefix
            }
            
        except Exception as e:
            logger.error(f"获取缓存信息失败: error={e}")
            return {"enabled": True, "error": str(e)} 