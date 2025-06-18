"""Loop Node Component
Supports three modes:
1. Conditional loop
2. Fixed number of cycles (fixed)
3. Iterator loop (iterator)"""

from typing import Dict, Any, List
import inspect


from knowledge_api.framework.workflow.model.node import Node
from knowledge_api.framework.workflow.model.node_status import NodeStatus
from knowledge_api.utils.log_config import get_logger

logger = get_logger()

class LoopNode(Node):
    """Loop Node Component
Processing loop execution internal node"""
    
    node_type = "loop"
    description = "loop execution internal node"
    
    def __init__(self, id: str, name: str, config: Dict[str, Any]):
        """Initialize the loop node

Args:
ID: Node ID
Name: Node name
Config: Node configuration"""
        super().__init__(id, name, self.node_type, config)
        
        # Loop mode: conditional (conditional loop), fixed (fixed number of times), iterator (iterator)
        self.mode = config.get("loop_mode", "fixed")
        
        # Maximum number of cycles (to prevent infinite loops)
        self.iterations = config.get("max_iterations", 10)
        
        # Loop variable name (used to track the number of loops)
        self.loop_variable = config.get("loop_variable", "index")
        
        # Conditional loop related configuration
        self.condition_key = config.get("condition_key", "")
        self.condition_value = config.get("condition_value", "")
        self.condition_operator = config.get("condition_operator", "==")
        
        # Iterator loop related configuration
        self.iterator_key = config.get("iterator_source", "")
        self.iterator_variable = config.get("iterator_variable", "item")
        
        # Internal nodes and edges
        self.internal_nodes = config.get("internal_nodes", [])
        self.internal_edges = config.get("internal_edges", [])
        
        # Initialize output port
        self._initialize_outputs()
    
    def _initialize_outputs(self):
        """Initialize output port"""
        self.outputs = [
            {
                "id": f"output_loop_index_{self.id}",
                "key": "loop_index",
                "type": "number",
                "description": "Current number of cycles (for iteration mode)"
            },
            {
                "id": f"output_loop_item_{self.id}",
                "key": "loop_item",
                "type": "any",
                "description": "Current iteration item (for iterator mode)"
            }
        ]
    
    async def process(self, context):
        """processing loop node

Args:
Context: workflow context

Returns:
processing result"""
        try:
            # Import WorkflowContext
            from knowledge_api.framework.workflow.types import WorkflowContext
            
            # Check the context type
            if isinstance(context, WorkflowContext):
                logger.info(f"循环节点 {self.id} 收到WorkflowContext对象")
                context_data = context.data
            else:
                logger.info(f"循环节点 {self.id} 收到字典对象，将转换为WorkflowContext")
                context_data = context
                # Create a new WorkflowContext object for subsequent use
                context = WorkflowContext(data=context_data)
        except ImportError:
            logger.error("Unable to import WorkflowContext type")
            # If you cannot import WorkflowContext, use the incoming context
            context_data = context if isinstance(context, dict) else getattr(context, 'data', {})
            
        logger.info(f"循环节点 {self.id} 开始执行，模式: {self.mode}")
        
        # Log current user messages (for debugging)
        if "user_message" in context_data:
            logger.info(f"当前用户消息: '{context_data['user_message']}'")
            
        # Check if execution needs to be resumed
        loop_state = context_data.get("_loop_state", {})
        resuming = False
        if loop_state and loop_state.get("node_id") == self.id:
            logger.info(f"检测到循环状态，尝试恢复执行循环: {loop_state}")
            resuming = True
            
            # Make sure the processing node flag is reset to handle the new message
            waiting_node_id = loop_state.get("waiting_node_id")
            if waiting_node_id and "user_message" in context_data and context_data["user_message"]:
                node_processed_key = f"{waiting_node_id}_processed"
                if node_processed_key in context_data:
                    logger.info(f"恢复执行，重置节点 {waiting_node_id} 的处理标记")
                    context_data[node_processed_key] = False
        
        # Create loop context
        loop_context = context_data.copy()
        logger.info(f"从 WorkflowContext.data 复制上下文数据")
        
        # Make sure global variables and references are set correctly
        if "global" in loop_context:
            # Add a reference to state
            if "state" in loop_context["global"]:
                logger.info(f"添加 global -> state 的引用")
            
            # Add a reference to game_state
            if "game_state" in loop_context:
                logger.info(f"添加 global -> game_state 的引用")
                
            # Record state.status value
            if "state" in loop_context["global"] and "status" in loop_context["global"]["state"]:
                logger.info(f"当前state.status值: {loop_context['global']['state']['status']}")
        
        # Record the value of the current loop condition
        if self.mode == "conditional" and self.condition_key:
            # Attempt to obtain the value of the condition from the context
            try:
                condition_value = self._get_value_from_context(loop_context, self.condition_key)
                logger.info(f"循环条件 {self.condition_key} 的当前值: {condition_value}")
            except Exception as e:
                logger.warning(f"无法获取条件 {self.condition_key} 的值: {str(e)}")
                
        # loop execution
        iteration = 0
        results = []
        
        # If execution resumes, obtain the previous state
        if resuming:
            iteration = loop_state.get("current_iteration", 0)
            results = loop_state.get("results", [])
            logger.info(f"恢复循环执行，当前迭代: {iteration}")
        
        # Execute according to circular mode
        if self.mode == "fixed":
            # Fixed number of cycles
            logger.info(f"执行固定次数循环，次数: {self.iterations}")
            
            while iteration < self.iterations:
                # Execute internal node
                result = await self._execute_internal_nodes(loop_context, iteration)
                
                # Check if any internal nodes are waiting
                if result.get("waiting"):
                    # Save the loop state for recovery
                    loop_state = {
                        "node_id": self.id,
                        "mode": self.mode,
                        "iteration": self.iterations,
                        "current_iteration": iteration,
                        "waiting_node_id": result.get("waiting_node_id"),
                        "results": results
                    }
                    loop_context["_loop_state"] = loop_state
                    logger.info(f"内部节点 {result.get('waiting_node_id')} 处于等待状态，暂停循环执行")
                    
                    # Save loop state to original context
                    context.data["_loop_state"] = loop_state
                    
                    # Set the state of the loop node to wait
                    self.status = NodeStatus.WAITING
                    
                    # Returns the result, including the waiting state
                    return {
                        "loop_index": iteration,
                        "loop_waiting": True,
                        "waiting_node_id": result.get("waiting_node_id"),
                        "loop_state": loop_state
                    }
                
                results.append(result)
                iteration += 1
                
                # After the current iteration completes, clear user messages and processing markers to ensure that the next iteration is waiting for user input
                loop_context["user_message"] = ""
                for key in list(loop_context.keys()):
                    if isinstance(key, str) and key.endswith("_processed"):
                        del loop_context[key]
                        logger.info(f"完成当前迭代，清除节点处理标记: {key}")
                
        elif self.mode == "conditional":
            # conditional loop
            logger.info(f"执行条件循环，条件: {self.condition_key} {self.condition_operator} {self.condition_value}")
            max_iterations = int(self.config.get("max_iterations", 10))
            
            while iteration < max_iterations:
                # Check conditions
                condition_result = self._check_condition(loop_context)
                
                if not condition_result:
                    logger.info(f"条件不满足，循环终止")
                    break
                
                # Execute internal node
                result = await self._execute_internal_nodes(loop_context, iteration)
                
                # Check if any internal nodes are waiting
                if result.get("waiting"):
                    # Save the loop state for recovery
                    loop_state = {
                        "node_id": self.id,
                        "mode": self.mode,
                        "iteration": max_iterations,
                        "current_iteration": iteration,
                        "waiting_node_id": result.get("waiting_node_id"),
                        "results": results
                    }
                    loop_context["_loop_state"] = loop_state
                    logger.info(f"内部节点 {result.get('waiting_node_id')} 处于等待状态，暂停循环执行")
                    
                    # Save loop state to original context
                    context.data["_loop_state"] = loop_state
                    
                    # Set the state of the loop node to wait
                    self.status = NodeStatus.WAITING
                    
                    # Returns the result, including the waiting state
                    return {
                        "loop_index": iteration,
                        "loop_waiting": True,
                        "waiting_node_id": result.get("waiting_node_id"),
                        "loop_state": loop_state
                    }
                
                results.append(result)
                iteration += 1
                
                # After the current iteration completes, clear user messages and processing markers to ensure that the next iteration is waiting for user input
                loop_context["user_message"] = ""
                logger.info(f"完成当前迭代，清除用户消息")
                
                # Clear all processing tags
                for key in list(loop_context.keys()):
                    if isinstance(key, str) and key.endswith("_processed"):
                        del loop_context[key]
                        logger.info(f"完成当前迭代，清除节点处理标记: {key}")
                
        elif self.mode == "iterator":
            # iterative loop
            items = []
            
            # Get iteration item
            try:
                items = self._get_iterator_data(loop_context)
                if not isinstance(items, list):
                    logger.warning(f"迭代项 {self.iterator_key} 不是列表类型: {items}")
                    items = [items]
            except Exception as e:
                logger.warning(f"无法获取迭代项 {self.iterator_key}: {str(e)}")
                items = []
            
            logger.info(f"执行迭代循环，项目数量: {len(items)}")
            
            item_index = 0
            if resuming and "item_index" in loop_state:
                item_index = loop_state.get("item_index", 0)
                logger.info(f"从项目索引 {item_index} 恢复迭代循环")
            
            for i in range(item_index, len(items)):
                item = items[i]
                if iteration >= int(self.config.get("max_iterations", 10)):
                    logger.info(f"达到最大迭代次数，循环终止")
                    break
                
                # Execute internal node
                result = await self._execute_internal_nodes(loop_context, iteration, item)
                
                # Check if any internal nodes are waiting
                if result.get("waiting"):
                    # Save the loop state for recovery
                    loop_state = {
                        "node_id": self.id,
                        "mode": self.mode,
                        "iteration": len(items),
                        "current_iteration": iteration,
                        "waiting_node_id": result.get("waiting_node_id"),
                        "results": results,
                        "item_index": i
                    }
                    loop_context["_loop_state"] = loop_state
                    logger.info(f"内部节点 {result.get('waiting_node_id')} 处于等待状态，暂停循环执行")
                    
                    # Save loop state to original context
                    context.data["_loop_state"] = loop_state
                    
                    # Set the state of the loop node to wait
                    self.status = NodeStatus.WAITING
                    
                    # Returns the result, including the waiting state
                    return {
                        "loop_index": iteration,
                        "loop_item": item,
                        "loop_waiting": True,
                        "waiting_node_id": result.get("waiting_node_id"),
                        "loop_state": loop_state
                    }
                
                results.append(result)
                iteration += 1
                
                # After the current iteration completes, clear user messages and processing markers to ensure that the next iteration is waiting for user input
                loop_context["user_message"] = ""
                logger.info(f"完成当前迭代，清除用户消息")
                
                # Clear all processing tags
                for key in list(loop_context.keys()):
                    if isinstance(key, str) and key.endswith("_processed"):
                        del loop_context[key]
                        logger.info(f"完成当前迭代，清除节点处理标记: {key}")
        
        # The reason for the completion of the recording cycle
        if iteration == 0:
            reason = "No Iteration"
        elif self.mode == "fixed" and iteration >= self.iterations:
            reason = "Complete all fixed iterations"
        elif self.mode == "conditional" and iteration >= int(self.config.get("max_iterations", 10)):
            reason = "Maximum number of cycles reached"
        elif self.mode == "iterator" and iteration >= len(self._get_value_from_context(loop_context, self.iterator_key, default=[])):
            reason = "Complete all iterations"
        else:
            reason = "Condition not satisfied"
        
        logger.info(f"循环节点 {self.id} 完成执行，总循环次数: {iteration}")
        
        # clear loop state
        if "_loop_state" in loop_context:
            del loop_context["_loop_state"]
            logger.info("The loop is complete, clear the loop state")
            
        # Also clears the loop state in the original context
        if "_loop_state" in context.data:
            del context.data["_loop_state"]
        
        # Update original context
        if isinstance(context, WorkflowContext):
            for key, value in loop_context.items():
                if key != "_loop" and key != "_loop_state":  # Do not copy internal loop variables
                    logger.info(f"更新原始上下文字段: {key}")
                    context.data[key] = value
                    
        # Return result
        return {
            "loop_index": iteration - 1 if iteration > 0 else None,
            "loop_item": loop_context.get("_loop", {}).get("item"),
            "loop_results": results,
            "total_iterations": iteration
        }
    
    def _check_condition(self, context: Dict[str, Any]) -> bool:
        """Check cycle conditions

Args:
Context: the current context

Returns:
Conditional check result"""
        if not self.condition_key:
            return False
        
        # Get the conditional value from the context
        actual_value = self._get_value_from_context(context, self.condition_key)
        expected_value = self.condition_value
        
        # Record condition check details
        logger.info(f"循环条件检查: '{self.condition_key}' ({actual_value}) {self.condition_operator} '{expected_value}'")
        
        # Boolean special handling: if the actual value is a Boolean type, the expected value is converted to a Boolean type
        if isinstance(actual_value, bool):
            # Boolean special treatment
            if isinstance(expected_value, str):
                # String to Boolean, case insensitive
                expected_str = expected_value.lower().strip()
                if expected_str in ('true', 'yes', '1', 't', 'y'):
                    expected_value = True
                elif expected_str in ('false', 'no', '0', 'f', 'n'):
                    expected_value = False
                logger.info(f"将字符串 '{self.condition_value}' 转换为布尔值: {expected_value}")
        # Number Type Processing
        elif isinstance(actual_value, (int, float)) and isinstance(expected_value, str):
            try:
                # Attempt to convert string to the same numeric type as the actual value
                if isinstance(actual_value, int):
                    expected_value = int(expected_value)
                elif isinstance(actual_value, float):
                    expected_value = float(expected_value)
                logger.info(f"将字符串 '{self.condition_value}' 转换为数字: {expected_value}")
            except (ValueError, TypeError):
                logger.warning(f"无法将预期值 '{expected_value}' 转换为与实际值 '{actual_value}' 相同的类型")
        
        # Compare values by operator
        if self.condition_operator == "==":
            result = actual_value == expected_value
        elif self.condition_operator == "!=":
            result = actual_value != expected_value
        elif self.condition_operator == ">":
            result = actual_value > expected_value
        elif self.condition_operator == ">=":
            result = actual_value >= expected_value
        elif self.condition_operator == "<":
            result = actual_value < expected_value
        elif self.condition_operator == "<=":
            result = actual_value <= expected_value
        elif self.condition_operator == "in":
            # Check if the value is contained in a string or list
            if isinstance(expected_value, str) and isinstance(actual_value, str):
                result = actual_value in expected_value
            elif isinstance(expected_value, (list, tuple, set)):
                result = actual_value in expected_value
            else:
                result = False
                logger.warning(f"'in' 操作符要求预期值为字符串或可迭代对象，但收到了 {type(expected_value)}")
        elif self.condition_operator == "contains":
            # Checks if a string or list contains a value
            if isinstance(actual_value, str) and isinstance(expected_value, str):
                result = expected_value in actual_value
            elif isinstance(actual_value, (list, tuple, set)):
                result = expected_value in actual_value
            else:
                result = False
                logger.warning(f"'contains' 操作符要求实际值为字符串或可迭代对象，但收到了 {type(actual_value)}")
        else:
            logger.warning(f"未知的条件操作符: {self.condition_operator}")
            result = False
        
        logger.info(f"条件检查结果: {result}")
        return result
    
    def _get_iterator_data(self, context: Dict[str, Any]) -> List[Any]:
        """Get iterator data

Args:
Context: context

Returns:
iterator data list"""
        if not self.iterator_key:
            return []
        
        # Get iterator data from context
        iterator_data = self._get_value_from_context(context, self.iterator_key)
        logger.info(f"获取到迭代数据源 {self.iterator_key}: 类型={type(iterator_data)}")
        
        # Data type checking and conversion
        if iterator_data is None:
            logger.warning(f"迭代器数据为空: {self.iterator_key}")
            return []
            
        # Make sure the data is an iterable type
        if isinstance(iterator_data, (list, tuple, set)):
            # Directly working with lists/tuples/collections
            items = list(iterator_data)
        elif hasattr(iterator_data, '__iter__') and not isinstance(iterator_data, (str, dict)):
            # Other iterables (but not strings or dictionaries)
            try:
                items = list(iterator_data)
            except Exception as e:
                logger.warning(f"无法将可迭代对象转换为列表: {str(e)}")
                items = []
        elif hasattr(iterator_data, 'items') and callable(iterator_data.items):
            # dictionary object
            items = list(iterator_data.items())
        else:
            # Non-iterable object, wrapped as a single-element list
            logger.warning(f"迭代器数据 {self.iterator_key} 不是可迭代类型: {type(iterator_data)}")
            items = [iterator_data]
        
        # Record final data
        logger.info(f"迭代数据列表大小: {len(items)}")
        if len(items) > 0:
            # Record the type of the first element
            first_item = items[0]
            logger.info(f"第一个迭代项类型: {type(first_item)}")
            
            # Check if it is a GameRole type
            has_chat = hasattr(first_item, 'chat') and callable(getattr(first_item, 'chat'))
            has_identity = hasattr(first_item, 'identity')
            
            if has_chat or has_identity:
                logger.info(f"迭代数据包含GameRole类似对象: has_chat={has_chat}, has_identity={has_identity}")
        
        return items
    
    def _get_value_from_context(self, context: Dict[str, Any], key_path: str, default: Any = None) -> Any:
        """Get values from context (supports path access, such as'global.players')

Search rules:
1. First try to get the value directly from the path
2. Then try to find the output of the specified node
3. Then try to find by component type
4. Finally, search directly from the context root level

Args:
Context: context
key_path: key path
Default: default value

Returns:
value"""
        if not key_path:
            return default
        
        # Record the original key path for easy debugging
        original_key_path = key_path
        
        # special mapping processing
        # 1. gameState.xxx -> state.xxx
        if key_path.startswith("gameState."):
            mapped_path = "state." + key_path[len("gameState."):]
            logger.info(f"将 {key_path} 映射到 {mapped_path}")
            key_path = mapped_path
        
        # 2. game_state.xxx -> state.xxx
        elif key_path.startswith("game_state."):
            mapped_path = "state." + key_path[len("game_state."):]
            logger.info(f"将 {key_path} 映射到 {mapped_path}")
            key_path = mapped_path
            
        # decomposition path part
        parts = key_path.split('.')
        
        # Check if it is a path in node_xxx format
        if len(parts) >= 2 and parts[0].startswith("node_"):
            node_id = parts[0]
            field_name = '.'.join(parts[1:])
            
            # Layer 1: Find the output of the specified node
            # Finding Node Results in Context
            node_results = context.get("node_results", {})
            if node_id in node_results and field_name in node_results[node_id]:
                result = node_results[node_id][field_name]
                logger.info(f"从节点 {node_id} 的输出中找到 {field_name} 的值: {result}")
                return result
            
            # Layer 2: Finding Component Types
            # Try to find directly by component type
            if field_name == "players" or field_name == "characters":
                # Find fields for specific component types
                component_types = ["game_state", "gameState", "state"]
                for comp_type in component_types:
                    if comp_type in context and field_name in context[comp_type]:
                        result = context[comp_type][field_name]
                        logger.info(f"从组件类型 {comp_type} 中找到 {field_name} 的值: {result}")
                        return result
            
            # Layer 3: Find field names directly from the context
            # For example, if looking for node_xxx players, you can also directly try to find context.players
            if field_name in context:
                result = context[field_name]
                logger.info(f"从上下文根级别找到 {field_name} 的值: {result}")
                return result
        
        # Try to find directly by path (original logic)
        current = context
        try:
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                elif hasattr(current, part):
                    current = getattr(current, part)
                else:
                    raise KeyError(f"找不到键: {part}")
            # If found successfully, return the result
            logger.info(f"成功找到 {original_key_path} -> {key_path} 的值: {current}")
            return current
        except (KeyError, AttributeError) as e:
            logger.info(f"直接路径查找失败: {e}")
        
        # Try an alternate lookup strategy
        fallback_paths = []
        
        # 1. If it's state.xxx but can't find it, try global.xxx
        if parts[0] == "state" and "global" in context:
            fallback_paths.append(["global"] + parts[1:])
        
        # 2. If gameState.xxx or game_state.xxx, try looking for xxx directly in context
        if original_key_path.startswith(("gameState.", "game_state.")):
            # Extract the last attribute name
            attr_name = original_key_path.split(".")[-1]
            if attr_name in context:
                logger.info(f"尝试直接从 context 根级别获取 {attr_name}")
                return context[attr_name]
        
        # 3. Try to loop to find all alternate paths
        for path in fallback_paths:
            try:
                current = context
                for part in path:
                    if isinstance(current, dict) and part in current:
                        current = current[part]
                    elif hasattr(current, part):
                        current = getattr(current, part)
                    else:
                        raise KeyError(f"找不到键: {part}")
                # If the return result is found
                logger.info(f"通过备用路径 {'.'.join(path)} 找到值: {current}")
                return current
            except (KeyError, AttributeError) as e:
                logger.info(f"备用路径查找失败: {'.'.join(path)}, 错误: {e}")
        
        # 4. Finally, try to get the last field name directly from the context root level
        # This is the ultimate safety net mechanism
        final_field = parts[-1]
        if final_field in context:
            result = context[final_field]
            logger.info(f"兜底：直接从上下文根级别找到 {final_field} 的值: {result}")
            return result
            
        # If all attempts fail, log the warning and return the default value
        logger.warning(f"无法从上下文中获取值: {original_key_path}, 尝试了所有可能的路径")
        return default
    
    async def _execute_internal_nodes(self, context: Dict[str, Any], iteration: int, item: Any = None) -> Dict[str, Any]:
        """Execute internal node

Args:
Context: the current context
Iteration: current number of iterations
Item: Current iteration item (if any)

Returns:
internal node execution result"""
        logger.info(f"执行内部节点，迭代次数: {iteration}")
        
        # Import the required classes

        # Update context to add loop-related information
        iteration_context = context.copy()  # Use shallow copy instead of deep copy
        
        # Ensure _loop data format is correct
        loop_data = {
            "index": iteration,
            "item": item,
            "is_loop_context": True  # Add clear markup
        }
        
        # Add additional debugging information
        if item is not None:
            loop_data["item_type"] = type(item).__name__
            loop_data["has_chat"] = hasattr(item, "chat") and callable(getattr(item, "chat"))
            loop_data["has_identity"] = hasattr(item, "identity")
            
            # If there is an identity attribute, record the value
            if hasattr(item, "identity"):
                loop_data["identity"] = getattr(item, "identity")
        
        # Set cyclic data
        iteration_context["_loop"] = loop_data
        
        logger.info(f"循环迭代数据: {loop_data}")
        
        # Check if execution is being resumed
        resuming = False
        if "_loop_state" in context:
            loop_state = context.get("_loop_state", {})
            if loop_state and loop_state.get("node_id") == self.id:
                resuming = True
                logger.info(f"检测到正在恢复循环执行，保留用户消息")
        
        # The processing logic of the first iteration is different from that of the non-first iteration
        if iteration > 0 and not resuming:
            # On non-first iteration and non-recovery state, clear user messages to ensure waiting for new input
            if "user_message" in iteration_context:
                logger.info(f"非首次迭代，清除上次的用户消息: {iteration_context.get('user_message', '')}")
                iteration_context["user_message"] = ""
                
            # Clear processing flags for all nodes
            for key in list(iteration_context.keys()):
                if isinstance(key, str) and key.endswith("_processed"):
                    del iteration_context[key]
                    logger.info(f"清除节点处理标记: {key}")
        
        # Import WorkflowContext
        try:
            from knowledge_api.framework.workflow.types import WorkflowContext
            # Create a WorkflowContext object, which is required for the message node
            workflow_context = WorkflowContext(data=iteration_context)
            logger.info(f"为内部节点创建了WorkflowContext对象")
            
            # Make sure the broadcast message function exists
            if "broadcast_message" in context:
                workflow_context.data["broadcast_message"] = context["broadcast_message"]
                logger.info(f"复制了broadcast_message函数")
                
            # Make sure other important functions are passed correctly
            for func_key in ["broadcast_message", "send_message", "update_state"]:
                if func_key in context and callable(context[func_key]):
                    workflow_context.data[func_key] = context[func_key]
                    logger.info(f"复制了{func_key}函数")
                    
            # Get a list of websockets connections (if any)
            if "websockets" in context:
                workflow_context.data["websockets"] = context["websockets"]
                logger.info(f"复制了websockets连接列表")
                
            # Copy user messages (if any)
            if "user_message" in context:
                # If resuming execution, ensure that user messages are copied
                if resuming and context.get("user_message"):
                    workflow_context.data["user_message"] = context["user_message"]
                    logger.info(f"恢复执行时复制用户消息: {context.get('user_message', '')}")
                
                logger.info(f"当前用户消息状态: {context.get('user_message', '')}")
            
        except ImportError:
            logger.error("Unable to import WorkflowContext type")
            return {"error": "Unable to import WorkflowContext type"}
        
        # Save the execution results of each internal node
        internal_node_results = {}
        
        # Get all internal nodes
        if not self.internal_nodes:
            logger.warning(f"循环节点 {self.id} 没有内部节点")
            return {"iteration": iteration, "item": item}
        
        # Create a map of internal node instances
        internal_node_instances = {}
        node_type_registry = {}
        
        # Import the required node type from node regedit
        try:
            from knowledge_api.framework.workflow.nodes.node_registry import node_registry
            node_type_registry = node_registry
        except ImportError:
            logger.error("Unable to import node regedit")
            return {"error": "Unable to import node regedit"}
        
        # Create an internal node instance
        for node_def in self.internal_nodes:
            node_id = node_def.get("id")
            node_name = node_def.get("name", "unnamed node")
            component_type = node_def.get("component_type")
            node_config = node_def.get("config", {})
            
            if not node_id or not component_type:
                logger.warning(f"内部节点定义缺失必要字段: {node_def}")
                continue
            
            # Check if the node type is registered
            if component_type not in node_type_registry:
                logger.warning(f"未知的节点类型: {component_type}")
                continue
            
            # Create node instance
            try:
                node_class = node_type_registry[component_type]
                
                # Decide how to instantiate based on the __init__ parameters of the node class
                init_params = list(inspect.signature(node_class.__init__).parameters.keys())
                
                if len(init_params) == 4 and 'config' in init_params:
                    # Suppose the constructor is __init__ (self, id, name, config)
                    node = node_class(node_id, node_name, node_config)
                elif len(init_params) == 5 and 'component_type' in init_params and 'config' in init_params:
                    # Suppose the constructor is __init__ (self, id, name, component_type, config)
                    node = node_class(node_id, node_name, component_type, node_config)
                else:
                    # Attempt for generic instantiation may fail
                    logger.warning(f"节点 {component_type} 的构造函数参数不匹配，尝试通用实例化")
                    try:
                        # Try (id, name, config) - works with MessageNode, PlayerTurnNode, etc
                        node = node_class(node_id, node_name, node_config)
                    except TypeError:
                        try:
                            # Try (id, name, component_type, config) - works with LoopNode, GameStateNode, etc
                            node = node_class(node_id, node_name, component_type, node_config)
                        except Exception as init_e:
                            logger.error(f"无法使用已知参数组合实例化节点 {node_id} ({component_type}): {init_e}")
                            continue 
                
                # Set input and output configuration
                node.inputs = node_def.get("inputs", [])
                node.outputs = node_def.get("outputs", [])
                
                # Add to Node Map
                internal_node_instances[node_id] = node
                logger.info(f"创建内部节点实例: {node_id}, 类型: {component_type}")
            except Exception as e:
                logger.error(f"创建内部节点 {node_id} 实例失败: {str(e)}")
                import traceback
                logger.error(f"详细错误信息: {traceback.format_exc()}")
                continue
        
        # Create a node connection diagram (simplified version)
        node_connections = {}
        node_inputs_map = {}  # Record Node Input Configuration
        
        # Build a node connection graph
        for edge in self.internal_edges:
            source = edge.get("source")
            target = edge.get("target")
            
            if not source or not target:
                continue
            
            if source not in node_connections:
                node_connections[source] = []
            
            node_connections[source].append(target)
            logger.info(f"内部边缘: {source} -> {target}")
        
        # Build Node Input Mapping
        for node_id, node in internal_node_instances.items():
            if hasattr(node, "inputs") and node.inputs:
                node_inputs_map[node_id] = []
                for input_config in node.inputs:
                    input_key = input_config.get("key")
                    source_node = input_config.get("sourceNode")
                    source_output = input_config.get("sourceOutput")
                    
                    if input_key and source_node and source_output:
                        node_inputs_map[node_id].append({
                            "key": input_key,
                            "sourceNode": source_node,
                            "sourceOutput": source_output
                        })
                        logger.info(f"节点 {node_id} 输入 {input_key} 来自 {source_node}.{source_output}")
        
        # Find the starting node (node without edge)
        start_nodes = []
        all_targets = set()
        
        # Collect all nodes as targets
        for targets in node_connections.values():
            all_targets.update(targets)
        
        # Find the node that is not targeted, i.e. the starting node
        for node_id in internal_node_instances.keys():
            if node_id not in all_targets:
                start_nodes.append(node_id)
                logger.info(f"发现起始节点: {node_id}")
        
        # If there is no clear starting node, use the first node
        if not start_nodes and internal_node_instances:
            start_nodes = [list(internal_node_instances.keys())[0]]
            logger.info(f"没有明确的起始节点，使用第一个节点: {start_nodes[0]}")
        
        # execution node
        visited_nodes = set()
        execution_order = []  # Record node execution order
        current_nodes = start_nodes.copy()
        
        # Handling global variable references
        for node_id, node in internal_node_instances.items():
            # Handling input references
            for input_def in node.inputs:
                source_node = input_def.get("sourceNode")
                
                # If you refer to a global variable
                if source_node == "global":
                    source_output = input_def.get("sourceOutput")
                    input_key = input_def.get("key")
                    
                    if source_output and input_key and "global" in iteration_context:
                        # Get a value from a global variable
                        global_value = self._get_value_from_context(iteration_context["global"], source_output)
                        
                        # If there is no current_node_inputs, create an empty dictionary
                        if "current_node_inputs" not in workflow_context.data:
                            workflow_context.data["current_node_inputs"] = {}
                        
                        # Add to input
                        workflow_context.data["current_node_inputs"][input_key] = global_value
                        logger.info(f"节点 {node_id} 从全局变量获取输入: {input_key}={global_value}")
        
        # Check if there are any nodes waiting to be restored.
        waiting_node_id = None
        loop_state = context.get("_loop_state", {})
        if loop_state and loop_state.get("node_id") == self.id:
            waiting_node_id = loop_state.get("waiting_node_id")
            if waiting_node_id:
                logger.info(f"检测到等待恢复的节点: {waiting_node_id}")
                
                # If a waiting node is found, execute directly from that node
                if waiting_node_id in internal_node_instances:
                    current_nodes = [waiting_node_id]
                    logger.info(f"从等待节点 {waiting_node_id} 开始恢复执行")
        
        # BFS executes all nodes
        while current_nodes:
            next_nodes = []
            
            for node_id in current_nodes:
                if node_id in visited_nodes:
                    continue
                
                visited_nodes.add(node_id)
                node = internal_node_instances.get(node_id)
                
                if not node:
                    continue
                
                try:
                    # pre-execution node recording
                    execution_order.append(node_id)
                    logger.info(f"开始执行节点: {node_id} (序号: {len(execution_order)})")
                    
                    # Prepare node inputs before executing nodes
                    await self._prepare_internal_node_inputs(node, internal_node_results, workflow_context)
                    
                    # Execution Node - Use WorkflowContext object instead of dictionary
                    logger.info(f"执行内部节点: {node_id}")
                    result = await node.execute(workflow_context)
                    
                    # Record details of execution results
                    logger.info(f"节点 {node_id} 执行完成，状态: {node.status}")
                    logger.info(f"节点 {node_id} 结果类型: {type(result)}")
                    # Check if the node is in a waiting state
                    if node.status == NodeStatus.WAITING:
                        logger.info(f"节点 {node_id} 处于等待状态，暂停内部循环执行")
                        
                        # Save partial results
                        internal_node_results[node_id] = result
                        
                        # Log user message information
                        if "user_message" in workflow_context.data:
                            logger.info(f"等待时的用户消息: {workflow_context.data.get('user_message', '')}")
                        
                        # Returns a result with a wait state
                        return {
                            "waiting": True,
                            "waiting_node_id": node_id,
                            "iteration": iteration,
                            "item": item,
                            "partial_results": internal_node_results
                        }
                    
                    if isinstance(result, dict):
                        # Record all keys of the result dictionary
                        logger.info(f"节点 {node_id} 结果键: {list(result.keys())}")
                        
                        # Record the details of some key values
                        important_keys = ["message", "content", "player", "memory_roles"]
                        for key in important_keys:
                            if key in result:
                                value = result[key]
                                value_type = type(value).__name__
                                value_str = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                                logger.info(f"节点 {node_id} 结果 {key}: ({value_type}) {value_str}")
                    
                    # Save the result
                    internal_node_results[node_id] = result
                    
                    # Update context, add output
                    for output_def in node.outputs:
                        output_key = output_def.get("key")
                        if output_key and output_key in result:
                            workflow_context.data[output_key] = result[output_key]
                            # Update iteration_context at the same time to stay in sync
                            iteration_context[output_key] = result[output_key]
                            logger.info(f"更新上下文: {output_key} = {str(result[output_key])[:50]}")
                    
                    # Get the next node
                    next_node_ids = node_connections.get(node_id, [])
                    if next_node_ids:
                        logger.info(f"节点 {node_id} 的下一个节点: {next_node_ids}")
                    else:
                        logger.info(f"节点 {node_id} 没有下一个节点")
                    
                    next_nodes.extend(next_node_ids)
                
                except Exception as e:
                    logger.error(f"执行内部节点 {node_id} 失败: {str(e)}")
                    import traceback
                    logger.error(f"详细错误信息: {traceback.format_exc()}")
                    continue
            
            # Update the current node list
            current_nodes = next_nodes
        
        # record execution order
        logger.info(f"内部节点执行顺序: {execution_order}")
        
        # Returns the execution result of the internal node
        return {
            "iteration": iteration,
            "item": item,
            "internal_results": internal_node_results
        }
    
    async def _prepare_internal_node_inputs(self, node: Node, node_results: Dict[str, Dict[str, Any]], workflow_context):
        """Prepare input data for internal nodes
_prepare_node_inputs Method Implementation in Reference engine.py

Rule:
1. If sourceNode and sourceOutput are specified, pass them according to the specified relationship
2. If there is no specified relationship, but the output and input key names of the upper and lower nodes match, the one-to-one correspondence is passed

Args:
Node: The current node to execute
node_results: result dictionary of executed nodes
workflow_context: Workflow Context"""
        # If the node has no input configuration, return directly
        if not node.inputs:
            logger.info(f"节点 {node.id} 没有输入配置")
            return
        
        input_data = {}
        
        # Process each input
        for input_config in node.inputs:
            input_key = input_config.get("key")
            if not input_key:
                continue
                
            source_node_id = input_config.get("sourceNode")
            source_output = input_config.get("sourceOutput")
            
            # Case 1: Source node and output are specified
            if source_node_id and source_output:
                logger.info(f"按指定关系获取输入: {input_key} <- {source_node_id}.{source_output}")
                
                # Get the execution result of the source node
                source_result = node_results.get(source_node_id)
                if not source_result:
                    logger.warning(f"来源节点 {source_node_id} 的执行结果不存在")
                    continue
                
                # Get source output data
                output_value = source_result.get(source_output)
                if output_value is None:
                    logger.warning(f"来源节点 {source_node_id} 的输出 {source_output} 不存在")
                    continue
                
                # Set input data
                input_data[input_key] = output_value
                logger.info(f"设置输入 {input_key} = {str(output_value)[:50]}")
                
            # Case 2: No source node is specified, try key name matching
            else:
                found_matching_output = False
                
                # Traverse the executed node results
                for prev_node_id, prev_result in node_results.items():
                    # Check if there is any output matching the current input key name in the result
                    if input_key in prev_result:
                        input_data[input_key] = prev_result[input_key]
                        found_matching_output = True
                        logger.info(f"按键名匹配设置输入: {input_key} <- {prev_node_id}.{input_key}")
                        break
                
                if not found_matching_output:
                    logger.info(f"未找到与输入 {input_key} 匹配的输出")
        
        # Check if it is in a loop context, and if so, associate the current iteration item to the node
        if "_loop" in workflow_context.data and "item" in workflow_context.data["_loop"]:
            loop_item = workflow_context.data["_loop"]["item"]
            
            # Special treatment for AI player speaking nodes
            if node.component_type == "ai_player_speak" and hasattr(node, "speaker_id") and node.speaker_id == "none":
                logger.info(f"检测到AI玩家发言节点，speaker_id=none，将循环项作为发言者")
                # No additional input is required at this point, the loop item itself is already the speaker
                
            # Checks for fields in the input that do not specify a source but are named "item", "player", "character", etc
            for input_key in ["item", "player", "character", "game_role"]:
                if input_key in [cfg.get("key") for cfg in node.inputs] and input_key not in input_data:
                    input_data[input_key] = loop_item
                    logger.info(f"将循环项关联到输入: {input_key}")
        
        # Enhanced handling: Special handling of message and ai_player_speak nodes, adding all available variables
        if node.component_type in ["message", "ai_player_speak"]:
            # Collect output from all existing results to input_data
            for node_id, result in node_results.items():
                if isinstance(result, dict):
                    for key, value in result.items():
                        # Avoid overwriting set inputs
                        if key not in input_data:
                            input_data[key] = value
                            logger.info(f"添加额外变量: {key}")
            
            # Add the values in the loop data to the input as well
            if "_loop" in workflow_context.data and isinstance(workflow_context.data["_loop"], dict):
                loop_data = workflow_context.data["_loop"]
                input_data["loop_index"] = loop_data.get("index")
                input_data["loop_item"] = loop_data.get("item")
                logger.info(f"添加循环变量: loop_index={loop_data.get('index')}")
                
            # Add all top-level key-value pairs in the context to the input as well
            for key, value in workflow_context.data.items():
                if key != "current_node_inputs" and key != "_loop" and key not in input_data:
                    if not isinstance(value, dict) and not isinstance(value, list) and not callable(value):
                        input_data[key] = value
                        logger.info(f"添加上下文变量: {key}")
                        
            # If there is global data, add global variables as well
            if "global" in workflow_context.data and isinstance(workflow_context.data["global"], dict):
                global_data = workflow_context.data["global"]
                for key, value in global_data.items():
                    if key not in input_data:
                        input_data[key] = value
                        logger.info(f"添加全局变量: {key}")
            
            # If you have state or game_state data, add their fields as well
            for state_key in ["state", "game_state"]:
                if state_key in workflow_context.data and isinstance(workflow_context.data[state_key], dict):
                    state_data = workflow_context.data[state_key]
                    for key, value in state_data.items():
                        if key not in input_data:
                            input_data[key] = value
                            logger.info(f"添加状态变量: {key}")
        
        # If there is input data, add it to the context
        if input_data:
            workflow_context.data["current_node_inputs"] = input_data
            logger.info(f"节点 {node.id} 输入数据: {list(input_data.keys())}")
        else:
            logger.warning(f"节点 {node.id} 没有找到任何输入数据")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        result = super().to_dict()
        result.update({
            "loop_mode": self.mode,
            "max_iterations": self.iterations,
            "loop_variable": self.loop_variable,
            "condition_key": self.condition_key,
            "condition_value": self.condition_value,
            "condition_operator": self.condition_operator,
            "iterator_source": self.iterator_key,
            "iterator_variable": self.iterator_variable,
            "internal_nodes": self.internal_nodes,
            "internal_edges": self.internal_edges
        })
        return result 