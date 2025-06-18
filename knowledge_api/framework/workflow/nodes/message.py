"""message node"""
import logging
from typing import Dict, Any, Optional
from knowledge_api.framework.workflow.model.node import Node
from knowledge_api.framework.workflow.model.node_status import NodeStatus
from knowledge_api.utils.log_config import get_logger

# Initialize the logger
logger = get_logger()

class MessageNode(Node):
    """Message node for sending messages to users

Configuration parameters:
- initialMessage: initial message content (if no inputs)
- content_template: message content template (if there are inputs, it will be used for formatting)
- default_role: Message sender role, defaults to system

Input:
- Supports arbitrary names and numbers of input parameters that will be used to replace variables in the template

Output:
- message: formatted message content"""
    # Node type identifier
    node_type: str = "message"
    def __init__(self, id: str, name: str, config: Dict[str, Any]):
        super().__init__(id, name, self.node_type, config)
        
        self.initial_message = config.get("initialMessage", "")
        self.content_template = config.get("content_template", "")
        self.default_role = config.get("default_role", "system")
    
    async def process(self, context):
        """processing message node

Args:
Context: Workflow context, possibly of WorkflowContext or dictionary type

Returns:
processing result"""
        logger.info(f"消息节点 {self.id} 处理开始")
        
        # Check the context type and get the data
        try:
            if hasattr(context, 'data') and isinstance(context.data, dict):
                # If it is a WorkflowContext object
                context_data = context.data
            elif isinstance(context, dict):
                # If it is an ordinary dictionary
                logger.info(f"消息节点 {self.id} 收到字典对象而非 WorkflowContext")
                context_data = context
            else:
                logger.error(f"消息节点 {self.id} 收到未知类型的上下文: {type(context)}")
                self.status = NodeStatus.ERROR
                return {
                    "error": f"未知的上下文类型: {type(context)}"
                }
        except Exception as e:
            # Log exception details
            logger.error(f"消息节点 {self.id} 处理上下文时发生异常: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            self.status = NodeStatus.ERROR
            return {
                "error": f"处理上下文时发生异常: {str(e)}"
            }
        
        # Get session ID
        session_id = context_data.get("session_id")
        if not session_id:
            logger.warning("The session ID does not exist and the message cannot be sent")
            self.status = NodeStatus.ERROR
            return {
                "error": "Session ID does not exist"
            }
        
        # Get Node Input
        input_data = context_data.get("current_node_inputs", {})
        
        # Log all input variables for debugging
        logger.info(f"消息节点 {self.id} 收到的输入变量键: {list(input_data.keys())}")
        
        # record nested structure
        for key, value in input_data.items():
            if isinstance(value, dict):
                logger.debug(f"字典字段 '{key}' 包含子字段: {list(value.keys())}")
        
        # Extract all variable placeholders from the template
        import re
        template_vars = re.findall(r'{{(.*?)}}', self.content_template)
        if template_vars:
            # Remove spaces and check if these variables are in the input data
            template_vars = [v.strip() for v in template_vars]
            logger.info(f"模板需要的变量: {template_vars}")
            
            # Check if template variables are accessible
            for var in template_vars:
                var_parts = var.split('.')
                if len(var_parts) == 1:
                    # direct field
                    if var in input_data:
                        logger.debug(f"找到直接变量: {var}")
                    else:
                        logger.debug(f"未找到直接变量: {var}，将在渲染时尝试从嵌套结构中获取")
                else:
                    # Nested fields (such as state.riddle)
                    parent = var_parts[0]
                    child = var_parts[1]
                    if parent in input_data and isinstance(input_data[parent], dict) and child in input_data[parent]:
                        # Records find nested variables, but do not reveal the full content
                        logger.debug(f"找到嵌套变量: {var}")
        
        # Recording Content Template
        logger.info(f"内容模板: {self.content_template}")
        
        # Determine message content
        message_content = ""
        if input_data and self.content_template:
            # If there is input data, format it using the template rendering method of the parent class
            message_content = self.render_template(self.content_template, input_data)
        else:
            # Otherwise, use the initial message
            message_content = self.initial_message or self.content_template
        
        logger.info(f"发送消息：{message_content}")
        
        # Send message
        broadcast_func = context_data.get("broadcast_message")
        if callable(broadcast_func):
            await broadcast_func(session_id, {
                "type": "message",
                "role": self.default_role,
                "content": message_content,
                "node_id": self.id
            })
        else:
            logger.warning(f"消息节点 {self.id} 无法发送消息：广播函数不可用")
        
        # Set the status to complete
        self.status = NodeStatus.COMPLETED
        
        # Return result
        return {
            "message": message_content
        } 