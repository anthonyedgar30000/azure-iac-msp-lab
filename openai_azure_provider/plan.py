from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlparse

from .config import AzureOpenAISettings


def build_connection_plan(settings: AzureOpenAISettings) -> dict[str, Any]:
    """Return a non-secret, non-executing connection plan."""

    parsed = urlparse(settings.base_url)
    return {
        "schema_version": "openai-azure-provider.connection-plan.v1",
        "provider": "azure_openai_v1",
        "sdk": "openai-python",
        "authentication": "microsoft_entra_token_provider",
        "endpoint": {
            "host": parsed.hostname,
            "path": parsed.path,
            "https_required": True,
        },
        "model_deployment": settings.deployment,
        "token_scope": settings.token_scope,
        "timeout_seconds": settings.timeout_seconds,
        "max_retries": settings.max_retries,
        "client_constructed": False,
        "azure_authentication_performed": False,
        "model_request_performed": False,
        "mcp_connection_configured": False,
    }


def main() -> int:
    settings = AzureOpenAISettings.from_env()
    print(json.dumps(build_connection_plan(settings), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
