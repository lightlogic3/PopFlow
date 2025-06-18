"""Task Manager Module
Provides asynchronous task distribution, scheduling, and monitoring capabilities"""
import asyncio
import logging
import time
import uuid
import signal
import sys
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union, TypeVar, Generic, Awaitable, cast, Set
from datetime import datetime

from .thread_pool import get_thread_pool, ThreadPoolExecutorEnhanced

# Type variable definition
T = TypeVar('T')


# task state enumeration
class TaskStatus(str, Enum):
    """task state enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class Task(Generic[T]):
    """Task class, representing an asynchronous task"""

    def __init__(self,
                 func: Callable[..., T],
                 args: tuple = (),
                 kwargs: Dict[str, Any] = None,
                 task_id: Optional[str] = None,
                 timeout: Optional[float] = None,
                 description: str = "",
                 on_complete: Optional[Callable[[str, Any], None]] = None,
                 on_error: Optional[Callable[[str, Exception], None]] = None):
        """initialization task

Args:
Func: The function to be executed
Args: position argument
Kwargs: keyword argument, default to empty dictionary
task_id: Task ID, automatically generated if None
Timeout: Timeout time (seconds), if None, use thread pool default timeout
Description: Mission description
on_complete: Callback function on task completion
on_error: Callback function in case of task error"""
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.task_id = task_id or f"task_{str(uuid.uuid4())[:8]}"
        self.timeout = timeout
        self.description = description or getattr(func, "__name__", "unnamed_task")
        self.on_complete = on_complete
        self.on_error = on_error

        # Task status information
        self.status = TaskStatus.PENDING
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.result: Optional[T] = None
        self.error: Optional[Exception] = None

        # underlying asynchronous task
        self._task: Optional[asyncio.Task] = None

    async def execute(self) -> T:
        """Execute tasks and return results

Returns:
Task execution result

