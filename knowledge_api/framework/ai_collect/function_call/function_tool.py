from typing import Dict, List, Any, Callable, Optional, Union
import json
import inspect
from functools import wraps


class FunctionTool:
    """Wrapper class for a single function tool"""

    def __init__(self,
                 func: Callable,
                 name: Optional[str] = None,
                 description: Optional[str] = None):
        """Initialization Function Tool

Args:
Func: The function to encapsulate
Name: function name, if not provided, use the original name of the function
Description: Function description"""
        self.func = func
        self.name = name or func.__name__
        self.description = description or func.__doc__ or ""
        self._parameters = self._extract_parameters()

    def _extract_parameters(self) -> Dict[str, Any]:
        """Extracting parameter information from function signatures"""
        sig = inspect.signature(self.func)
        props = {}
        required = []

        for param_name, param in sig.parameters.items():
            if param_name == 'self':  # Skip the self parameter of the class method
                continue

            # Get parameter type annotation
            param_type = param.annotation
            type_str = "string"  # default type

            if param_type is inspect.Parameter.empty:
                type_str = "string"
            elif param_type is str:
                type_str = "string"
            elif param_type is int:
                type_str = "integer"
            elif param_type is float:
                type_str = "number"
            elif param_type is bool:
                type_str = "boolean"
            elif param_type is list or param_type is List:
                type_str = "array"
            elif param_type is dict or param_type is Dict:
                type_str = "object"

            # build parameter properties
            param_info = {
                "type": type_str,
                "description": ""  # Default empty description
            }

            # Check if there is a default value
            if param.default is inspect.Parameter.empty:
                required.append(param_name)

            props[param_name] = param_info

        return {
            "type": "object",
            "properties": props,
            "required": required
        }

    def set_parameter_description(self, param_name: str, description: str) -> 'FunctionTool':
        """Description of setting parameters"""
        if param_name in self._parameters["properties"]:
            self._parameters["properties"][param_name]["description"] = description
        return self

    def set_parameter_enum(self, param_name: str, enum_values: List[Any]) -> 'FunctionTool':
        """Set the enumeration value of the parameter"""
        if param_name in self._parameters["properties"]:
            self._parameters["properties"][param_name]["enum"] = enum_values
        return self

    def execute(self, **kwargs) -> Any:
        """execution function"""
        return self.func(**kwargs)

    def to_dict(self) -> Dict[str, Any]:
        """The tool definition format required to convert to the Bean Bag API"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self._parameters
            }
        }
