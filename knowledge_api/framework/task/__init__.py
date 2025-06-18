"""FastAPI asynchronous task processing framework
Provides asynchronous task processing, thread pools, and task decorators for FastAPI projects"""
from contextlib import asynccontextmanager
import asyncio
import logging

from fastapi import FastAPI

# Export thread pool module
from knowledge_api.framework.task.thread_pool import (
    ThreadPoolExecutorEnhanced,
    get_thread_pool,
    thread_pool_lifespan
)

# Export Task Manager Module
from knowledge_api.framework.task.task_manager import (
    Task,
    TaskStatus,
    TaskManager,
    get_task_manager
)

# Export task decorator module
from knowledge_api.framework.task.task_decorator import (
    background_task,
    async_task,
    throttled_task,
    retry_task
)


@asynccontextmanager
async def setup_async_framework(app: FastAPI, max_workers: int = None, graceful_shutdown_timeout: float = 30.0):
    """Setting up an asynchronous task framework
Initialize the thread pool and task manager

Args:
App: FastAPI Application Example
max_workers: Maximum number of worker threads in the thread pool
graceful_shutdown_timeout: Timeout (seconds) to wait for a task to complete when the app exits"""
    # Get the thread pool and task manager
    thread_pool = get_thread_pool(max_workers=max_workers)
    task_manager = get_task_manager()

    # Set the graceful close timeout for Task Manager
    task_manager.graceful_shutdown_timeout = graceful_shutdown_timeout

    # Add an instance to the application state
    app.state.thread_pool = thread_pool
    app.state.task_manager = task_manager

    # Set up regular cleanup tasks
    cleanup_task = None

    @app.on_event("startup")
    async def start_cleanup_task():
        """Start a regular cleanup task"""
        nonlocal cleanup_task

        async def periodic_cleanup():
            """Regularly clean up completed tasks"""
            while True:
                try:
                    await asyncio.sleep(3600)  # It runs hourly.
                    removed = task_manager.cleanup_completed_tasks(max_age=86400)  # Clean up the tasks from the day before
                    if removed > 0:
                        logging.info(f"已清理 {removed} 个已完成的任务")
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logging.error(f"清理任务时出错: {e}")

        cleanup_task = asyncio.create_task(periodic_cleanup())

    @app.on_event("shutdown")
    async def wait_for_tasks():
        """Wait for active tasks to complete"""
        # Cancel the cleanup task
        if cleanup_task and not cleanup_task.done():
            cleanup_task.cancel()
            try:
                await cleanup_task
            except asyncio.CancelledError:
                pass

        # Check if there are any active tasks
        active_count = task_manager.get_active_count()
        if active_count > 0:
            logging.info(f"应用关闭，等待 {active_count} 个活跃任务完成...")

            # Get all active tasks
            active_tasks = [task._task for task in task_manager.tasks.values()
                            if task.status == TaskStatus.RUNNING and task._task is not None]

            if active_tasks:
                # Wait for all tasks to complete, but set a timeout
                try:
                    done, pending = await asyncio.wait(
                        active_tasks,
                        timeout=graceful_shutdown_timeout,
                        return_when=asyncio.ALL_COMPLETED
                    )

                    if pending:
                        logging.warning(f"{len(pending)} 个任务未能在关闭前完成")
                    else:
                        logging.info(f"所有 {len(done)} 个活跃任务已完成")
                except Exception as e:
                    logging.error(f"等待任务完成时出错: {e}")

    try:
        yield
    finally:
        # Clean up completed tasks
        task_manager.cleanup_completed_tasks()

        # Close the thread pool
        thread_pool.shutdown(wait=True)


# version information
__version__ = "0.1.0"