Raises:
Exception: if the task fails to execute"""
        if self.status == TaskStatus.RUNNING:
            raise RuntimeError(f"Task {self.task_id} is already running")

        if self.status == TaskStatus.COMPLETED:
            return cast(T, self.result)

        self.status = TaskStatus.RUNNING
        self.start_time = time.time()

        # If it is a temporary task (ID starts with temp_task_), log the execution
        log_id = None
        if self.task_id.startswith("temp_task_"):
            try:
                # Get database session
                from knowledge_api.framework.database.database import get_session
                from knowledge_api.mapper.task_manage import (
                    TaskManageCRUD,
                    TaskExecutionLogCRUD,
                    TaskExecutionLogCreate,
                    TaskStatus as DBTaskStatus
                )
                db = next(get_session())

                try:
                    # Create task log
                    log_crud = TaskExecutionLogCRUD(db)
                    log_create = TaskExecutionLogCreate(task_id=self.task_id)
                    log = await log_crud.create(log_create)
                    log_id = log.id

                    # Update task status to Running
                    task_crud = TaskManageCRUD(db)
                    await task_crud.update_status(self.task_id, DBTaskStatus.RUNNING)
                finally:
                    db.close()
            except Exception as e:
                logging.error(f"为临时任务 {self.task_id} 创建执行日志失败: {str(e)}")
                # Continue to execute tasks, even if log creation fails

        pool = get_thread_pool()

        try:
            # Executing a function in a thread pool
            if self.timeout is not None:
                if asyncio.iscoroutinefunction(self.func):
                    # For asynchronous functions, special handling is required
                    async def run_async_func():
                        return await self.func(*self.args, **self.kwargs)

                    self.result = await asyncio.wait_for(
                        run_async_func(),
                        timeout=self.timeout
                    )
                else:
                    # For synchronous functions, use a thread pool
                    self.result = await pool.submit_async_with_timeout(
                        self.timeout, self.func, *self.args, **self.kwargs
                    )
            else:
                if asyncio.iscoroutinefunction(self.func):
                    # For asynchronous functions, directly await
                    self.result = await self.func(*self.args, **self.kwargs)
                else:
                    # For synchronous functions, use a thread pool
                    self.result = await pool.submit_async(
                        self.func, *self.args, **self.kwargs
                    )

            self.status = TaskStatus.COMPLETED

            # call completion callback
            if self.on_complete:
                try:
                    self.on_complete(self.task_id, self.result)
                except Exception as e:
                    logging.error(f"Error in on_complete callback for task {self.task_id}: {str(e)}")

            # If it is a temporary task, update the log and task status
            if self.task_id.startswith("temp_task_") and log_id:
                try:
                    from knowledge_api.framework.database.database import get_session
                    from knowledge_api.mapper.task_manage import (
                        TaskManageCRUD,
                        TaskExecutionLogCRUD,
                        TaskStatus as DBTaskStatus
                    )
                    db = next(get_session())

                    try:
                        # changelog
                        log_crud = TaskExecutionLogCRUD(db)
                        result_str = None
                        if self.result is not None:
                            try:
                                import json
                                result_str = json.dumps(self.result)
                            except (TypeError, OverflowError):
                                result_str = str(self.result)

                        await log_crud.update(
                            log_id,
                            datetime.now(),
                            DBTaskStatus.COMPLETED,
                            result_str
                        )

                        # Update task status
                        task_crud = TaskManageCRUD(db)
                        await task_crud.update_status(self.task_id, DBTaskStatus.COMPLETED)
                    finally:
                        db.close()
                except Exception as e:
                    logging.error(f"更新临时任务 {self.task_id} 执行日志失败: {str(e)}")

            return cast(T, self.result)

        except asyncio.TimeoutError:
            self.status = TaskStatus.TIMEOUT
            self.error = asyncio.TimeoutError(f"Task {self.task_id} timed out after {self.timeout}s")

            # call error callback
            if self.on_error:
                try:
                    self.on_error(self.task_id, self.error)
                except Exception as e:
                    logging.error(f"Error in on_error callback for task {self.task_id}: {str(e)}")

            # If it is a temporary task, update the log and task status
            if self.task_id.startswith("temp_task_") and log_id:
                try:
                    from knowledge_api.framework.database.database import get_session
                    from knowledge_api.mapper.task_manage import (
                        TaskManageCRUD,
                        TaskExecutionLogCRUD,
                        TaskStatus as DBTaskStatus
                    )
                    db = next(get_session())

                    try:
                        # changelog
                        log_crud = TaskExecutionLogCRUD(db)
                        await log_crud.update(
                            log_id,
                            datetime.now(),
                            DBTaskStatus.FAILED,
                            None,
                            f"任务超时: {self.timeout}秒"
                        )

                        # Update task status
                        task_crud = TaskManageCRUD(db)
                        await task_crud.update_status(self.task_id, DBTaskStatus.FAILED)
                    finally:
                        db.close()
                except Exception as e:
                    logging.error(f"更新临时任务 {self.task_id} 执行日志失败: {str(e)}")

            raise self.error

        except Exception as e:
            self.status = TaskStatus.FAILED
            self.error = e

            # call error callback
            if self.on_error:
                try:
                    self.on_error(self.task_id, self.error)
                except Exception as callback_e:
                    logging.error(f"Error in on_error callback for task {self.task_id}: {str(callback_e)}")

            # If it is a temporary task, update the log and task status
            if self.task_id.startswith("temp_task_") and log_id:
                try:
                    from knowledge_api.framework.database.database import get_session
                    from knowledge_api.mapper.task_manage import (
                        TaskManageCRUD,
                        TaskExecutionLogCRUD,
                        TaskStatus as DBTaskStatus
                    )
                    db = next(get_session())

                    try:
                        # changelog
                        log_crud = TaskExecutionLogCRUD(db)
                        await log_crud.update(
                            log_id,
                            datetime.now(),
                            DBTaskStatus.FAILED,
                            None,
                            str(e)
                        )

                        # Update task status
                        task_crud = TaskManageCRUD(db)
                        await task_crud.update_status(self.task_id, DBTaskStatus.FAILED)
                    finally:
                        db.close()
                except Exception as log_e:
                    logging.error(f"更新临时任务 {self.task_id} 执行日志失败: {str(log_e)}")

            raise

        finally:
            self.end_time = time.time()

    def cancel(self) -> bool:
        """Cancel task execution

