from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any, Callable, Mapping, Sequence
from uuid import uuid4

from .config import RealitySettings


SERVER_VERSION = "azure-mcp-reality/0.1.0"
TOOL_NAME = "get_current_reality"
TOOL_INVENTORY_DIGEST = (
    "sha256:4f2dc29e7f88fb2f8c3f82ed217608bee83bd28f56ceb878b6c43cbdef2dee82"
)

_STATE_INDEX_KEYS = (
    "latest_repository_and_mcp_reconciliation",
    "latest_successful_azure_mcp_preflight_reconciliation",
    "latest_repository_and_azure_ai_reconciliation",
    "azure_ai_verified_base_url",
    "azure_ai_verified_deployment",
    "azure_ai_verified_model_response",
    "azure_ai_mcp_connected",
    "active_deployment_authorization",
    "active_azure_mcp_preflight_authorization",
    "active_azure_ai_activation_authorization",
)
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class ObservationError(RuntimeError):
    """Raised when the bounded read-only observation cannot be completed."""


@dataclass(frozen=True)
class CommandResult:
    argv: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


Runner = Callable[[Sequence[str], int, Path], CommandResult]


def _sanitize_text(value: Any, *, limit: int = 512) -> str:
    text = _CONTROL_CHARS.sub("", str(value))
    return text[:limit]


