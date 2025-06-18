"""Player turn node"""
import logging
from typing import Dict, Any, Optional

from knowledge_api.framework.workflow.types import WorkflowContext
from knowledge_api.utils.log_config import get_logger
from knowledge_api.framework.workflow.model.node import Node
from knowledge_api.framework.workflow.model.node_status import NodeStatus

# Initialize the logger
logger = get_logger()


class PlayerTurnNode(Node):
    """The player turns the node, waiting for the player to enter a message

Configuration parameters:
- timeout: timeout (seconds)
- turn_message: turn prompt message
- result_key: Result saved key name

Output:
- player_message: Message content entered by the player
- turn_complete: Round completed"""
    # Node type identifier
    node_type: str = "function_tool"

    def __init__(self, id: str, name: str, config: Dict[str, Any]):
        super().__init__(id, name, self.node_type, config)

        self.timeout = config.get("timeout", 60)  # Default 60 second timeout
        self.turn_message = config.get("turn_message", "Please enter your turn operation")
        self.result_key = config.get("result_key", "player_turn_result")

    async def process(self, context: WorkflowContext) -> Dict[str, Any]:
        """Handle player rounds

At this node, instead of actively waiting for player input, we check if there is already a user message in the context
If so, process the message and return the result
If not, return to the WAITING state and wait for the workflow engine to resume execution after receiving the user message

Args:
Context: workflow context

Returns:
processing result"""
        logger.info(f"玩家回合节点 {self.id} 处理开始")

        # Get session ID
        session_id = context.data.get("session_id")
        if not session_id:
            logger.warning("The session ID does not exist and cannot handle player rounds")
            self.status = NodeStatus.ERROR
            return {
                "error": "Session ID does not exist"
            }

        # Check if it is inside the loop
        is_in_loop = "_loop" in context.data and context.data.get("_loop", {}).get("is_loop_context", False)
        loop_index = context.data.get("_loop", {}).get("index", -1)
        if is_in_loop:
            logger.info(f"检测到节点在循环内部执行，循环索引: {loop_index}")

        # Check if execution is resumed from the workflow
        is_resuming = context.data.get("processing_new_message", False)
        if is_resuming:
            logger.info(f"检测到工作流正在处理新消息，重置节点状态")
            # Reset processing flag
            node_processed_key = f"{self.id}_processed"
            context.data[node_processed_key] = False

        # Special handling: detecting the second and subsequent iterations in the loop
        node_processed_key = f"{self.id}_processed"
        if is_in_loop and loop_index > 0 and node_processed_key not in context.data:
            logger.info(f"循环中的非首次迭代 (索引 {loop_index})，强制进入等待状态")

            # Send a round prompt and wait
            logger.info(f"循环迭代 {loop_index}: 等待玩家输入消息：{self.turn_message}")

            # Send a round alert message
            broadcast_func = context.data.get("broadcast_message")
            if callable(broadcast_func):
                await broadcast_func(session_id, {
                    "type": "player_turn",
                    "message": self.turn_message,
                    "node_id": self.id
                })

            # Set the status to wait
            self.status = NodeStatus.WAITING

            # Return waiting status result
            return {
                "waiting_for_player": True,
                "turn_message": self.turn_message,
                "loop_index": loop_index
            }

        # Check if the node has processed the message
        if context.data.get(node_processed_key):
            logger.info(f"节点 {self.id} 已经处理过消息，重置状态并等待新消息")
            # Reset the node state and prepare to receive new messages
            context.data[node_processed_key] = False

            # Make sure user messages are cleared to avoid reuse in loops
            if "user_message" in context.data:
                logger.info(f"清除已处理的用户消息: {context.data['user_message']}")
                context.data["user_message"] = ""

            # Send a round prompt and wait
            logger.info(f"等待玩家输入新消息：{self.turn_message}")

            # Send a round alert message
            broadcast_func = context.data.get("broadcast_message")
            if callable(broadcast_func):
                await broadcast_func(session_id, {
                    "type": "player_turn",
                    "message": self.turn_message,
                    "node_id": self.id
                })

            # Set the status to wait
            self.status = NodeStatus.WAITING

            # Return waiting status result
            return {
                "waiting_for_player": True,
                "turn_message": self.turn_message
            }

        # Check for user messages
        user_message = context.data.get("user_message")
        logger.info(f"检查用户消息: '{user_message}'")

        # If the user message is empty or None, wait for the player to enter
        if user_message is None or user_message == "":
            # Send a round prompt and wait
            logger.info(f"等待玩家输入消息：{self.turn_message}")

            # Send a round alert message
            broadcast_func = context.data.get("broadcast_message")
            if callable(broadcast_func):
                await broadcast_func(session_id, {
                    "type": "player_turn",
                    "message": self.turn_message,
                    "node_id": self.id
                })

            # Set the status to wait
            self.status = NodeStatus.WAITING

            # Return waiting status result
            return {
                "waiting_for_player": True,
                "turn_message": self.turn_message
            }

        # If there is a user message, process the message
        logger.info(f"收到玩家消息：'{user_message}'")

        # Save user messages to the results
        result = {
            "player_message": user_message,
            "turn_complete": True
        }

        # Save the result to context
        context.data[self.result_key] = result

        # Marks that the node has processed the message
        context.data[node_processed_key] = True

        # Clear user messages to ensure that the next node is not reused
        logger.info(f"用户消息已处理，清除以避免重复使用")
        context.data["user_message"] = ""

        # Set the status to complete
        self.status = NodeStatus.COMPLETED
        logger.info(f"玩家回合节点 {self.id} 处理完成，继续执行后续节点")

        return result