Returns:
Whether the cancellation was successful"""
        if self._task and not self._task.done():
            self.status = TaskStatus.CANCELLED
            return self._task.cancel()
        return False

    @property
    def duration(self) -> Optional[float]:
        """Get task execution time (seconds)

Returns:
Execution time, return None if the task is not completed"""
        if self.start_time is None:
            return None

        end = self.end_time or time.time()
        return end - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert the task to a dictionary representation

Returns:
Dictionary of tasks"""
        return {
            "task_id": self.task_id,
            "description": self.description,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "has_error": self.error is not None,
            "error_message": str(self.error) if self.error else None
        }


class TaskManager:
    """Task Manager to manage the creation, execution, and monitoring of asynchronous tasks"""

    def __init__(self, graceful_shutdown_timeout: float = 30.0):
        """Initialize Task Manager

Args:
graceful_shutdown_timeout: Timeout (seconds) to wait for a task to complete when the app exits"""
        self.tasks: Dict[str, Task] = {}
        self.logger = logging.getLogger("task_manager")
        self._active_tasks: Set[str] = set()  # Track active tasks
        self.graceful_shutdown_timeout = graceful_shutdown_timeout
        self._shutdown_handler_installed = False

    def _install_signal_handlers(self):
        """Install a signal handler to gracefully close when the app exits"""
        if self._shutdown_handler_installed:
            return

        def shutdown_handler(signum, frame):
            loop = asyncio.get_event_loop()
            if loop.is_running():
                self.logger.info(f"接收到退出信号 {signum}，等待任务完成...")
                loop.create_task(self._wait_for_tasks())
            else:
                # If the event loop is not running, directly synchronize and wait
                import threading
                threading.Thread(target=self._sync_wait_for_tasks).start()

        # Install the signal processor
        signal.signal(signal.SIGINT, shutdown_handler)
        signal.signal(signal.SIGTERM, shutdown_handler)

        self._shutdown_handler_installed = True

    async def _wait_for_tasks(self):
        """Wait for all active tasks to complete or time out"""
        if not self._active_tasks:
            self.logger.info("No active tasks, quit immediately")
            return

        self.logger.info(f"等待 {len(self._active_tasks)} 个活跃任务完成，最多等待 {self.graceful_shutdown_timeout} 秒")

        try:
            start_time = time.time()
            pending_tasks = [self.tasks[task_id]._task for task_id in self._active_tasks
                             if task_id in self.tasks and self.tasks[task_id]._task is not None]

            if not pending_tasks:
                return

            # Wait for all tasks to complete, but set a timeout
            done, pending = await asyncio.wait(
                pending_tasks,
                timeout=self.graceful_shutdown_timeout,
                return_when=asyncio.ALL_COMPLETED
            )

            elapsed = time.time() - start_time

            if pending:
                self.logger.warning(f"{len(pending)} 个任务在 {elapsed:.2f} 秒内未能完成，即将中断")
                for task in pending:
                    task.cancel()
            else:
                self.logger.info(f"所有 {len(done)} 个任务在 {elapsed:.2f} 秒内完成")

        except Exception as e:
            self.logger.error(f"等待任务完成时出错: {e}")
        finally:
            # Make sure to quit
            import os
            os._exit(0)

    def _sync_wait_for_tasks(self):
        """Synchronized version waiting for task completion"""
        if not self._active_tasks:
            print("No active tasks, quit immediately")
            return

        print(f"等待 {len(self._active_tasks)} 个活跃任务完成，最多等待 {self.graceful_shutdown_timeout} 秒")

        try:
            start_time = time.time()
            active_count = len(self._active_tasks)

            # Simply wait for a specified time
            while time.time() - start_time < self.graceful_shutdown_timeout and self._active_tasks:
                time.sleep(0.5)

            if self._active_tasks:
                print(f"{len(self._active_tasks)} 个任务在 {self.graceful_shutdown_timeout} 秒内未能完成，即将中断")
            else:
                print(f"所有 {active_count} 个任务已完成")

        except Exception as e:
            print(f"等待任务完成时出错: {e}")
        finally:
            # Make sure to quit
            import os
            os._exit(0)

    async def submit(self,
                     func: Callable[..., T],
                     *args,
                     task_id: Optional[str] = None,
                     timeout: Optional[float] = None,
                     description: str = "",
                     wait: bool = False,
                     on_complete: Optional[Callable[[str, Any], None]] = None,
                     on_error: Optional[Callable[[str, Exception], None]] = None,
                     **kwargs) -> Union[str, T]:
        """submit task

Args:
Func: The function to be executed
* args: position parameter
task_id: Task ID, automatically generated if None
Timeout: Timeout (seconds)
Description: Mission description
Wait: Whether to wait for the task to complete
on_complete: Callback function on task completion
on_error: Callback function in case of task error
** kwargs: keyword arguments

Returns:
If wait is True, the task result is returned; otherwise, the task ID is returned.

Raises:
Exception: Thrown if wait is True and task execution fails"""
        # Make sure the signal processor is installed
        self._install_signal_handlers()

        # Create task
        task = Task(
            func=func,
            args=args,
            kwargs=kwargs,
            task_id=task_id,
            timeout=timeout,
            description=description,
            on_complete=on_complete,
            on_error=on_error
        )

        # storage task
        self.tasks[task.task_id] = task
        self._active_tasks.add(task.task_id)

        # Create asynchronous tasks and add completion callbacks
        async def task_wrapper():
            try:
                return await task.execute()
            finally:
                # Remove from active collection when task is completed
                self._active_tasks.discard(task.task_id)

        task._task = asyncio.create_task(task_wrapper())

        # If you don't wait, return the task ID directly.
        if not wait:
            return task.task_id

        # Wait for the task to complete and return the result
        try:
            return await task._task
        except Exception as e:
            self.logger.error(f"Task {task.task_id} failed: {str(e)}")
            raise

    async def get_task(self, task_id: str) -> Optional[Task]:
        """Get task object

Args:
task_id: Task ID

Returns:
Task object, return None if none exists"""
        return self.tasks.get(task_id)

    async def get_result(self, task_id: str) -> Any:
        """Get task result

Args:
task_id: Task ID

Returns:
task result

Raises:
ValueError: if the task does not exist
RuntimeError: if the task has not been completed
Exception: if the task fails to execute"""
        task = await self.get_task(task_id)

        if task is None:
            raise ValueError(f"Task {task_id} not found")

        if task.status == TaskStatus.PENDING or task.status == TaskStatus.RUNNING:
            # If the task has not been completed, wait for it to complete
            try:
                return await task._task
            except Exception as e:
                self.logger.error(f"Task {task_id} failed: {str(e)}")
                raise

        if task.status == TaskStatus.FAILED:
            # If the task fails, throw the original exception
            raise task.error if task.error else RuntimeError(f"Task {task_id} failed without specific error")

        if task.status == TaskStatus.TIMEOUT:
            # If the task times out, throw a timeout exception
            raise asyncio.TimeoutError(f"Task {task_id} timed out")

        if task.status == TaskStatus.CANCELLED:
            # If the task is cancelled, throw a cancellation exception
            raise asyncio.CancelledError(f"Task {task_id} was cancelled")

        # If the task has been completed, return the result
        return task.result

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel task

