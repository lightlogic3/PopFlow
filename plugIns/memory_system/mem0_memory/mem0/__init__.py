# import importlib.metadata

# __version__ = importlib.metadata.version("mem0ai")
__version__ = "0.1.100"

from plugIns.memory_system.mem0_memory.mem0.client.main import MemoryClient,AsyncMemoryClient
from plugIns.memory_system.mem0_memory.mem0.memory.main import AsyncMemory, Memory  # noqa

__all__ = [
    "Memory",
    "MemoryClient",
    "AsyncMemory",
    "AsyncMemoryClient",
]


