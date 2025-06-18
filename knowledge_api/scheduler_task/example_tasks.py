"""Example Timed Task

Example of timed tasks tagged with scheduled_task decorator"""
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from knowledge_api.framework.redis.cache_manager import CacheManager
from knowledge_api.scheduler_task import scheduled_task

logger = logging.getLogger(__name__)


@scheduled_task(
    name="Simple task example",
    description="A simple example task to log a message and return a result",
    tags=["example", "foundation"]
)
async def simple_task(message: str = "Hello World") -> Dict[str, Any]:
    """Simple task example

@param message: message content
@Return: execution result"""

    data=await CacheManager().get_system_config("AGENT_CONFIG_ROLE_TASK",
                                                                      "doubao-1-5-thinking-pro-250415")
    logger.info(f"Simple task executed with message: {message}、，{data}")
    # sleep
    return {
        "message": data,
        "timestamp": datetime.now().isoformat()
    }