Args:
task_id: Task ID

Returns:
Whether the cancellation was successful"""
        task = await self.get_task(task_id)

        if task is None:
            return False

        cancelled = task.cancel()
        if cancelled:
            self._active_tasks.discard(task_id)
        return cancelled

    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get the status of all tasks

Returns:
Mapping task ID to task information"""
        return {task_id: task.to_dict() for task_id, task in self.tasks.items()}

    def get_active_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get the status of all active tasks

Returns:
Mapping task ID to task information"""
        return {task_id: self.tasks[task_id].to_dict()
                for task_id in self._active_tasks
                if task_id in self.tasks}

    def get_tasks_by_status(self, status: TaskStatus) -> Dict[str, Dict[str, Any]]:
        """Get a task with a specific state

Args:
Status: task status

Returns:
Mapping task ID to task information"""
        return {
            task_id: task.to_dict()
            for task_id, task in self.tasks.items()
            if task.status == status
        }

    def cleanup_completed_tasks(self, max_age: float = 3600.0) -> int:
        """Clean up completed tasks

Args:
max_age: Maximum retention time in seconds

Returns:
Number of tasks cleared"""
        now = time.time()
        to_remove = []

        for task_id, task in self.tasks.items():
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.TIMEOUT, TaskStatus.CANCELLED):
                if task.end_time and (now - task.end_time) > max_age:
                    to_remove.append(task_id)

        for task_id in to_remove:
            del self.tasks[task_id]

        return len(to_remove)

    def get_active_count(self) -> int:
        """Get the number of active tasks

