"""Redis message queuing module
Provides Redis-based message queuing functionality for asynchronous processing tasks"""
import json
import time
import asyncio
import uuid
from typing import Dict, Any, List, Optional, Callable, Awaitable, Union
from datetime import datetime

from knowledge_api.framework.redis.connection import get_async_redis
from knowledge_api.utils.log_config import get_logger

logger = get_logger()

class RedisMessageQueue:
    """Redis message queue

Redis-based message queue that supports asynchronous message publishing and subscription processing

Features:
- Supports a multi-producer, multi-consumer model
Message persistence and retry mechanism
Distributed consumer coordination
- Batch message processing
- Message priority

Example:
"Python
#Create a queue
Queue = RedisMessageQueue ("memory_tasks")

#Send a message
Await queue. send_message ({"user_id": "123", "data": {"content": "message content"}})

#Define the processing function
Async def process_message (message):
Print (f "Processing message: {message}")
Returns True

Start the consumer
Await queue start_consumer (process_message)
"..."""
    
    def __init__(
        self, 
        queue_name: str,
        max_retries: int = 3,
        retry_delay: int = 60,
        batch_size: int = 10,
        processing_timeout: int = 300,
        prefix: str = "queue:",
        enable_priority: bool = False
    ):
        """Initialize message queue

Args:
queue_name: Queue name
max_retries: Maximum number of retries for message processing
retry_delay: Retry delay (seconds)
batch_size: Batch Size
processing_timeout: Processing timeout (seconds)
Prefix: key prefix
enable_priority: Whether priority is enabled"""
        self.queue_name = f"{prefix}{queue_name}"
        self.processing_queue = f"{self.queue_name}:processing"
        self.failed_queue = f"{self.queue_name}:failed"
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.batch_size = batch_size
        self.processing_timeout = processing_timeout
        self.enable_priority = enable_priority
        
        # consumer status
        self.is_running = False
        self.consumer_id = str(uuid.uuid4())
        
    async def send_message(
        self, 
        data: Dict[str, Any], 
        priority: int = 0,
        delay: int = 0
    ) -> bool:
        """Send message to queue

Args:
Data: Message data
Priority: Priority (0-9, the smaller the value, the higher the priority, only valid if enable_priority = True)
Delay: Delay processing time (seconds)

Returns:
Bool: whether it was sent successfully"""
        try:
            redis = await get_async_redis()
            
            # Prepare message
            message = {
                "id": str(uuid.uuid4()),
                "data": data,
                "created_at": datetime.now().isoformat(),
                "retry_count": 0,
                "priority": priority,
                "visible_after": int(time.time() + delay) if delay > 0 else 0
            }
            
            # Serialize message
            message_str = json.dumps(message)
            
            # Select different addition methods according to whether priority is enabled or not
            if self.enable_priority and delay == 0:
                # Implementing Priority Queues Using Ordered Collections
                score = priority * 10000000000 + int(time.time() * 1000)  # Priority + timestamp
                await redis.zadd(self.queue_name, {message_str: score})
                logger.debug(f"消息已添加到优先级队列 {self.queue_name}, 优先级: {priority}, ID: {message['id']}")
            else:
                # Implementing normal queues using lists
                if delay > 0:
                    # Delay messages are added to the delay queue
                    delay_queue = f"{self.queue_name}:delayed"
                    score = int(time.time() + delay)
                    await redis.zadd(delay_queue, {message_str: score})
                    logger.debug(f"消息已添加到延迟队列，延迟: {delay}秒, ID: {message['id']}")
                else:
                    # General Message Direct Entry
                    await redis.lpush(self.queue_name, message_str)
                    logger.debug(f"消息已添加到队列 {self.queue_name}, ID: {message['id']}")
                    
            return True
        except Exception as e:
            logger.error(f"发送消息到队列失败: {e}")
            return False
    
    async def send_batch(self, messages: List[Dict[str, Any]]) -> int:
        """send messages in bulk

Args:
Messages: Message List

Returns:
Int: Number of messages sent successfully"""
        if not messages:
            return 0
            
        try:
            redis = await get_async_redis()
            pipeline = redis.pipeline()
            
            success_count = 0
            for msg_data in messages:
                # Prepare message
                message = {
                    "id": str(uuid.uuid4()),
                    "data": msg_data,
                    "created_at": datetime.now().isoformat(),
                    "retry_count": 0,
                    "priority": 0,
                    "visible_after": 0
                }
                
                # Serialize message
                message_str = json.dumps(message)
                
                # Add to Pipeline
                pipeline.lpush(self.queue_name, message_str)
                success_count += 1
                
            # execution pipeline
            await pipeline.execute()
            logger.debug(f"批量添加了 {success_count} 条消息到队列 {self.queue_name}")
            
            return success_count
        except Exception as e:
            logger.error(f"批量发送消息失败: {e}")
            return 0
    
    async def receive_message(self) -> Optional[Dict[str, Any]]:
        """Receive a message from the queue

Returns:
Optional [Dict [str, Any]]: Message data, return None if queue is empty"""
        try:
            redis = await get_async_redis()
            
            # First check if there are any messages in the delay queue that can be processed
            delay_queue = f"{self.queue_name}:delayed"
            current_time = int(time.time())
            
            # Get all visible delayed messages
            delayed_messages = await redis.zrangebyscore(
                delay_queue, 
                0, 
                current_time, 
                start=0, 
                num=1
            )
            
            if delayed_messages:
                # Move delayed messages to the main queue
                message_str = delayed_messages[0]
                await redis.zrem(delay_queue, message_str)
                await redis.lpush(self.queue_name, message_str)
                logger.debug("Delayed messages have been moved to the main queue")
            
            # Select different acquisition methods according to whether priority is enabled or not
            if self.enable_priority:
                # Get the highest priority message from an ordered collection
                messages = await redis.zrange(self.queue_name, 0, 0)
                if messages:
                    message_str = messages[0]
                    await redis.zrem(self.queue_name, message_str)
                else:
                    return None
            else:
                # A message pops up from the right side of the list (FIFO mode)
                message_str = await redis.rpop(self.queue_name)
                if not message_str:
                    return None
            
            # deserialize message
            message = json.loads(message_str)
            
            # Add a message to the processing queue
            processing_message = {
                **message,
                "processing_started": int(time.time()),
                "consumer_id": self.consumer_id
            }
            await redis.hset(
                self.processing_queue,
                message["id"],
                json.dumps(processing_message)
            )
            
            # Set processing timeout
            await redis.expire(self.processing_queue, self.processing_timeout)
            
            return message
        except Exception as e:
            logger.error(f"接收消息失败: {e}")
            return None
    
    async def receive_batch(self, count: int = None) -> List[Dict[str, Any]]:
        """receive messages in bulk

Args:
Count: The number of messages received, the default is batch_size

Returns:
List [Dict [str, Any]]: Message list"""
        if count is None:
            count = self.batch_size
            
        try:
            redis = await get_async_redis()
            
            # Check for processed messages in the delay queue
            delay_queue = f"{self.queue_name}:delayed"
            current_time = int(time.time())
            
            # Get all visible delayed messages
            delayed_messages = await redis.zrangebyscore(
                delay_queue, 
                0, 
                current_time, 
                start=0, 
                num=count
            )
            
            if delayed_messages:
                # Move delayed messages to the main queue
                pipeline = redis.pipeline()
                for message_str in delayed_messages:
                    pipeline.zrem(delay_queue, message_str)
                    pipeline.lpush(self.queue_name, message_str)
                await pipeline.execute()
                logger.debug(f"已将 {len(delayed_messages)} 条延迟消息移至主队列")
            
            # Get message
            messages = []
            pipeline = redis.pipeline()
            
            if self.enable_priority:
                # Get the highest priority message from an ordered collection
                raw_messages = await redis.zrange(self.queue_name, 0, count - 1)
                if raw_messages:
                    for message_str in raw_messages:
                        pipeline.zrem(self.queue_name, message_str)
                        try:
                            message = json.loads(message_str)
                            messages.append(message)
                        except json.JSONDecodeError:
                            logger.error(f"解析消息失败: {message_str}")
                    await pipeline.execute()
            else:
                # Get messages from the list in bulk
                for _ in range(count):
                    message_str = await redis.rpop(self.queue_name)
                    if not message_str:
                        break
                    try:
                        message = json.loads(message_str)
                        messages.append(message)
                    except json.JSONDecodeError:
                        logger.error(f"解析消息失败: {message_str}")
            
            # Add a message to the processing queue
            if messages:
                pipeline = redis.pipeline()
                for message in messages:
                    processing_message = {
                        **message,
                        "processing_started": int(time.time()),
                        "consumer_id": self.consumer_id
                    }
                    pipeline.hset(
                        self.processing_queue,
                        message["id"],
                        json.dumps(processing_message)
                    )
                
                # Set processing timeout
                pipeline.expire(self.processing_queue, self.processing_timeout)
                await pipeline.execute()
            
            return messages
        except Exception as e:
            logger.error(f"批量接收消息失败: {e}")
            return []
    
    async def ack_message(self, message_id: str) -> bool:
        """Confirm that the message has been processed

Args:
message_id: Message ID

Returns:
Bool: confirm success"""
        try:
            redis = await get_async_redis()
            
            # Delete messages from the processing queue
            result = await redis.hdel(self.processing_queue, message_id)
            
            if result:
                logger.debug(f"消息确认成功，已从处理队列移除: {message_id}")
            else:
                logger.warning(f"消息确认失败，未找到消息或已超时: {message_id}")
                
            return bool(result)
        except Exception as e:
            logger.error(f"确认消息失败: {e}")
            return False
    
    async def nack_message(self, message_id: str, requeue: bool = True) -> bool:
        """Deny message processing, optional re-entry

Args:
message_id: Message ID
Requeue: whether to re-join the team

Returns:
Bool: whether the operation was successful"""
        try:
            redis = await get_async_redis()
            
            # Get message
            message_str = await redis.hget(self.processing_queue, message_id)
            if not message_str:
                logger.warning(f"消息否认失败，未找到消息或已超时: {message_id}")
                return False
                
            # deserialize message
            message = json.loads(message_str)
            
            # Delete messages from the processing queue
            await redis.hdel(self.processing_queue, message_id)
            
            if requeue:
                # Increase the number of retries
                message["retry_count"] = message.get("retry_count", 0) + 1
                
                # Check if the number of retries has been exceeded
                if message["retry_count"] <= self.max_retries:
                    # Set Delay Visibility Time
                    message["visible_after"] = int(time.time() + self.retry_delay)
                    
                    # Add to delay queue
                    delay_queue = f"{self.queue_name}:delayed"
                    await redis.zadd(delay_queue, {json.dumps(message): message["visible_after"]})
                    
                    logger.debug(f"消息已重新入队等待重试，重试次数: {message['retry_count']}, ID: {message_id}")
                else:
                    # Add to Failure Queue
                    await redis.lpush(self.failed_queue, json.dumps(message))
                    logger.warning(f"消息处理失败且超过最大重试次数，已移至失败队列: {message_id}")
            else:
                # Add directly to the failure queue
                await redis.lpush(self.failed_queue, json.dumps(message))
                logger.debug(f"消息已直接移至失败队列: {message_id}")
                
            return True
        except Exception as e:
            logger.error(f"否认消息失败: {e}")
            return False
    
    async def requeue_timed_out_messages(self) -> int:
        """Re-entry timeout message

Returns:
Int: number of re-enlistment messages"""
        try:
            redis = await get_async_redis()
            
            # Get all messages in process
            all_messages = await redis.hgetall(self.processing_queue)
            if not all_messages:
                return 0
                
            requeued_count = 0
            current_time = int(time.time())
            pipeline = redis.pipeline()
            
            for message_id, message_str in all_messages.items():
                try:
                    message = json.loads(message_str)
                    processing_started = message.get("processing_started", 0)
                    
                    # Check for timeout
                    if current_time - processing_started > self.processing_timeout:
                        # Increase the number of retries
                        message["retry_count"] = message.get("retry_count", 0) + 1
                        
                        # Delete from the processing queue
                        pipeline.hdel(self.processing_queue, message_id)
                        
                        # Check if the number of retries has been exceeded
                        if message["retry_count"] <= self.max_retries:
                            # Rejoin the team
                            if self.enable_priority:
                                score = message.get("priority", 0) * 10000000000 + int(time.time() * 1000)
                                pipeline.zadd(self.queue_name, {json.dumps(message): score})
                            else:
                                pipeline.lpush(self.queue_name, json.dumps(message))
                                
                            requeued_count += 1
                        else:
                            # Add to Failure Queue
                            pipeline.lpush(self.failed_queue, json.dumps(message))
                except Exception as e:
                    logger.error(f"处理超时消息出错: {e}, 消息: {message_str}")
            
            # execution pipeline
            if requeued_count > 0:
                await pipeline.execute()
                logger.info(f"已重新入队 {requeued_count} 条超时消息")
                
            return requeued_count
        except Exception as e:
            logger.error(f"重新入队超时消息失败: {e}")
            return 0
    
    async def get_queue_length(self) -> Dict[str, int]:
        """Get queue length information

Returns:
Dict [str, int]: length of each queue"""
        try:
            redis = await get_async_redis()
            
            # Get the main queue length
            if self.enable_priority:
                main_queue_length = await redis.zcard(self.queue_name)
            else:
                main_queue_length = await redis.llen(self.queue_name)
                
            # Get other queue lengths
            processing_queue_length = await redis.hlen(self.processing_queue)
            failed_queue_length = await redis.llen(self.failed_queue)
            delayed_queue_length = await redis.zcard(f"{self.queue_name}:delayed")
            
            return {
                "main": main_queue_length,
                "processing": processing_queue_length,
                "failed": failed_queue_length,
                "delayed": delayed_queue_length,
                "total": main_queue_length + processing_queue_length + delayed_queue_length
            }
        except Exception as e:
            logger.error(f"获取队列长度失败: {e}")
            return {
                "main": -1,
                "processing": -1,
                "failed": -1,
                "delayed": -1,
                "total": -1
            }
    
    async def clear_queue(self, include_failed: bool = False) -> bool:
        """clear the queue

Args:
include_failed: Whether to clear the failure queue at the same time

Returns:
Bool: Was it successful?"""
        try:
            redis = await get_async_redis()
            
            # Clear the main queue
            if self.enable_priority:
                await redis.delete(self.queue_name)
            else:
                await redis.delete(self.queue_name)
                
            # Clear the processing queue and delay queue
            await redis.delete(self.processing_queue)
            await redis.delete(f"{self.queue_name}:delayed")
            
            # Clear the failure queue
            if include_failed:
                await redis.delete(self.failed_queue)
                
            logger.info(f"队列 {self.queue_name} 已清空")
            return True
        except Exception as e:
            logger.error(f"清空队列失败: {e}")
            return False
    
    async def start_consumer(
        self, 
        callback: Callable[[Dict[str, Any]], Awaitable[bool]],
        batch_size: int = None,
        poll_interval: float = 1.0,
        batch_mode: bool = False
    ):
        """Start the consumer cycle

Args:
Callback: The callback function that handles the message, receives the message data, and returns whether it was successful or not
batch_size: Batch size, default instance batch_size
poll_interval: polling interval (seconds)
batch_mode: Whether batch mode is enabled"""
        if batch_size is None:
            batch_size = self.batch_size
            
        self.is_running = True
        logger.info(f"消息队列消费者已启动，队列: {self.queue_name}, 消费者ID: {self.consumer_id}")
        
        try:
            while self.is_running:
                # Handling delay queues and timeout messages
                try:
                    await self.requeue_timed_out_messages()
                except Exception as e:
                    logger.error(f"处理超时消息出错: {e}")
                
                try:
                    # Choose different consumption methods according to the model
                    if batch_mode:
                        # Batch mode
                        messages = await self.receive_batch(batch_size)
                        if messages:
                            logger.debug(f"批量接收到 {len(messages)} 条消息")
                            
                            # Call callback function
                            success = await callback(messages)
                            
                            # Batch confirmation or denial
                            pipeline = (await get_async_redis()).pipeline()
                            for message in messages:
                                if success:
                                    # Confirm all messages
                                    pipeline.hdel(self.processing_queue, message["id"])
                                else:
                                    # Deny all messages and increase the retry count
                                    message["retry_count"] = message.get("retry_count", 0) + 1
                                    pipeline.hdel(self.processing_queue, message["id"])
                                    
                                    if message["retry_count"] <= self.max_retries:
                                        # Rejoin the team
                                        message["visible_after"] = int(time.time() + self.retry_delay)
                                        delay_queue = f"{self.queue_name}:delayed"
                                        pipeline.zadd(delay_queue, {json.dumps(message): message["visible_after"]})
                                    else:
                                        # Add to Failure Queue
                                        pipeline.lpush(self.failed_queue, json.dumps(message))
                            
                            # execution pipeline
                            await pipeline.execute()
                        else:
                            # No news, wait.
                            await asyncio.sleep(poll_interval)
                    else:
                        # Single processing mode
                        message = await self.receive_message()
                        if message:
                            logger.debug(f"接收到消息: {message['id']}")
                            
                            # Call callback function
                            try:
                                # Increase the retry interval to avoid the same error caused by an immediate retry
                                retry_with_backoff = message.get("retry_count", 0) * 2  # exponential backoff
                                
                                # Check if the message has been processed recently (to prevent duplicate processing).
                                message_key = f"{message.get('id', '')}"
                                redis = await get_async_redis()
                                is_recently_processed = await redis.exists(f"msg_processed:{message_key}")
                                
                                if is_recently_processed:
                                    logger.warning(f"消息 {message_key} 最近已处理过，跳过")
                                    await self.ack_message(message["id"])
                                    continue
                                
                                # Set processing flag, valid period 5 minutes
                                await redis.set(f"msg_processed:{message_key}", "1", ex=300)
                                
                                # process message
                                success = await callback(message["data"])
                                
                                if success:
                                    # confirmation message
                                    await self.ack_message(message["id"])
                                    logger.debug(f"消息 {message['id']} 处理成功并确认")
                                else:
                                    # Check if the maximum number of retries has been reached
                                    if message.get("retry_count", 0) >= self.max_retries:
                                        logger.warning(f"消息 {message['id']} 已达到最大重试次数，移至失败队列")
                                        # Confirm directly and manually add to the failure queue
                                        await self.ack_message(message["id"])
                                        await redis.lpush(self.failed_queue, json.dumps(message))
                                    else:
                                        # Deny the message, re-join the team, and use the retreat strategy
                                        logger.info(f"消息 {message['id']} 处理失败，重新入队，重试次数: {message.get('retry_count', 0) + 1}")
                                        await self.nack_message(message["id"], requeue=True)
                                        
                                        # If there is a backoff delay, set the delay manually
                                        if retry_with_backoff > 0:
                                            message["retry_count"] = message.get("retry_count", 0) + 1
                                            message["visible_after"] = int(time.time() + retry_with_backoff)
                                            # Delete messages from the processing queue
                                            await redis.hdel(self.processing_queue, message["id"])
                                            # Add to delay queue
                                            delay_queue = f"{self.queue_name}:delayed"
                                            await redis.zadd(delay_queue, {json.dumps(message): message["visible_after"]})
                                            logger.info(f"消息 {message['id']} 已添加到延迟队列，延迟: {retry_with_backoff}秒")
                            except Exception as e:
                                logger.error(f"处理消息出错: {e}, 消息ID: {message['id']}")
                                # Check if the number of retries has been exceeded
                                if message.get("retry_count", 0) >= self.max_retries:
                                    logger.warning(f"消息 {message['id']} 处理出错且已达最大重试次数，移至失败队列")
                                    try:
                                        # Confirm directly and manually add to the failure queue
                                        redis = await get_async_redis()
                                        await self.ack_message(message["id"])
                                        message["error"] = str(e)[:200]  # Record error messages, but limit the length
                                        await redis.lpush(self.failed_queue, json.dumps(message))
                                    except Exception as inner_e:
                                        logger.error(f"移动消息到失败队列出错: {inner_e}")
                                else:
                                    # Deny the news, re-join the team
                                    try:
                                        await self.nack_message(message["id"], requeue=True)
                                        logger.info(f"消息 {message['id']} 处理出错，重新入队")
                                    except Exception as nack_error:
                                        logger.error(f"否认消息失败: {nack_error}")
                        else:
                            # No news, wait.
                            await asyncio.sleep(poll_interval)
                except Exception as e:
                    logger.error(f"消费者循环出错: {e}")
                    await asyncio.sleep(poll_interval)
        except asyncio.CancelledError:
            logger.info("Message queue consumer task cancelled")
        except Exception as e:
            logger.error(f"消息队列消费者异常退出: {e}")
        finally:
            self.is_running = False
            logger.info(f"消息队列消费者已停止，队列: {self.queue_name}")
    
    def stop_consumer(self):
        """Stop the consumer cycle"""
        self.is_running = False
        logger.info(f"消息队列消费者停止信号已发送，队列: {self.queue_name}") 