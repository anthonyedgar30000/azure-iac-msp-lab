#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SCHEMA = "servicetracer.azure-mcp-reality-bridge.v1"
FALSE_AUTHORITY_FIELDS = {
    "pull_request_merge_authorized",
    "azure_authentication_authorized",
    "azure_resource_creation_authorized",
    "entra_application_mutation_authorized",
    "managed_identity_mutation_authorized",
    "azure_rbac_mutation_authorized",
    "api_management_mutation_authorized",
    "container_apps_mutation_authorized",
    "chatgpt_app_registration_authorized",
    "openai_api_execution_authorized",
}
REQUIRED_DENIED_CAPABILITIES = {
    "create_resource",
    "update_resource",
    "delete_resource",
    "deploy_template",
    "assign_role",
    "remove_role",
    "read_secret_value",
    "write_secret_value",
    "execute_guest_command",
}
REQUIRED_OBSERVATION_STATES = {
    "observed",
    "not_present",
    "not_observed",
    "observation_failed",
    "conflicting",
}


class ContractError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def require_object(value: Any, field: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{field} must be an object")
    return value


def require_list(value: Any, field: str, *, allow_empty: bool = False) -> list[Any]:
    require(isinstance(value, list), f"{field} must be an array")
    require(allow_empty or bool(value), f"{field} must not be empty")
    return value


def require_text(value: Any, field: str) -> str:
    require(isinstance(value, str) and bool(value.strip()), f"{field} must be a non-empty string")
    return value.strip()


def validate_contract(document: dict[str, Any]) -> None:
    require(document.get("schema_version") == SCHEMA, "unexpected schema_version")
    require(document.get("status") == "repository_contract_only", "contract must remain repository-only")
    require_text(document.get("objective"), "objective")

    distinctions = set(require_list(document.get("canonical_distinctions"), "canonical_distinctions"))
    for marker in (
        "tool_advertised != tool_authorized",
        "read_only_annotation != effective_least_privilege",
        "not_observed != absent",
    ):
        require(marker in distinctions, f"missing canonical distinction: {marker}")

    transport = require_object(document.get("transport"), "transport")
    require(transport.get("required") == "streamable_http", "transport must be streamable_http")
    require(transport.get("endpoint_path") == "/mcp", "endpoint_path must be /mcp")
    require(transport.get("tls_required") is True, "TLS must be required")
    require(transport.get("remote_endpoint_deployed") is False, "endpoint must not be promoted as deployed")
    require(transport.get("endpoint_url") is None, "unverified endpoint URL must remain null")

    hosting = require_object(document.get("hosting"), "hosting")
    for field in (
        "architecture_selected",
        "region_selected",
        "resource_group_selected",
        "cost_estimate_observed",
        "quota_observed",
    ):
        require(hosting.get(field) is False, f"hosting.{field} must remain false")

    authentication = require_object(document.get("authentication"), "authentication")
    require(authentication.get("selected_model") is None, "authentication model is not yet selected")
    require(authentication.get("anonymous_access_allowed") is False, "anonymous access must be denied")
    require(authentication.get("static_long_lived_secret_allowed") is False, "long-lived static secrets must be denied")
    for field in (
        "client_identity_observed",
        "server_identity_observed",
        "federated_credentials_observed",
        "admin_consent_observed",
    ):
        require(authentication.get(field) is False, f"authentication.{field} must remain false")

    scope = require_object(document.get("azure_scope"), "azure_scope")
    require(scope.get("tenant_id") is None, "tenant_id must remain unset")
    require(require_list(scope.get("subscription_ids"), "azure_scope.subscription_ids", allow_empty=True) == [], "subscription_ids must remain empty")
    require(require_list(scope.get("resource_group_allowlist"), "azure_scope.resource_group_allowlist", allow_empty=True) == [], "resource-group allowlist must remain empty")
    require(scope.get("cross_subscription_discovery_allowed") is False, "cross-subscription discovery must be denied")
    require(scope.get("default_subscription_inference_allowed") is False, "default subscription inference must be denied")

    admission = require_object(document.get("tool_admission"), "tool_admission")
    require(admission.get("default_policy") == "deny", "tool admission must default deny")
    annotations = require_object(admission.get("required_annotations"), "tool_admission.required_annotations")
    require(annotations == {
        "read_only": True,
        "destructive": False,
        "secret": False,
        "local_required": False,
    }, "required tool annotations changed")
    require(require_list(admission.get("allowed_tool_names"), "tool_admission.allowed_tool_names", allow_empty=True) == [], "no tool may be pre-authorized")
    require(admission.get("tool_inventory_digest") is None, "tool inventory digest must remain unset")
    require(admission.get("server_version") is None, "server version must remain unset")
    denied = set(require_list(admission.get("denied_capabilities"), "tool_admission.denied_capabilities"))
    require(REQUIRED_DENIED_CAPABILITIES.issubset(denied), "denied capabilities are incomplete")
    require_text(admission.get("admission_rule"), "tool_admission.admission_rule")

    authority = require_object(document.get("authority"), "authority")
    require(authority.get("repository_design_authorized") is True, "repository design must be authorized")
    require(authority.get("pull_request_creation_authorized") is True, "pull-request creation must be authorized")
    for field in FALSE_AUTHORITY_FIELDS:
        require(authority.get(field) is False, f"authority.{field} must remain false")

    evidence = require_object(document.get("evidence_contract"), "evidence_contract")
    statuses = set(require_list(evidence.get("observation_status_values"), "evidence_contract.observation_status_values"))
    require(statuses == REQUIRED_OBSERVATION_STATES, "observation states changed")
    require(evidence.get("secret_redaction_required") is True, "secret redaction must be required")
    require(evidence.get("raw_protected_payload_commit_allowed") is False, "protected payload commits must be denied")

    rollback = require_object(document.get("failure_and_rollback"), "failure_and_rollback")
    require(rollback.get("cleanup_authorized") is False, "cleanup must remain unauthorized")
    require_text(rollback.get("rollback_action"), "failure_and_rollback.rollback_action")


def load_and_validate(path: Path) -> None:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError(f"missing contract: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(f"invalid JSON: {exc}") from exc
    validate_contract(require_object(document, str(path)))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "contract",
        nargs="?",
        type=Path,
        default=Path(".project/contracts/azure-mcp-reality-bridge.json"),
    )
    args = parser.parse_args()
    try:
        load_and_validate(args.contract)
    except (ContractError, OSError) as exc:
        print(f"azure-mcp reality-bridge contract validation failed: {exc}")
        return 1
    print("azure-mcp reality-bridge contract validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