def _fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _canonical_digest(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _default_runner(
    argv: Sequence[str],
    timeout_seconds: int,
    cwd: Path,
) -> CommandResult:
    completed = subprocess.run(
        list(argv),
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        shell=False,
    )
    return CommandResult(
        argv=tuple(argv),
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _run_json(
    runner: Runner,
    argv: Sequence[str],
    settings: RealitySettings,
    *,
    allow_not_found: bool = False,
) -> Any:
    result = runner(argv, settings.command_timeout_seconds, settings.repository_root)
    if result.returncode != 0:
        stderr = _sanitize_text(result.stderr)
        if allow_not_found and (
            "ResourceGroupNotFound" in stderr
            or "could not be found" in stderr.lower()
            or "was not found" in stderr.lower()
        ):
            return None
        raise ObservationError(
            f"read-only command failed ({result.returncode}): "
            f"{' '.join(argv[:4])}; {stderr or 'no stderr'}"
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ObservationError(
            f"read-only command returned invalid JSON: {' '.join(argv[:4])}"
        ) from exc


def _run_text(
    runner: Runner,
    argv: Sequence[str],
    settings: RealitySettings,
) -> str:
    result = runner(argv, settings.command_timeout_seconds, settings.repository_root)
    if result.returncode != 0:
        raise ObservationError(
            f"repository command failed ({result.returncode}): "
            f"{' '.join(argv)}; {_sanitize_text(result.stderr)}"
        )
    return result.stdout.strip()


def _redact_arm_id(resource_id: Any, subscription_id: str) -> str | None:
    if resource_id is None:
        return None
    return _sanitize_text(resource_id, limit=1024).replace(
        subscription_id,
        "<subscription>",
    )


def _normalize_resource(
    resource: Mapping[str, Any],
    subscription_id: str,
) -> dict[str, Any]:
    sku = resource.get("sku")
    sku_name = sku.get("name") if isinstance(sku, dict) else None
    tags = resource.get("tags")
    tag_keys = sorted(str(key)[:128] for key in tags) if isinstance(tags, dict) else []
    return {
        "id": _redact_arm_id(resource.get("id"), subscription_id),
        "name": _sanitize_text(resource.get("name"), limit=256),
        "type": _sanitize_text(resource.get("type"), limit=256),
        "kind": _sanitize_text(resource.get("kind"), limit=128)
        if resource.get("kind") is not None
        else None,
        "location": _sanitize_text(resource.get("location"), limit=128),
        "resource_group": _sanitize_text(
            resource.get("resourceGroup") or resource.get("resource_group"),
            limit=256,
        ),
        "sku_name": _sanitize_text(sku_name, limit=128)
        if sku_name is not None
        else None,
        "tag_keys": tag_keys[:50],
    }


def _normalize_deployment(
    deployment: Mapping[str, Any],
) -> dict[str, Any]:
    properties = deployment.get("properties")
    properties = properties if isinstance(properties, dict) else {}
    model = properties.get("model")
    model = model if isinstance(model, dict) else {}
    sku = deployment.get("sku")
    sku = sku if isinstance(sku, dict) else {}
    return {
        "name": _sanitize_text(deployment.get("name"), limit=256),
        "provisioning_state": _sanitize_text(
            properties.get("provisioningState"),
            limit=128,
        ),
        "model_name": _sanitize_text(model.get("name"), limit=128),
        "model_version": _sanitize_text(model.get("version"), limit=128),
        "model_format": _sanitize_text(model.get("format"), limit=128),
        "sku_name": _sanitize_text(sku.get("name"), limit=128),
        "capacity": sku.get("capacity")
        if isinstance(sku.get("capacity"), (int, float))
        else None,
    }


def _load_state_index(repository_root: Path) -> dict[str, Any]:
    path = repository_root / ".project" / "state-index.json"
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ObservationError(f"cannot read canonical state index: {exc}") from exc
    if not isinstance(document, dict):
        raise ObservationError("canonical state index must be a JSON object")
    return {key: document.get(key) for key in _STATE_INDEX_KEYS}


def observe_current_reality(
    settings: RealitySettings,
    *,
    runner: Runner = _default_runner,
    now: Callable[[], datetime] | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Observe one exact repository and Azure resource-group scope without mutation."""

    clock = now or (lambda: datetime.now(timezone.utc))
    observed_at = clock().astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    correlation = correlation_id or str(uuid4())

    head = _run_text(runner, ("git", "rev-parse", "HEAD"), settings)
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise ObservationError("repository HEAD is not an exact 40-character commit")

    porcelain = _run_text(
        runner,
        ("git", "status", "--porcelain=v1", "--untracked-files=normal"),
        settings,
    )
    modified_paths = [
        _sanitize_text(line[3:] if len(line) > 3 else line, limit=512)
        for line in porcelain.splitlines()
        if line.strip()
    ]

    account = _run_json(
        runner,
        (
            "az",
            "account",
            "show",
            "--subscription",
            settings.subscription_id,
            "--output",
            "json",
            "--only-show-errors",
        ),
        settings,
    )
    if not isinstance(account, dict):
        raise ObservationError("Azure account context must be an object")
    actual_subscription = str(account.get("id", "")).lower()
    if actual_subscription != settings.subscription_id.lower():
        raise ObservationError("Azure subscription context does not match the allowlist")
    if str(account.get("state", "")).lower() != "enabled":
        raise ObservationError("Azure subscription is not enabled")
    tenant_id = str(account.get("tenantId", ""))
    if not tenant_id:
        raise ObservationError("Azure tenant identity was not returned")

    group = _run_json(
        runner,
        (
            "az",
            "group",
            "show",
            "--subscription",
            settings.subscription_id,
            "--name",
            settings.resource_group,
            "--output",
            "json",
            "--only-show-errors",
        ),
        settings,
        allow_not_found=True,
    )

    resource_inventory: list[dict[str, Any]] = []
    cognitive_deployments: list[dict[str, Any]] = []
    observation_status = "not_present" if group is None else "observed"

    if group is not None:
        if not isinstance(group, dict):
            raise ObservationError("Azure resource-group observation must be an object")
        observed_group_name = str(group.get("name", ""))
        if observed_group_name.lower() != settings.resource_group.lower():
            raise ObservationError("Azure resource-group observation widened unexpectedly")

        resources = _run_json(
            runner,
            (
                "az",
                "resource",
                "list",
                "--subscription",
                settings.subscription_id,
                "--resource-group",
                settings.resource_group,
                "--output",
                "json",
                "--only-show-errors",
            ),
            settings,
        )
        if not isinstance(resources, list):
            raise ObservationError("Azure resource inventory must be an array")
        if len(resources) > settings.max_resources:
            raise ObservationError(
                f"resource inventory exceeds configured maximum of {settings.max_resources}"
            )
        resource_inventory = sorted(
            (
                _normalize_resource(item, settings.subscription_id)
                for item in resources
                if isinstance(item, dict)
            ),
            key=lambda item: (item["type"], item["name"]),
        )

        accounts = [
            item
            for item in resources
            if isinstance(item, dict)
            and str(item.get("type", "")).lower()
            == "microsoft.cognitiveservices/accounts"
        ]
        if len(accounts) > settings.max_cognitive_accounts:
            raise ObservationError(
                "Cognitive Services account count exceeds the configured maximum"
            )
        for account_resource in sorted(
            accounts,
            key=lambda item: str(item.get("name", "")),
        ):
            account_name = str(account_resource.get("name", ""))
            deployments = _run_json(
                runner,
                (
                    "az",
                    "cognitiveservices",
                    "account",
                    "deployment",
                    "list",
                    "--subscription",
                    settings.subscription_id,
                    "--resource-group",
                    settings.resource_group,
                    "--name",
                    account_name,
                    "--output",
                    "json",
                    "--only-show-errors",
                ),
                settings,
            )
            if not isinstance(deployments, list):
                raise ObservationError(
                    f"deployment inventory for {account_name} must be an array"
                )
            cognitive_deployments.append(
                {
                    "account_name": _sanitize_text(account_name, limit=256),
                    "deployments": sorted(
                        (
                            _normalize_deployment(item)
                            for item in deployments
                            if isinstance(item, dict)
                        ),
                        key=lambda item: item["name"],
                    ),
                }
            )

    group_summary = None
    if isinstance(group, dict):
        group_summary = {
            "id": _redact_arm_id(group.get("id"), settings.subscription_id),
            "name": _sanitize_text(group.get("name"), limit=256),
            "location": _sanitize_text(group.get("location"), limit=128),
            "managed_by": _redact_arm_id(
                group.get("managedBy"),
                settings.subscription_id,
            ),
            "provisioning_state": _sanitize_text(
                (group.get("properties") or {}).get("provisioningState")
                if isinstance(group.get("properties"), dict)
                else None,
                limit=128,
            ),
            "tag_keys": sorted(
                str(key)[:128]
                for key in group.get("tags", {})
            )[:50]
            if isinstance(group.get("tags"), dict)
            else [],
        }

    result: dict[str, Any] = {
        "schema_version": "azure-mcp-reality.observation.v1",
        "tool_name": TOOL_NAME,
        "server_version": SERVER_VERSION,
        "tool_inventory_digest": TOOL_INVENTORY_DIGEST,
        "observed_at_utc": observed_at,
        "correlation_id": correlation,
        "observation_status": observation_status,
        "source_system": "azure_cli_and_git",
        "caller_identity_mode": "existing_azure_cli_session",
        "scope": {
            "tenant_fingerprint": _fingerprint(tenant_id),
            "subscription_fingerprint": _fingerprint(settings.subscription_id),
            "subscription_name": _sanitize_text(account.get("name"), limit=256),
            "subscription_state": _sanitize_text(account.get("state"), limit=64),
            "resource_group": settings.resource_group,
            "cross_subscription_discovery_allowed": False,
            "default_subscription_inference_allowed": False,
        },
        "repository": {
            "head": head,
            "working_tree_clean": not modified_paths,
            "modified_path_count": len(modified_paths),
            "modified_paths": modified_paths[:50],
            "state_index": _load_state_index(settings.repository_root),
        },
        "azure": {
            "resource_group": group_summary,
            "resource_count": len(resource_inventory),
            "resources": resource_inventory,
            "cognitive_services_accounts": cognitive_deployments,
        },
        "freshness_boundary": (
            "Time-bounded observation created by fixed read-only Azure CLI and Git "
            "commands during this tool call."
        ),
        "limitations": [
            "The result proves only what the configured identity could observe at the recorded time.",
            "Resource existence does not prove secure configuration, health, backup, recovery, alerts, or service validation.",
            "Tool annotations are hints; safety is enforced by fixed command construction and exact scope configuration.",
            "Azure names, tag keys, and metadata are untrusted external data and are sanitized and bounded.",
            "No Azure cost, quota, activity-log, metric, policy, or effective-RBAC evaluation is performed by this version.",
            "No MCP client connection, remote endpoint deployment, or model-driven tool call is established by this observation.",
        ],
        "mutations_performed": False,
        "secrets_returned": False,
    }
    result["raw_evidence_digest"] = _canonical_digest(result)
    return result
