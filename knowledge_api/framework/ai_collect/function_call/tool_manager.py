from typing import Dict, List, Any
import json
import asyncio
from knowledge_api.framework.ai_collect.function_call.tool_registry import ToolRegistry


class ToolManager:
    """Tool manager to handle function calls for model requests"""

    def __init__(self, registry: ToolRegistry):
        """Initialization Tool Manager

Args:
Registry: tool regedit"""
        self.registry = registry

    def handle_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Processing tool calls returned by the model

Args:
tool_calls: List of tool calls returned by the model

Returns:
Tool call result list"""
        results = []

        for tool_call in tool_calls:
            if tool_call.type == "function":
                function_call = tool_call.function
                tool_call_id = tool_call.id
                name = function_call.name
                arguments_str = function_call.arguments

                try:
                    # parsing parameters
                    arguments = json.loads(arguments_str)

                    # execution tool
                    result = self.registry.execute_tool(name, **arguments)

                    # Add result - return the original result directly without JSON serialization
                    results.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": result
                    })
                except Exception as e:
                    # Handle errors
                    error_result = {"error": f"执行工具'{name}'时出错: {str(e)}"}
                    results.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": error_result
                    })

        return results
        
    async def handle_tool_calls_async(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Asynchronous processing of tool calls returned by the model

Args:
tool_calls: List of tool calls returned by the model

Returns:
Tool call result list"""
        results = []
        tasks = []

        for tool_call in tool_calls:
            if tool_call.type == "function":
                function_call = tool_call.function
                tool_call_id = tool_call.id
                name = function_call.name
                arguments_str = function_call.arguments

                try:
                    # parsing parameters
                    arguments = json.loads(arguments_str)
                    
                    # Create asynchronous task
                    task = self._execute_tool_async(name, tool_call_id, arguments)
                    tasks.append(task)
                except Exception as e:
                    # Handle errors
                    error_result = {"error": f"执行工具'{name}'时出错: {str(e)}"}
                    results.append({
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "content": error_result
                    })

        # Wait for all asynchronous tasks to complete
        if tasks:
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            results.extend([r for r in task_results if r is not None])

        return results
    
    async def _execute_tool_async(self, name: str, tool_call_id: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single tool call asynchronously

Args:
Name: tool name
tool_call_id: Tool Call ID
Arguments: tool parameters

Returns:
Tool call result"""
        try:
            # Check if the tool is an asynchronous function
            tool = self.registry.get_tool(name)
            tool_function = tool.func
            
            # Execution tools (support synchronous and asynchronous)
            if asyncio.iscoroutinefunction(tool_function):
                # asynchronous execution
                result = await tool_function(**arguments)
            else:
                # Synchronous execution (running in a thread pool to avoid blocking the event loop)
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, lambda: tool_function(**arguments)
                )
            
            # Return the original result directly without JSON serialization
            return {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": result
            }
        except Exception as e:
            # Handle errors
            error_result = {"error": f"执行工具'{name}'时出错: {str(e)}"}
            return {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": error_result
            }