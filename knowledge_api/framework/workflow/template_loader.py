"""Workflow Template Loader"""
import os
import json
import logging
from typing import Dict, Any, Optional

from knowledge_api.utils.log_config import get_logger

# Initialize the logger
logger = get_logger()

# template directory
TEMPLATE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "templates"
)

def load_template(template_id: str) -> Optional[Dict[str, Any]]:
    """Load workflow template

Args:
template_id: Template ID

Returns:
Loaded template, return None if loading fails"""
    # If the template ID is a file name (without a path), look in the template directory
    if not os.path.isabs(template_id) and not template_id.endswith(".json"):
        template_path = os.path.join(TEMPLATE_DIR, f"{template_id}.json")
    else:
        template_path = template_id
    
    # If no extension exists, add the .json extension
    if not os.path.splitext(template_path)[1]:
        template_path += ".json"
    
    try:
        # Check if the file exists
        if not os.path.exists(template_path):
            logger.warning(f"模板文件不存在：{template_path}")
            return None
        
        # Load template file
        with open(template_path, "r", encoding="utf-8") as f:
            template = json.load(f)
        
        logger.info(f"成功加载模板：{template.get('name', template_id)}")
        return template
    except Exception as e:
        logger.error(f"加载模板失败：{str(e)}")
        return None

def list_templates() -> Dict[str, Dict[str, Any]]:
    """List all available templates

Returns:
Template ID to template metadata mapping"""
    templates = {}
    
    try:
        # Traverse the template directory
        for filename in os.listdir(TEMPLATE_DIR):
            if filename.endswith(".json"):
                template_id = os.path.splitext(filename)[0]
                template_path = os.path.join(TEMPLATE_DIR, filename)
                
                try:
                    # Load template file
                    with open(template_path, "r", encoding="utf-8") as f:
                        template = json.load(f)
                    
                    # Extracting template metadata
                    templates[template_id] = {
                        "id": template_id,
                        "name": template.get("name", template_id),
                        "description": template.get("description", ""),
                        "game_type": template.get("game_type", "")
                    }
                except Exception as e:
                    logger.error(f"加载模板元数据失败：{str(e)}")
    except Exception as e:
        logger.error(f"列出模板失败：{str(e)}")
    
    return templates 