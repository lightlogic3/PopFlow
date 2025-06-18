from typing import Dict, Optional, Any, List
from pydantic import BaseModel


class TaskGameInput(BaseModel):
    """Game task input model
Used to pass parameters required for game initialization"""
    task_id: str  # Task ID
    session_id: Optional[str] = None  # Session ID, WebSocket connection usage
    game_type: str  # Game Type
    roles: List[str] # The role selected by the user.
    user_info:Dict[str,Any] # User information, access to other configuration information


