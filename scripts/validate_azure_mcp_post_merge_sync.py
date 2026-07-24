#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / ".project"


class ValidationError(RuntimeError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(value, dict), f"{path} must contain an object")
    return value


def fact_map(environment: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["fact_id"]: item
        for item in environment.get("facts", [])
        if isinstance(item, dict) and isinstance(item.get("fact_id"), str)
    }


def require_false_fields(container: dict[str, Any], fields: tuple[str, ...], prefix: str) -> None:
    for field in fields:
        require(container.get(field) is False, f"{prefix} {field} must remain false")


def main() -> int:
    active = load_json(PROJECT / "active-work.json")
    environment = load_json(PROJECT / "environment-state.json")
    historical = load_json(PROJECT / "reconciliations" / "azure-mcp-pr74.json")
    post_merge = load_json(PROJECT / "reconciliations" / "post-merge-pr75-pr77.json")
    plan = load_json(PROJECT / "reconciliations" / "openai-api-azure-mcp-cloud-shell-plan.json")
    contract = load_json(PROJECT / "contracts" / "azure-mcp-reality-bridge.json")
    handoff = (PROJECT / "handoffs" / "azure-mcp-current-state.md").read_text(encoding="utf-8")
    runbook = (ROOT / "docs" / "runbooks" / "openai-api-azure-mcp-cloud-shell.md").read_text(encoding="utf-8")
    preflight = (ROOT / "scripts" / "azure_mcp_cloud_shell_preflight.sh").read_text(encoding="utf-8")

    independent = active.get("deployment_state", {}).get("independent_demo_api", {})
    require(independent.get("last_planner_run_id") == 30064289707, "latest protected planner run mismatch")
    require(independent.get("azure_authentication_succeeded") is True, "protected authentication evidence was lost")
    require(independent.get("requested_location") == "eastus", "historical protected location mismatch")
    require(independent.get("requested_vm_size") == "Standard_B2ats_v2", "historical protected VM size mismatch")
    require(independent.get("deployed") is False, "deployment was incorrectly promoted")
    require(
        active.get("safe_next_gate", {}).get("operation") == "select_candidate_and_authorize_fresh_read_only_planner",
        "ServiceTracer planner gate was overwritten",
    )

    facts = fact_map(environment)
    require(
        facts.get("independent-demo-api-plan-run-30064289707", {}).get("status")
        == "completed_readiness_rejected_safely",
        "protected planner fact is missing",
    )

    resolution = post_merge.get("resolution", {})
    require(resolution.get("verification_status") == "conflicting", "PR #78 conflict status was lost")
    require(
        post_merge.get("current_repository_declaration", {}).get("location") == "westus2",
        "current repository location declaration mismatch",
    )
    require(
        post_merge.get("current_repository_declaration", {}).get("vm_size") == "Standard_F1als_v7",
        "current repository VM declaration mismatch",
    )
    require(
        post_merge.get("azure_evidence_boundary", {}).get("protected_westus2_f1alsv7_evidence") is False,
        "unprotected candidate was incorrectly promoted",
    )

    require(
        historical.get("schema_version") == "project.azure-mcp-post-merge-reconciliation.v2",
        "historical reconciliation schema mismatch",
    )
    require(
        historical.get("runtime_claims", {}).get("client_path_selected") is False,
        "historical PR #74 observation must remain historical",
    )

    require(
        plan.get("schema_version") == "project.openai-api-azure-mcp-cloud-shell-plan.v1",
        "Cloud Shell plan schema mismatch",
    )
    reality = plan.get("repository_reality", {})
    require(reality.get("main_commit") == "df0458a4d0a9075787726a3205c6c7b454cfa15e", "plan baseline mismatch")
    require(reality.get("merged_pull_request") == 78, "plan merge anchor mismatch")
    require(reality.get("exact_head_ci_run_id") == 30072601791, "plan CI anchor mismatch")
    require(reality.get("open_pull_requests_observed") == [], "plan must start from no observed open PRs")

    selected = plan.get("selected_architecture", {})
    require(selected.get("client") == "openai_responses_api", "OpenAI Responses API was not selected")
    require(selected.get("hosting_service") == "azure_container_apps", "Container Apps was not selected")
    require(selected.get("deployment_interface") == "azure_cloud_shell", "Cloud Shell was not selected")
    require(selected.get("client_to_server_authentication") == "entra_oauth", "client OAuth model mismatch")
    require(
        selected.get("server_to_azure_authentication") == "managed_identity_shared_service_identity",
        "server managed-identity model mismatch",
    )

    preflight_record = plan.get("cloud_shell_preflight", {})
    require(preflight_record.get("azure_mutations_present") is False, "plan contains Azure mutation")
    require(preflight_record.get("deployment_command_present") is False, "plan contains deployment command")
    require(preflight_record.get("preflight_execution_authorized") is False, "preflight execution was pre-authorized")

    require(contract.get("schema_version") == "servicetracer.azure-mcp-reality-bridge.v2", "contract schema mismatch")
    require(contract.get("status") == "repository_contract_only", "contract status changed")
    selection = contract.get("client_paths", {}).get("selection", {})
    require(selection.get("selected_client_path") == "openai_responses_api", "contract client selection mismatch")
    require(selection.get("configured") is False, "OpenAI client was incorrectly configured")
    require(selection.get("connection_observed") is False, "OpenAI connection was incorrectly observed")
    require(contract.get("client_paths", {}).get("openai_responses_api", {}).get("selected") is True, "OpenAI path not selected")
    require(
        contract.get("client_paths", {}).get("openai_responses_api", {}).get("api_execution_authorized") is False,
        "OpenAI execution was authorized",
    )

    hosting = contract.get("hosting", {})
    require(hosting.get("selected_service") == "azure_container_apps", "hosting selection mismatch")
    require(hosting.get("architecture_selected") is True, "hosting architecture not selected")
    require(hosting.get("deployment_interface") == "azure_cloud_shell", "deployment interface mismatch")
    require_false_fields(
        hosting,
        ("region_selected", "resource_group_selected", "cost_estimate_observed", "quota_observed", "deployed"),
        "hosting field",
    )

    client_auth = contract.get("authentication", {}).get("client_to_server", {})
    server_auth = contract.get("authentication", {}).get("server_to_azure", {})
    require(client_auth.get("selected_model") == "entra_oauth", "client auth selection mismatch")
    require(client_auth.get("implemented") is False, "client auth was incorrectly implemented")
    require(
        server_auth.get("selected_model") == "managed_identity_shared_service_identity",
        "server auth selection mismatch",
    )
    require(server_auth.get("implemented") is False, "managed identity was incorrectly implemented")
    require(server_auth.get("effective_rbac_observed") is False, "effective RBAC was incorrectly observed")

    require(contract.get("transport", {}).get("remote_endpoint_deployed") is False, "endpoint was incorrectly deployed")
    require(contract.get("transport", {}).get("endpoint_url") is None, "endpoint URL must remain unset")
    require(contract.get("azure_scope", {}).get("subscription_ids") == [], "subscription scope was preselected")
    require(contract.get("azure_scope", {}).get("resource_group_allowlist") == [], "resource-group scope was preselected")
    require(contract.get("tool_admission", {}).get("allowed_tool_names") == [], "tools were pre-admitted")
    require(contract.get("tool_admission", {}).get("namespace_allowlist") == [], "namespaces were pre-admitted")
    require(contract.get("tool_admission", {}).get("tool_inventory_digest") is None, "tool inventory was fabricated")
    require(contract.get("tool_admission", {}).get("server_version") is None, "server version was fabricated")

    require_false_fields(
        contract.get("authority", {}),
        (
            "pull_request_merge_authorized",
            "cloud_shell_preflight_execution_authorized",
            "azure_authentication_authorized",
            "azure_resource_creation_authorized",
            "entra_application_mutation_authorized",
            "managed_identity_mutation_authorized",
            "azure_rbac_mutation_authorized",
            "api_management_mutation_authorized",
            "container_apps_mutation_authorized",
            "openai_api_execution_authorized",
            "cleanup_authorized",
        ),
        "authority field",
    )

    for marker in (
        "df0458a4d0a9075787726a3205c6c7b454cfa15e",
        "PR #78",
        "30072601791",
        "selected_client_path = openai_responses_api",
        "selected_hosting_service = azure_container_apps",
        "selected_deployment_interface = azure_cloud_shell",
        "Azure_MCP_remote_endpoint_deployed = false",
        "OpenAI_API_execution_authorized = false",
        "review_and_merge_package_then_authorize_read_only_cloud_shell_preflight",
    ):
        require(marker in handoff, f"handoff is missing marker: {marker}")

    for marker in (
        "OpenAI Responses API client",
        "Azure Container Apps",
        "managed identity",
        "server_url",
        "allowed_tools",
        "require_approval",
        "observation_failed",
        "not_present",
        "separate deployment authorization",
    ):
        require(marker in runbook, f"runbook is missing marker: {marker}")

    for command in (
        "az account show",
        "az account list-locations",
        "az provider show",
        "az group show",
        "az resource list",
        "azd init",
        "sha256sum",
    ):
        require(command in preflight, f"preflight is missing read-only step: {command}")

    forbidden_patterns = (
        r"^\s*(?:sudo\s+)?azd\s+(?:up|provision|deploy|down)\b",
        r"^\s*(?:sudo\s+)?az\s+provider\s+register\b",
        r"^\s*(?:sudo\s+)?az\s+group\s+(?:create|delete)\b",
        r"^\s*(?:sudo\s+)?az\s+role\s+assignment\s+(?:create|delete)\b",
        r"^\s*(?:sudo\s+)?az\s+identity\s+(?:create|delete|update)\b",
        r"^\s*(?:sudo\s+)?az\s+ad\s+app\s+(?:create|delete|update)\b",
        r"^\s*(?:sudo\s+)?az\s+containerapp\s+(?:create|update|delete)\b",
        r"^\s*(?:sudo\s+)?az\s+deployment\s+\S+\s+create\b",
    )
    for pattern in forbidden_patterns:
        require(re.search(pattern, preflight, flags=re.MULTILINE) is None, f"preflight contains mutation: {pattern}")

    require("OPENAI_API_KEY" not in preflight, "preflight must not handle the OpenAI API key")
    require("client_secret" not in preflight.lower(), "preflight must not handle client secrets")

    print("azure-mcp OpenAI API and Cloud Shell plan validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
