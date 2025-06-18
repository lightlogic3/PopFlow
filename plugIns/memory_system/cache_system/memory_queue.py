"""
记忆系统队列管理模块
为记忆系统提供基于Redis的消息队列功能，解决高并发写入问题
"""
import asyncio
import json
import logging
import time
from typing import Dict, Any, List
from datetime import datetime

from knowledge_api.framework.redis.redis_queue import RedisMessageQueue
from knowledge_api.utils.log_config import get_logger
from knowledge_api.framework.redis.connection import get_async_redis
from knowledge_api.framework.redis.redis_lock import RedisLock
from ..model import MemoryContext
from ..utils.key_utils import MemoryKeyBuilder

logger = get_logger()

# 添加自定义的JSON编码器
class DateTimeEncoder(json.JSONEncoder):
    """处理datetime对象的JSON编码器"""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class MemoryQueueManager:
    """记忆系统队列管理器
    
    连接记忆管理器与Redis消息队列，解决高并发下记忆写入的问题。
    
    特性:
    - 完全基于Redis实现队列管理，不依赖内存缓存
    - 支持异步存储记忆，避免API阻塞
    - 消息持久化确保记忆不丢失
    - 自动重试机制处理暂时性故障
    - 批量处理提高性能
    - 支持优先级，确保重要记忆优先处理
    - 自动处理等待队列，确保按顺序处理所有消息
    
    示例:
        ```python
        # 创建队列管理器
        queue_manager = MemoryQueueManager(memory_manager)
        
        # 初始化队列和消费者
        await queue_manager.initialize()
        
        # 使用队列存储记忆
        await queue_manager.store_memory(
            data={"content": "这是一条重要记忆"},
            user_id="user_123",
            role_id="assistant",
            session_id="session_001"
        )
        ```
    """
    
    def __init__(
        self, 
        memory_manager,
        queue_name: str = "memory_tasks",
        max_retries: int = 3,
        batch_size: int = 10,
        poll_interval: float = 1.0,
        enable_priority: bool = True,
        auto_start: bool = True
    ):
        """
        初始化记忆队列管理器
        
        Args:
            memory_manager: 记忆管理器实例
            queue_name: 队列名称
            max_retries: 消息处理最大重试次数
            batch_size: 批处理大小
            poll_interval: 轮询间隔(秒)
            enable_priority: 是否启用优先级
            auto_start: 是否自动启动消费者
        """
        self.memory_manager = memory_manager
        self.queue = RedisMessageQueue(
            queue_name=queue_name,
            max_retries=max_retries,
            batch_size=batch_size,
            processing_timeout=300,  # 5分钟处理超时
            enable_priority=enable_priority
        )
        self.poll_interval = poll_interval
        self.auto_start = auto_start
        self.consumer_task = None
        self._initialized = False
        
        # 记录处理统计
        self._stats = {
            "processed_count": 0,
            "success_count": 0,
            "error_count": 0,
            "retry_count": 0,
            "start_time": None
        }
        
    async def initialize(self):
        """初始化队列管理器，启动消费者"""
        if self._initialized:
            return
            
        # 初始化统计信息
        self._stats["start_time"] = datetime.now().isoformat()
        
        # 确保Redis连接可用
        redis = await get_async_redis()
        if not redis:
            logger.error("Redis连接不可用，队列管理器无法初始化")
            return
            
        # 启动消费者
        if self.auto_start:
            self.consumer_task = asyncio.create_task(
                self.queue.start_consumer(
                    callback=self._process_memory_message,
                    poll_interval=self.poll_interval
                )
            )
            logger.info("记忆队列消费者已启动，轮询间隔: {:.1f}秒".format(self.poll_interval))
            
        self._initialized = True
        logger.info("记忆队列管理器初始化完成")
        
    async def store_memory(
        self, 
        data: Dict[str, Any], 
        user_id: str = None, 
        role_id: str = None,
        session_id: str = None,
        priority: int = 0
    ) -> bool:
        """
        异步存储记忆到队列
        
        Args:
            data: 记忆数据
            user_id: 用户ID，必填
            role_id: 角色ID，必填，用于角色隔离
            session_id: 会话ID，可选，为None时表示全部会话
            priority: 优先级(0-9，值越小优先级越高)
            
        Returns:
            bool: 是否成功加入队列
        """
        if not self._initialized:
            await self.initialize()
            
        # 检查必填参数
        if not user_id:
            logger.error("存储记忆失败: user_id不能为空")
            return False
            
        if not role_id:
            logger.error("存储记忆失败: role_id不能为空")
            return False
            
        # 添加时间戳，如果没有
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat()
            
        # 准备消息
        message = {
            "data": data,
            "user_id": user_id,
            "role_id": role_id,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "queue_time": time.time()
        }
        
        # 添加到队列
        success = await self.queue.send_message(
            data=message,
            priority=priority
        )
        
        if success:
            logger.info(f"记忆已添加到队列，用户ID: {user_id}, 角色ID: {role_id}, 会话ID: {session_id or 'all_sessions'}, 优先级: {priority}")
        else:
            logger.error(f"记忆添加到队列失败，用户ID: {user_id}, 角色ID: {role_id}")
            
        return success
    
    async def store_batch(self, items: List[Dict[str, Any]]) -> int:
        """
        批量存储记忆到队列
        
        Args:
            items: 记忆列表，每项必须包含data, user_id, role_id, 以及可选的session_id
            
        Returns:
            int: 成功加入队列的记忆数量
        """
        if not self._initialized:
            await self.initialize()
            
        # 准备消息
        messages = []
        current_time = datetime.now().isoformat()
        queue_time = time.time()
        
        for item in items:
            if not isinstance(item, dict) or 'data' not in item:
                logger.warning(f"跳过无效的记忆项: {item}")
                continue
                
            # 检查必填字段
            if 'user_id' not in item or not item['user_id']:
                logger.warning(f"跳过缺少user_id的记忆项: {item}")
                continue
                
            if 'role_id' not in item or not item['role_id']:
                logger.warning(f"跳过缺少role_id的记忆项: {item}")
                continue
                
            # 添加时间戳，如果没有
            if 'timestamp' not in item["data"]:
                item["data"]['timestamp'] = current_time
                
            # 获取session_id
            session_id = item.get("session_id")
                
            message = {
                "data": item["data"],
                "user_id": item.get("user_id"),
                "role_id": item.get("role_id"),
                "session_id": session_id,
                "timestamp": current_time,
                "queue_time": queue_time,
                "priority": item.get("priority", 0)
            }
            messages.append(message)
            
        if not messages:
            return 0
            
        # 批量添加到队列
        success_count = await self.queue.send_batch(messages)
        
        logger.info(f"批量添加记忆到队列，成功: {success_count}/{len(items)}")
        return success_count
    
    async def add_to_dialog_cache(self, user_id: str, role_id: str, session_id: str, data: Dict[str, Any]) -> bool:
        """
        将对话添加到Redis缓存
        
        Args:
            user_id: 用户ID，必填
            role_id: 角色ID，必填，用于角色隔离
            session_id: 会话ID，可选，为None时表示全部会话
            data: 对话数据
            
        Returns:
            bool: 是否成功添加
        """
        if not user_id:
            logger.error("添加对话到缓存失败: user_id不能为空")
            return False
            
        if not role_id:
            logger.error("添加对话到缓存失败: role_id不能为空")
            return False
            
        # 使用MemoryKeyBuilder构建缓存键
        key_builder = MemoryKeyBuilder()
        cache_key = key_builder.build_dialog_cache_key(user_id, role_id, session_id)
        
        try:
            redis = await get_async_redis()
            
            # 将数据序列化为JSON，使用自定义编码器处理datetime对象
            data_json = json.dumps(data, cls=DateTimeEncoder, ensure_ascii=False)
            
            # 添加到Redis列表
            await redis.rpush(cache_key, data_json)
            
            # 获取当前缓存大小
            cache_size = await redis.llen(cache_key)
            
            session_display = session_id if session_id else "all_sessions"
            logger.info(f"对话添加到Redis缓存，用户: {user_id}, 角色: {role_id}, 会话: {session_display}, 当前缓存大小: {cache_size}")
            return True
        except Exception as e:
            logger.error(f"添加对话到Redis缓存失败: {e}")
            return False
    
    async def get_dialog_cache_size(self, user_id: str, role_id: str, session_id: str = None) -> int:
        """
        获取Redis缓存中的对话数量
        
        Args:
            user_id: 用户ID，必填
            role_id: 角色ID，必填，用于角色隔离
            session_id: 会话ID，可选，为None时表示全部会话
            
        Returns:
            int: 缓存中的对话数量
        """
        if not user_id or not role_id:
            return 0
            
        # 使用MemoryKeyBuilder构建缓存键
        key_builder = MemoryKeyBuilder()
        cache_key = key_builder.build_dialog_cache_key(user_id, role_id, session_id)
        
        try:
            redis = await get_async_redis()
            return await redis.llen(cache_key)
        except Exception as e:
            logger.error(f"获取Redis缓存大小失败: {e}")
            return 0
    
    async def get_and_clear_dialog_cache(self, user_id: str, role_id: str, session_id: str = None) -> List[Dict[str, Any]]:
        """
        获取并清空Redis缓存中的对话
        
        Args:
            user_id: 用户ID，必填
            role_id: 角色ID，必填，用于角色隔离
            session_id: 会话ID，可选，为None时表示全部会话
            
        Returns:
            List[Dict[str, Any]]: 缓存中的对话列表
        """
        if not user_id or not role_id:
            return []
            
        # 使用MemoryKeyBuilder构建缓存键
        key_builder = MemoryKeyBuilder()
        cache_key = key_builder.build_dialog_cache_key(user_id, role_id, session_id)
        
        try:
            redis = await get_async_redis()
            
            # 使用管道操作，原子性获取并清空列表
            async with redis.pipeline() as pipe:
                # 获取所有元素
                await pipe.lrange(cache_key, 0, -1)
                # 删除列表
                await pipe.delete(cache_key)
                # 执行操作
                results = await pipe.execute()
                
            # 解析结果
            dialog_jsons = results[0]
            
            if not dialog_jsons:
                session_display = session_id if session_id else "all_sessions"
                logger.info(f"Redis缓存为空，用户: {user_id}, 角色: {role_id}, 会话: {session_display}")
                return []
                
            # 将JSON解析为对象
            dialogs = []
            for dialog_json in dialog_jsons:
                try:
                    dialog = json.loads(dialog_json)
                    dialogs.append(dialog)
                except Exception as e:
                    logger.error(f"解析缓存对话失败: {e}")
            
            session_display = session_id if session_id else "all_sessions"
            logger.info(f"从Redis缓存获取并清空 {len(dialogs)} 条对话，用户: {user_id}, 角色: {role_id}, 会话: {session_display}")
            return dialogs
        except Exception as e:
            logger.error(f"获取并清空Redis缓存失败: {e}")
            return []
    
    async def add_to_waiting_queue(self, user_id: str, role_id: str, session_id: str, dialogs: List[Dict[str, Any]]) -> bool:
        """
        将对话添加到Redis等待队列
        
        Args:
            user_id: 用户ID，必填
            role_id: 角色ID，必填，用于角色隔离
            session_id: 会话ID，可选，为None时表示全部会话
            dialogs: 对话列表
            
        Returns:
            bool: 是否成功添加
        """
        if not user_id or not role_id:
            return False
            
        if not dialogs:
            return True
            
        # 使用MemoryKeyBuilder构建等待队列键
        key_builder = MemoryKeyBuilder()
        waiting_key = key_builder.build_waiting_queue_key(user_id, role_id, session_id)
        
        try:
            redis = await get_async_redis()
            
            # 将数据序列化为JSON并添加到Redis列表，使用自定义编码器处理datetime对象
            pipeline = redis.pipeline()
            for dialog in dialogs:
                dialog_json = json.dumps(dialog, cls=DateTimeEncoder, ensure_ascii=False)
                pipeline.rpush(waiting_key, dialog_json)
            await pipeline.execute()
            
            # 获取当前等待队列大小
            queue_size = await redis.llen(waiting_key)
            
            session_display = session_id if session_id else "all_sessions"
            logger.info(f"已将 {len(dialogs)} 条对话添加到等待队列，当前队列大小: {queue_size}，用户: {user_id}, 角色: {role_id}, 会话: {session_display}")
            return True
        except Exception as e:
            logger.error(f"添加对话到等待队列失败: {e}")
            return False
    
    async def get_and_clear_waiting_queue(self, user_id: str, role_id: str, session_id: str = None) -> List[Dict[str, Any]]:
        """
        获取并清空Redis等待队列中的对话
        
        Args:
            user_id: 用户ID，必填
            role_id: 角色ID，必填，用于角色隔离
            session_id: 会话ID，可选，为None时表示全部会话
            
        Returns:
            List[Dict[str, Any]]: 等待队列中的对话列表
        """
        if not user_id or not role_id:
            return []
            
        # 使用MemoryKeyBuilder构建等待队列键
        key_builder = MemoryKeyBuilder()
        waiting_key = key_builder.build_waiting_queue_key(user_id, role_id, session_id)
        
        try:
            redis = await get_async_redis()
            
            # 使用管道操作，原子性获取并清空列表
            async with redis.pipeline() as pipe:
                # 获取所有元素
                await pipe.lrange(waiting_key, 0, -1)
                # 删除列表
                await pipe.delete(waiting_key)
                # 执行操作
                results = await pipe.execute()
                
            # 解析结果
            dialog_jsons = results[0]
            
            if not dialog_jsons:
                return []
                
            # 将JSON解析为对象
            dialogs = []
            for dialog_json in dialog_jsons:
                try:
                    dialog = json.loads(dialog_json)
                    dialogs.append(dialog)
                except Exception as e:
                    logger.error(f"解析等待队列对话失败: {e}")
            
            session_display = session_id if session_id else "all_sessions"
            logger.info(f"从等待队列获取并清空 {len(dialogs)} 条对话，用户: {user_id}, 角色: {role_id}, 会话: {session_display}")
            return dialogs
        except Exception as e:
            logger.error(f"获取并清空等待队列失败: {e}")
            return []
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """
        获取队列状态
        
        Returns:
            Dict[str, Any]: 队列状态信息
        """
        if not self._initialized:
            await self.initialize()
            
        # 获取队列长度
        queue_length = await self.queue.get_queue_length()
        
        # 获取统计信息
        stats = self._stats.copy()
        stats["queue_length"] = queue_length
        
        # 计算处理速率（每秒处理的消息数）
        if stats["start_time"]:
            start_time = datetime.fromisoformat(stats["start_time"])
            elapsed_seconds = (datetime.now() - start_time).total_seconds()
            if elapsed_seconds > 0:
                stats["processing_rate"] = stats["processed_count"] / elapsed_seconds
            else:
                stats["processing_rate"] = 0
        else:
            stats["processing_rate"] = 0
            
        # 获取Redis内存使用情况
        try:
            redis = await get_async_redis()
            memory_info = await redis.info("memory")
            stats["redis_used_memory"] = memory_info.get("used_memory_human", "未知")
        except Exception as e:
            logger.error(f"获取Redis内存信息失败: {e}")
            stats["redis_used_memory"] = "获取失败"
        
        # 返回队列状态
        return {
            **stats,
            "consumer_running": self.consumer_task is not None and not self.consumer_task.done(),
            "initialized": self._initialized
        }
    
    async def _process_memory_message(self, message: Dict[str, Any]) -> bool:
        """
        处理记忆消息
        
        Args:
            message: 消息数据
            
        Returns:
            bool: 处理是否成功
        """
        start_time = time.time()
        self._stats["processed_count"] += 1
        
        try:
            # 提取消息内容
            data = message.get("data")
            user_id = message.get("user_id")
            role_id = message.get("role_id")
            session_id = message.get("session_id")
            queue_time = message.get("queue_time", 0)
            
            if not data:
                logger.warning("收到空记忆数据，跳过处理")
                self._stats["success_count"] += 1
                return True  # 返回True表示处理完成，避免重试
            
            if not user_id or not role_id:
                logger.error(f"记忆消息缺少必要字段: user_id={user_id}, role_id={role_id}")
                self._stats["error_count"] += 1
                return False
                
            # 计算消息在队列中等待的时间
            wait_time = time.time() - queue_time if queue_time else 0
            session_display = session_id if session_id else "all_sessions"
            logger.info(f"处理记忆消息 - 用户: {user_id}, 角色: {role_id}, 会话: {session_display}, 等待时间: {wait_time:.2f}秒")
            
            # 获取对话批次大小
            dialog_batch_size = getattr(self.memory_manager, "_dialog_batch_size", 1)
            
            # 使用Redis添加到对话缓存
            await self.add_to_dialog_cache(user_id, role_id, session_id, data)
            
            # 获取当前缓存大小
            cache_size = await self.get_dialog_cache_size(user_id, role_id, session_id)
            
            # 检查是否有处理任务在执行
            key_builder = MemoryKeyBuilder()
            redis = await get_async_redis()
            processing_lock_key = key_builder.build_processing_lock_key(user_id, role_id, session_id)
            is_processing = await redis.exists(f"redis_lock:{processing_lock_key}")
            
            # 检查是否需要触发处理
            should_process = cache_size >= dialog_batch_size
            
            logger.info(f"队列消息状态 - 用户: {user_id}, 角色: {role_id}, 会话: {session_display}, 缓存大小: {cache_size}, " +
                      f"批次大小: {dialog_batch_size}, 是否处理中: {is_processing}, 是否应处理: {should_process}")
            
            # 如果达到批次大小且没有处理任务在执行，创建处理任务
            if should_process and not is_processing:
                # 获取处理锁
                process_lock = RedisLock(processing_lock_key, expire=60, max_retries=3)
                
                if await process_lock.acquire():
                    logger.info(f"获取处理锁成功，开始处理对话批次，用户: {user_id}, 角色: {role_id}, 会话: {session_display}")
                    
                    # 创建后台任务处理对话批次
                    try:
                        dialogs = await self.get_and_clear_dialog_cache(user_id, role_id, session_id)
                        
                        if dialogs:
                            # 使用MemoryManager的内部方法处理对话批次
                            asyncio.create_task(self._process_dialogs(
                                user_id, role_id, session_id, dialogs, process_lock
                            ))
                            logger.info(f"创建处理任务成功，用户: {user_id}, 角色: {role_id}, 会话: {session_display}")
                        else:
                            # 如果没有对话需要处理，释放锁
                            await process_lock.release()
                            logger.info(f"缓存为空，释放处理锁，用户: {user_id}, 角色: {role_id}, 会话: {session_display}")
                    except Exception as e:
                        # 如果创建任务失败，释放锁
                        await process_lock.release()
                        logger.error(f"创建处理任务失败: {e}")
                        self._stats["error_count"] += 1
                        return False
                else:
                    logger.info(f"获取处理锁失败，可能有其他任务正在处理，用户: {user_id}, 角色: {role_id}, 会话: {session_display}")
                    
                    # 检查是否需要加入等待队列
                    if should_process:
                        # 获取对话并加入等待队列
                        dialogs = await self.get_and_clear_dialog_cache(user_id, role_id, session_id)
                        if dialogs:
                            await self.add_to_waiting_queue(user_id, role_id, session_id, dialogs)
            
            # 处理成功
            self._stats["success_count"] += 1
            
            # 记录处理时间
            process_time = time.time() - start_time
            logger.info(f"消息处理完成，耗时: {process_time:.3f}秒")
            
            return True
        except Exception as e:
            self._stats["error_count"] += 1
            self._stats["retry_count"] += 1
            logger.error(f"处理记忆消息异常: {e}")
            return False
    
    async def _process_dialogs(self, user_id: str, role_id: str, session_id: str, dialogs: List[Dict[str, Any]], process_lock: RedisLock):
        """
        处理对话批次
        
        Args:
            user_id: 用户ID
            role_id: 角色ID
            session_id: 会话ID
            dialogs: 对话列表
            process_lock: 处理锁
        """
        logger.info(f"===== 开始处理对话批次 =====")
        session_display = session_id if session_id else "all_sessions"
        logger.info(f"批次信息 - 用户: {user_id}, 角色: {role_id}, 会话: {session_display}, 对话数量: {len(dialogs)}")
        
        try:
            # 构建用户元数据
            user_metadata = await self.memory_manager.get_or_create_user_metadata(user_id, role_id, session_id)
            
            # 获取并记录当前auto_summarize设置
            auto_summarize = getattr(self.memory_manager, "_auto_summarize", False)
            logger.info(f"当前auto_summarize设置: {auto_summarize}")
            
            # 处理对话批次 - 强制启用汇总
            if len(dialogs) > 1:
                # 强制汇总对话
                logger.info(f"强制执行对话汇总，对话数量: {len(dialogs)}")
                summarized_data = self.memory_manager._summarize_dialog_batch(dialogs)
                
                # 存储汇总后的数据
                try:
                    # 确保传给插件的是MemoryContext对象
                    if isinstance(summarized_data, dict):
                        memory_context = MemoryContext.from_dict(summarized_data)
                    else:
                        memory_context = summarized_data
                    await self.memory_manager._current_memory.store(memory_context, user_metadata=user_metadata)
                    logger.info(f"汇总数据存储成功，用户: {user_id}, 角色: {role_id}, 会话: {session_display}")
                except Exception as e:
                    logger.error(f"汇总数据存储失败: {e}")
            else:
                # 只有一条对话，直接存储
                # 确保传给插件的是MemoryContext对象
                if isinstance(dialogs[0], dict):
                    memory_context = MemoryContext.from_dict(dialogs[0])
                else:
                    memory_context = dialogs[0]
                await self.memory_manager._current_memory.store(memory_context, user_metadata=user_metadata)
                logger.info(f"单条对话存储成功，用户: {user_id}, 角色: {role_id}, 会话: {session_display}")
        except Exception as e:
            logger.error(f"处理对话批次异常: {e}")
        finally:
            # 释放处理锁
            try:
                await process_lock.release()
                logger.info(f"释放处理锁，用户: {user_id}, 角色: {role_id}, 会话: {session_display}")
                
                # 检查等待队列是否有新的对话需要处理
                waiting_dialogs = await self.get_and_clear_waiting_queue(user_id, role_id, session_id)
                
                if waiting_dialogs:
                    logger.info(f"等待队列中有 {len(waiting_dialogs)} 条对话，将加入缓存并触发处理")
                    
                    # 添加到缓存
                    for dialog in waiting_dialogs:
                        await self.add_to_dialog_cache(user_id, role_id, session_id, dialog)
                    
                    # 获取当前缓存大小
                    cache_size = await self.get_dialog_cache_size(user_id, role_id, session_id)
                    
                    # 获取对话批次大小
                    dialog_batch_size = getattr(self.memory_manager, "_dialog_batch_size", 1)
                    
                    # 如果达到批次大小，创建新的处理任务
                    if cache_size >= dialog_batch_size:
                        logger.info(f"缓存大小({cache_size})达到批次大小({dialog_batch_size})，触发处理")
                        asyncio.create_task(self.memory_manager._process_dialog_batch(user_id, role_id, session_id))
            except Exception as e:
                logger.error(f"释放处理锁或处理等待队列失败: {e}")
            
            logger.info(f"===== 对话批次处理结束 =====")
    
    async def close(self):
        """关闭队列管理器，停止消费者"""
        if not self._initialized:
            return
            
        if self.consumer_task and not self.consumer_task.done():
            # 发送停止信号
            self.queue.stop_consumer()
            
            # 等待任务完成
            try:
                await asyncio.wait_for(self.consumer_task, timeout=5.0)
                logger.info("消费者任务正常结束")
            except asyncio.TimeoutError:
                # 强制取消
                self.consumer_task.cancel()
                try:
                    await self.consumer_task
                except asyncio.CancelledError:
                    logger.info("消费者任务已强制取消")
                    
            self.consumer_task = None
            
        # 记录统计信息
        logger.info(f"队列管理器关闭，处理统计: 总处理 {self._stats['processed_count']} 条, " +
                  f"成功 {self._stats['success_count']} 条, 错误 {self._stats['error_count']} 条")
            
        self._initialized = False
        logger.info("记忆队列管理器已关闭") 