"""Workflow Engine Module

Provides core functionality for workflow loading, execution, and management"""

from datetime import datetime
from typing import Dict, List, Any, Optional
import inspect

from knowledge_api.framework.workflow.model.node import Node
from knowledge_api.framework.workflow.model.node_factory import NodeFactory
from knowledge_api.framework.workflow.model.node_status import NodeStatus
from knowledge_api.framework.workflow.nodes.node_registry import node_registry
from knowledge_api.framework.workflow.types import (
    WorkflowDefinition,
    WorkflowContext
)
from knowledge_api.framework.workflow.template_loader import load_template
from knowledge_api.utils.log_config import get_logger

logger = get_logger()


class WorkflowEngine:
    """Workflow Engine

Responsible for loading, executing, and managing workflows"""
    
    def __init__(self, node_factory: Optional[NodeFactory] = None):
        """Initialize the workflow engine

Args:
node_factory: Node factory for creating node instances"""
        # Node Factory
        self.node_factory = node_factory if node_factory else NodeFactory()
        
        # workflow definition
        self.workflow_definition: Optional[WorkflowDefinition] = None
        
        # Node instance mapping
        self.nodes: Dict[str, Node] = {}
        
        # Connection mapping (source_node_id, source_output_id ) -> [( target_node_id, target_input_id) ]
        self.connections: Dict[str, List[str]] = {}
        
        # Conditional Edge Map source_node_id - > [ (target_node_id, condition) ]
        self.conditional_edges: Dict[str, List[Dict[str, Any]]] = {}
        
        # Start node (node without input connection)
        self.start_nodes: List[str] = []
        self.start_node: Optional[str] = None
        
        # Current workflow status
        self.is_running = False
        self.current_context: Optional[WorkflowContext] = None
        
        # Save node execution result
        self.node_results: Dict[str, Dict[str, Any]] = {}

    def load_workflow(self, workflow_definition: Dict[str, Any]) -> None:
        """Load workflow definition

Args:
workflow_definition: Workflow Definition (Dictionary Format)"""
        logger.info(f"开始加载工作流: {workflow_definition.get('id', '未知')}")
        
        # Reset current state
        self.nodes = {}
        self.connections = {}
        self.conditional_edges = {}
        self.start_nodes = []
        self.node_results = {}
        
        # Set the starting node
        self.start_node = workflow_definition.get("start_node")
        logger.info(f"工作流起始节点: {self.start_node}")
        
        # Create node instance
        for node_config in workflow_definition.get("nodes", []):
            try:
                node_id = node_config.get("id")
                node_name = node_config.get("name", "unnamed")
                component_type = node_config.get("component_type")
                
                if not node_id or not component_type:
                    logger.warning(f"节点配置缺少必要字段：{node_config}")
                    continue
                
                logger.info(f"正在处理节点: ID={node_id}, 类型={component_type}")
                
                # Copy node configuration and adjust field names
                node_def = {}
                node_def["id"] = node_id
                node_def["name"] = node_name
                node_def["type"] = component_type
                
                # replication configuration
                config = node_config.get("config", {})
                node_def["properties"] = config
                
                # Processing input and output
                node_def["inputs"] = node_config.get("inputs", [])
                node_def["outputs"] = node_config.get("outputs", [])
                
                # Create a node directly using node regedit
                if component_type in node_registry:
                    node_class = node_registry[component_type]
                    # Decide how to instantiate based on the __init__ parameters of the node class
                    init_params = list(inspect.signature(node_class.__init__).parameters.keys())
                    
                    if len(init_params) == 4 and 'config' in init_params:
                        # Suppose the constructor is __init__ (self, id, name, config)
                        node = node_class(node_id, node_name, config)
                    elif len(init_params) == 5 and 'component_type' in init_params and 'config' in init_params:
                        # Suppose the constructor is __init__ (self, id, name, component_type, config)
                        node = node_class(node_id, node_name, component_type, config)
                    else:
                        # Attempt for generic instantiation may fail
                        logger.warning(f"节点 {component_type} 的构造函数参数不匹配，尝试通用实例化")
                        try:
                           # Try (id, name, config) - works with MessageNode, PlayerTurnNode, etc
                           node = node_class(node_id, node_name, config)
                        except TypeError:
                            try:
                                # Try (id, name, component_type, config) - works with LoopNode, GameStateNode, etc
                                node = node_class(node_id, node_name, component_type, config)
                            except Exception as init_e:
                                logger.error(f"无法使用已知参数组合实例化节点 {node_id} ({component_type}): {init_e}")
                                continue 

                    # Node = node_class (node_id, node_name, config) #old BigInt
                else:
                    logger.warning(f"未知的节点类型: {component_type}，跳过")
                    continue
                
                # Save input and output configuration
                node.inputs = node_config.get("inputs", [])
                node.outputs = node_config.get("outputs", [])
                
                # Add to Node Map
                self.nodes[node_id] = node
                
                logger.info(f"已成功创建节点: {node_id}")
            except Exception as e:
                logger.error(f"创建节点失败: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
        
        # Handling connections and conditional edges
        edges = workflow_definition.get("edges", [])
        
        # Record all edge definitions to assist with debugging
        logger.info(f"工作流共有 {len(edges)} 条边缘")
        for i, edge in enumerate(edges):
            logger.info(f"边缘 {i+1}: {edge}")
        
        # First collect the edges of all conditional nodes
        for edge in edges:
            source_node_id = edge.get("source")
            target_node_id = edge.get("target")
            condition = edge.get("condition")
            
            if not source_node_id or not target_node_id:
                logger.warning(f"边缺少源或目标节点: {edge}")
                continue
            
            # Get source node
            source_node = self.nodes.get(source_node_id)
            if not source_node:
                logger.warning(f"未找到源节点: {source_node_id}")
                continue
            
            # Check if the source node is a conditional node
            if condition and (source_node.node_type == "conditional" or getattr(source_node, "component_type", "") == "conditional"):
                # Add Conditional Edge
                if source_node_id not in self.conditional_edges:
                    self.conditional_edges[source_node_id] = []
                
                # Building Conditional Edge Data
                edge_data = {
                    "target": target_node_id,
                    "key": condition.get("key", ""),
                    "value": condition.get("value", ""),
                    "operator": condition.get("operator", "==")
                }
                
                self.conditional_edges[source_node_id].append(edge_data)
                logger.info(f"已添加条件边缘: {source_node_id} -> {target_node_id}, 条件: {condition}")
            else:
                # Check if the node is a conditional node but no condition
                if source_node.node_type == "conditional" or getattr(source_node, "component_type", "") == "conditional":
                    logger.warning(f"条件节点 {source_node_id} 缺少条件定义，但有边缘连接到 {target_node_id}")
                
                # Add a normal connection
                if source_node_id not in self.connections:
                    self.connections[source_node_id] = []
                
                self.connections[source_node_id].append(target_node_id)
                logger.info(f"已添加连接: {source_node_id} -> {target_node_id}")
        
        # Set edge conditions for conditional nodes
        for node_id, edge_conditions in self.conditional_edges.items():
            node = self.nodes.get(node_id)
            if node and hasattr(node, "set_edge_conditions"):
                node.set_edge_conditions(edge_conditions)
                logger.info(f"为条件节点 {node_id} 设置了 {len(edge_conditions)} 个边缘条件")
            else:
                logger.warning(f"节点 {node_id} 不支持设置边缘条件或不存在")
        
        # Determine the starting node
        if not self.start_nodes and self.start_node and self.start_node in self.nodes:
            self.start_nodes = [self.start_node]
        
        # Save workflow definition
        self.workflow_definition = workflow_definition
        
        logger.info(f"工作流加载完成: ID={workflow_definition.get('id', '未知')}, 名称={workflow_definition.get('name', '未知')}")
        logger.info(f"工作流节点数量: {len(self.nodes)}")
        logger.info(f"工作流普通连接数量: {sum(len(targets) for targets in self.connections.values())}")
        logger.info(f"工作流条件连接数量: {sum(len(targets) for targets in self.conditional_edges.values())}")
        logger.info(f"工作流起始节点: {self.start_nodes}")
    
    async def execute_workflow(self, context_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """execution workflow

Args:
context_data: Initial Context Data

Returns:
Final context data"""
        if not self.start_node:
            raise ValueError("The workflow is not yet loaded or the starting node is missing")
        
        logger.info(f"开始执行工作流，起始节点：{self.start_node}")
        
        # Create workflow context
        if context_data is None:
            context_data = {}
            
        self.current_context = WorkflowContext(data=context_data)
        
        # Execute from the starting node
        current_node_id = self.start_node
        
        # execution start node
        return await self._execute_from_node(current_node_id)
    
    async def resume_workflow(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """Restore execution workflow

Args:
context_data: Updated context data

Returns:
Final context data"""
        if not self.current_context:
            logger.warning("The workflow has not started execution and cannot be resumed")
            return await self.execute_workflow(context_data)
        
        # Update context data
        if context_data:
            # Save original user messages (for logging)
            user_message = context_data.get("user_message", "")
            logger.info(f"恢复工作流执行，用户消息: {user_message}")
            
            # Update context data
            self.current_context.data.update(context_data)
            
            # Marks that a new message is currently being processed
            self.current_context.data["processing_new_message"] = True
            
            # Reset the processing flag of the relevant node
            loop_state = self.current_context.data.get("_loop_state", {})
            if loop_state and "waiting_node_id" in loop_state:
                waiting_node_id = loop_state["waiting_node_id"]
                node_processed_key = f"{waiting_node_id}_processed"
                if node_processed_key in self.current_context.data:
                    logger.info(f"重置等待节点 {waiting_node_id} 的处理标记")
                    self.current_context.data[node_processed_key] = False
        
        # Check if a loop iteration has been completed and need to move on to the next iteration
        loop_state = self.current_context.data.get("_loop_state", {})
        if loop_state and "current_iteration" in loop_state:
            current_iteration = loop_state.get("current_iteration", 0)
            # Check if there is a key to mark the completion of the iteration
            iteration_completed_key = "_iteration_completed"
            if iteration_completed_key in self.current_context.data and self.current_context.data[iteration_completed_key]:
                # An iteration has been completed, update the loop status to move on to the next iteration
                logger.info(f"检测到已完成循环迭代 {current_iteration}，准备进入下一次迭代")
                loop_state["current_iteration"] = current_iteration + 1
                self.current_context.data["_loop_state"] = loop_state
                # Remove completion tag
                del self.current_context.data[iteration_completed_key]
        
        # Get the current node ID
        current_node_id = self.current_context.data.get("current_node_id")
        
        # Check if there is a loop state
        loop_state = self.current_context.data.get("_loop_state")
        if loop_state and "node_id" in loop_state:
            # There is a loop state, using the loop node ID as the current node
            current_node_id = loop_state["node_id"]
            logger.info(f"检测到循环状态，恢复执行循环节点: {current_node_id}")
            
            # Record current loop information
            logger.info(f"当前循环状态: 迭代={loop_state.get('current_iteration')}, 等待节点={loop_state.get('waiting_node_id')}")
            
            # Make sure user messages are logged in the loop state
            if "user_message" in context_data:
                logger.info(f"确保用户消息能被传递到循环节点: {context_data.get('user_message')}")
        
        if not current_node_id or current_node_id not in self.nodes:
            logger.warning(f"无效的当前节点ID：{current_node_id}，从起始节点重新开始")
            current_node_id = self.start_node
        else:
            logger.info(f"从节点 {current_node_id} 恢复工作流执行")
        
        # Continue execution from the current node
        result = await self._execute_from_node(current_node_id)
        
        # Clear the flag that a new message is being processed
        if "processing_new_message" in result:
            del result["processing_new_message"]
            
        return result
    
    async def _execute_from_node(self, start_node_id: str) -> Dict[str, Any]:
        """Start execution of the workflow from the specified node

Args:
start_node_id: Start Node ID

Returns:
workflow context data"""
        # Prevent infinite loops
        visited_nodes = set()
        current_node_id = start_node_id
        
        logger.info(f"从节点 {start_node_id} 开始执行工作流")
        
        while current_node_id and current_node_id not in visited_nodes:
            # Mark a node as visited
            visited_nodes.add(current_node_id)
            
            # Get the current node
            current_node = self.nodes.get(current_node_id)
            if not current_node:
                logger.warning(f"未找到节点：{current_node_id}")
                break
            
            logger.info(f"执行节点：{current_node.name}({current_node.id})")
            
            # Prepare node input
            await self._prepare_node_inputs(current_node)
            
            # execution node
            result = await current_node.execute(self.current_context)
            
            # Save node execution result
            self.node_results[current_node.id] = result
            
            # If the node state is waiting, the workflow execution is suspended
            if current_node.status == NodeStatus.WAITING:
                logger.info(f"节点 {current_node.name} 正在等待，暂停工作流执行")
                # Update the current node ID in the context
                self.current_context.data["current_node_id"] = current_node_id
                return self.current_context.data
            
            # Check if it is a conditional node
            if current_node.node_type == "conditional" or current_node.__class__.__name__ == "ConditionalNode":
                logger.info(f"处理条件节点 {current_node.id} 的分支选择")
                
                # Get the selected path
                selected_path = result.get("selected_path")
                
                if selected_path:
                    logger.info(f"条件节点选择路径: {selected_path}")
                    # Get the selected node
                    next_node = self.nodes.get(selected_path)
                    
                    if next_node:
                        logger.info(f"执行条件选择的节点: {next_node.name}({next_node.id})")
                        
                        # Prepare node input
                        await self._prepare_node_inputs(next_node)
                        
                        # execution node
                        next_result = await next_node.execute(self.current_context)
                        
                        # Save node execution result
                        self.node_results[selected_path] = next_result
                        
                        # If the node state is waiting, the workflow execution is suspended
                        if next_node.status == NodeStatus.WAITING:
                            logger.info(f"节点 {next_node.name} 正在等待，暂停工作流执行")
                            # Update the current node ID in the context
                            self.current_context.data["current_node_id"] = selected_path
                            return self.current_context.data
                            
                        # Check if there are any follow-up nodes
                        next_next_nodes = self.connections.get(selected_path, [])
                        if next_next_nodes:
                            current_node_id = next_next_nodes[0]
                            logger.info(f"从节点 {selected_path} 转到下一个节点 {current_node_id}")
                            continue
                        else:
                            logger.info(f"节点 {next_node.name} 没有后续节点，工作流执行完成")
                    else:
                        logger.warning(f"未找到条件选择的节点: {selected_path}")
                else:
                    logger.warning(f"条件节点没有选择路径，尝试使用普通连接")
                    # If no path is selected, try using a normal connection
                    next_nodes = self.connections.get(current_node_id, [])
                    if next_nodes:
                        current_node_id = next_nodes[0]
                        logger.info(f"使用普通连接: {current_node_id} -> {next_nodes[0]}")
                        continue
                
                # Condition node executed, no more nodes to execute
                break
            
            # Check if it is a circular node
            loop_state = result.get("loop_state")
            if loop_state and result.get("loop_waiting"):
                # This is the case where the loop node completes one iteration and waits
                logger.info(f"循环节点 {current_node.id} 完成一次迭代，等待下一次迭代")
                # Mark this iteration as complete
                self.current_context.data["_iteration_completed"] = True
            
            # Get the next node
            next_nodes = self.connections.get(current_node_id, [])
            if not next_nodes:
                logger.info(f"节点 {current_node.name} 没有后续节点，工作流执行完成")
                break
            
            # Select the first subsequent node as the next node to execute
            next_node_id = next_nodes[0]
            logger.info(f"从节点 {current_node_id} 转到下一个节点 {next_node_id}")
            current_node_id = next_node_id
        
        logger.info("Workflow execution complete")
        return self.current_context.data

    async def _prepare_node_inputs(self, node: Node) -> None:
        """Prepare node input

Process the input configuration of the node and obtain data from the output of the upstream node

Args:
Node: current node"""
        # If the node has no input configuration, return directly
        if not node.inputs:
            return

        input_data = {}

        # Process each input
        for input_config in node.inputs:
            input_key = input_config.get("key")
            source_node_id = input_config.get("sourceNode")
            source_output = input_config.get("sourceOutput")

            # If no source node or output is specified, skip
            if not input_key or not source_node_id or not source_output:
                continue

            # Get the execution result of the source node
            source_result = self.node_results.get(source_node_id)
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

        # Add input data to context
        self.current_context.data["current_node_inputs"] = input_data

        # Add all existing node results at the same time, allowing nodes to access all variables
        if node.component_type in ["message", "ai_player_speak"]:
            # Collect output from all existing results to current_node_inputs
            for node_id, result in self.node_results.items():
                if isinstance(result, dict):
                    for key, value in result.items():
                        # Avoid overwriting set inputs
                        if key not in input_data:
                            input_data[key] = value

            # Add values from the global data to the input as well
            if "global" in self.current_context.data and isinstance(self.current_context.data["global"], dict):
                global_data = self.current_context.data["global"]
                for key, value in global_data.items():
                    if key not in input_data:
                        input_data[key] = value

            # Update input data in context
            self.current_context.data["current_node_inputs"] = input_data
            logger.info(f"为节点 {node.id} 准备的输入变量: {list(input_data.keys())}")








    """Function here has no specific usage scenario"""
    def get_node_status(self, node_id: str) -> Optional[NodeStatus]:
        """Get node state

Args:
node_id: Node ID

Returns:
Node state"""
        node = self.nodes.get(node_id)
        return node.status if node else None
    
    def get_node_output(self, node_id: str, output_id: str) -> Any:
        """Get node output value

Args:
node_id: Node ID
output_id: Output ID

Returns:
output value"""
        node = self.nodes.get(node_id)
        return node.get_output(output_id) if node else None
    
    def reset_workflow(self) -> None:
        """Reset workflow state"""
        for node in self.nodes.values():
            node.reset()
        
        self.is_running = False
        self.current_context = None
        
        logger.info(f"工作流已重置: ID={self.workflow_definition.id if self.workflow_definition else '未知'}")
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """Get workflow status

Returns:
Workflow status information"""
        if not self.workflow_definition:
            return {"status": "workflow not loaded"}
        
        # statistical node status
        node_status_counts = {}
        for node in self.nodes.values():
            status = node.status.value
            node_status_counts[status] = node_status_counts.get(status, 0) + 1
        
        # build status information
        return {
            "workflow_id": self.workflow_definition.id,
            "name": self.workflow_definition.name,
            "is_running": self.is_running,
            "node_count": len(self.nodes),
            "node_status": node_status_counts,
            "timestamp": datetime.now().isoformat()
        }
    
    def export_workflow(self) -> Dict[str, Any]:
        """Export workflow definition

Returns:
Workflow Definition Dictionary"""
        if not self.workflow_definition:
            raise ValueError("Workflow not loaded")
        
        return self.workflow_definition.dict()

    def load_template_by_id(self, template_id: str) -> None:
        """Load workflow template by ID

Args:
template_id: Template ID"""
        template = load_template(template_id)
        if not template:
            raise ValueError(f"未找到模板：{template_id}")
        
        self.load_workflow(template)
    

