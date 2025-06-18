"""Timed task registration and management module

Provides a decorator mechanism for marking and registering executable timed tasks"""

from .decorator import scheduled_task, get_all_tasks, task_registry
from .scanner import scan_tasks

__all__ = ["scheduled_task", "get_all_tasks", "task_registry", "scan_tasks"]

# Automatic scanning tasks at app startup
scan_tasks()
