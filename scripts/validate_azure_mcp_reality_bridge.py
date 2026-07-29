#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SCHEMA = "servicetracer.azure-mcp-reality-bridge.v3"
STATUS = "local_read_only_tool_implemented_not_connected"
TOOL_NAME = "get_current_reality"
SERVER_VERSION = "azure-mcp-reality/0.1.0"
TOOL_DIGEST = "sha256:4f2dc29e7f88fb2f8c3f82ed217608bee83bd28f56ceb878b6c43cbdef2dee82"
OBSERVATION_STATES = {
    "observed",
    "not_present",
    "not_observed",
    "observation_failed",
    "conflicting",
}
FIXED_COMMANDS = [
    "git rev-parse HEAD",
    "git status --porcelain=v1",
    "az account show",
    "az group show",
    "az resource list",
    "az cognitiveservices account deployment list",
]
DENIED_CAPABILITIES = {
    "create_resource",
    "update_resource",
    "delete_resource",
    "deploy_template",
    "assign_role",
    "remove_role",
    "register_provider",
    "read_secret_value",
    "write_secret_value",
    "execute_guest_command",
    "open_network_access",
    "change_policy",
    "change_quota",
    "arbitrary_azure_cli_command",
    "model_selected_subscription",
    "model_selected_resource_group",
}
FALSE_AUTHORITY_FIELDS = {
    "local_read_only_tool_execution_authorized",
    "azure_authentication_or_query_performed_by_this_increment",
    "remote_mcp_endpoint_deployment_authorized",
    "chatgpt_app_registration_authorized",
    "azure_openai_mcp_model_call_authorized",
    "azure_resource_creation_authorized",
    "entra_application_mutation_authorized",
    "managed_identity_mutation_authorized",
    "azure_rbac_mutation_authorized",
    "api_management_mutation_authorized",
    "container_apps_mutation_authorized",
    "cleanup_authorized",
}


