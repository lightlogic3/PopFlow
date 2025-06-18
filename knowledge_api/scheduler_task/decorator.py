"""Timed Task Decorator and Task Registry

Provides decorators for marking timed tasks and automatically registering them in the task registry"""
import inspect
import logging
from functools import wraps
from typing import Dict, List, Callable, Any, Optional, Union, get_type_hints

logger = logging.getLogger(__name__)

# Task regedit
task_registry: Dict[str, Dict[str, Any]] = {}


def scheduled_task(name: str, description: str = "", tags: List[str] = None):
    """Mark a function as a schedulable, timed task

@param name: task name
@param description: task description
@Param tags: List of task tags for classification
@Return: Decorator function"""
    def decorator(func):
        # Get function signature information
        sig = inspect.signature(func)
        func_module = func.__module__
        func_name = func.__name__
        func_path = f"{func_module}.{func_name}"
        
        # Get function parameter information
        params = {}
        for param_name, param in sig.parameters.items():
            # Ignore the self parameter
            if param_name == "self":
                continue
                
            param_info = {
                "name": param_name,
                "required": param.default is inspect.Parameter.empty,
                "default": None if param.default is inspect.Parameter.empty else param.default,
                "type": "any"
            }
            
            # Try to get type hints
            try:
                type_hints = get_type_hints(func)
                if param_name in type_hints:
                    type_name = type_hints[param_name].__name__
                    param_info["type"] = type_name
            except (TypeError, ValueError):
                pass
                
            params[param_name] = param_info
            
        # Register a task
        task_info = {
            "name": name,
            "description": description,
            "tags": tags or [],
            "function": func,
            "module": func_module,
            "func_name": func_name,
            "func_path": func_path,
            "parameters": params,
            "doc": inspect.getdoc(func) or ""
        }
        
        task_registry[func_path] = task_info
        logger.info(f"任务已注册: {name} ({func_path})")
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
            
        return wrapper
        
    return decorator


def get_all_tasks() -> List[Dict[str, Any]]:
    """Get all registered task information

@Return: task information list"""
    result = []
    for task_path, task_info in task_registry.items():
        # Create a copy that does not contain the function object so that it can be serialized
        task_data = {k: v for k, v in task_info.items() if k != "function"}
        result.append(task_data)
    
    return result 