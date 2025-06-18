"""function tool node
Responsible for executing user-defined function code"""

import inspect
from typing import Dict, Any, List, Optional
import traceback

from knowledge_api.framework.workflow.types import WorkflowContext
from knowledge_api.utils.log_config import get_logger
from knowledge_api.framework.workflow.model.node import Node
from knowledge_api.framework.workflow.model.node_status import NodeStatus
logger = get_logger()

class FunctionToolNode(Node):
    """function tool node
Execute user-defined function code"""
    
    # Node type identifier
    node_type: str = "function_tool"
    
    # node description
    description: str = "Execute user-defined function code"
    
    def __init__(self, id: str, name: str, config: Dict[str, Any]):
        """Initialization function tool node

Args:
ID: Node ID
Name: Node name
Config: Node configuration, which must contain the following fields:
- function_impl: code string for function implementation, must contain async def main (args, context)
- function_schema: Optional function parameter structure description"""
        super().__init__(id, name, self.node_type, config)
        
        # authentication configuration item
        self._validate_config()
        
        # Save the function implementation code
        self.function_impl = config.get("function_impl", "")
        self.function_schema = config.get("function_schema", {})
        
        # Compile function code
        self._compiled_function = None
        self._compile_function()
        
        # Set to initialized state
        self.status = NodeStatus.IDLE
    
    def _validate_config(self) -> None:
        """Verify that the node configuration is valid"""
        if "function_impl" not in self.config:
            raise ValueError("The feature tool node configuration must contain function_impl fields")
        
        function_impl = self.config["function_impl"]
        if not isinstance(function_impl, str):
            raise ValueError("function_impl must be of type string")
        
        if "async def main(args, context)" not in function_impl and "async def main(args,context)" not in function_impl:
            raise ValueError("function_impl must contain'async def main (args, context) 'function definition")
    
    def _compile_function(self) -> None:
        """Compile function code"""
        try:
            # Create local variable space
            local_vars = {}
            
            # Compile and executable code
            exec(self.function_impl, globals(), local_vars)
            
            # Get main function
            if 'main' not in local_vars:
                raise ValueError("function_impl must define a function named'main'")
            
            main_func = local_vars['main']
            
            # Check if it is an asynchronous function
            if not inspect.iscoroutinefunction(main_func):
                raise ValueError("Main function must be asynchronous (async def)")
            
            # Save the compiled function
            self._compiled_function = main_func
            
        except Exception as e:
            error_message = f"编译函数代码失败: {str(e)}"
            logger.error(error_message)
            raise ValueError(error_message)
    
    async def process(self, context: WorkflowContext) -> Dict[str, Any]:
        """Process node logic and execute user-defined functions

Args:
Context: workflow context

Returns:
function execution result"""
        logger.info(f"FunctionToolNode开始处理: {self.id}")
        
        try:
            # Check if the function has been compiled
            if self._compiled_function is None:
                self._compile_function()
            
            # preparation parameters
            args = type('Args', (), {})()
            
            # Get parameters from the output of the previous node
            for input_def in self.inputs:
                key = input_def.get("key")
                if key:
                    # Attempt to obtain the value of the key from the context
                    value = context.data.get(key, None)
                    setattr(args, key, value)
            
            # execution function
            logger.info(f"正在执行用户定义函数: {self.id}")
            result = await self._compiled_function(args, context)
            logger.info(f"用户定义函数执行结果: {result}")
            
            # Prepare output results
            output_result = {}
            
            # Single output case: use the first output key as the result key
            if len(self.outputs) == 1:
                output_key = self.outputs[0].get("key")
                if output_key:
                    output_result[output_key] = result
            # Multiple output cases: Suppose result is a dictionary with corresponding output keys
            elif isinstance(result, dict):
                output_result = result
            else:
                logger.warning(f"函数返回值格式不匹配输出定义，使用默认键'result'")
                output_result["result"] = result
            
            # Update the result to the context
            context.data.update(output_result)
            
            # Set node status to complete
            self.status = NodeStatus.COMPLETED
            
            logger.info(f"FunctionToolNode处理完成: {self.id}")
            
            return output_result
        
        except Exception as e:
            error_message = f"功能工具节点执行失败: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_message)
            self.status = NodeStatus.FAILED
            self._error_message = error_message
            raise 