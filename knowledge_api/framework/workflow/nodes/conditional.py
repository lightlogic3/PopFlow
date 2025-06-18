"""conditional node"""
import logging
from typing import Dict, Any, Optional, List
from knowledge_api.framework.workflow.model.node import Node
from knowledge_api.framework.workflow.model.node_status import NodeStatus
from knowledge_api.framework.workflow.types import WorkflowContext
from knowledge_api.utils.log_config import get_logger

# Initialize the logger
logger = get_logger()

class ConditionalNode(Node):
    """Conditional node, choose different execution paths according to the condition judgment

Configuration parameters:
- condition_key: Conditional key name
- condition_value: Conditional value
- condition_operator: conditional operators (==, !=, >, <, >=, <=, in, not in)

Input:
- Arbitrary input, as a data source for conditional judgment

Output:
- condition_result: Conditional judgment result (Boolean)
- selected_path: ID of the selected path"""
    # Node type identifier
    node_type: str = "conditional"
    def __init__(self, id: str, name: str, config: Dict[str, Any]):
        super().__init__(id, name, self.node_type, config)
        
        self.condition_key = config.get("condition_key", "")
        self.condition_value = config.get("condition_value", "")
        self.condition_operator = config.get("condition_operator", "==")
        
        # storage edge condition
        self.edge_conditions = []
    
    def set_edge_conditions(self, edge_conditions: List[Dict[str, Any]]) -> None:
        """Set edge conditions

Args:
edge_conditions: List of edge conditions [{target, key, value, operator},...]"""
        self.edge_conditions = edge_conditions
        logger.info(f"条件节点 {self.id} 设置了 {len(edge_conditions)} 个边缘条件")
    
    def evaluate_condition(self, key: str, value, operator: str, context_value) -> bool:
        """evaluation conditions

Args:
Key: Conditional key name
Value: Conditional value
Operator: Conditional operator
context_value: Actual value in context

Returns:
Conditional evaluation results"""
        logger.info(f"评估条件: {context_value} {operator} {value}")
        
        if operator == "==":
            return context_value == value
        elif operator == "!=":
            return context_value != value
        elif operator == ">":
            return context_value > value
        elif operator == "<":
            return context_value < value
        elif operator == ">=":
            return context_value >= value
        elif operator == "<=":
            return context_value <= value
        elif operator == "in":
            return context_value in value
        elif operator == "not in":
            return context_value not in value
        else:
            logger.warning(f"未知的条件操作符: {operator}")
            return False
    
    async def process(self, context: WorkflowContext) -> Dict[str, Any]:
        """processing condition node

Args:
Context: workflow context

Returns:
processing result"""
        logger.info(f"条件节点 {self.id} 处理开始")
        
        # Get Node Input
        input_data = context.data.get("current_node_inputs", {})
        
        # Condition for default node configuration
        condition_key = self.condition_key
        condition_value = self.condition_value
        condition_operator = self.condition_operator
        
        # Check for edge conditions
        selected_path = None
        condition_result = False
        
        # Record key data in the current context
        player_turn_result = context.data.get("player_turn_result", {})
        logger.info(f"条件节点上下文数据: player_turn_result={player_turn_result}")
        logger.info(f"条件节点用户消息: user_message={context.data.get('user_message')}")
        
        if hasattr(self, "edge_conditions") and self.edge_conditions:
            logger.info(f"条件节点边缘条件数量: {len(self.edge_conditions)}")
            # Traverse all edge conditions
            for edge in self.edge_conditions:
                edge_key = edge.get("key", "")
                edge_value = edge.get("value", "")
                edge_operator = edge.get("operator", "==")
                edge_target = edge.get("target", "")
                
                logger.info(f"检查边缘条件: key={edge_key}, value={edge_value}, operator={edge_operator}, target={edge_target}")
                
                # Make sure there is a key name
                if not edge_key:
                    logger.warning("Edge condition Missing key name, skip")
                    continue
                
                # Prioritize the use of keys in edge conditions
                condition_key = edge_key
                condition_value = edge_value
                condition_operator = edge_operator
                
                # Get the actual value from the context
                context_value = None
                
                # Check the recent player turn node results
                if condition_key in player_turn_result:
                    context_value = player_turn_result.get(condition_key)
                    logger.info(f"从玩家回合结果中获取值: {condition_key}={context_value}")
                elif condition_key in context.data:
                    context_value = context.data.get(condition_key)
                    logger.info(f"从上下文中获取值: {condition_key}={context_value}")
                elif condition_key in input_data:
                    context_value = input_data.get(condition_key)
                    logger.info(f"从输入数据中获取值: {condition_key}={context_value}")
                else:
                    logger.warning(f"未找到条件键 {condition_key} 的值")
                    context_value = None
                
                # If no value is found, skip this condition
                if context_value is None:
                    logger.warning(f"条件键 {condition_key} 的值为空，跳过此条件")
                    continue
                
                # evaluation conditions
                try:
                    logger.info(f"条件评估: '{context_value}' {condition_operator} '{condition_value}'")
                    condition_result = self.evaluate_condition(
                        condition_key, condition_value, condition_operator, context_value
                    )
                    
                    logger.info(f"条件 {condition_key} {condition_operator} {condition_value} 评估结果: {condition_result}")
                    
                    # If the condition holds, choose this path
                    if condition_result:
                        selected_path = edge_target
                        logger.info(f"条件成立，选择路径: {selected_path}")
                        break
                except Exception as e:
                    logger.error(f"评估条件失败: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    continue
        else:
            logger.warning(f"条件节点 {self.id} 没有边缘条件")
        
        # Set the status to complete
        self.status = NodeStatus.COMPLETED
        
        # Save the result to context
        context.data["conditional_result"] = condition_result
        context.data["selected_path"] = selected_path
        
        # Return result
        return {
            "condition_result": condition_result,
            "selected_path": selected_path
        } 