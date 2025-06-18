from enum import Enum


class NodeStatus(Enum):
    """Node execution state enumeration"""
    IDLE = "idle"             # Initial/idle state
    READY = "ready"           # Ready and waiting to be executed
    RUNNING = "running"       # in progress
    COMPLETED = "completed"   # execution complete
    FAILED = "failed"         # execution failed
    SKIPPED = "skipped"       # Skipped
    WAITING = "waiting"       # Waiting for input or conditions
    PENDING = "pending"       # Wait for initialization