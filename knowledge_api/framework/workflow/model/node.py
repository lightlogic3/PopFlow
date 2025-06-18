from typing import Dict, Any, List, Set
from abc import ABC
import re

from knowledge_api.framework.workflow.model.node_status import NodeStatus

try:
    import jinja2
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False

from knowledge_api.framework.workflow.types import (
     WorkflowContext
)
from knowledge_api.utils.log_config import get_logger

logger = get_logger()



class Node(ABC):
    """Workflow node base class

Responsible for:
1. Define the input and output of the node
2. Manage node status
3. Execute node logic
4. Provide serialization support"""

    # Node type identifier, which must be overridden by subclasses
    node_type: str = None

    # Node description for front-end display
    description: str = "base node"

    def __init__(self, id: str, name: str, component_type: str, config: Dict[str, Any]):
        """initialize node

Args:
ID: Node ID
Name: Node name
component_type: Node Type
Config: Node configuration"""
        self.id = id
        self.name = name
        self.component_type = component_type
        self.config = config
        self._status = NodeStatus.PENDING

        # Input and output configuration
        self.inputs: List[Dict[str, Any]] = []
        self.outputs: List[Dict[str, Any]] = []

        # error message
        self._error_message = ""

        # upstream and downstream nodes
        self.upstream_nodes: Set[str] = set()
        self.downstream_nodes: Set[str] = set()

    async def process(self, context: WorkflowContext) -> Dict[str, Any]:
        """processing node

Args:
Context: workflow context

Returns:
processing result"""
        raise NotImplementedError("Subclasses must implement this method")

    def get_status(self) -> NodeStatus:
        """Get node state"""
        return self._status

    @property
    def status(self) -> NodeStatus:
        """Node state property getter"""
        return self._status

    @status.setter
    def status(self, value: NodeStatus) -> None:
        """Node status property setter"""
        self._status = value

    def set_status(self, status: NodeStatus, error_message: str = "") -> None:
        """Set Node State

Args:
Status: New status
error_message: error message (if any)"""
        self._status = status
        if status == NodeStatus.FAILED and error_message:
            self._error_message = error_message

    def get_error(self) -> str:
        """Get error message"""
        return self._error_message

    @property
    def error_message(self) -> str:
        """Error message property getter"""
        return self._error_message

    def reset(self) -> None:
        """Reset node state"""
        self._status = NodeStatus.IDLE
        self._error_message = ""

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """execution node

Args:
Context: workflow context

Returns:
updated context"""
        try:
            # Set the status to Running
            self._status = NodeStatus.RUNNING

            # execution node logic
            result = await self.process(context)

            # Set to COMPLETED only if the node state is still RUNNING
            # This allows the process method to set other states (such as WAITING) and maintain that state
            if self._status == NodeStatus.RUNNING:
                self._status = NodeStatus.COMPLETED

            return result
        except Exception as e:
            # Set status to failed
            self._status = NodeStatus.FAILED
            # Throw the exception again
            raise

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "name": self.name,
            "node_type": self.node_type,
            "description": self.description,
            "config": self.config,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "status": self._status.value
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Node':
        """Create an instance from a dictionary"""
        node = cls(
            id=data.get("id"),
            name=data.get("name"),
            component_type=data.get("node_type"),
            config=data.get("config", {})
        )

        # Set up input and output ports
        node.inputs = data.get("inputs", [])
        node.outputs = data.get("outputs", [])

        return node

    def validate_inputs(self) -> bool:
        """Verify that the node input meets the requirements

Returns:
Verification result, True means the verification is passed."""
        # Verify that all required inputs have values
        for input_config in self.inputs:
            if input_config.get("required", False):
                input_key = input_config.get("key")
                if not input_key:
                    continue

                # TODO: Check if the input value exists
                # It is difficult to verify the validity of the input before actual execution, as the input may come from the execution results of upstream nodes
                # So the main check here is whether the configuration is complete.
                source_node = input_config.get("sourceNode")
                source_output = input_config.get("sourceOutput")
                if not source_node or not source_output:
                    self._error_message = f"必需的输入 {input_key} 未指定来源节点或输出"
                    return False

        return True

    def add_downstream_node(self, node_id: str) -> None:
        """Add downstream nodes

Args:
node_id: Downstream Node ID"""
        self.downstream_nodes.add(node_id)

    def add_upstream_node(self, node_id: str) -> None:
        """Add upstream node

Args:
node_id: Upstream Node ID"""
        self.upstream_nodes.add(node_id)

    def is_in_loop_context(self, context) -> bool:
        """Checks whether the current node is executing in a loop context

Args:
Context: workflow context

Returns:
Bool: whether in the loop context"""
        # Get contextual data
        context_data = self._get_context_data(context)

        # Check for loop markers
        # 1. Basic check: _loop dictionary exists
        if "_loop" in context_data:
            loop_data = context_data["_loop"]

            # Make sure _loop is a dictionary and contains key data
            if isinstance(loop_data, dict):
                # 2. Check if it contains clear markings
                if loop_data.get("is_loop_context") is True:
                    return True

                # 3. Check if index and item are included
                if "index" in loop_data and "item" in loop_data:
                    return True

                # 4. Including only items can also be considered valid
                if "item" in loop_data and loop_data["item"] is not None:
                    return True

        # 5. Check for other possible circular markers
        for key in ["loop_index", "loop_item", "iteration", "current_iteration"]:
            if key in context_data and context_data[key] is not None:
                return True

        return False

    def get_loop_item(self, context) -> Any:
        """Get the current iteration item in the loop context

Args:
Context: workflow context

Returns:
Any: The current iteration item, if not in the loop, returns None"""
        # Get contextual data
        context_data = self._get_context_data(context)

        # If you have _loop dictionary, try getting the item.
        if "_loop" in context_data and isinstance(context_data["_loop"], dict):
            loop_data = context_data["_loop"]
            # Return directly to the item field
            if "item" in loop_data:
                return loop_data["item"]

        # Try to get from other possible fields
        for key in ["loop_item", "current_item", "iteration_item"]:
            if key in context_data:
                return context_data[key]

        # Not in the loop or item not found
        return None

    def is_game_role(self, obj) -> bool:
        """Checks if the object is a GameRole type or similar structure

Args:
Obj: object to check

Returns:
Bool: whether it is a GameRole type or similar structure"""
        if obj is None:
            return False

        # Main check feature: GameRole objects should have chat methods
        has_chat = hasattr(obj, "chat") and callable(getattr(obj, "chat"))

        # auxiliary check feature
        has_identity = hasattr(obj, "identity")
        has_memory = hasattr(obj, "memory")
        has_name = hasattr(obj, "name")

        # Strong feature: Must have chat method
        if has_chat:
            return True

        # Medium characteristics: identity and memory
        if has_identity and has_memory:
            return True

        # Weak features: have identity and name
        if has_identity and has_name:
            return True

        # type name check
        obj_type = type(obj).__name__
        if "GameRole" in obj_type or "Player" in obj_type or "Character" in obj_type:
            return True

        return False

    def _get_context_data(self, context) -> Dict[str, Any]:
        """Get the data dictionary from the context

Args:
Context: may be a WorkflowContext object or a regular dictionary

Returns:
Dict [str, Any]: Context data dictionary"""
        if hasattr(context, 'data') and isinstance(context.data, dict):
            # If it is a WorkflowContext object
            return context.data
        elif isinstance(context, dict):
            # If it is already a dictionary
            return context
        else:
            # Other situations
            return {}

    def render_template(self, template: str, data: Dict[str, Any]) -> str:
        """Generic template rendering methods with support for Jinja2 (if available) and basic template replacement

Args:
Template: template string
Data: Variable data

Returns:
Rendered string"""
        # data validity check
        if data is None:
            logger.warning("The data is empty when rendering the template, using the original template")
            return template

        if not isinstance(data, dict):
            logger.warning(f"渲染模板时数据类型错误: {type(data)}，使用原始模板")
            return template

        # Create a flattened dictionary that makes nested fields directly accessible
        flat_data = {}

        # Recursive flattening of the dictionary (including all fields in state being promoted to the top level)
        def flatten_nested_dict(d, prefix='', result=None):
            if result is None:
                result = {}

            for key, value in d.items():
                # Skip functions and special objects
                if callable(value) or key == '_loop':
                    continue

                # Build full key name
                full_key = f"{prefix}{key}" if prefix else key

                # Add the value to the resulting dictionary
                result[full_key] = value

                # Handling nested dictionaries
                if isinstance(value, dict):
                    # Recursive processing of nested dictionaries, adding prefixed keys
                    flatten_nested_dict(value, f"{full_key}.", result)

                    # Special handling: if it is a top-level state or game_state dictionary, raise its fields to the top level
                    if full_key in ['state', 'game_state'] and not prefix:
                        # Add internal fields to the top level
                        for inner_key, inner_value in value.items():
                            # Add only if there is no key with the same name at the top level
                            if inner_key not in d:
                                result[inner_key] = inner_value

                # No longer recursively process dictionaries in lists to avoid complexity

            return result

        # flattening data
        flat_data = flatten_nested_dict(data)

        # Merge flattened data and original data sources
        render_data = {**flat_data}
        logger.debug(f"渲染模板的可用变量: {list(render_data.keys())}")

        # Using Jinja2 (if available)
        if HAS_JINJA2:
            try:
                # Using loose mode, undefined variables are replaced with empty strings instead of throwing exceptions
                env = jinja2.Environment(undefined=jinja2.Undefined)
                template_obj = env.from_string(template)
                return template_obj.render(**render_data)
            except Exception as e:
                logger.warning(f"Jinja2模板渲染失败，将使用基础模板渲染: {str(e)}")
                # If Jinja2 rendering fails, fallback to base template processing

        # Basic template processing (using regular expressions)
        pattern = r"{{(.*?)}}"

        def replace_var(match):
            var_path = match.group(1).strip()

            # First try to get it from the flattened dictionary
            if var_path in render_data:
                var_value = render_data[var_path]
                return str(var_value) if var_value is not None else ""

            # If it contains a dot, try to access it layer by layer
            if '.' in var_path:
                parts = var_path.split('.')
                current = data
                try:
                    for part in parts:
                        if isinstance(current, dict) and part in current:
                            current = current[part]
                        else:
                            logger.warning(f"变量路径 {var_path} 不存在，使用空字符串代替")
                            return ""
                    return str(current) if current is not None else ""
                except Exception as e:
                    logger.warning(f"访问嵌套变量 {var_path} 失败: {str(e)}")
                    return ""

            # If you can't find it, return empty string.
            logger.warning(f"变量 {var_path} 不存在，使用空字符串代替")
            return ""

        try:
            # Replace all variables
            result = re.sub(pattern, replace_var, template)
            return result
        except Exception as e:
            logger.error(f"基础模板渲染失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return template