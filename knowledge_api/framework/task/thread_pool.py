"""thread pool implementation module
Provides an enhanced thread pool based on concurrent.futures to support asynchronous tasks"""
import asyncio
import concurrent.futures
import logging
import functools
import time
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, Generic, Awaitable

from contextlib import asynccontextmanager

# Define type variables
T = TypeVar('T')
R = TypeVar('R')

class ThreadPoolExecutorEnhanced(concurrent.futures.ThreadPoolExecutor):
    """Enhanced thread pool executor
Extends the standard ThreadPoolExecutor to include task statistics, monitoring, and asynchronous support"""
    
    def __init__(self, max_workers: Optional[int] = None, thread_name_prefix: str = '', 
                 initializer: Optional[Callable] = None, initargs: tuple = (), 
                 task_timeout: float = 60.0):
        """Initialize the enhanced thread pool

Args:
max_workers: Maximum number of worker threads, default is None (determined by the system)
thread_name_prefix: thread name prefix
Initializer: thread initialization function
Initargs: Initialize function parameters
task_timeout: Default task timeout (seconds)"""
        super().__init__(max_workers=max_workers, 
                        thread_name_prefix=thread_name_prefix,
                        initializer=initializer,
                        initargs=initargs)
        
        self.task_timeout = task_timeout
        self.logger = logging.getLogger("thread_pool")
        
        # Task Statistics
        self._active_tasks = 0
        self._completed_tasks = 0
        self._failed_tasks = 0
        self._task_times: List[float] = []
        
        # active task tracking
        self._task_registry: Dict[str, Dict[str, Any]] = {}
        
    async def submit_async(self, fn: Callable[..., T], *args, **kwargs) -> T:
        """Submit tasks asynchronously to the thread pool

Args:
Fn: Function to execute
* args: position parameter
** kwargs: keyword arguments

Returns:
The execution result of the function

Raises:
Concurrent.futures.TimeoutError: if the task execution times out
Exception: if the task fails to execute"""
        task_id = f"task_{int(time.time() * 1000)}_{self._active_tasks}"
        task_info = {
            "name": getattr(fn, "__name__", "unknown_task"),
            "start_time": time.time(),
            "status": "running"
        }
        
        self._task_registry[task_id] = task_info
        self._active_tasks += 1
        
        loop = asyncio.get_running_loop()
        
        try:
            # Use loop run_in_executor to run functions in a thread pool
            start_time = time.time()
            result = await loop.run_in_executor(
                self, 
                functools.partial(fn, *args, **kwargs)
            )
            
            execution_time = time.time() - start_time
            self._task_times.append(execution_time)
            
            # Update task information
            task_info["status"] = "completed"
            task_info["end_time"] = time.time()
            task_info["execution_time"] = execution_time
            
            self._completed_tasks += 1
            return result
            
        except Exception as e:
            # Task execution failed
            task_info["status"] = "failed"
            task_info["error"] = str(e)
            task_info["end_time"] = time.time()
            
            self._failed_tasks += 1
            self.logger.error(f"Task {task_id} failed: {str(e)}")
            raise
            
        finally:
            self._active_tasks -= 1
            
    async def submit_async_with_timeout(self, timeout: Optional[float], 
                                       fn: Callable[..., T], *args, **kwargs) -> T:
        """Asynchronous task submission with timeout control

Args:
Timeout: timeout (seconds), if None, the default timeout is used
Fn: Function to execute
* args: position parameter
** kwargs: keyword arguments

Returns:
function execution result

Raises:
asyncio. TimeoutError: if the task execution times out
Exception: if the task fails to execute"""
        actual_timeout = timeout if timeout is not None else self.task_timeout
        
        try:
            return await asyncio.wait_for(
                self.submit_async(fn, *args, **kwargs),
                timeout=actual_timeout
            )
        except asyncio.TimeoutError:
            self.logger.warning(f"Task {getattr(fn, '__name__', 'unknown')} timed out after {actual_timeout}s")
            raise
            
    def get_stats(self) -> Dict[str, Any]:
        """Get thread pool statistics

Returns:
A dictionary containing statistical information"""
        return {
            "active_tasks": self._active_tasks,
            "completed_tasks": self._completed_tasks,
            "failed_tasks": self._failed_tasks,
            "avg_task_time": sum(self._task_times) / len(self._task_times) if self._task_times else 0,
            "max_task_time": max(self._task_times) if self._task_times else 0,
            "min_task_time": min(self._task_times) if self._task_times else 0,
            "total_tasks": self._active_tasks + self._completed_tasks + self._failed_tasks
        }
        
    def get_active_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get information on currently active tasks

Returns:
Mapping task ID to task information"""
        return {
            task_id: info for task_id, info in self._task_registry.items() 
            if info["status"] == "running"
        }


# global singleton thread pool
_global_thread_pool: Optional[ThreadPoolExecutorEnhanced] = None

def get_thread_pool(max_workers: Optional[int] = None) -> ThreadPoolExecutorEnhanced:
    """Get a global thread pool instance (singleton mode)

Args:
max_workers: Maximum number of worker threads, only valid when first created

Returns:
thread pool instance"""
    global _global_thread_pool
    
    if _global_thread_pool is None:
        _global_thread_pool = ThreadPoolExecutorEnhanced(
            max_workers=max_workers,
            thread_name_prefix="fastapi-threadpool-"
        )
    
    return _global_thread_pool

@asynccontextmanager
async def thread_pool_lifespan(max_workers: Optional[int] = None):
    """Thread Pool Lifecycle Manager

Args:
max_workers: Maximum number of worker threads"""
    # Initialize the thread pool
    pool = get_thread_pool(max_workers)
    logger = logging.getLogger("thread_pool")
    logger.info(f"Thread pool initialized with {pool._max_workers} workers")
    
    try:
        yield pool
    finally:
        # Processing when the application is closed
        logger.info("Shutting down thread pool...")
        pool.shutdown(wait=True)
        logger.info(f"Thread pool shutdown completed. Stats: {pool.get_stats()}") 