class ContractError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def object_field(value: Any, field: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{field} must be an object")
    return value


def list_field(value: Any, field: str, *, allow_empty: bool = False) -> list[Any]:
    require(isinstance(value, list), f"{field} must be an array")
    require(allow_empty or bool(value), f"{field} must not be empty")
    return value


def text_field(value: Any, field: str) -> str:
    require(isinstance(value, str) and bool(value.strip()), f"{field} must be text")
    return value.strip()


def require_false(container: dict[str, Any], fields: set[str], prefix: str) -> None:
    for field in fields:
        require(container.get(field) is False, f"{prefix}.{field} must remain false")


def validate_contract(document: dict[str, Any]) -> None:
    require(document.get("schema_version") == SCHEMA, "unexpected schema_version")
    require(document.get("status") == STATUS, "unexpected contract status")
    text_field(document.get("objective"), "objective")

    distinctions = set(list_field(document.get("canonical_distinctions"), "canonical_distinctions"))
    for marker in (
        "tool_implemented != tool_called",
        "tool_called_locally != remote_mcp_endpoint_deployed",
        "model_inference_verified != mcp_tool_call_verified",
        "tool_advertised != tool_authorized",
        "read_only_annotation != effective_least_privilege",
        "not_observed != absent",
    ):
        require(marker in distinctions, f"missing canonical distinction: {marker}")

    baseline = object_field(document.get("repository_baseline"), "repository_baseline")
    require(baseline.get("base_branch") == "main", "base branch must be main")
    require(baseline.get("base_commit") == "b2fdf35a1e11803209e7764e047f5112596005b9", "base commit mismatch")
    require(baseline.get("latest_merged_pull_request") == 208, "latest PR mismatch")
    require(list_field(baseline.get("open_pull_requests_observed_before_branch"), "open PRs", allow_empty=True) == [], "open PR baseline changed")

    transport = object_field(document.get("transport"), "transport")
    require(transport.get("local_stdio_implemented") is True, "stdio must be implemented")
    require(transport.get("local_streamable_http_implemented") is True, "local HTTP must be implemented")
    require(transport.get("local_http_bind") == "127.0.0.1:8000", "local bind must remain loopback")
    require(transport.get("local_http_path") == "/mcp", "local MCP path mismatch")
    require(transport.get("remote_required") == "streamable_http", "remote transport mismatch")
    require(transport.get("remote_tls_required") is True, "remote TLS must be required")
    require(transport.get("remote_endpoint_deployed") is False, "remote endpoint must remain undeployed")
    require(transport.get("remote_endpoint_url") is None, "remote endpoint URL must remain unset")
    require(transport.get("anonymous_remote_access_allowed") is False, "anonymous remote access prohibited")

    hosting = object_field(document.get("hosting"), "hosting")
    require(hosting.get("selected_service") == "azure_container_apps", "hosting selection changed")
    require(hosting.get("deployed") is False, "hosting must remain undeployed")
    for field in ("template_source_commit", "template_inventory_digest", "container_image_version"):
        require(hosting.get(field) is None, f"hosting.{field} must remain unset")
    for field in ("region_selected", "resource_group_selected", "cost_estimate_observed", "quota_observed"):
        require(hosting.get(field) is False, f"hosting.{field} must remain false")

    clients = object_field(document.get("client_paths"), "client_paths")
    azure_openai = object_field(clients.get("azure_openai_responses_api"), "client_paths.azure_openai_responses_api")
    require(azure_openai.get("selected_for_model_inference") is True, "Azure OpenAI inference selection missing")
    require(azure_openai.get("entra_inference_verified") is True, "verified inference evidence missing")
    require(azure_openai.get("mcp_server_configured") is False, "MCP server must remain unconfigured")
    require(azure_openai.get("mcp_tool_call_verified") is False, "MCP call must remain unverified")
    require(clients["chatgpt_custom_app"].get("configured") is False, "ChatGPT app must remain unconfigured")
    require(clients["ide_mcp_clients"].get("configured") is False, "IDE MCP client must remain unconfigured")

    auth = object_field(document.get("authentication"), "authentication")
    local_auth = object_field(auth.get("local_tool_to_azure"), "authentication.local_tool_to_azure")
    require(local_auth.get("mode") == "existing_azure_cli_session", "local auth mode changed")
    require(local_auth.get("implemented_in_code") is True, "local auth code not recorded")
    require(local_auth.get("live_execution_observed") is False, "live execution must remain unobserved")
    require(local_auth.get("raw_tenant_or_subscription_ids_persisted") is False, "raw identity persistence prohibited")
    for section in ("remote_client_to_server", "remote_server_to_azure"):
        require(auth[section].get("implemented") is False, f"{section} must remain unimplemented")
    require(auth.get("static_long_lived_secret_allowed") is False, "long-lived secrets prohibited")

    scope = object_field(document.get("azure_scope"), "azure_scope")
    require(scope.get("runtime_subscription_environment_variable") == "AZURE_MCP_ALLOWED_SUBSCRIPTION_ID", "subscription scope source changed")
    require(scope.get("runtime_resource_group_environment_variable") == "AZURE_MCP_ALLOWED_RESOURCE_GROUP", "resource-group scope source changed")
    for field in ("subscription_id_persisted", "tenant_id_persisted", "resource_group_persisted", "cross_subscription_discovery_allowed", "default_subscription_inference_allowed", "model_supplied_scope_parameters_allowed"):
        require(scope.get(field) is False, f"azure_scope.{field} must remain false")

    admission = object_field(document.get("tool_admission"), "tool_admission")
    require(admission.get("default_policy") == "deny", "tool policy must default deny")
    require(admission.get("server_mode") == "local_observer_only", "server mode changed")
    require(list_field(admission.get("allowed_tool_names"), "allowed_tool_names") == [TOOL_NAME], "exactly one tool must be admitted")
    require(admission.get("server_version") == SERVER_VERSION, "server version mismatch")
    require(admission.get("tool_inventory_digest") == TOOL_DIGEST, "tool digest mismatch")
    tool = object_field(admission.get("tool"), "tool")
    require(tool.get("name") == TOOL_NAME, "tool name mismatch")
    require(tool.get("version") == "0.1.0", "tool version mismatch")
    require(list_field(tool.get("model_inputs"), "tool.model_inputs", allow_empty=True) == [], "model inputs prohibited")
    require(tool.get("annotations") == {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True}, "tool annotations changed")
    require(tool.get("fixed_read_only_commands") == FIXED_COMMANDS, "fixed command inventory changed")
    for field in ("returns_secret_values", "writes_files", "performs_azure_mutation"):
        require(tool.get(field) is False, f"tool.{field} must remain false")
    denied = set(list_field(admission.get("denied_capabilities"), "denied_capabilities"))
    require(DENIED_CAPABILITIES.issubset(denied), "denied capability set incomplete")

    implementation = object_field(document.get("implementation"), "implementation")
    require(implementation.get("package") == "azure_mcp_reality", "package path mismatch")
    require(implementation.get("mcp_sdk") == "mcp[cli]==1.24.0", "MCP SDK pin changed")
    for field in ("config", "observer", "server", "cli", "requirements", "runbook", "test"):
        text_field(implementation.get(field), f"implementation.{field}")

    evidence = object_field(document.get("evidence_contract"), "evidence_contract")
    require(set(list_field(evidence.get("observation_status_values"), "observation states")) == OBSERVATION_STATES, "observation states changed")
    required_fields = set(list_field(evidence.get("required_result_fields"), "required result fields"))
    for field in ("observed_at_utc", "correlation_id", "observation_status", "scope", "repository", "azure", "mutations_performed", "secrets_returned", "raw_evidence_digest"):
        require(field in required_fields, f"missing evidence field: {field}")
    for field in ("subscription_and_tenant_fingerprinted", "arm_subscription_segment_redacted", "secret_redaction_required"):
        require(evidence.get(field) is True, f"evidence_contract.{field} must be true")
    require(evidence.get("tag_values_returned") is False, "tag values must not be returned")
    require(evidence.get("raw_protected_payload_commit_allowed") is False, "protected payload commits prohibited")

    authority = object_field(document.get("authority"), "authority")
    for field in ("repository_branch_and_files_authorized", "pull_request_creation_authorized", "ordinary_exact_head_ci_authorized", "pull_request_merge_authorized"):
        require(authority.get(field) is True, f"authority.{field} must be true")
    require_false(authority, FALSE_AUTHORITY_FIELDS, "authority")

    cost = object_field(document.get("cost_and_quota"), "cost_and_quota")
    require(cost.get("expected_recurring_azure_resource_cost_delta_cad") == 0, "repository recurring cost must be CAD $0")
    require(cost.get("actual_azure_cost_freshly_observed") is False, "actual cost must remain unobserved")
    require(cost.get("azure_quota_freshly_observed") is False, "quota must remain unobserved")

    failure = object_field(document.get("failure_and_rollback"), "failure_and_rollback")
    fail_closed = set(list_field(failure.get("fail_closed_conditions"), "fail closed conditions"))
    for marker in ("missing_explicit_subscription", "default_subscription_inference_attempted", "subscription_context_mismatch", "tool_inventory_changed", "write_or_secret_capability_detected", "evidence_digest_missing"):
        require(marker in fail_closed, f"missing fail-closed marker: {marker}")
    require(failure.get("cleanup_authorized") is False, "cleanup must remain unauthorized")


def load_and_validate(path: Path) -> None:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError(f"missing contract: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(f"invalid JSON: {exc}") from exc
    validate_contract(object_field(document, str(path)))


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
