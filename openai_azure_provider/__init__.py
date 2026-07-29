"""Governed Azure OpenAI / Microsoft Foundry provider.

Importing this package performs no authentication and no network calls. Runtime
execution remains explicit through ``create_response`` or the invocation CLI.
"""

from .config import AzureOpenAISettings, ConfigurationError
from .plan import build_connection_plan

__all__ = [
    "AzureOpenAISettings",
    "ConfigurationError",
    "build_connection_plan",
]
