"""Task Decorator Module
Provides decorators for asynchronous task processing for easy interface integration"""
import asyncio
import functools
import logging
import time
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, cast, Awaitable

from .task_manager import get_task_manager, Task, TaskStatus

# Type variable definition
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])

# Logger
logger = logging.getLogger("task_decorators")


def background_task(timeout: Optional[float] = None, description: str = ""):
    """Background task decorator
Mark the function as a background task, execute it asynchronously, and immediately return the task ID.

Args:
Timeout: Timeout of the task in seconds
Description: Mission description

Returns:
decorator function"""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> str:
            # Get Task Manager
            task_manager = get_task_manager()
            
            # Submit the task and return the task ID immediately.
            task_id = await task_manager.submit(
                func=func,
                args=args,
                kwargs=kwargs,
                timeout=timeout,
                description=description or func.__name__,
                wait=False
            )
            
            return task_id
            
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> str:
            # For synchronous functions, run asynchronous versions using an event loop
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # If there is no running event loop, create a new one
                loop = asyncio.new_event_loop()
                return loop.run_until_complete(async_wrapper(*args, **kwargs))
            else:
                # If there is a running event loop, use create_task
                # Note: In this case we cannot wait for the result, but this is the behavior expected by the background task
                asyncio.create_task(async_wrapper(*args, **kwargs))
                # Generate a temporary task ID (the actual ID will be generated when the task is created)
                return f"pending_task_{int(time.time() * 1000)}"
                
        # Decide which wrapper to use based on whether the original function is asynchronous
        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)
            
    return decorator


def async_task(timeout: Optional[float] = None, description: str = ""):
    """asynchronous task decorator
Mark a function as an asynchronous task, execute it asynchronously, and wait for the result

Args:
Timeout: Timeout of the task in seconds
Description: Mission description

Returns:
decorator function"""
    def decorator(func: Callable[..., T]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            # Get Task Manager
            task_manager = get_task_manager()
            
            # Submit the task and wait for the result
            result = await task_manager.submit(
                func=func,
                args=args,
                kwargs=kwargs,
                timeout=timeout,
                description=description or func.__name__,
                wait=True
            )
            
            return result
            
        return async_wrapper
            
    return decorator


def throttled_task(rate_limit: int, time_window: float = 60.0):
    """Throttle Task Decorator
Limit the number of calls to a function within a specified time window

Args:
rate_limit: Maximum number of calls in a time window
time_window: Time window length in seconds

Returns:
decorator function"""
    # Create a throttle status dictionary
    throttle_state = {
        "calls": [],  # Call timestamp list
        "current_tokens": rate_limit,  # Number of currently available tokens
        "last_refill": time.time()  # Last token replenishment time
    }
    
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Check and update token buckets
            now = time.time()
            elapsed = now - throttle_state["last_refill"]
            
            # Calculate the number of new available tokens
            new_tokens = min(
                rate_limit,
                throttle_state["current_tokens"] + int(elapsed * (rate_limit / time_window))
            )
            
            if new_tokens <= 0:
                # No token available, request rejected
                raise RuntimeError(f"Rate limit exceeded for {func.__name__}. "
                                 f"Limit: {rate_limit} calls per {time_window} seconds")
                                 
            # update status
            throttle_state["current_tokens"] = new_tokens - 1
            throttle_state["last_refill"] = now
            
            # execution function
            return await func(*args, **kwargs)
            
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Check and update token buckets
            now = time.time()
            elapsed = now - throttle_state["last_refill"]
            
            # Calculate the number of new available tokens
            new_tokens = min(
                rate_limit,
                throttle_state["current_tokens"] + int(elapsed * (rate_limit / time_window))
            )
            
            if new_tokens <= 0:
                # No token available, request rejected
                raise RuntimeError(f"Rate limit exceeded for {func.__name__}. "
                                 f"Limit: {rate_limit} calls per {time_window} seconds")
                                 
            # update status
            throttle_state["current_tokens"] = new_tokens - 1
            throttle_state["last_refill"] = now
            
            # execution function
            return func(*args, **kwargs)
            
        # Decide which wrapper to use based on whether the original function is asynchronous
        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)
            
    return decorator


def retry_task(max_retries: int = 3, retry_delay: float = 1.0, 
              exceptions: Union[type, tuple] = Exception):
    """Retry task decorator
Automatically retry functions on failure

Args:
max_retries:
retry_delay: Retry interval (seconds)
Exceptions: Exception type that triggers retry

Returns:
decorator function"""
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            retries = 0
            last_exception = None
            
            while retries <= max_retries:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    last_exception = e
                    
                    if retries <= max_retries:
                        logger.warning(
                            f"Retry {retries}/{max_retries} for {func.__name__} "
                            f"after error: {str(e)}"
                        )
                        # Wait for a while and try again.
                        await asyncio.sleep(retry_delay)
                    else:
                        # Reach the maximum number of retries and rethrow the last caught exception
                        logger.error(
                            f"Max retries ({max_retries}) reached for {func.__name__}. "
                            f"Last error: {str(e)}"
                        )
                        raise last_exception
                        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            retries = 0
            last_exception = None
            
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    last_exception = e
                    
                    if retries <= max_retries:
                        logger.warning(
                            f"Retry {retries}/{max_retries} for {func.__name__} "
                            f"after error: {str(e)}"
                        )
                        # Wait for a while and try again.
                        time.sleep(retry_delay)
                    else:
                        # Reach the maximum number of retries and rethrow the last caught exception
                        logger.error(
                            f"Max retries ({max_retries}) reached for {func.__name__}. "
                            f"Last error: {str(e)}"
                        )
                        raise last_exception
                        
        # Decide which wrapper to use based on whether the original function is asynchronous
        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)
            
    return decorator 