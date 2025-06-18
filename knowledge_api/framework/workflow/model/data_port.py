
from typing import Dict, Any
import uuid
try:
    import jinja2
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False
from knowledge_api.utils.log_config import get_logger

logger = get_logger()


class DataPort:
    """Data port definition"""

    def __init__(self, port_id: str, key: str, data_type: str,
                 description: str = "", required: bool = False):
        """Initialize data port

Args:
port_id: Port ID
Key: data key name
data_type: Data Type
Description: Description
Required: Required"""
        self.id = port_id
        self.key = key
        self.type = data_type
        self.description = description
        self.required = required

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "key": self.key,
            "type": self.type,
            "description": self.description,
            "required": self.required
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataPort':
        """Create an instance from a dictionary"""
        return cls(
            port_id=data.get("id", str(uuid.uuid4())),
            key=data.get("key", ""),
            data_type=data.get("type", "any"),
            description=data.get("description", ""),
            required=data.get("required", False)
        )



