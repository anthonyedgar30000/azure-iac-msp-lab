from __future__ import annotations

from dataclasses import dataclass
import os
import re
from typing import Mapping
from urllib.parse import urlparse


DEFAULT_TOKEN_SCOPE = "https://ai.azure.com/.default"
_ALLOWED_HOST_SUFFIXES = (".openai.azure.com", ".services.ai.azure.com")
_DEPLOYMENT_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class ConfigurationError(ValueError):
    """Raised when provider configuration violates a fail-closed boundary."""


def _parse_bounded_int(
    environ: Mapping[str, str],
    name: str,
    *,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    raw = environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer") from exc
    if not minimum <= value <= maximum:
        raise ConfigurationError(
            f"{name} must be between {minimum} and {maximum}"
        )
    return value


def _normalize_base_url(raw: str) -> str:
    value = raw.strip()
    if not value:
        raise ConfigurationError("AZURE_OPENAI_BASE_URL is required")

    parsed = urlparse(value)
    if parsed.scheme != "https":
        raise ConfigurationError("AZURE_OPENAI_BASE_URL must use HTTPS")
    if parsed.username or parsed.password:
        raise ConfigurationError("AZURE_OPENAI_BASE_URL must not contain user info")
    if parsed.port is not None:
        raise ConfigurationError("AZURE_OPENAI_BASE_URL must not specify a port")
    if parsed.query or parsed.fragment or parsed.params:
        raise ConfigurationError(
            "AZURE_OPENAI_BASE_URL must not contain query, fragment, or params"
        )

    host = (parsed.hostname or "").lower()
    if not any(host.endswith(suffix) for suffix in _ALLOWED_HOST_SUFFIXES):
        raise ConfigurationError(
            "AZURE_OPENAI_BASE_URL must target an approved Azure AI hostname"
        )

    normalized_path = parsed.path.rstrip("/")
    if normalized_path != "/openai/v1":
        raise ConfigurationError(
            "AZURE_OPENAI_BASE_URL path must be exactly /openai/v1/"
        )

    return f"https://{host}/openai/v1/"


@dataclass(frozen=True, slots=True)
class AzureOpenAISettings:
    """Validated settings for the OpenAI SDK against an Azure v1 endpoint."""

    base_url: str
    deployment: str
    token_scope: str = DEFAULT_TOKEN_SCOPE
    timeout_seconds: int = 30
    max_retries: int = 0

    @classmethod
    def from_env(
        cls,
        environ: Mapping[str, str] | None = None,
    ) -> "AzureOpenAISettings":
        source = os.environ if environ is None else environ

        if source.get("AZURE_OPENAI_API_KEY", "").strip():
            raise ConfigurationError(
                "AZURE_OPENAI_API_KEY is prohibited for this Entra-only provider"
            )

        deployment = source.get("AZURE_OPENAI_MODEL_DEPLOYMENT", "").strip()
        if not deployment:
            raise ConfigurationError(
                "AZURE_OPENAI_MODEL_DEPLOYMENT is required"
            )
        if not _DEPLOYMENT_PATTERN.fullmatch(deployment):
            raise ConfigurationError(
                "AZURE_OPENAI_MODEL_DEPLOYMENT contains unsupported characters"
            )

        token_scope = source.get(
            "AZURE_OPENAI_TOKEN_SCOPE",
            DEFAULT_TOKEN_SCOPE,
        ).strip()
        if token_scope != DEFAULT_TOKEN_SCOPE:
            raise ConfigurationError(
                "AZURE_OPENAI_TOKEN_SCOPE must remain pinned to "
                f"{DEFAULT_TOKEN_SCOPE}"
            )

        return cls(
            base_url=_normalize_base_url(
                source.get("AZURE_OPENAI_BASE_URL", "")
            ),
            deployment=deployment,
            token_scope=token_scope,
            timeout_seconds=_parse_bounded_int(
                source,
                "AZURE_OPENAI_TIMEOUT_SECONDS",
                default=30,
                minimum=1,
                maximum=120,
            ),
            max_retries=_parse_bounded_int(
                source,
                "AZURE_OPENAI_MAX_RETRIES",
                default=0,
                minimum=0,
                maximum=2,
            ),
        )
