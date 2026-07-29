"""Governed read-only Azure MCP reality observer."""

from .config import ConfigurationError, RealitySettings
from .observer import (
    ObservationError,
    SERVER_VERSION,
    TOOL_INVENTORY_DIGEST,
    TOOL_NAME,
    observe_current_reality,
)

__all__ = [
    "ConfigurationError",
    "ObservationError",
    "RealitySettings",
    "SERVER_VERSION",
    "TOOL_INVENTORY_DIGEST",
    "TOOL_NAME",
    "observe_current_reality",
]
