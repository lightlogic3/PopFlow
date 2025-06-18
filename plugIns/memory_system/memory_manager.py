from typing import Dict, Any, List, Optional, Union
import time
import asyncio
import logging
import threading
from datetime import datetime
from collections import defaultdict

from knowledge_api.framework.redis.connection import get_async_redis
from .memory_factory import MemoryFactory, MemoryLevel
from .memory_interface import MemoryInterface, UserMetadata
from plugIns.memory_system.cache_system.memory_queue import MemoryQueueManager
from knowledge_api.framework.redis.redis_lock import RedisLock
from plugIns.memory_system.cache_system.dialog_history_manager import DialogHistoryManager
from .model import MemoryContext
from .utils.json_utils import serialize_with_datetime, deserialize_datetime_aware
from .utils.key_utils import MemoryKeyBuilder


class MemoryManager:
    """
    记忆系统管理器 V2版本 - 单例模式

    负责管理不同级别的记忆系统，提供统一的接口，并可以根据查询复杂度自动选择合适的记忆级别。
    支持多用户多角色的记忆隔离，通过user_id+role_id进行核心隔离，session_id作为可选的会话级隔离。
    
    采用单例模式确保全局唯一实例，避免资源重复创建和状态不一致问题。
    """
    
    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls, *args, **kwargs):
        """单例模式实现，确保只创建一个实例"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(MemoryManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, 
                 default_level: MemoryLevel = MemoryLevel.LEVEL_6_CONVERSATION,
                 dialog_batch_size: int = -1,  # -1表示使用实现类默认值
                 auto_summarize: bool = True,
                 use_queue: bool = False,  # 队列开关
                 max_history_size: int = 10):  # 最大历史对话轮数
        """
        初始化记忆管理器（单例模式，只初始化一次）

        Args:
            default_level: 默认使用的记忆级别
            dialog_batch_size: 对话多少次后触发存储，-1表示使用实现类默认值
            auto_summarize: 是否自动汇总对话内容
            use_queue: 是否使用Redis队列进行异步处理
            max_history_size: 最大历史对话轮数，默认10轮
        """
        # 单例模式：只初始化一次
        if self._initialized:
            return
            
        with self._lock:
            if self._initialized:
                return
                
            self._factory = MemoryFactory()
            self._factory.register_default_systems()

            self._default_level = default_level
            self._current_level = default_level
            self._current_memory = None

            # 先保存用户指定的批次大小，后续在设置记忆级别时再确定实际值
            self._user_specified_batch_size = dialog_batch_size

            # 缓存各级记忆系统
            self._memory_cache: Dict[MemoryLevel, MemoryInterface] = {}

            # 性能监控
            self._performance_history = []

            # 用户元数据缓存 - 使用user_id:role_id作为键
            self._user_metadata_cache: Dict[str, UserMetadata] = {}

            # 日志记录器
            self._logger = logging.getLogger("MemoryManagerV2")

            # 对话批次大小 - 暂时设置为默认值
            self._dialog_batch_size = 1  # 默认值，会在set_memory_level中更新

            # 是否自动汇总
            self._auto_summarize = auto_summarize

            # 对话历史管理器
            self._history_manager = DialogHistoryManager.get_instance(max_history_size=max_history_size)
            self._logger.info(f"对话历史管理器初始化完成，最大历史轮数: {max_history_size}")

            # 后台任务列表
            self._background_tasks = {}

            # 队列处理相关
            self._use_queue = use_queue
            self._queue_manager = None

            # 键值构建器
            self._key_builder = MemoryKeyBuilder()

            # 对话批次处理器
            from .processors.dialog_batch_processor import DialogBatchProcessor
            self._batch_processor = DialogBatchProcessor(self)

            # 如果启用队列，初始化队列管理器
            if self._use_queue:
                self._init_queue_manager()

            self._initialized = True
            self._logger.info("记忆管理器V2单例实例初始化完成")

    @classmethod
    def get_instance(cls, **kwargs):
        """
        获取单例实例的类方法
        
        Args:
            **kwargs: 初始化参数（仅在首次创建时生效）
            
        Returns:
            MemoryManager: 单例实例
        """
        if cls._instance is None:
            cls(**kwargs)
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """
        重置单例实例（主要用于测试）
        
        Warning: 此方法会清除所有状态，谨慎使用
        """
        with cls._lock:
            if cls._instance is not None:
                # 如果有队列管理器，先关闭
                if hasattr(cls._instance, '_queue_manager') and cls._instance._queue_manager:
                    # 这里不能直接调用async方法，需要在外部处理
                    cls._instance._logger.warning("重置实例时检测到队列管理器，请确保先调用close_queue()")
                
                cls._instance = None
                cls._initialized = False

    def _init_queue_manager(self):
        """初始化队列管理器"""
        self._queue_manager = MemoryQueueManager(
            memory_manager=self,
            queue_name="memory_tasks",
            max_retries=3,
            batch_size=10,
            poll_interval=1.0,
            enable_priority=True,
            auto_start=True
        )
        self._logger.info("队列管理器已初始化，将使用Redis消息队列进行异步记忆处理")

    async def _ensure_queue_initialized(self):
        """确保队列已初始化"""
        await self.set_memory_level(self._default_level)
        if self._use_queue and self._queue_manager and not self._queue_manager._initialized:
            await self._queue_manager.initialize()
            self._logger.info("队列管理器已初始化完成")

    async def set_memory_level(self, level: Union[int, MemoryLevel], **kwargs) -> bool:
        """
        设置当前使用的记忆级别

        Args:
            level: 记忆级别(可以是MemoryLevel枚举或整数1-5)
            **kwargs: 传递给记忆系统的额外参数

        Returns:
            bool: 设置是否成功
        """
        # 使用Redis锁
        async with RedisLock("memory_manager_v2:set_level", expire=10) as lock_acquired:
            if not lock_acquired:
                self._logger.warning(f"获取设置记忆级别锁失败")
                return False

            # 如果传入的是整数，转换为枚举
            if isinstance(level, int):
                try:
                    level = MemoryLevel(level)
                except ValueError:
                    self._logger.error(f"无效的记忆级别: {level}，应当是1-5之间的整数")
                    return False

            # 检查是否已经创建过该级别的记忆系统
            if level in self._memory_cache:
                self._current_memory = self._memory_cache[level]
            else:
                # 创建新的记忆系统实例
                try:
                    self._current_memory = await self._factory.create(level, **kwargs)
                    self._memory_cache[level] = self._current_memory
                except Exception as e:
                    self._logger.error(f"创建记忆系统失败: {e}")
                    return False

            # 更新当前记忆级别
            self._current_level = level

            # 更新对话批次大小：如果用户未指定（-1），则使用实现类的值
            if self._user_specified_batch_size == -1 and hasattr(self._current_memory, 'dialog_batch_size'):
                # 从当前记忆系统获取批次大小
                memory_batch_size = getattr(self._current_memory, 'dialog_batch_size', 1)
                self._dialog_batch_size = memory_batch_size
                self._logger.info(f"根据记忆系统实现类更新对话批次大小为: {self._dialog_batch_size}")
            elif self._user_specified_batch_size > 0:
                # 使用用户指定的批次大小
                self._dialog_batch_size = self._user_specified_batch_size
            else:
                # 默认为1
                self._dialog_batch_size = 1

            self._logger.info(f"设置记忆级别: {level}, 对话批次大小: {self._dialog_batch_size}")
            return True

    def get_current_level(self) -> MemoryLevel:
        """
        获取当前正在使用的记忆级别

        Returns:
            MemoryLevel: 当前记忆级别
        """
        return self._current_level

    async def register_custom_memory_system(self, level: MemoryLevel, memory_class: type) -> bool:
        """
        注册自定义记忆系统

        Args:
            level: 要替换的记忆级别
            memory_class: 自定义记忆系统类

        Returns:
            bool: 注册是否成功
        """
        # 使用Redis锁
        async with RedisLock("memory_manager_v2:register_system", expire=10) as lock_acquired:
            if not lock_acquired:
                self._logger.warning(f"获取注册记忆系统锁失败")
                return False

            try:
                # 注册到工厂
                self._factory.register(level, memory_class)

                # 从缓存中移除该级别的旧实例(如果存在)
                if level in self._memory_cache:
                    del self._memory_cache[level]

                # 如果当前正在使用该级别，重新创建实例
                if self._current_level == level:
                    self._current_memory = await self._factory.create(level)

                return True
            except Exception as e:
                self._logger.error(f"注册自定义记忆系统失败: {e}")
                return False

    async def get_or_create_user_metadata(self, user_id: str, role_id: str, session_id: Optional[str] = None) -> UserMetadata:
        """
        获取或创建用户元数据

        Args:
            user_id: 用户ID，必填
            role_id: 角色ID，必填
            session_id: 会话ID，可选

        Returns:
            UserMetadata: 用户元数据
        """
        if not user_id or not role_id:
            raise ValueError("user_id和role_id都是必填字段")

        cache_key = f"{user_id}:{role_id}"

        # 使用Redis锁
        lock_key = self._key_builder.build_metadata_lock_key(user_id, role_id)
        async with RedisLock(lock_key, expire=5) as lock_acquired:
            if not lock_acquired:
                self._logger.warning(f"获取用户元数据锁失败: {cache_key}")
                # 如果已经有缓存，直接返回，避免等待
                if cache_key in self._user_metadata_cache:
                    existing = self._user_metadata_cache[cache_key]
                    # 更新session_id
                    if session_id:
                        existing.session_id = session_id
                    return existing
                # 否则创建新的，但不加入缓存
                return UserMetadata(user_id=user_id, role_id=role_id, session_id=session_id)

            if cache_key not in self._user_metadata_cache:
                self._user_metadata_cache[cache_key] = UserMetadata(
                    user_id=user_id, 
                    role_id=role_id, 
                    session_id=session_id
                )
            else:
                # 更新session_id
                if session_id:
                    self._user_metadata_cache[cache_key].session_id = session_id

            return self._user_metadata_cache[cache_key]

    async def store(self,
                    memory_context: Union[MemoryContext, Dict[str, Any]],
                    user_id: str,
                    role_id: str,
                    session_id: Optional[str] = None,
                    force_immediate: bool = False,
                    use_queue: bool = None) -> bool:
        """
        存储数据到当前记忆系统

        Args:
            memory_context: 要存储的记忆内容，可以是MemoryContext对象或符合其结构的字典
            user_id: 用户ID，必填
            role_id: 角色ID，必填  
            session_id: 会话ID，可选
            force_immediate: 是否强制立即存储，不使用批处理
            use_queue: 是否使用队列，覆盖全局设置

        Returns:
            bool: 存储是否成功
        """
        # 调试信息
        self._logger.info(f"===== 开始存储过程 =====")
        
        # 验证必填参数
        if not user_id or not role_id:
            self._logger.error(f"存储失败: user_id和role_id都是必填字段")
            return False
        
        # 处理memory_context参数(如果是字典格式，保持兼容性)
        data = memory_context
        if not isinstance(memory_context, dict):
            data = memory_context.dict()

        content_preview = data.get('content', '')[:50] + ('...' if len(data.get('content', '')) > 50 else '')

        # 获取用户元数据
        user_metadata = await self.get_or_create_user_metadata(user_id, role_id, session_id)

        self._logger.info(f"存储参数: user_id={user_id}, role_id={role_id}, session_id={session_id}, force_immediate={force_immediate}")
        self._logger.info(f"内容预览: {content_preview}")

        if self._current_memory is None:
            self._logger.error("当前记忆系统未初始化")
            return False

        # 确定是否使用队列
        should_use_queue = use_queue if use_queue is not None else self._use_queue

        # 如果启用队列且不强制立即存储，使用队列处理
        if should_use_queue and not force_immediate:
            self._logger.info(f"使用队列进行异步存储，用户: {user_id}, 角色: {role_id}, 会话: {session_id}")

            # 确保队列已初始化
            await self._ensure_queue_initialized()

            # 添加时间戳，如果没有
            if 'timestamp' not in data:
                data['timestamp'] = datetime.now().isoformat()

            # 异步存储到队列
            return await self._queue_manager.store_memory(
                data=data,
                user_id=user_id,
                role_id=role_id,
                session_id=session_id
            )

        self._logger.info(
            f"准备存储对话, 用户:{user_id}, 角色:{role_id}, 会话:{session_id}, 强制立即:{force_immediate}, 批次大小:{self._dialog_batch_size}")

        # 添加时间戳，如果没有
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat()
            self._logger.info(f"添加时间戳: {data['timestamp']}")

        # 检查是否有任务正在处理
        redis = await get_async_redis()
        processing_lock_key = self._key_builder.build_processing_lock_key(user_id, role_id, session_id)
        is_processing = await redis.exists(f"redis_lock:{processing_lock_key}")

        # 使用Redis存储对话缓存
        dialog_cache_key = self._key_builder.build_dialog_cache_key(user_id, role_id, session_id)
        # 序列化对话数据
        dialog_json = serialize_with_datetime(data)
        self._logger.info(f"序列化对话数据成功，准备存入Redis")
        await redis.rpush(dialog_cache_key, dialog_json)

        # 获取当前缓存大小
        current_size = await redis.llen(dialog_cache_key)
        self._logger.info(
            f"将对话添加到Redis缓存, 用户:{user_id}, 角色:{role_id}, 会话:{session_id}, 当前缓存大小: {current_size}, 批次阈值: {self._dialog_batch_size}")

        # 输出状态信息，便于调试
        if is_processing:
            self._logger.info(f"当前有处理任务正在执行, 用户: {user_id}, 角色: {role_id}, 会话: {session_id}")

        # 检查是否需要立即存储
        should_process = force_immediate or current_size >= self._dialog_batch_size

        if should_process and not is_processing:
            # 如果没有正在处理的任务，则获取锁进行处理
            self._logger.info(f"触发存储条件且无处理任务正在执行，准备处理, 用户:{user_id}, 角色:{role_id}, 会话:{session_id}")

            # 创建异步任务处理
            try:
                task = asyncio.create_task(self._process_dialog_batch(user_id, role_id, session_id))
                self._logger.info(f"已创建异步处理任务, 用户:{user_id}, 角色:{role_id}, 会话:{session_id}")
            except Exception as e:
                self._logger.error(f"创建异步处理任务失败: {e}")
                return False
        elif should_process and is_processing:
            self._logger.info(f"触发存储条件但已有处理任务在执行，添加到缓存等待后续处理, 用户:{user_id}, 角色:{role_id}, 会话:{session_id}")
        else:
            self._logger.info(f"不需要立即存储，返回成功, 用户:{user_id}, 角色:{role_id}, 会话:{session_id}")

        self._logger.info(f"===== 存储过程结束 =====")
        return True

    async def _process_dialog_batch(self, user_id: str, role_id: str, session_id: Optional[str] = None) -> bool:
        """
        处理对话批次 - 委托给对话批次处理器

        Args:
            user_id: 用户ID
            role_id: 角色ID
            session_id: 会话ID

        Returns:
            bool: 处理是否成功
        """
        return await self._batch_processor.process_dialog_batch(user_id, role_id, session_id)

    async def retrieve(self, query: str,
                      user_id: str,
                      role_id: str,
                      session_id: Optional[str] = None,
                      top_k: int = 5,
                      **kwargs) -> List[Dict[str, Any]]:
        """
        从当前记忆系统检索数据

        Args:
            query: 查询文本
            user_id: 用户ID，必填
            role_id: 角色ID，必填
            session_id: 会话ID，可选
            top_k: 返回结果数量
            **kwargs: 额外参数

        Returns:
            List[Dict[str, Any]]: 检索结果列表
        """
        if self._current_memory is None:
            return []

        # 验证必填参数
        if not user_id or not role_id:
            self._logger.error(f"检索失败: user_id和role_id都是必填字段")
            return []

        start_time = time.time()

        try:
            # 获取用户元数据
            user_metadata = await self.get_or_create_user_metadata(user_id, role_id, session_id)

            # 设置user_metadata到kwargs中
            kwargs['user_metadata'] = user_metadata

            self._logger.info(f"执行检索，查询: {query}, 用户: {user_id}, 角色: {role_id}, 会话: {session_id}, top_k: {top_k}")
            results = await self._current_memory.retrieve(query, top_k=top_k, **kwargs)

            # 记录性能数据
            elapsed = time.time() - start_time
            self._performance_history.append({
                "query": query,
                "memory_level": self._current_level,
                "latency": elapsed,
                "results_count": len(results),
                "user_id": user_id,
                "role_id": role_id,
                "session_id": session_id
            })

            return results
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._logger.error(f"检索失败: {e}")
            return []

    async def retrieve_with_auto_level(self, query: str,
                                       user_id: str,
                                       role_id: str,
                                       session_id: Optional[str] = None,
                                       top_k: int = 5,
                                       context: Dict[str, Any] = None,
                                       **kwargs) -> List[Dict[str, Any]]:
        """
        根据查询自动选择合适的记忆级别并检索

        Args:
            query: 查询文本
            user_id: 用户ID，必填
            role_id: 角色ID，必填
            session_id: 会话ID，可选
            top_k: 返回结果数量
            context: 上下文信息，用于帮助选择记忆级别
            **kwargs: 额外参数

        Returns:
            List[Dict[str, Any]]: 检索结果列表
        """
        # 验证必填参数
        if not user_id or not role_id:
            self._logger.error(f"检索失败: user_id和role_id都是必填字段")
            return []

        context = context or {}

        # 根据查询和上下文选择记忆级别
        level = await self.select_memory_level(query, context)

        # 暂时切换到该级别
        original_level = self._current_level
        await self.set_memory_level(level)

        # 执行检索
        results = await self.retrieve(query, user_id=user_id, role_id=role_id, session_id=session_id, top_k=top_k, **kwargs)

        # 恢复原来的记忆级别
        await self.set_memory_level(original_level)

        return results

    async def select_memory_level(self, query: str, context: Dict[str, Any] = None,
                                  complexity: str = None) -> MemoryLevel:
        """
        根据查询和上下文选择合适的记忆级别

        Args:
            query: 查询文本
            context: 上下文信息
            complexity: 直接指定复杂度，可选值为"low", "medium", "high"

        Returns:
            MemoryLevel: 选择的记忆级别
        """
        context = context or {}

        # 如果直接指定了复杂度，按复杂度选择
        if complexity:
            if complexity.lower() == "low":
                return MemoryLevel.LEVEL_6_CONVERSATION
            elif complexity.lower() == "medium":
                return MemoryLevel.LEVEL_6_CONVERSATION
            elif complexity.lower() == "high":
                return MemoryLevel.LEVEL_10_CONVERSATION

        # 简单的启发式规则，实际应用中可能需要更复杂的逻辑
        query_length = len(query)
        has_complex_keywords = any(keyword in query.lower() for keyword in
                                   ["关系", "概念", "知识图谱", "关联", "最近", "全局"])

        # 考虑上下文中的复杂度提示
        context_complexity = context.get("complexity", 0)  # 0-10的复杂度评分

        # 根据查询长度、关键词和上下文复杂度综合评分
        complexity_score = 0

        # 查询长度评分
        if query_length < 10:
            complexity_score += 1
        elif query_length < 30:
            complexity_score += 2
        else:
            complexity_score += 3

        # 关键词评分
        if has_complex_keywords:
            complexity_score += 3

        # 上下文复杂度评分
        complexity_score += context_complexity // 2

        # 根据综合评分选择记忆级别
        if complexity_score <= 3:
            return MemoryLevel.LEVEL_6_CONVERSATION
        elif complexity_score <= 5:
            return MemoryLevel.LEVEL_10_CONVERSATION
        else:
            return MemoryLevel.LEVEL_6_CONVERSATION

    async def update(self, memory_id: str, data: Dict[str, Any],
                     user_id: str, role_id: str, session_id: Optional[str] = None) -> bool:
        """
        更新记忆

        Args:
            memory_id: 记忆ID
            data: 更新的数据
            user_id: 用户ID，必填
            role_id: 角色ID，必填
            session_id: 会话ID，可选

        Returns:
            bool: 更新是否成功
        """
        if self._current_memory is None:
            return False

        # 验证必填参数
        if not user_id or not role_id:
            self._logger.error(f"更新失败: user_id和role_id都是必填字段")
            return False

        user_metadata = await self.get_or_create_user_metadata(user_id, role_id, session_id)

        # 添加日志
        self._logger.info(f"更新记忆, ID:{memory_id}, 用户:{user_id}, 角色:{role_id}, 会话:{session_id}")
        return await self._current_memory.update(memory_id, data, user_metadata=user_metadata)

    async def delete(self, memory_id: str,
                     user_id: str, role_id: str, session_id: Optional[str] = None) -> bool:
        """
        删除记忆

        Args:
            memory_id: 记忆ID
            user_id: 用户ID，必填
            role_id: 角色ID，必填
            session_id: 会话ID，可选

        Returns:
            bool: 删除是否成功
        """
        if self._current_memory is None:
            return False

        # 验证必填参数
        if not user_id or not role_id:
            self._logger.error(f"删除失败: user_id和role_id都是必填字段")
            return False

        user_metadata = await self.get_or_create_user_metadata(user_id, role_id, session_id)

        # 添加日志
        self._logger.info(f"删除记忆, ID:{memory_id}, 用户:{user_id}, 角色:{role_id}, 会话:{session_id}")
        return await self._current_memory.delete(memory_id, user_metadata=user_metadata)

    async def sync_from_database(self, user_id: str, role_id: str, session_id: Optional[str] = None,
                                 start_time: datetime = None, end_time: datetime = None) -> bool:
        """
        从关系数据库同步数据到向量数据库

        Args:
            user_id: 用户ID，必填
            role_id: 角色ID，必填
            session_id: 会话ID，可选
            start_time: 同步的起始时间
            end_time: 同步的结束时间
            run_in_background: 是否在后台运行同步过程

        Returns:
            bool: 同步是否成功启动
        """
        if self._current_memory is None:
            return False

        # 验证必填参数
        if not user_id or not role_id:
            self._logger.error(f"同步失败: user_id和role_id都是必填字段")
            return False

        user_metadata = await self.get_or_create_user_metadata(user_id, role_id, session_id)
        self._logger.info(f"开始同步数据，用户: {user_id}, 角色: {role_id}, 会话: {session_id}")

        return await self._current_memory.sync_to_database(
            user_metadata=user_metadata,
            start_time=start_time,
            end_time=end_time
        )

    async def get_sync_status(self, user_id: str, role_id: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取同步状态

        Args:
            user_id: 用户ID，必填
            role_id: 角色ID，必填
            session_id: 会话ID，可选

        Returns:
            Dict[str, Any]: 同步状态信息
        """
        if self._current_memory is None:
            return {
                "is_syncing": False,
                "progress": 0.0,
                "last_sync_time": None,
                "error": "记忆系统未初始化"
            }

        # 验证必填参数
        if not user_id or not role_id:
            self._logger.error(f"获取同步状态失败: user_id和role_id都是必填字段")
            return {
                "is_syncing": False,
                "progress": 0.0,
                "last_sync_time": None,
                "error": "缺少必要的用户信息"
            }

        user_metadata = await self.get_or_create_user_metadata(user_id, role_id, session_id)
        return await self._current_memory.get_sync_status(user_metadata)

    async def is_memory_enabled(self, user_id: str, role_id: str) -> bool:
        """
        检查用户的记忆系统是否已启用

        Args:
            user_id: 用户ID，必填
            role_id: 角色ID，必填

        Returns:
            bool: 记忆系统是否已启用
        """
        if self._current_memory is None:
            return False

        # 验证必填参数
        if not user_id or not role_id:
            return False

        # 检查用户元数据是否存在
        cache_key = f"{user_id}:{role_id}"
        lock_key = self._key_builder.build_metadata_lock_key(user_id, role_id)

        async with RedisLock(lock_key, expire=5) as lock_acquired:
            if not lock_acquired:
                self._logger.warning(f"获取用户元数据锁失败: {cache_key}")
                # 如果锁获取失败，尝试直接检查缓存
                return cache_key in self._user_metadata_cache

            return cache_key in self._user_metadata_cache

    async def enable_memory(self, user_id: str, role_id: str, session_id: Optional[str] = None, run_sync: bool = True) -> bool:
        """
        为用户启用记忆系统

        Args:
            user_id: 用户ID，必填
            role_id: 角色ID，必填
            session_id: 会话ID，可选
            run_sync: 是否立即执行同步

        Returns:
            bool: 启用是否成功
        """
        # 验证必填参数
        if not user_id or not role_id:
            self._logger.error(f"启用记忆失败: user_id和role_id都是必填字段")
            return False

        # 创建用户元数据
        await self.get_or_create_user_metadata(user_id, role_id, session_id)

        # 如果需要，执行同步
        if run_sync:
            return await self.sync_from_database(user_id, role_id, session_id)

        return True

    async def disable_memory(self, user_id: str, role_id: str) -> bool:
        """
        为用户禁用记忆系统

        Args:
            user_id: 用户ID，必填
            role_id: 角色ID，必填

        Returns:
            bool: 禁用是否成功
        """
        # 验证必填参数
        if not user_id or not role_id:
            self._logger.error(f"禁用记忆失败: user_id和role_id都是必填字段")
            return False

        cache_key = f"{user_id}:{role_id}"
        lock_key = self._key_builder.build_metadata_lock_key(user_id, role_id)

        async with RedisLock(lock_key, expire=5) as lock_acquired:
            if not lock_acquired:
                self._logger.warning(f"获取用户元数据锁失败: {cache_key}")
                return False

            if cache_key in self._user_metadata_cache:
                del self._user_metadata_cache[cache_key]

        return True

    def get_performance_metrics(self, user_id: str = None, role_id: str = None) -> Dict[str, Any]:
        """
        获取性能指标

        Args:
            user_id: 用户ID，如果指定则只返回该用户的指标
            role_id: 角色ID，如果指定则只返回该角色的指标

        Returns:
            Dict[str, Any]: 性能指标
        """
        # 过滤性能历史记录
        filtered_history = self._performance_history
        if user_id:
            filtered_history = [entry for entry in filtered_history if entry.get("user_id") == user_id]
        if role_id:
            filtered_history = [entry for entry in filtered_history if entry.get("role_id") == role_id]

        if not filtered_history:
            return {
                "average_latency": 0,
                "queries_count": 0,
                "level_usage": {},
                "memory_system_metrics": {}
            }

        # 计算平均延迟
        avg_latency = sum(entry["latency"] for entry in filtered_history) / len(filtered_history)

        # 统计各级别使用情况
        level_counts = {}
        for entry in filtered_history:
            level = entry["memory_level"]
            level_counts[level] = level_counts.get(level, 0) + 1

        # 获取当前记忆系统的性能指标
        memory_metrics = {}
        if self._current_memory:
            memory_metrics = self._current_memory.performance_metrics

        return {
            "average_latency": avg_latency,
            "queries_count": len(filtered_history),
            "level_usage": level_counts,
            "memory_system_metrics": memory_metrics
        }

    async def clear_cache(self, user_id: str = None, role_id: str = None, session_id: Optional[str] = None) -> None:
        """
        清除缓存

        Args:
            user_id: 用户ID，如果指定则只清除该用户的缓存
            role_id: 角色ID，如果指定则只清除该角色的缓存
            session_id: 会话ID，如果指定则只清除该会话的缓存
        """
        async with RedisLock("memory_manager_v2:clear_cache", expire=10) as lock_acquired:
            if not lock_acquired:
                self._logger.warning(f"获取清除缓存锁失败")
                return

            # 如果指定了用户ID和角色ID
            if user_id and role_id:
                if session_id:
                    # 清除特定会话的缓存
                    cache_key = f"{user_id}:{role_id}"
                    if cache_key in self._user_metadata_cache:
                        # 只清除该会话的session_id设置
                        metadata = self._user_metadata_cache[cache_key]
                        if metadata.session_id == session_id:
                            metadata.session_id = None
                else:
                    # 清除该用户角色的所有缓存
                    cache_key = f"{user_id}:{role_id}"
                    if cache_key in self._user_metadata_cache:
                        del self._user_metadata_cache[cache_key]

            # 如果只指定了用户ID，清除该用户的所有角色缓存
            elif user_id:
                keys_to_remove = []
                for key in self._user_metadata_cache:
                    if key.startswith(f"{user_id}:"):
                        keys_to_remove.append(key)

                for key in keys_to_remove:
                    del self._user_metadata_cache[key]

            # 如果都没指定，清除所有缓存
            else:
                self._user_metadata_cache.clear()
                self._performance_history.clear()

    async def force_process_pending_dialogs(self, user_id: str = None, role_id: str = None, session_id: Optional[str] = None) -> None:
        """
        强制处理待处理的对话

        Args:
            user_id: 用户ID，如果指定则只处理该用户的对话
            role_id: 角色ID，如果指定则只处理该角色的对话
            session_id: 会话ID，如果指定则只处理该会话的对话
        """
        async with RedisLock("memory_manager_v2:force_process", expire=10) as lock_acquired:
            if not lock_acquired:
                self._logger.warning(f"获取强制处理对话锁失败")
                return

            if user_id and role_id:
                # 处理特定用户角色的对话
                await self._process_dialog_batch(user_id, role_id, session_id)
            else:
                # 处理所有待处理的对话 - 需要从Redis中获取所有缓存键
                # 这里简化处理，实际应用中可能需要更复杂的逻辑
                redis = await get_async_redis()
                pattern = "memory_manager:dialog_cache:*"
                keys = await redis.keys(pattern)

                for key in keys:
                    # 解析键值获取用户ID、角色ID和会话ID
                    try:
                        cache_part = key.split(":", 3)[-1]  # 去掉前缀
                        user_id_part, role_id_part, session_id_part = self._key_builder.parse_cache_key(cache_part)
                        await self._process_dialog_batch(user_id_part, role_id_part, session_id_part)
                    except Exception as e:
                        self._logger.error(f"解析缓存键失败: {key}, 错误: {e}")

    def set_dialog_batch_size(self, batch_size: int) -> None:
        """
        设置对话批次大小

        Args:
            batch_size: 批次大小
        """
        if batch_size < 1:
            raise ValueError("批次大小必须大于0")
        self._dialog_batch_size = batch_size

    def set_auto_summarize(self, auto_summarize: bool) -> None:
        """
        设置是否自动汇总对话

        Args:
            auto_summarize: 是否自动汇总
        """
        self._auto_summarize = auto_summarize

    def get_pending_dialog_count(self, user_id: str = None, role_id: str = None, session_id: Optional[str] = None) -> int:
        """
        获取待处理对话数量

        Args:
            user_id: 用户ID
            role_id: 角色ID
            session_id: 会话ID

        Returns:
            int: 待处理对话数量
        """
        # 这需要异步调用Redis，但这个方法是同步的，所以返回0
        # 在实际应用中，可能需要改为异步方法
        return 0

    def enable_queue(self, enabled: bool = True):
        """
        启用或禁用队列处理

        Args:
            enabled: 是否启用队列
        """
        self._use_queue = enabled

        # 如果启用队列但队列管理器未初始化，则初始化队列管理器
        if enabled and self._queue_manager is None:
            self._init_queue_manager()

        self._logger.info(f"队列处理已{'启用' if enabled else '禁用'}")

    async def get_queue_status(self) -> Dict[str, Any]:
        """
        获取队列状态

        Returns:
            Dict[str, Any]: 队列状态信息，如果队列未启用则返回None
        """
        if not self._use_queue or self._queue_manager is None:
            return None

        # 确保队列已初始化
        await self._ensure_queue_initialized()

        # 获取队列状态
        return await self._queue_manager.get_queue_status()

    async def batch_store(self, items: List[Dict[str, Any]]) -> int:
        """
        批量存储记忆

        Args:
            items: 记忆列表，每项必须包含data, user_id, role_id, session_id(可选)

        Returns:
            int: 成功存储的记忆数量
        """
        if not self._use_queue or self._queue_manager is None:
            self._logger.warning("批量存储需要启用队列处理")
            return 0

        # 确保队列已初始化
        await self._ensure_queue_initialized()

        # 批量存储到队列，直接传递items，让队列管理器处理参数验证
        return await self._queue_manager.store_batch(items)

    async def close_queue(self):
        """关闭队列管理器"""
        if self._queue_manager:
            await self._queue_manager.close()
            self._logger.info("队列管理器已关闭")

    async def get_dialog_history(self, user_id: str, role_id: str, session_id: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取用户对话历史

        Args:
            user_id: 用户ID，必填
            role_id: 角色ID，必填
            session_id: 会话ID，可选，为None时表示全部会话
            limit: 获取的最大条数，None表示获取全部

        Returns:
            List[Dict[str, Any]]: 对话历史列表，按时间从旧到新排序
        """
        # 验证必填参数
        if not user_id or not role_id:
            self._logger.error(f"获取对话历史失败: user_id和role_id都是必填字段")
            return []

        self._logger.debug(f"获取对话历史，用户: {user_id}, 角色: {role_id}, 会话: {session_id or 'all_sessions'}, 限制: {limit or '全部'}")
        return await self._history_manager.get_dialog_history(user_id, role_id, session_id, limit)

    async def clear_dialog_history(self, user_id: str, role_id: str, session_id: Optional[str] = None) -> bool:
        """
        清空用户对话历史

        Args:
            user_id: 用户ID，必填
            role_id: 角色ID，必填
            session_id: 会话ID，可选，为None时表示全部会话

        Returns:
            bool: 操作是否成功
        """
        # 验证必填参数
        if not user_id or not role_id:
            self._logger.error(f"清空对话历史失败: user_id和role_id都是必填字段")
            return False

        self._logger.debug(f"清空对话历史，用户: {user_id}, 角色: {role_id}, 会话: {session_id or 'all_sessions'}")
        return await self._history_manager.clear_dialog_history(user_id, role_id, session_id)

    def set_max_history_size(self, size: int) -> None:
        """
        设置最大历史对话轮数

        Args:
            size: 最大历史对话轮数
        """
        self._history_manager.set_max_history_size(size)
        self._logger.info(f"设置最大历史对话轮数为: {size}")

    def get_max_history_size(self) -> int:
        """
        获取最大历史对话轮数

        Returns:
            int: 最大历史对话轮数
        """
        return self._history_manager.get_max_history_size()