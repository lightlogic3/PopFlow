import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from knowledge_api.framework.redis.connection import get_async_redis
from knowledge_api.framework.redis.redis_lock import RedisLock
from ..utils.json_utils import serialize_with_datetime, deserialize_datetime_aware
from ..utils.key_utils import MemoryKeyBuilder
from ..model import MemoryContext


class DialogBatchProcessor:
    """对话批次处理器"""
    
    def __init__(self, memory_manager):
        """
        初始化处理器
        
        Args:
            memory_manager: 记忆管理器实例
        """
        self.memory_manager = memory_manager
        self._logger = logging.getLogger("DialogBatchProcessor")
        self._key_builder = MemoryKeyBuilder()
    
    async def process_dialog_batch(self, user_id: str, role_id: str, session_id: Optional[str] = None) -> bool:
        """
        处理对话批次

        Args:
            user_id: 用户ID
            role_id: 角色ID
            session_id: 会话ID

        Returns:
            bool: 处理是否成功
        """
        cache_key = self._key_builder.build_user_cache_key(user_id, role_id, session_id)
        self._logger.info(f"===== 开始处理对话批次 =====")
        self._logger.info(f"处理批次参数: user_id={user_id}, role_id={role_id}, session_id={session_id}")

        # 使用Redis锁检查是否正在处理
        processing_lock_key = self._key_builder.build_processing_lock_key(user_id, role_id, session_id)
        processing_lock = RedisLock(processing_lock_key, expire=60, max_retries=3)
        is_processing = False

        try:
            # 尝试获取处理锁
            self._logger.info(f"尝试获取处理锁: {cache_key}")
            is_processing = await processing_lock.acquire()

            if not is_processing:
                self._logger.warning(f"用户 {user_id} 角色 {role_id} 的对话批次正在处理中，将当前对话加入等待队列")

                # 获取当前缓存中的对话
                dialog_batch = await self._get_dialog_batch(user_id, role_id, session_id)

                if not dialog_batch:
                    self._logger.info(f"缓存中没有对话需要处理，用户: {user_id}, 角色: {role_id}")
                    return True

                # 将对话添加到等待队列
                return await self._add_to_waiting_queue(user_id, role_id, session_id, dialog_batch)

            self._logger.info(f"成功获取处理锁，开始处理用户 {user_id} 角色 {role_id} 的对话批次")

            # 获取缓存并处理
            dialog_batch = await self._get_dialog_batch(user_id, role_id, session_id)

            if not dialog_batch:
                self._logger.info(f"没有对话需要处理，用户: {user_id}, 角色: {role_id}")
                await processing_lock.release()
                self._logger.info(f"释放处理锁 (无对话): {cache_key}")
                return True

            # 在后台处理
            self._logger.info(f"创建后台任务处理 {len(dialog_batch)} 条对话，用户: {user_id}, 角色: {role_id}")
            task = asyncio.create_task(self._background_store(user_id, role_id, session_id, dialog_batch, processing_lock))
            
            # 将任务添加到管理器的任务列表
            self.memory_manager._background_tasks[cache_key] = task

            # 成功创建任务
            self._logger.info(f"成功创建后台处理任务: {cache_key}")
            return True
        except Exception as e:
            self._logger.error(f"获取处理锁过程中出错: {e}")
            # 确保处理锁被释放
            if is_processing:
                try:
                    await processing_lock.release()
                    self._logger.info(f"由于异常释放处理锁: {cache_key}")
                except Exception as release_error:
                    self._logger.error(f"释放处理锁失败: {release_error}")
            return False
        finally:
            self._logger.info(f"===== 处理对话批次结束 =====")

    async def _get_dialog_batch(self, user_id: str, role_id: str, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取并清空对话批次缓存
        
        Args:
            user_id: 用户ID
            role_id: 角色ID
            session_id: 会话ID
            
        Returns:
            List[Dict[str, Any]]: 对话批次
        """
        dialog_cache_key = self._key_builder.build_dialog_cache_key(user_id, role_id, session_id)
        self._logger.info(f"获取对话批次，用户: {user_id}, 角色: {role_id}, 会话: {session_id}")

        try:
            redis = await get_async_redis()

            # 使用管道操作，原子性获取并清空列表
            async with redis.pipeline() as pipe:
                # 获取所有元素
                await pipe.lrange(dialog_cache_key, 0, -1)
                # 删除列表
                await pipe.delete(dialog_cache_key)
                # 执行操作
                results = await pipe.execute()

            # 解析结果
            dialog_jsons = results[0]

            if not dialog_jsons:
                self._logger.info(f"Redis缓存中没有找到用户对话: {user_id}:{role_id}")
                return []

            # 将JSON解析为对象
            dialogs = []
            for i, dialog_json in enumerate(dialog_jsons):
                try:
                    dialog = deserialize_datetime_aware(dialog_json)
                    dialogs.append(dialog)
                    # 添加详细调试信息
                    content_preview = dialog.get('content', '')[:50] + ('...' if len(dialog.get('content', '')) > 50 else '')
                    self._logger.debug(f"获取第 {i+1} 条对话: 角色={dialog.get('source', 'unknown')}, 时间={dialog.get('timestamp', 'unknown')}, 内容={content_preview}")
                except Exception as e:
                    self._logger.error(f"解析缓存对话失败: {e}")

            self._logger.info(f"获取到 {len(dialogs)} 条对话，并清空缓存")
            
            # 输出获取到的对话摘要信息
            for i, dialog in enumerate(dialogs):
                source = dialog.get('source', 'unknown')
                timestamp = dialog.get('timestamp', 'unknown')
                content_len = len(dialog.get('content', ''))
                self._logger.info(f"对话 {i+1}: {source} | {timestamp} | 长度: {content_len}")
                
            return dialogs
        except Exception as e:
            self._logger.error(f"获取对话批次出错: {e}")
            return []

    async def _add_to_waiting_queue(self, user_id: str, role_id: str, session_id: Optional[str], dialog_batch: List[Dict[str, Any]]) -> bool:
        """
        将对话添加到等待队列
        
        Args:
            user_id: 用户ID
            role_id: 角色ID  
            session_id: 会话ID
            dialog_batch: 对话批次
            
        Returns:
            bool: 操作是否成功
        """
        waiting_key = self._key_builder.build_waiting_queue_key(user_id, role_id, session_id)
        
        try:
            redis = await get_async_redis()
            
            # 序列化对话批次
            waiting_dialogs = [serialize_with_datetime(dialog) for dialog in dialog_batch]

            # 添加到Redis等待队列
            pipeline = redis.pipeline()
            for dialog_str in waiting_dialogs:
                pipeline.rpush(waiting_key, dialog_str)
            await pipeline.execute()

            # 获取等待队列长度
            waiting_count = await redis.llen(waiting_key)

            self._logger.info(
                f"已将 {len(dialog_batch)} 条对话添加到等待队列，当前等待队列大小: {waiting_count}，用户: {user_id}, 角色: {role_id}")
            return True
        except Exception as e:
            self._logger.error(f"添加对话到等待队列失败: {e}")
            # 如果添加到等待队列失败，将对话放回缓存
            await self._restore_dialog_batch(user_id, role_id, session_id, dialog_batch)
            return False

    async def _restore_dialog_batch(self, user_id: str, role_id: str, session_id: Optional[str], dialog_batch: List[Dict[str, Any]]) -> bool:
        """
        恢复对话批次到缓存
        
        Args:
            user_id: 用户ID
            role_id: 角色ID
            session_id: 会话ID
            dialog_batch: 对话批次
            
        Returns:
            bool: 恢复是否成功
        """
        if not dialog_batch:
            return True

        dialog_cache_key = self._key_builder.build_dialog_cache_key(user_id, role_id, session_id)

        try:
            redis = await get_async_redis()

            # 序列化对话并添加到Redis列表
            pipeline = redis.pipeline()
            for dialog in dialog_batch:
                dialog_json = serialize_with_datetime(dialog)
                # 添加到列表头部，确保这些对话会被先处理
                pipeline.lpush(dialog_cache_key, dialog_json)
            await pipeline.execute()

            # 获取当前缓存大小
            cache_size = await redis.llen(dialog_cache_key)

            self._logger.info(f"已将 {len(dialog_batch)} 条对话恢复到缓存，当前缓存大小: {cache_size}，用户: {user_id}, 角色: {role_id}")
            return True
        except Exception as e:
            self._logger.error(f"恢复对话批次到缓存失败: {e}")
            return False 

    async def _background_store(self, user_id: str, role_id: str, session_id: Optional[str], 
                               dialog_batch: List[Dict[str, Any]], processing_lock: RedisLock) -> None:
        """
        后台处理存储任务

        Args:
            user_id: 用户ID
            role_id: 角色ID
            session_id: 会话ID
            dialog_batch: 对话批次
            processing_lock: 处理锁
        """
        cache_key = self._key_builder.build_user_cache_key(user_id, role_id, session_id)
        self._logger.info(f"===== 开始后台存储任务 =====")
        self._logger.info(f"后台存储参数: user_id={user_id}, role_id={role_id}, session_id={session_id}, 对话数量={len(dialog_batch)}")
        redis = await get_async_redis()

        try:
            # 获取用户元数据
            self._logger.info(f"获取用户元数据: {user_id}, role_id: {role_id}")
            user_metadata = await self.memory_manager.get_or_create_user_metadata(user_id, role_id, session_id)

            # 检查auto_summarize状态并记录日志
            self._logger.info(f"当前auto_summarize设置: {self.memory_manager._auto_summarize}")

            # 存储对话到历史缓存
            self._logger.info(f"存储 {len(dialog_batch)} 条对话到历史缓存，用户: {user_id}, 角色: {role_id}, 会话: {session_id or 'all_sessions'}")
            await self.memory_manager._history_manager.store_dialog_batch(user_id, role_id, session_id, dialog_batch)

            # 强制启用自动汇总，合并对话为一条记录
            if len(dialog_batch) > 1:
                self._logger.info(f"执行对话汇总, 对话数量: {len(dialog_batch)}")

                # 获取历史对话
                self._logger.info(f"获取用户历史对话，用户: {user_id}, 角色: {role_id}, 会话: {session_id or 'all_sessions'}")
                history_dialogs = await self.memory_manager.get_dialog_history(user_id, role_id, session_id)
                self._logger.info(f"获取到 {len(history_dialogs)} 条历史对话")

                summarized_data = self._summarize_dialog_batch(dialog_batch, history_dialogs)
                self._logger.info(f"汇总完成, 用户: {user_id}, 汇总前: {len(dialog_batch)}条, 汇总后: 1条")

                # 存储汇总后的数据
                self._logger.info(f"开始存储汇总数据, 用户: {user_id}")
                try:
                    # 确保传给插件的是MemoryContext对象
                    if isinstance(summarized_data, dict):
                        memory_context = MemoryContext.from_dict(summarized_data)
                    else:
                        memory_context = summarized_data
                    
                    await self.memory_manager._current_memory.store(memory_context, user_metadata=user_metadata)
                    self._logger.info(f"汇总数据存储成功")
                except Exception as e:
                    # 捕获容量限制和拒绝的情况
                    error_msg = str(e).lower()
                    if "capacity" in error_msg or "limit" in error_msg or "reject" in error_msg:
                        self._logger.warning(f"汇总数据存储受到限制: {e}")
                    else:
                        self._logger.error(f"汇总数据存储失败: {e}")
            else:
                # 只有一条对话，直接存储
                self._logger.info(f"开始逐个存储 {len(dialog_batch)} 条对话，用户: {user_id}")
                success_count = 0
                failed_count = 0
                pending_dialogs = []  # 存储失败但可能是因为临时问题的对话

                for i, dialog in enumerate(dialog_batch):
                    try:
                        self._logger.info(f"存储第 {i + 1}/{len(dialog_batch)} 条对话")
                        
                        # 确保传给插件的是MemoryContext对象
                        if isinstance(dialog, dict):
                            memory_context = MemoryContext.from_dict(dialog)
                        else:
                            memory_context = dialog
                            
                        await self.memory_manager._current_memory.store(memory_context, user_metadata=user_metadata)
                        success_count += 1
                        self._logger.debug(f"第 {i + 1} 条对话存储成功")
                    except Exception as e:
                        error_msg = str(e).lower()
                        # 区分容量限制和其他错误
                        if "capacity" in error_msg or "limit" in error_msg or "reject" in error_msg:
                            self._logger.warning(f"第 {i + 1} 条对话存储受限: {e}")
                            failed_count += 1
                        else:
                            self._logger.error(f"第 {i + 1} 条对话存储失败: {e}")
                            # 对于非容量限制的错误，可能是临时问题，放入待处理列表
                            pending_dialogs.append(dialog)
                            failed_count += 1

                # 如果有待处理的对话，放回缓存，下次再处理
                if pending_dialogs:
                    # 恢复到Redis缓存
                    await self._restore_dialog_batch(user_id, role_id, session_id, pending_dialogs)
                    self._logger.info(f"将 {len(pending_dialogs)} 条未成功处理的对话放回缓存")

                self._logger.info(f"对话存储完成, 成功: {success_count}/{len(dialog_batch)}, 失败: {failed_count}")

            self._logger.info(f"后台存储任务完成，用户: {user_id}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._logger.error(f"后台存储任务异常: {e}")
        finally:
            # 释放处理锁
            try:
                self._logger.info(f"准备释放处理锁，用户: {user_id}")
                await processing_lock.release()
                self._logger.info(f"处理锁释放成功，用户: {user_id}")

                # 检查等待队列中是否有新的对话需要处理
                waiting_key = self._key_builder.build_waiting_queue_key(user_id, role_id, session_id)

                # 查看等待队列大小
                waiting_count = await redis.llen(waiting_key)
                if waiting_count > 0:
                    self._logger.info(f"检测到 {waiting_count} 条等待处理的对话，用户: {user_id}, 角色: {role_id}")
                    # 创建异步任务处理等待队列
                    asyncio.create_task(self._process_waiting_queue(user_id, role_id, session_id))
                else:
                    # 查看普通缓存中是否有未处理的对话
                    dialog_cache_key = self._key_builder.build_dialog_cache_key(user_id, role_id, session_id)
                    current_cache_size = await redis.llen(dialog_cache_key)

                    if current_cache_size > 0:
                        self._logger.info(f"缓存中有 {current_cache_size} 条未处理的对话，将触发处理")
                        # 检查是否达到了批次大小
                        if current_cache_size >= self.memory_manager._dialog_batch_size:
                            # 创建异步任务处理
                            asyncio.create_task(self.process_dialog_batch(user_id, role_id, session_id))
                        else:
                            self._logger.info(
                                f"缓存大小 {current_cache_size} 未达到批次大小 {self.memory_manager._dialog_batch_size}，暂不处理")
            except Exception as e:
                self._logger.error(f"释放处理锁失败: {e}")

            # 从任务列表移除
            if cache_key in self.memory_manager._background_tasks:
                del self.memory_manager._background_tasks[cache_key]
                self._logger.info(f"从后台任务列表移除: {cache_key}")

            self._logger.info(f"===== 后台存储任务结束 =====")

    async def _process_waiting_queue(self, user_id: str, role_id: str, session_id: Optional[str] = None) -> bool:
        """
        处理等待队列中的对话
        
        Args:
            user_id: 用户ID
            role_id: 角色ID
            session_id: 会话ID
            
        Returns:
            bool: 处理是否成功
        """
        waiting_key = self._key_builder.build_waiting_queue_key(user_id, role_id, session_id)
        self._logger.info(f"===== 开始处理等待队列 =====")
        self._logger.info(f"等待队列处理参数: user_id={user_id}, role_id={role_id}, session_id={session_id}")

        redis = await get_async_redis()

        try:
            # 使用管道操作，原子性获取并清空等待队列
            async with redis.pipeline() as pipe:
                # 获取所有元素
                await pipe.lrange(waiting_key, 0, -1)
                # 删除列表
                await pipe.delete(waiting_key)
                # 执行操作
                results = await pipe.execute()

            # 解析结果
            waiting_dialogs_raw = results[0]

            if not waiting_dialogs_raw:
                self._logger.info(f"等待队列为空，无需处理")
                return True

            # 解析对话数据
            waiting_dialogs = []
            for dialog_str in waiting_dialogs_raw:
                try:
                    dialog = deserialize_datetime_aware(dialog_str)
                    waiting_dialogs.append(dialog)
                except Exception as e:
                    self._logger.error(f"解析等待队列对话失败: {e}")

            self._logger.info(f"从等待队列获取了 {len(waiting_dialogs)} 条对话")

            if not waiting_dialogs:
                return True

            # 将等待队列的对话添加到缓存
            dialog_cache_key = self._key_builder.build_dialog_cache_key(user_id, role_id, session_id)

            # 序列化对话并添加到Redis列表
            pipeline = redis.pipeline()
            for dialog in waiting_dialogs:
                dialog_json = serialize_with_datetime(dialog)
                pipeline.rpush(dialog_cache_key, dialog_json)
            await pipeline.execute()

            self._logger.info(f"将 {len(waiting_dialogs)} 条等待队列的对话添加到缓存")

            # 获取当前缓存大小
            current_cache_size = await redis.llen(dialog_cache_key)

            # 如果达到批次大小，触发处理
            if current_cache_size >= self.memory_manager._dialog_batch_size:
                self._logger.info(f"缓存大小 {current_cache_size} 达到批次大小 {self.memory_manager._dialog_batch_size}，触发处理")
                return await self.process_dialog_batch(user_id, role_id, session_id)
            else:
                self._logger.info(f"缓存大小 {current_cache_size} 未达到批次大小 {self.memory_manager._dialog_batch_size}，暂不处理")
                return True
        except Exception as e:
            self._logger.error(f"处理等待队列失败: {e}")
            return False
        finally:
            self._logger.info(f"===== 等待队列处理结束 =====")

    def _summarize_dialog_batch(self, dialog_batch: List[Dict[str, Any]],
                                history_dialogs: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        汇总对话批次为一条记录，按照特定格式组织对话内容

        Args:
            dialog_batch: 对话批次
            history_dialogs: 历史对话列表，默认为None

        Returns:
            Dict[str, Any]: 汇总后的数据
        """
        # 添加调试日志
        self._logger.info(f"开始汇总对话批次, 数量: {len(dialog_batch)}")
        if history_dialogs:
            self._logger.info(f"包含历史对话, 数量: {len(history_dialogs)}")

        # 按时间戳排序对话，确保正确的时间顺序
        try:
            sorted_dialogs = sorted(dialog_batch, key=lambda x: x.get('timestamp', ''))
            self._logger.info(f"对话已按时间戳排序")
        except Exception as e:
            self._logger.warning(f"对话排序失败，使用原始顺序: {e}")
            sorted_dialogs = dialog_batch

        # 提取所有对话内容和元数据
        formatted_dialog = []
        metadata = {}
        roles = []

        for i, dialog in enumerate(sorted_dialogs):
            # 提取角色和内容
            content = dialog.get('content', '')
            role = dialog.get('source', '').lower()
            timestamp = dialog.get('timestamp', '')

            self._logger.debug(f"处理第 {i + 1} 条对话, 角色: {role}, 时间: {timestamp}, 内容长度: {len(content)}")

            # 根据来源判断角色
            if 'assistant' in role or role == 'ai':
                current_role = 'AI'
            elif 'user' in role:
                current_role = '用户'
            else:
                current_role = role.capitalize()  # 默认使用来源作为角色

            # 始终为每条对话创建新的格式化条目，保持对话结构清晰
            if content:
                formatted_dialog.append(f"{current_role}：{content}")
                roles.append(current_role)
                self._logger.debug(f"添加对话: {current_role} - {content[:50]}...")

            # 合并元数据
            if 'metadata' in dialog and isinstance(dialog['metadata'], dict):
                for key, value in dialog['metadata'].items():
                    metadata[key] = value

        # 汇总内容
        combined_content = ""
        if formatted_dialog:
            combined_content = "\n\n".join(formatted_dialog)
            self._logger.info(
                f"格式化了 {len(sorted_dialogs)} 条对话为 {len(formatted_dialog)} 个回合, 包含角色: {set(roles)}")

        # 创建汇总记录
        summary = {
            'content': combined_content,
            'metadata': metadata,
            'timestamp': datetime.now().isoformat(),
            'is_summarized': True,
            "source_dialog": sorted_dialogs,  # 使用排序后的对话
            'summary_count': len(sorted_dialogs),
            'dialog_roles': list(set(roles)),
        }

        # 添加历史对话到汇总数据
        if history_dialogs:
            summary['history'] = history_dialogs
            self._logger.info(f"已添加 {len(history_dialogs)} 条历史对话到汇总数据")

        self._logger.info(f"汇总完成, 内容长度: {len(combined_content)}, 角色数量: {len(set(roles))}")
        self._logger.info(f"汇总内容预览: {combined_content[:100]}...")
        return summary 