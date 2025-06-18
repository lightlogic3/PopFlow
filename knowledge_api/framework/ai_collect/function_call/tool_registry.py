from typing import Dict, List, Any, Callable, Optional, Union
from functools import wraps

from knowledge_api.framework.ai_collect.function_call.function_tool import FunctionTool


class ToolRegistry:
    """Tool regedit to manage multiple functions"""

    def __init__(self):
        """Initialization tool regedit"""
        self.tools: Dict[str, FunctionTool] = {}

    def register(self,
                 func_or_tool: Union[Callable, FunctionTool],
                 name: Optional[str] = None,
                 description: Optional[str] = None) -> FunctionTool:
        """Register a functional tool

Args:
func_or_tool: Function to register or existing FunctionTool instance
Name: Function name (optional)
Description: Function description (optional)

Returns:
Registered FunctionTool instance"""
        if isinstance(func_or_tool, FunctionTool):
            tool = func_or_tool
            if name:
                tool.name = name
            if description:
                tool.description = description
        else:
            tool = FunctionTool(func_or_tool, name, description)

        self.tools[tool.name] = tool
        return tool

    def register_decorator(self, name: Optional[str] = None, description: Optional[str] = None):
        """Create a decorator to register function tools

Usage:
@tool_registry register_decorator (description = "Get weather info")
Def get_weather (location: str, unit: str = "degrees celsius"):
So..."""

        def decorator(func):
            self.register(func, name, description)

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return decorator

    def get_tool(self, name: str) -> Optional[FunctionTool]:
        """Get the tool with the specified name"""
        return self.tools.get(name)

    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get a list of API definitions for all tools"""
        return [tool.to_dict() for tool in self.tools.values()]

    def execute_tool(self, name: str, **kwargs) -> Any:
        """Execute the tool with the specified name"""
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"未找到名为'{name}'的工具")
        return tool.execute(**kwargs)