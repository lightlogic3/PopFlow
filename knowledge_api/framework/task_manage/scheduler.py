"""Timed Task Scheduler"""
import importlib
import json
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.base import JobLookupError
from sqlmodel import Session

from knowledge_api.mapper.task_manage import (
    TaskManageCRUD,
    TaskExecutionLogCRUD,
    TaskManage,
    TaskStatus,
    TriggerType,
    TaskExecutionLogCreate
)
# Import ID Generator
# Add a reference to scheduler_task module
from knowledge_api.scheduler_task import task_registry

logger = logging.getLogger(__name__)

# asynchronous task execution function
async def _execute_task_async(task_id: str, func_path: str, func_args: Dict[str, Any]):
    """Asynchronous functions that perform tasks

@Param task_id: Task ID
@Param func_path: function path
@Param func_args: function parameters"""
    # Get database session
    from knowledge_api.framework.database.database import get_session
    db = next(get_session())

    # Created log ID
    log_id = None

    try:
        # Create task log
        try:
            log_crud = TaskExecutionLogCRUD(db)
            log_create = TaskExecutionLogCreate(task_id=task_id)
            log = await log_crud.create(log_create)
            log_id = log.id
            logger.info(f"为任务 {task_id} 创建执行日志 {log_id}")
        except Exception as e:
            logger.error(f"为任务 {task_id} 创建执行日志失败: {str(e)}")
            logger.error(traceback.format_exc())
            # Continue to execute tasks, even if log creation fails

        # Update task status to Running
        try:
            task_crud = TaskManageCRUD(db)
            await task_crud.update_status(task_id, TaskStatus.RUNNING)
            logger.info(f"更新任务 {task_id} 状态为 RUNNING")
        except Exception as e:
            logger.error(f"更新任务 {task_id} 状态失败: {str(e)}")
            logger.error(traceback.format_exc())

        result = None
        error = None
        status = TaskStatus.COMPLETED

        try:
            # Get function
            func = None
            if func_path in task_registry:
                func = task_registry[func_path]["function"]
                logger.info(f"从注册表中获取函数 {func_path}")
            else:
                # dynamic import function
                func_module, func_name = func_path.rsplit('.', 1)
                module = importlib.import_module(func_module)
                func = getattr(module, func_name)
                logger.info(f"动态导入函数 {func_path}")

            if not func:
                raise ImportError(f"未找到函数: {func_path}")

            # Execute a task
            logger.info(f"开始执行任务 {task_id}, 函数: {func_path}")
            result = await func(**func_args)
            logger.info(f"任务 {task_id} 执行成功")
        except Exception as e:
            logger.error(f"任务 {task_id} 执行失败: {str(e)}")
            logger.error(traceback.format_exc())
            error = str(e)
            status = TaskStatus.FAILED

        # Update task log
        end_time = datetime.now()

        if log_id:
            try:
                # Attempt to serialize the result
                result_str = None
                if result is not None:
                    try:
                        result_str = json.dumps(result)
                    except (TypeError, OverflowError):
                        result_str = str(result)

                await log_crud.update(log_id, end_time, status, result_str, error)
                logger.info(f"更新任务 {task_id} 执行日志 {log_id}")
            except Exception as e:
                logger.error(f"更新任务 {task_id} 执行日志失败: {str(e)}")
                logger.error(traceback.format_exc())

        # Update task status
        try:
            task = await task_crud.get_by_id(task_id)
            if task:
                if task.trigger_type == TriggerType.DATE:
                    # After a single task is completed, the status is set to completed.
                    await task_crud.update_status(task_id, status)
                    logger.info(f"更新单次任务 {task_id} 状态为 {status}")
                elif status == TaskStatus.FAILED:
                    # Failed tasks are marked as failures
                    await task_crud.update_status(task_id, status)
                    logger.info(f"更新失败任务 {task_id} 状态为 {status}")
                else:
                    # In other cases, reset to the waiting state and wait for the next execution.
                    await task_crud.update_status(task_id, TaskStatus.PENDING)
                    logger.info(f"重置任务 {task_id} 状态为 PENDING")

                # Get the scheduler to update the next runtime
                # Note: Here, you must obtain the scheduler instance by importing it, rather than directly referencing it
                try:
                    from knowledge_api.manage.api.task_manage_api import task_scheduler
                    job_id = f"task_{task_id}"
                    job = task_scheduler.scheduler.get_job(job_id)
                    if job and job.next_run_time:
                        await task_crud.update_next_run_time(task_id, job.next_run_time)
                        logger.info(f"更新任务 {task_id} 下次运行时间为 {job.next_run_time}")
                except Exception as e:
                    logger.warning(f"更新任务 {task_id} 下次运行时间失败: {str(e)}")
        except Exception as e:
            logger.error(f"更新任务 {task_id} 状态失败: {str(e)}")
            logger.error(traceback.format_exc())

    except Exception as e:
        logger.error(f"任务执行器异常: {str(e)}")
        logger.error(traceback.format_exc())

        # Attempt to flag the task as a failure
        try:
            task_crud = TaskManageCRUD(db)
            await task_crud.update_status(task_id, TaskStatus.FAILED)
            logger.info(f"将任务 {task_id} 标记为失败状态")
        except Exception as log_e:
            logger.error(f"标记任务 {task_id} 为失败状态时出错: {str(log_e)}")
    finally:
        # Close the database session
        try:
            db.close()
            logger.debug(f"关闭任务 {task_id} 的数据库会话")
        except Exception as e:
            logger.error(f"关闭数据库会话失败: {str(e)}")


