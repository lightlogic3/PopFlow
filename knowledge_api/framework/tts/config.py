"""TTS service configuration"""
from typing import Dict, Any

TIMBRE_STATUS = {
    "ACTIVE": "active",     # active state
    "INACTIVE": "inactive", # inactive state
    "PENDING": "pending",   # pending state
    "TRAINING": "training"  # Training state
}

# Default timbre parameters
DEFAULT_SPEECH_PARAMS: Dict[str, Any] = {
    "speed_ratio": 1.0,
    "volume_ratio": 1.0,
    "pitch_ratio": 1.0
} 