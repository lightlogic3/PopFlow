"""Type definitions for workflow engines"""

from typing import Dict, List, Any, Optional, Callable, Union, Set
from pydantic import BaseModel, Field


class NodeInput(BaseModel):
    """Node input definition"""
    id: str
    name: Optional[str] = None
    key: Optional[str] = None
    description: Optional[str] = None
    data_type: Optional[str] = "any"
    type: Optional[str] = None
    required: bool = True
    default_value: Optional[Any] = None
    sourceNode: Optional[str] = None
    sourceOutput: Optional[str] = None

    class Config:
        extra = "allow"


class NodeOutput(BaseModel):
    """Node output definition"""
    id: str
    name: Optional[str] = None
    key: Optional[str] = None
    description: Optional[str] = None
    data_type: Optional[str] = "any"
    type: Optional[str] = None

    class Config:
        extra = "allow"


class NodeConnection(BaseModel):
    """Node connection definition"""
    source_node_id: str
    source_output_id: str
    target_node_id: str
    target_input_id: str


class NodePosition(BaseModel):
    """Node location definition (for UI display)"""
    x: float
    y: float


class NodeDefinition(BaseModel):
    """Node definition"""
    id: str
    type: str
    name: str
    description: Optional[str] = None
    component_type: Optional[str] = None
    inputs: List[Union[NodeInput, Dict[str, Any]]] = Field(default_factory=list)
    outputs: List[Union[NodeOutput, Dict[str, Any]]] = Field(default_factory=list)
    position: Optional[NodePosition] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    config: Optional[Dict[str, Any]] = None

    class Config:
        extra = "allow"


class WorkflowDefinition(BaseModel):
    """workflow definition"""
    id: str
    name: str
    description: Optional[str] = None
    nodes: List[NodeDefinition] = Field(default_factory=list)
    connections: List[NodeConnection] = Field(default_factory=list)
    version: str = "1.0.0"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    author: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)


class NodeExecutionResult(BaseModel):
    """Node execution result"""
    node_id: str
    node_type: str
    success: bool
    error_message: Optional[str] = None
    outputs: Dict[str, Any] = Field(default_factory=dict)
    execution_time: float = 0.0


class WorkflowContext:
    """workflow context

Used to store data and status during workflow execution"""
    
    def __init__(self, data: Dict[str, Any] = None):
        """Initialize the workflow context

Args:
Data: initial data"""
        self.data = data or {}


class WorkflowExecutionResult(BaseModel):
    """workflow execution result"""
    workflow_id: str
    success: bool
    error_message: Optional[str] = None
    node_results: List[NodeExecutionResult] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    execution_time: float = 0.0


# For compatibility, add WorkflowTemplate type aliases
WorkflowTemplate = Dict[str, Any]
NodeConfig = Dict[str, Any] 