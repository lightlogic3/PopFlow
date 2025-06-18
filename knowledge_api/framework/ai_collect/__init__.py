"""AI big language model collection module, automatically registers all subclass implementations of BaseLLM"""

import importlib
import inspect
import os
from typing import Dict, Type
# Create a global LLM regedit
LLM_REGISTRY: Dict[str, Type] = {}
# First import the base class
from .base_llm import BaseLLM
# Get all Python files in the current directory, excluding __init__ and __pycache__
current_dir = os.path.dirname(os.path.abspath(__file__))
module_files = [
    f[:-3] for f in os.listdir(current_dir)
    if f.endswith('.py') and f != '__init__.py' and not f.startswith('__')
]

# Import all modules and check BaseLLM subclasses
for module_name in module_files:
    try:
        # import module
        module = importlib.import_module(f'.{module_name}', __package__)
        
        # Find all BaseLLM subclasses in this module
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, BaseLLM) and 
                obj is not BaseLLM and
                hasattr(obj, 'llm_type') and 
                obj.llm_type is not None):
                
                # Register to global regedit
                LLM_REGISTRY[obj.llm_type] = obj
                print(f"已注册LLM: {obj.llm_type} -> {obj.__name__}")
    except Exception as e:
        print(f"导入模块 {module_name} 时出错: {e}")

# Modify the BaseLLM class to use global regedit
BaseLLM._registry = LLM_REGISTRY

# Exporting main classes and functions
from .base_llm import BaseLLM, GameMessage
from .llm_factory import LLMFactory
from .message import Message, SystemMessage

# Provides a function to retrieve all registered LLMs
def get_registered_llms() -> Dict[str, Type[BaseLLM]]:
    """Get all registered LLM types"""
    return LLM_REGISTRY.copy()

__all__ = [
    'BaseLLM', 
    'LLMFactory', 
    'GameMessage', 
    'Message', 
    'SystemMessage',
    'get_registered_llms',
    'LLM_REGISTRY'
]

