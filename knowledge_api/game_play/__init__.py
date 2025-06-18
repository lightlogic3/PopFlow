"""Game type automatic registration module, providing automatic discovery and registration of game types"""

import importlib
import inspect
import os
from typing import Dict, Type

# Create global game type regedit
GAME_REGISTRY: Dict[str, Type] = {}

# First import the base class
from .base_game import BaseGame

# Get all Python files in the current directory, excluding __init__ and __pycache__
current_dir = os.path.dirname(os.path.abspath(__file__))
module_files = [
    f[:-3] for f in os.listdir(current_dir)
    if f.endswith('.py') and f != '__init__.py' and not f.startswith('__')
]

# Import all modules and check BaseGame subclasses
for module_name in module_files:
    try:
        # import module
        module = importlib.import_module(f'.{module_name}', __package__)
        
        # Find all BaseGame subclasses in this module
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, BaseGame) and 
                obj is not BaseGame and
                hasattr(obj, 'game_type') and 
                obj.game_type is not None):
                
                # Register to global regedit
                GAME_REGISTRY[obj.game_type] = obj
                print(f"已注册游戏类型: {obj.game_type} -> {obj.__name__}")
    except Exception as e:
        print(f"导入模块 {module_name} 时出错: {e}")

# Modify the BaseGame class to use global regedit
BaseGame._registry = GAME_REGISTRY

# Export main and factory classes
from .base_game import BaseGame
from .game_factory import GameFactory

# Provides a function to retrieve all registered game types
def get_registered_games() -> Dict[str, Type[BaseGame]]:
    """Get all registered game types"""
    return GAME_REGISTRY.copy()

__all__ = [
    'BaseGame',
    'GameFactory',
    'get_registered_games',
    'GAME_REGISTRY'
] 