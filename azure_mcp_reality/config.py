from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
from typing import Mapping
from uuid import UUID


class ConfigurationError(ValueError):
    """Raised when the read-only reality observer is not safely configured."""


_RESOURCE_GROUP_PATTERN = re.compile(r"^[A-Za-z0-9._()\-]{1,90}$")


def _required(environ: Mapping[str, str], name: str) -> str:
    value = environ.get(name, "").strip()
    if not value:
        raise ConfigurationError(f"{name} is required")
    return value


def _bounded_int(
    environ: Mapping[str, str],
    name: str,
    *,
    default: int,
    minimum: int,
    maximum: int,
) -> int:
    raw = environ.get(name, str(default)).strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigurationError(f"{name} must be an integer") from exc
    if not minimum <= value <= maximum:
        raise ConfigurationError(f"{name} must be between {minimum} and {maximum}")
    return value


@dataclass(frozen=True)
class RealitySettings:
    """Exact subscription, resource-group, and repository scope for one observation."""

    subscription_id: str
    resource_group: str
    repository_root: Path
    command_timeout_seconds: int = 20
    max_resources: int = 200
    max_cognitive_accounts: int = 10

    @classmethod
    def from_env(
        cls,
        environ: Mapping[str, str] | None = None,
    ) -> "RealitySettings":
        source = os.environ if environ is None else environ

        subscription_id = _required(source, "AZURE_MCP_ALLOWED_SUBSCRIPTION_ID")
        try:
            subscription_id = str(UUID(subscription_id))
        except ValueError as exc:
            raise ConfigurationError(
                "AZURE_MCP_ALLOWED_SUBSCRIPTION_ID must be a UUID"
            ) from exc

        resource_group = _required(source, "AZURE_MCP_ALLOWED_RESOURCE_GROUP")
        if (
            not _RESOURCE_GROUP_PATTERN.fullmatch(resource_group)
            or resource_group.endswith(".")
        ):
            raise ConfigurationError(
                "AZURE_MCP_ALLOWED_RESOURCE_GROUP is not a valid bounded resource-group name"
            )

        repository_root = Path(
            source.get("AZURE_MCP_REPOSITORY_ROOT", ".")
        ).expanduser().resolve()
        state_index = repository_root / ".project" / "state-index.json"
        if not state_index.is_file():
            raise ConfigurationError(
                "AZURE_MCP_REPOSITORY_ROOT must contain .project/state-index.json"
            )

        for denied in (
            "AZURE_MCP_ALLOW_MUTATION",
            "AZURE_MCP_ALLOW_CROSS_SUBSCRIPTION",
            "AZURE_MCP_ALLOW_DEFAULT_SUBSCRIPTION",
        ):
            if source.get(denied, "").strip():
                raise ConfigurationError(f"{denied} is prohibited")

        return cls(
            subscription_id=subscription_id,
            resource_group=resource_group,
            repository_root=repository_root,
            command_timeout_seconds=_bounded_int(
                source,
                "AZURE_MCP_COMMAND_TIMEOUT_SECONDS",
                default=20,
                minimum=5,
                maximum=60,
            ),
            max_resources=_bounded_int(
                source,
                "AZURE_MCP_MAX_RESOURCES",
                default=200,
                minimum=1,
                maximum=500,
            ),
            max_cognitive_accounts=_bounded_int(
                source,
                "AZURE_MCP_MAX_COGNITIVE_ACCOUNTS",
                default=10,
                minimum=1,
                maximum=25,
            ),
        )