Returns:
number of active tasks"""
        return len(self._active_tasks)

    async def submit_time_consuming_tasks(self,
                                          func: Callable[..., T],
                                          *args,
                                          kwargs: Dict[str, Any] = None,
                                          task_id: Optional[str] = None,
                                          timeout: Optional[float] = None,
                                          description: str = "ad hoc time-consuming task",
                                          wait: bool = False) -> str:
        """Submit temporary time-consuming tasks and persist them to the database

Args:
Func: The function to be executed
* args: position parameter
Kwargs: keyword argument dictionary
task_id: Task ID, automatically generated if None
Timeout: Timeout (seconds)
Description: Mission description
Wait: Whether to wait for the task to complete

Returns:
Task ID

Raises:
Exception: Thrown if wait is True and task execution fails"""
        if kwargs is None:
            kwargs = {}

        # Generate a temporary task ID
        if task_id is None:
            task_id = f"temp_task_{str(uuid.uuid4())[:8]}"

        # Get database session
        from knowledge_api.framework.database.database import get_session
        from knowledge_api.mapper.task_manage import (
            TaskManageCRUD,
            TaskManageCreate,
            TaskStatus as DBTaskStatus,
            TriggerType
        )

        db = next(get_session())

        try:
            # 1. First create a database task record
            task_create = TaskManageCreate(
                id=task_id,
                name=description,
                task_type="temporary task",
                trigger_type=TriggerType.DATE,  # Use the DATE type to indicate that it will be executed only once
                trigger_args={"run_date": datetime.now().isoformat()},
                func_path=f"{func.__module__}.{func.__name__}" if hasattr(func, "__module__") and hasattr(func,
                                                                                                          "__name__") else "temp_function",
                func_args=kwargs,
                max_instances=1,
                description=description
            )

            crud = TaskManageCRUD(db)
            await crud.create(task_create)

            # 2. Then create the task directly and execute it without going through the submit method
            task = Task(
                func=func,
                args=args,
                kwargs=kwargs,
                task_id=task_id,
                timeout=timeout,
                description=description
            )

            # storage task
            self.tasks[task.task_id] = task
            self._active_tasks.add(task.task_id)

            # Create asynchronous tasks and add completion callbacks
            async def task_wrapper():
                try:
                    return await task.execute()
                finally:
                    # Remove from active collection when task is completed
                    self._active_tasks.discard(task.task_id)

            task._task = asyncio.create_task(task_wrapper())

            # If you need to wait, wait for the task to complete
            if wait:
                try:
                    result = await task._task
                    # Update task status to completed
                    await crud.update_status(task_id, DBTaskStatus.COMPLETED)
                    return result
                except Exception as e:
                    self.logger.error(f"Task {task.task_id} failed: {str(e)}")
                    raise

            return task_id

        except Exception as e:
            # Update status failed on error
            try:
                await crud.update_status(task_id, DBTaskStatus.FAILED)
            except:
                pass
            raise
        finally:
            db.close()


# Global Task Manager instance
_global_task_manager: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    """Get the Global Task Manager instance (singleton mode)

Returns:
Task Manager instance"""
    global _global_task_manager

    if _global_task_manager is None:
        _global_task_manager = TaskManager()

    return _global_task_manager
