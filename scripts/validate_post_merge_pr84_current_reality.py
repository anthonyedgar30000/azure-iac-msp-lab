#!/usr/bin/env python3
"""Validate canonical project reality after PR #84 merged."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / ".project/current-reality.json"
HANDOFF = ROOT / ".project/handoffs/current-state.md"
RECONCILIATION = ROOT / ".project/reconciliations/post-merge-pr84-current-reality.json"
BLOCKED = ROOT / ".project/evidence/servicetracer-demo-api-timeout-fix-deployment-blocked-20260724.json"

MAIN = "c96d9cbb765a023921fa819cf7d99c957e8ad608"
SOURCE = "5c938a7e07da3a22b27bb5ac5aa52b7ccf22ba37"
DEPLOYED = "8b3d55c616d8820edd523f77021a35fe24167bd0"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    current = load(CURRENT)
    reconciliation = load(RECONCILIATION)
    blocked = load(BLOCKED)
    handoff = HANDOFF.read_text(encoding="utf-8")

    repo = current["repository_state"]
    require(repo["observed_head"] == MAIN, "main watermark mismatch")
    require(repo["latest_merged_pull_request"] == 84, "latest merged PR mismatch")
    require(repo["open_pull_requests_observed"] == [], "open PR observation mismatch")

    anchors = current["evidence_anchors"]
    require(anchors["pr84_source_head"] == SOURCE, "PR #84 source mismatch")
    require(anchors["pr84_merge_commit"] == MAIN, "PR #84 merge mismatch")
    require(anchors["pr84_ci_run_id"] == 30137351716, "PR #84 CI mismatch")
    require(anchors["pr84_source_vs_merge_file_content_difference_observed"] is False, "content-equivalence boundary regressed")

    api = current["independent_demo_api"]
    provenance = api["deployment_provenance"]
    require(provenance["deployed_source_ref"] == DEPLOYED, "deployed source mismatch")
    require(provenance["resource_count"] == 7, "resource count changed")
    require(provenance["vm_power_state"] == "VM running", "VM running state missing")
    require(provenance["extension_provisioning_state"] == "Succeeded", "extension state missing")

    repo_sync = api["repository_reconciliation"]
    require(repo_sync["main_ahead_by_commits"] == 83, "deployed-source comparison mismatch")
    require(repo_sync["workload_source_or_iac_path_changed"] is True, "runtime drift was hidden")
    require(repo_sync["timeout_fix_merged_into_main"] is True, "merged timeout fix missing")
    require(repo_sync["timeout_fix_deployed"] is False, "undeployed fix fabricated")

    runtime = api["runtime"]
    require(runtime["health_status"] == "healthy", "public health missing")
    require(runtime["health_contract"] == "pre_timeout_fix_contract", "runtime contract boundary changed")
    require(runtime["corrected_timeout_fields_observed"] is False, "corrected runtime fabricated")
    require(runtime["live_twenty_attempt_replay_performed"] is False, "replay fabricated")
    require(runtime["full_workload_operationally_verified"] is False, "full verification fabricated")

    deployment = api["deployment_attempt"]
    require(deployment["authorization_status"] == "consumed_blocked", "grant outcome mismatch")
    require(deployment["missing_action"] == "Microsoft.Compute/virtualMachines/extensions/write", "missing action mismatch")
    require(deployment["what_if_result_observed"] is False, "What-If result fabricated")
    require(deployment["deployment_step_executed"] is False, "deployment execution fabricated")
    require(deployment["azure_resource_mutation_performed"] is False, "Azure mutation fabricated")

    operations = api["security_and_operations"]
    require(operations["required_extension_write_effective"] is False, "extension write effectiveness fabricated")
    require(operations["effective_least_privilege_verified"] is False, "least privilege fabricated")
    require(operations["recovery_services_vault_count"] == 0, "vault observation mismatch")
    require(operations["recovery_tested"] is False, "recovery test fabricated")
    require(operations["month_to_date_actual_cost"]["currency"] == "CAD", "cost currency mismatch")
    require(operations["month_to_date_actual_cost"]["pre_tax_cost"] == 0.734335248846279, "cost observation mismatch")

    frontend = api["frontend"]
    require(frontend["integration_merged_into_main"] is True, "frontend merge missing")
    require(frontend["github_pages_publication_verified_after_merge"] is False, "Pages publication fabricated")
    require(frontend["live_browser_rendering_of_corrected_api_verified"] is False, "live browser verification fabricated")

    require(reconciliation["baseline"]["main"] == MAIN, "reconciliation baseline mismatch")
    require(reconciliation["problem"]["classification"] == "canonical_shared_state_stale_after_pr84_merge", "classification mismatch")
    require(reconciliation["problem"]["azure_contradiction"] is False, "false Azure contradiction")
    require(reconciliation["resolution"]["historical_planner_evidence_preserved"] is True, "planner history lost")

    require(blocked["authorization"]["final_status"] == "consumed_blocked", "blocked evidence status mismatch")
    require(blocked["resolved_state"]["azure_resource_mutation_performed"] is False, "blocked evidence mutation boundary regressed")

    authority = current["authority"]
    for key in (
        "pull_request_merge_authorized",
        "workflow_dispatch_authorized",
        "azure_authentication_authorized",
        "azure_mutations_authorized",
        "azure_rbac_mutations_authorized",
        "guest_commands_authorized",
        "transaction_replay_authorized",
        "github_pages_publication_authorized",
        "cleanup_authorized",
    ):
        require(authority[key] is False, f"{key} must remain false")

    for marker in (
        MAIN,
        SOURCE,
        DEPLOYED,
        "merged_into_main != deployed_to_VM",
        "Microsoft.Compute/virtualMachines/extensions/write",
        "deployment grant status: consumed_blocked",
        "GitHub Pages publication after merge verified: false",
    ):
        require(marker in handoff, f"handoff missing {marker!r}")

    print("post-merge PR #84 current-reality validation passed")


if __name__ == "__main__":
    main()
