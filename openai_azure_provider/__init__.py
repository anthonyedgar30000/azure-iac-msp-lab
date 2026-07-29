"""Governed Azure OpenAI / Microsoft Foundry provider scaffold.

Importing this package performs no authentication and no network calls.
"""

from .config import AzureOpenAISettings, ConfigurationError
from .plan import build_connection_plan

__all__ = [
    "AzureOpenAISettings",
    "ConfigurationError",
    "build_connection_plan",
]
