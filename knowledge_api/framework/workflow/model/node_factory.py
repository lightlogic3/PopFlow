
from typing import Dict,List, Type

from knowledge_api.framework.workflow.model.node import Node

try:
    import jinja2
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False

from knowledge_api.framework.workflow.types import (
    NodeDefinition
)
from knowledge_api.utils.log_config import get_logger

logger = get_logger()


class NodeFactory:
    """Node factory class

Responsible for creating and registering node types"""

    def __init__(self):
        """Initialize Node Factory"""
        self.node_types: Dict[str, Type[Node]] = {}

    def register_node_type(self, node_type: str, node_class: Type[Node]) -> None:
        """Registered Node Type

Args:
node_type: Node Type Identifier
node_class: Node class"""
        if not issubclass(node_class, Node):
            raise ValueError(f"节点类 {node_class.__name__} 必须是 Node 的子类")

        self.node_types[node_type] = node_class
        logger.info(f"注册节点类型: {node_type} -> {node_class.__name__}")

    def create_node(self, node_definition: NodeDefinition) -> Node:
        """Create node instance

Args:
node_definition: Node Definition

Returns:
Node instance"""
        node_type = node_definition.type

        if node_type not in self.node_types:
            # Node type is not registered, use default node processing
            logger.warning(f"节点类型 {node_type} 未注册，使用默认节点处理")
            return Node(node_definition.id, node_definition.name, node_definition.type, node_definition.properties)

        # Create node instance
        node_class = self.node_types[node_type]

        # The MessageNode constructor requires only three parameters
        if node_class.__name__ == "MessageNode" or node_class.__name__ == "PlayerTurnNode":
            return node_class(node_definition.id, node_definition.name, node_definition.properties)

        # general node constructor
        return node_class(node_definition.id, node_definition.name, node_definition.type, node_definition.properties)

    def get_registered_types(self) -> List[str]:
        """Get all registered node types

Returns:
Node type list"""
        return list(self.node_types.keys())