#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / ".project/evidence/servicetracer-demo-api-post-deployment-inventory-20260724T163938Z.json"
HANDOFF = ROOT / ".project/handoffs/servicetracer-demo-api-post-deployment-current-state.md"
FOLLOW_UP = ROOT / ".project/reconciliations/servicetracer-demo-api-post-deployment-follow-up.json"
RUNNER = ROOT / "scripts/servicetracer_demo_api_readonly_follow_up.py"
RUNBOOK = ROOT / "docs/runbooks/servicetracer-demo-api-post-deployment-inventory.md"

EXPECTED_ARCHIVE_SHA = "95512590ba39a6ef68a78ececf525268af49ba18f2f5d9a582adff4aff85fca0"
EXPECTED_MAIN = "e20ef494fe93806085d2b983cde2c58a504ab217"
EXPECTED_DEPLOYED = "8b3d55c616d8820edd523f77021a35fe24167bd0"
EXPECTED_MANIFEST_COUNT = 21

FORBIDDEN_RUNNER_FRAGMENTS = (
    '"group", "create"',
    '"deployment", "group", "create"',
    '"provider", "register"',
    '"role", "assignment", "create"',
    '"role", "assignment", "delete"',
    '"vm", "run-command"',
    '"vm", "restart"',
    '"resource", "delete"',
    '"group", "delete"',
    '"extension", "add"',
)


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path} must contain a JSON object")
    return value


def validate() -> None:
    for path in (EVIDENCE, HANDOFF, FOLLOW_UP, RUNNER, RUNBOOK):
        assert path.is_file(), f"missing required path: {path}"

    evidence = load_json(EVIDENCE)
    follow_up = load_json(FOLLOW_UP)
    handoff = HANDOFF.read_text(encoding="utf-8")
    runner = RUNNER.read_text(encoding="utf-8")
    runbook = RUNBOOK.read_text(encoding="utf-8")

    assert evidence["schema_version"] == "project.servicetracer-demo-api-post-deployment-inventory.v1"
    source = evidence["evidence_source"]
    assert source["archive_sha256"] == EXPECTED_ARCHIVE_SHA
    assert source["manifest_entry_count"] == EXPECTED_MANIFEST_COUNT
    assert source["manifest_hashes_verified"] is True
    assert len(source["manifest_entries"]) == EXPECTED_MANIFEST_COUNT
    assert source["raw_archive_committed"] is False
    assert source["capture_channel"] == "operator_authenticated_azure_cloud_shell"

    repository = evidence["repository_reconciliation"]
    assert repository["repository_main_at_promotion_start"] == EXPECTED_MAIN
    assert repository["deployed_source_ref"] == EXPECTED_DEPLOYED
    comparison = repository["deployed_source_vs_main"]
    assert comparison["ahead_by_commits"] == 9
    assert comparison["behind_by_commits"] == 0
    assert comparison["workload_source_or_iac_path_changed"] is False

    azure = evidence["azure_context"]
    assert azure["subscription_name"] == "Azure subscription 1"
    assert azure["raw_subscription_or_tenant_identifiers_persisted"] is False

    provenance = evidence["deployment_provenance"]
    assert provenance["resource_group"]["name"] == "rg-st-demo-api-dev-westus2"
    assert provenance["resource_group"]["location"] == "westus2"
    assert provenance["resource_count"] == 7
    deployment = provenance["deployment_record"]
    assert deployment["status"] == "observed"
    assert deployment["provisioning_state"] == "Succeeded"
    assert deployment["source_ref"] == EXPECTED_DEPLOYED

    runtime = evidence["runtime_control_plane"]
    assert runtime["vm"]["size"] == "Standard_F1als_v7"
    assert runtime["vm"]["power_state"] == "VM running"
    assert runtime["vm"]["provisioning_state"] == "Succeeded"
    assert runtime["vm"]["identity_type"] == "SystemAssigned"
    assert runtime["public_ip"]["fqdn_matches_expected"] is True
    assert runtime["extension"]["provisioning_state"] == "Succeeded"

    ops = evidence["security_and_operations"]
    assert ops["diagnostic_settings"]["supported_resources_observed"] == 6
    assert ops["diagnostic_settings"]["supported_resources_with_zero_settings"] == 6
    assert ops["monitoring"]["metric_alert_count"] == 0
    assert ops["monitoring"]["action_group_count"] == 0
    assert ops["monitoring"]["alert_delivery_verified"] is False
    assert ops["resource_group_locks"]["count"] == 0
    assert ops["rbac"]["state"] == "not_observed"
    assert ops["backup"]["state"] == "not_observed"
    assert ops["cost"]["state"] == "not_observed"

    combined = evidence["combined_verification"]
    assert combined["deployment_provenance_verified"] is True
    assert combined["public_endpoint_identity_verified"] is True
    assert combined["backend_transaction_success_verified"] is False
    assert combined["effective_rbac_observed"] is False
    assert combined["recovery_tested"] is False
    assert combined["actual_cost_observed"] is False

    authority = evidence["mutation_and_authority"]
    assert authority["azure_mutations_performed"] is False
    assert authority["guest_commands_performed"] is False
    assert authority["transaction_replay_performed"] is False
    assert authority["pull_request_merge_authorized"] is False
    assert authority["corrected_follow_up_execution_authorized"] is False

    assert follow_up["status"] == "repository_plan_only"
    assert follow_up["execution_boundary"]["execution_authorized"] is False
    assert follow_up["execution_boundary"]["azure_mutations_authorized"] is False

    for fragment in FORBIDDEN_RUNNER_FRAGMENTS:
        assert fragment not in runner, f"forbidden runner fragment: {fragment}"

    cost_segment = runner[runner.index("def collect_cost"):runner.index("def collect_backup")]
    assert '"Currency"' not in cost_segment
    assert '{"type": "Dimension", "name": "ResourceId"}' in cost_segment

    backup_segment = runner[runner.index("def collect_backup"):runner.index("def main")]
    assert '"resource", "list"' in backup_segment
    assert '"backup", "item", "list"' in backup_segment
    assert '"extension", "show"' not in backup_segment
    assert '"extension", "add"' not in backup_segment

    rbac_start = runner.index("def collect_rbac")
    rbac_end = runner.index("def collect_cost", rbac_start)
    rbac_segment = runner[rbac_start:rbac_end]
    assert '"--scope"' in rbac_segment
    assert '"--include-inherited"' in rbac_segment
    assert '"--all"' not in rbac_segment

    for distinction in (
        "resource_exists != securely_configured",
        "RBAC_assignment != effective_least_privilege",
        "backup_configured != recovery_tested",
        "not_observed != absent",
    ):
        assert distinction in handoff or distinction in runbook

    print("ServiceTracer post-deployment evidence validation passed.")


if __name__ == "__main__":
    validate()