class TaskScheduler:
    """Timed Task Scheduler"""

    def __init__(self, db_url: str):
        """Initialization scheduler

@Param db_url: database connection URL"""
        # Configure job store and executor
        jobstores = {
            'default': SQLAlchemyJobStore(url=db_url)
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 1
        }

        # Create scheduler
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            job_defaults=job_defaults
        )

        self._running = False

    async def start(self):
        """Start Scheduler"""
        if not self._running:
            self.scheduler.start()
            self._running = True
            logger.info("Task scheduler started")

    async def shutdown(self):
        """Close scheduler"""
        if self._running:
            self.scheduler.shutdown()
            self._running = False
            logger.info("Task scheduler shutdown")

    async def add_job(self, db: Session, task: TaskManage) -> str:
        """Add a task to the scheduler

@Param db: database session
@Param task: task data
@return: task ID"""
        # import function
        func = None

        # First check if it is a registered task
        if task.func_path in task_registry:
            func = task_registry[task.func_path]["function"]
            logger.info(f"使用已注册的任务函数: {task.func_path}")
        else:
            # Attempt to import a function dynamically
            try:
                func_module, func_name = task.func_path.rsplit('.', 1)
                module = importlib.import_module(func_module)
                func = getattr(module, func_name)
            except (ImportError, AttributeError) as e:
                logger.error(f"无法导入函数 {task.func_path}: {e}")
                await self._update_task_status(db, task.id, TaskStatus.FAILED)
                return task.id

        if not func:
            logger.error(f"未找到函数: {task.func_path}")
            await self._update_task_status(db, task.id, TaskStatus.FAILED)
            return task.id

        # Create trigger
        trigger = self._create_trigger(task.trigger_type, task.trigger_args)
        if not trigger:
            logger.error(f"为任务 {task.id} 创建触发器失败")
            await self._update_task_status(db, task.id, TaskStatus.FAILED)
            return task.id

        # Add Task
        job_id = f"task_{task.id}"

        # First check if the job already exists, and remove it if it does
        try:
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                logger.info(f"已移除现有作业: {job_id}")
        except Exception as e:
            logger.warning(f"检查作业 {job_id} 是否存在时出错: {e}")

        try:
            # Make sure the task parameters are serializable
            cleaned_args = self._clean_args(task.func_args)

            # Use global execution functions instead of instance methods
            self.scheduler.add_job(
                _execute_task_async,  # Using synchronous wrapper functions
                trigger=trigger,
                id=job_id,
                name=task.name,
                max_instances=task.max_instances,
                replace_existing=True,
                kwargs={
                    'task_id': task.id,
                    'func_path': task.func_path,
                    'func_args': cleaned_args
                }
            )

            await self._update_task_status(db, task.id, TaskStatus.PENDING)
            logger.info(f"任务 {task.id} 已添加到调度器，作业ID为 {job_id}")

            # Update next runtime
            job = self.scheduler.get_job(job_id)
            if job and job.next_run_time:
                await self._update_next_run_time(db, task.id, job.next_run_time)

            return task.id
        except Exception as e:
            logger.error(f"将任务 {task.id} 添加到调度器失败: {str(e)}")
            logger.error(traceback.format_exc())
            await self._update_task_status(db, task.id, TaskStatus.FAILED)
            return task.id

    def _clean_args(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up the parameters to ensure that all parameters are serializable

@Param args: raw parameter dictionary
@Return: Cleaned parameter dictionary"""
        if not args:
            return {}

        cleaned = {}
        for key, value in args.items():
            # Try JSON serialization to test if parameters are serializable
            try:
                json.dumps(value)
                cleaned[key] = value
            except (TypeError, OverflowError):
                # If it cannot be serialized, it is converted to a string.
                cleaned[key] = str(value)
                logger.warning(f"参数 {key} 无法序列化，已转换为字符串")

        return cleaned

    async def remove_job(self, db: Session, task_id: str) -> bool:
        """Remove task from scheduler

@Param db: database session
@Param task_id: Task ID
@Return: whether the removal was successful"""
        job_id = f"task_{task_id}"
        try:
            # Check if the job exists
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                logger.info(f"任务 {task_id} 已从调度器移除")
            else:
                logger.info(f"任务 {task_id} 不存在于调度器中，无需移除")

            await self._update_task_status(db, task_id, TaskStatus.COMPLETED)
            return True
        except JobLookupError:
            logger.info(f"任务 {task_id} 不存在于调度器中，无需移除")
            await self._update_task_status(db, task_id, TaskStatus.COMPLETED)
            return True
        except Exception as e:
            logger.error(f"移除任务 {task_id} 失败: {e}")
            return False

    async def pause_job(self, db: Session, task_id: str) -> bool:
        """Suspend task

@Param db: database session
@Param task_id: Task ID
@Return: whether to pause successfully"""
        job_id = f"task_{task_id}"
        try:
            # Check if the job exists
            if self.scheduler.get_job(job_id):
                self.scheduler.pause_job(job_id)
                logger.info(f"任务 {task_id} 已暂停")
                await self._update_task_status(db, task_id, TaskStatus.PAUSED)
                return True
            else:
                logger.warning(f"任务 {task_id} 不存在于调度器中，无法暂停")
                return False
        except Exception as e:
            logger.error(f"暂停任务 {task_id} 失败: {e}")
            return False

    async def resume_job(self, db: Session, task_id: str) -> bool:
        """recovery task

@Param db: database session
@Param task_id: Task ID
@Return: whether the recovery was successful"""
        job_id = f"task_{task_id}"
        try:
            # Check if the job exists
            if self.scheduler.get_job(job_id):
                self.scheduler.resume_job(job_id)
                logger.info(f"任务 {task_id} 已恢复")

                # Update next runtime
                job = self.scheduler.get_job(job_id)
                if job and job.next_run_time:
                    await self._update_next_run_time(db, task_id, job.next_run_time)

                await self._update_task_status(db, task_id, TaskStatus.PENDING)
                return True
            else:
                # If the job doesn't exist, try adding it again
                task_crud = TaskManageCRUD(db)
                task = await task_crud.get_by_id(task_id)
                if task:
                    await self.add_job(db, task)
                    logger.info(f"任务 {task_id} 不存在，已重新添加")
                    return True
                else:
                    logger.warning(f"任务 {task_id} 不存在于数据库中")
                    return False
        except Exception as e:
            logger.error(f"恢复任务 {task_id} 失败: {e}")
            return False

    async def trigger_job(self, db: Session, task_id: str) -> bool:
        """Trigger task execution immediately

@Param db: database session
@Param task_id: Task ID
@Return: whether it was successfully triggered"""
        job_id = f"task_{task_id}"
        try:
            # Check if the job exists
            job = self.scheduler.get_job(job_id)
            if job:
                self.scheduler.modify_job(job_id, next_run_time=datetime.now())
                logger.info(f"任务 {task_id} 已触发立即执行")
                return True
            else:
                # If the job doesn't exist, try to add it again and execute it immediately
                task_crud = TaskManageCRUD(db)
                task = await task_crud.get_by_id(task_id)
                if task:
                    await self.add_job(db, task)
                    self.scheduler.modify_job(job_id, next_run_time=datetime.now())
                    logger.info(f"任务 {task_id} 不存在，已重新添加并触发执行")
                    return True
                else:
                    logger.warning(f"任务 {task_id} 不存在于数据库中")
                    return False
        except Exception as e:
            logger.error(f"触发任务 {task_id} 失败: {e}")
            return False

    async def load_tasks(self, db: Session) -> List[str]:
        """Load all active tasks from the database to the scheduler

@Param db: database session
@Return: List of loaded task IDs"""
        task_crud = TaskManageCRUD(db)
        tasks = await task_crud.get_all()

        task_ids = []
        for task in tasks:
            # Only load non-completed and non-failed tasks
            if task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED,TaskStatus.PAUSED]:
                task_id = await self.add_job(db, task)
                task_ids.append(task_id)

        logger.info(f"已从数据库加载 {len(task_ids)} 个任务")
        return task_ids

    def _create_trigger(self, trigger_type: TriggerType, trigger_args: Dict[str, Any]) -> Optional[Union[DateTrigger, IntervalTrigger, CronTrigger]]:
        """Create trigger

@Param trigger_type: trigger type
@Param trigger_args: trigger parameters
@Return: Trigger or None"""
        try:
            if trigger_type == TriggerType.DATE:
                # date trigger
                run_date = trigger_args.get('run_date')
                if isinstance(run_date, str):
                    run_date = datetime.fromisoformat(run_date)
                return DateTrigger(run_date=run_date)

            elif trigger_type == TriggerType.INTERVAL:
                # interval trigger
                return IntervalTrigger(**trigger_args)

            elif trigger_type == TriggerType.CRON:
                # Cron trigger
                return CronTrigger(**trigger_args)

            else:
                logger.error(f"未知的触发器类型: {trigger_type}")
                return None

        except Exception as e:
            logger.error(f"使用参数 {trigger_args} 创建触发器 {trigger_type} 失败: {e}")
            return None
    
    async def _update_task_status(self, db: Session, task_id: str, status: TaskStatus) -> None:
        """Update task status

@Param db: database session
@Param task_id: Task ID
@param status: new status"""
        task_crud = TaskManageCRUD(db)
        await task_crud.update_status(task_id, status)
    
    async def _update_next_run_time(self, db: Session, task_id: str, next_run_time: datetime) -> None:
        """Update task next run time

@Param db: database session
@Param task_id: Task ID
@Param next_run_time: next run time"""
        task_crud = TaskManageCRUD(db)
        await task_crud.update_next_run_time(task_id, next_run_time) 