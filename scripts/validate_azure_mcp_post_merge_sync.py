#!/usr/bin/env python3
from __future__ import annotations

import json
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


def main() -> int:
    active = load_json(PROJECT / "active-work.json")
    environment = load_json(PROJECT / "environment-state.json")
    reconciliation = load_json(PROJECT / "reconciliations" / "azure-mcp-pr74.json")
    contract = load_json(PROJECT / "contracts" / "azure-mcp-reality-bridge.json")
    handoff = (PROJECT / "handoffs" / "azure-mcp-current-state.md").read_text(encoding="utf-8")

    # Preserve the newer PR #76 project reality instead of reviving PR #77's stale state.
    architecture = active.get("architecture_baseline", {})
    require(
        architecture.get("authorization_status") == "ratified_for_bounded_read_only_planning",
        "PR #76 planner authorization state was regressed",
    )

    independent = active.get("deployment_state", {}).get("independent_demo_api", {})
    require(independent.get("last_planner_run_id") == 30064289707, "latest planner run mismatch")
    require(independent.get("azure_authentication_succeeded") is True, "planner authentication evidence was lost")
    require(independent.get("requested_location") == "eastus", "planner location evidence mismatch")
    require(independent.get("requested_vm_size") == "Standard_B2ats_v2", "planner VM-size evidence mismatch")
    require(independent.get("requested_sku_unrestricted") is False, "blocked SKU was incorrectly promoted")
    require(
        independent.get("requested_sku_restriction_reason") == "NotAvailableForSubscription",
        "blocked SKU reason mismatch",
    )
    require(independent.get("target_resource_group_observed") is False, "target resource group was incorrectly observed")
    require(independent.get("arm_validation_performed") is False, "ARM validation was incorrectly promoted")
    require(independent.get("what_if_performed") is False, "What-If was incorrectly promoted")
    require(independent.get("plan_accepted") is False, "plan was incorrectly accepted")
    require(independent.get("deployed") is False, "deployment was incorrectly promoted")
    require(active.get("safe_next_gate", {}).get("operation") == "select_candidate_and_authorize_fresh_read_only_planner", "planner next gate mismatch")

    facts = fact_map(environment)
    require(
        facts.get("independent-demo-api-plan-run-30064289707", {}).get("status")
        == "completed_readiness_rejected_safely",
        "promoted planner run fact is missing or regressed",
    )
    require(
        facts.get("independent-demo-api-target-resource-group-state", {}).get("status") == "not_observed",
        "target resource-group state must remain not_observed",
    )

    require(
        reconciliation.get("schema_version") == "project.azure-mcp-post-merge-reconciliation.v2",
        "reconciliation schema mismatch",
    )
    baseline = reconciliation.get("integration_baseline", {})
    require(
        baseline.get("main_commit") == "551ca0ee2c7d1955b3bd81c09f46f43dceeae3a6",
        "integration baseline mismatch",
    )
    require(baseline.get("merged_pull_request") == 76, "integration PR mismatch")
    require(baseline.get("promoted_planner_run_id") == 30064289707, "reconciliation planner run mismatch")
    require(
        baseline.get("planner_artifact_sha256")
        == "7aae2cff0df757a4b436c5b87507162624813e64bd32946bada8a87e5d7adc22",
        "planner artifact digest mismatch",
    )

    integration = reconciliation.get("repository_integration", {})
    for field in ("active_work_modified", "environment_state_modified", "current_project_handoff_modified"):
        require(integration.get(field) is False, f"{field} must remain false")
    require(
        integration.get("dedicated_handoff") == ".project/handoffs/azure-mcp-current-state.md",
        "dedicated handoff path mismatch",
    )

    runtime = reconciliation.get("runtime_claims", {})
    for field in (
        "remote_endpoint_deployed",
        "client_path_selected",
        "client_connected",
        "authentication_model_selected",
        "azure_authentication_authorized",
        "azure_resources_created",
        "entra_identity_created_or_changed",
        "azure_rbac_changed",
        "tenant_scope_selected",
        "subscription_scope_selected",
        "resource_group_scope_selected",
        "server_version_observed",
        "tool_inventory_observed",
        "cost_observed",
        "quota_observed",
    ):
        require(runtime.get(field) is False, f"Azure MCP runtime field {field} must remain false")
    require(runtime.get("endpoint_url") is None, "Azure MCP endpoint URL must remain unset")
    require(runtime.get("tool_names_admitted") == [], "no MCP tool may be pre-admitted")
    require(runtime.get("azure_runtime_state") == "not_observed", "MCP runtime must remain not_observed")

    authority = reconciliation.get("authority", {})
    for field in (
        "pull_request_merge_authorized",
        "azure_authentication_authorized",
        "azure_resource_creation_authorized",
        "entra_identity_mutation_authorized",
        "azure_rbac_mutation_authorized",
        "azure_mcp_hosting_authorized",
        "client_configuration_authorized",
        "tool_admission_authorized",
        "openai_api_execution_authorized",
        "chatgpt_app_registration_authorized",
        "cleanup_authorized",
    ):
        require(authority.get(field) is False, f"authority field {field} must remain false")

    require(reconciliation.get("next_gate", {}).get("operation") == "select_and_verify_client_path", "MCP next gate mismatch")

    require(contract.get("status") == "repository_contract_only", "base Azure MCP contract status changed")
    require(contract.get("transport", {}).get("remote_endpoint_deployed") is False, "contract claims endpoint deployment")
    require(contract.get("transport", {}).get("endpoint_url") is None, "contract endpoint URL must remain unset")
    require(contract.get("tool_admission", {}).get("allowed_tool_names") == [], "contract must deny tools by default")
    require(contract.get("authority", {}).get("azure_authentication_authorized") is False, "contract authorizes authentication")

    for marker in (
        "551ca0ee2c7d1955b3bd81c09f46f43dceeae3a6",
        "PR #74",
        "PR #76",
        "30064289707",
        "select_and_verify_client_path",
        "remote_endpoint_deployed = false",
        "MCP_tool_admission_authorized = false",
    ):
        require(marker in handoff, f"Azure MCP handoff is missing marker: {marker}")

    print("azure-mcp post-merge reconciliation validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
