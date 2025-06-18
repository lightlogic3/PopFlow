"""Workflow Engine Module

This module provides a flexible workflow engine for building and executing game logic workflows."""
from typing import Dict, Any, List

from knowledge_api.framework.workflow.types import (
    NodeInput, NodeOutput, NodeConnection, NodePosition,
    NodeDefinition, WorkflowDefinition, NodeExecutionResult,
    WorkflowContext, WorkflowExecutionResult
)
from knowledge_api.framework.workflow.engine import WorkflowEngine
from knowledge_api.framework.workflow.template_loader import load_template, list_templates
from knowledge_api.utils.log_config import get_logger
from knowledge_api.framework.workflow.model.node import Node
from knowledge_api.framework.workflow.model.node_factory import NodeFactory
from knowledge_api.framework.workflow.model.node_status import NodeStatus
logger = get_logger()

__all__ = [
    "Node", "NodeFactory", "WorkflowEngine", 
    "NodeInput", "NodeOutput", "NodeConnection", "NodePosition",
    "NodeDefinition", "WorkflowDefinition", "NodeExecutionResult",
    "WorkflowContext", "WorkflowExecutionResult", "NodeStatus",
    "load_templates", "get_workflow_engine"
]

# Global Workflow Engine Instance
_workflow_engines: Dict[str, WorkflowEngine] = {}

def load_templates() -> Dict[str, Dict[str, Any]]:
    """Load all available workflow templates

Returns:
Template ID to template metadata mapping"""
    return list_templates()

def get_workflow_engine(template_id: str) -> WorkflowEngine:
    """Get the workflow engine instance

If the workflow engine with the specified ID does not exist, create a new instance and load the template

Args:
template_id: Template ID

Returns:
workflow engine instance"""
    global _workflow_engines
    
    # Check if there is an engine instance
    if template_id in _workflow_engines:
        return _workflow_engines[template_id]
    
    # Create a new workflow engine
    engine = WorkflowEngine()
    
    # load template
    try:
        engine.load_template_by_id(template_id)
        _workflow_engines[template_id] = engine
        logger.info(f"成功创建工作流引擎: {template_id}")
        return engine
    except Exception as e:
        logger.error(f"创建工作流引擎失败: {str(e)}")
        raise 