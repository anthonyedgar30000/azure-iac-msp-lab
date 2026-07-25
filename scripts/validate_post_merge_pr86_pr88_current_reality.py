#!/usr/bin/env python3
"""Validate canonical repository reality after PR #93 and PR #92 merges.

The file name is retained for workflow compatibility. Historical PR #86/#88 state
remains validated, while the canonical watermark advances to the final main that
contains PR #93 followed by PR #92.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / ".project/current-reality.json"
HANDOFF = ROOT / ".project/handoffs/current-state.md"
LATEST = ROOT / ".project/reconciliations/post-merge-pr92-pr93-current-reality.json"
HISTORICAL = ROOT / ".project/reconciliations/post-merge-pr86-pr88-current-reality.json"

CURRENT_MAIN = "665e051375594d11e58e434231bd06775dbdc560"
PR92_SOURCE = "5b5af74d57fb5fd87ece2a34239cc6f29d04b12b"
PR92_MERGE = CURRENT_MAIN
PR93_SOURCE = "eecb5c872f76cb5e51df6f5451d5a61b79d87bba"
PR93_MERGE = "99dc79c7093fa4cd5655c2d5a65095dd796f9f75"
DEPLOYED = "8b3d55c616d8820edd523f77021a35fe24167bd0"
PR86_MERGE = "67d1aa9c784825e835097f684ddf629727ca5e22"
PR88_MERGE = "726c42ea1dddf402a42d8d0c591c660ebc50733f"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    current = load(CURRENT)
    latest = load(LATEST)
    historical = load(HISTORICAL)
    handoff = HANDOFF.read_text(encoding="utf-8")

    repo = current["repository_state"]
    require(repo["observed_head"] == CURRENT_MAIN, "current main watermark mismatch")
    require(repo["latest_merged_pull_request"] == 92, "latest merge-by-time mismatch")
    require(repo["also_merged_pull_requests"] == [93], "PR #93 merge missing")
    require(repo["merge_order"] == [93, 92], "merge order mismatch")
    require(repo["open_pull_requests_observed"] == [], "open PR observation mismatch")
    require(repo["local_working_tree"] == "not_observed", "local state was fabricated")

    ci = repo["exact_head_ci"]
    require(ci["pr92_source_head"] == PR92_SOURCE, "PR #92 source mismatch")
    require(ci["pr92_ci_run_id"] == 30160681565, "PR #92 CI run mismatch")
    require(ci["pr92_ci_conclusion"] == "success", "PR #92 CI changed")
    require(ci["pr92_reviewed_package_ci_run_id"] == 30160596671, "PR #92 package CI mismatch")
    require(ci["pr92_operator_check_rollup"] == "all_checks_passed", "PR #92 UI rollup lost")
    require(ci["pr93_source_head"] == PR93_SOURCE, "PR #93 source mismatch")
    require(ci["pr93_ci_run_ids"] == [30160683469, 30160683486], "PR #93 runs mismatch")
    require(ci["pr93_ci_conclusions"] == ["success", "success"], "PR #93 CI changed")
    require(ci["pr89_ci_conclusion"] == "failure", "PR #89 failure was erased")
    require(ci["pr90_ci_conclusions"] == ["success", "success", "success", "success"], "PR #90 repair lost")

    merge = repo["merge_result_ci"]
    require(merge["pr93_merge_commit"] == PR93_MERGE, "PR #93 merge mismatch")
    require(merge["pr92_merge_commit"] == PR92_MERGE, "PR #92 merge mismatch")
    require(merge["pr93_merge_commit_run"] == "not_observed", "PR #93 merge CI fabricated")
    require(merge["pr92_merge_commit_run"] == "not_observed", "PR #92 merge CI fabricated")
    require(merge["final_combined_main_ci"] == "not_observed", "combined main CI fabricated")

    operator = repo["operator_merge_reconciliation"]
    require(operator["pr92_recorded_agent_merge_authority"] is False, "PR #92 authority rewritten")
    require(operator["pr93_recorded_agent_merge_authority"] is False, "PR #93 authority rewritten")
    require(operator["pr92_human_operator_merge_observed"] is True, "PR #92 operator merge lost")
    require(operator["pr93_human_operator_merge_observed"] is True, "PR #93 operator merge lost")

    anchors = current["evidence_anchors"]
    require(anchors["pr86_merge_commit"] == PR86_MERGE, "PR #86 history lost")
    require(anchors["pr88_merge_commit"] == PR88_MERGE, "PR #88 history lost")
    require(anchors["pr92_merge_commit"] == PR92_MERGE, "PR #92 anchor mismatch")
    require(anchors["pr93_merge_commit"] == PR93_MERGE, "PR #93 anchor mismatch")
    require(anchors["pr92_protected_run_id"] == "not_observed", "protected run ID fabricated")
    require(anchors["pr92_protected_artifact"] == "not_observed", "protected artifact fabricated")

    api = current["independent_demo_api"]
    provenance = api["deployment_provenance"]
    require(provenance["deployed_source_ref"] == DEPLOYED, "deployed source mismatch")
    require(provenance["latest_observation_completed_at"] == "2026-07-25T00:47:40Z", "Azure timestamp changed")
    require(provenance["resource_count"] == 7, "resource count changed")
    require(provenance["vm_power_state"] == "VM running", "VM state lost")

    repository = api["repository_reconciliation"]
    require(repository["main_ahead_by_commits"] == 158, "commit comparison mismatch")
    require(repository["main_behind_by_commits"] == 0, "behind count mismatch")
    require(repository["verify_only_attempt_2_package_merged_into_main"] is True, "PR #92 package missing")
    require(repository["structured_pr82_validator_fix_merged_into_main"] is True, "PR #93 repair missing")
    require(repository["timeout_fix_deployed"] is False, "undeployed fix fabricated")

    runtime = api["runtime"]
    require(runtime["health_contract"] == "pre_timeout_fix_contract", "runtime boundary changed")
    require(runtime["corrected_timeout_fields_observed"] is False, "corrected runtime fabricated")
    require(runtime["backend_transaction_success_verified"] is False, "backend success fabricated")
    require(runtime["full_workload_operationally_verified"] is False, "operational verification fabricated")

    deployment = api["deployment_attempt"]
    require(deployment["authorization_status"] == "consumed_blocked", "deployment grant changed")
    require(deployment["deployment_step_executed"] is False, "deployment execution fabricated")
    require(deployment["azure_resource_mutation_performed"] is False, "Azure mutation fabricated")

    resolved = api["resolved_state"]
    require(resolved["protected_verify_only_check_rollup_passed"] is True, "check rollup lost")
    require(resolved["protected_verify_only_artifact_inspected"] is False, "artifact inspection fabricated")
    require(resolved["extension_write_permission_verified"] is False, "permission fabricated")
    require(resolved["corrected_runtime_deployed"] is False, "deployment fabricated")

    rbac = current["rbac_reconciliation"]["resolved_state"]
    require(rbac["execution_truth"] == "conflicting_with_new_check_rollup", "RBAC conflict collapsed")
    require(rbac["apply_success"] == "assumed_not_evidenced", "RBAC success fabricated")
    require(rbac["effective_target_identity_permission"] == "unverified", "permission fabricated")
    require(
        rbac["protected_verify_only_outcome"]
        == "check_rollup_passed_exact_run_and_artifact_not_observed",
        "protected outcome overstated",
    )
    require(rbac["deployment_authorized"] is False, "deployment authority fabricated")

    cleanup = current["resource_group_cleanup"]
    require(cleanup["dependency_collection_executed"] is False, "cleanup query fabricated")
    require(cleanup["candidate_orphan_status"] == "not_established", "orphan status fabricated")
    require(cleanup["azure_cleanup_performed"] is False, "cleanup fabricated")

    require(historical["baseline"]["main"] == PR88_MERGE, "historical PR #88 baseline changed")
    require(latest["baseline"]["main"] == CURRENT_MAIN, "latest reconciliation baseline mismatch")
    require(latest["pull_requests"]["merge_order"] == [93, 92], "latest merge order mismatch")
    require(latest["resolved_state"]["named_protected_verifier_outcome_observed"] is False, "run result fabricated")
    require(latest["azure_boundary"]["azure_mutation_performed"] is False, "Azure mutation fabricated")

    operations = api["security_and_operations"]
    require(operations["required_extension_write_effective"] == "unverified", "permission state mismatch")
    require(operations["backup_scope"] == "intentionally_out_of_scope_for_lab_v1", "backup scope mismatch")
    require(operations["month_to_date_actual_cost"]["currency"] == "CAD", "cost currency mismatch")
    require(operations["month_to_date_actual_cost"]["pre_tax_cost"] == 0.734335248846279, "cost changed")

    authority = current["authority"]
    for key in (
        "pull_request_merge_authorized",
        "workflow_dispatch_authorized",
        "azure_authentication_authorized",
        "azure_mutations_authorized",
        "azure_rbac_mutations_authorized",
        "resource_graph_query_authorized",
        "guest_commands_authorized",
        "transaction_replay_authorized",
        "github_pages_publication_authorized",
        "cleanup_authorized",
    ):
        require(authority[key] is False, f"{key} must remain false")

    for marker in (
        CURRENT_MAIN,
        PR92_SOURCE,
        PR93_SOURCE,
        PR93_MERGE,
        DEPLOYED,
        "checks_green != protected_Azure_artifact_inspected",
        "human_operator_merge != prior_agent_merge_authority",
        "deployment grant status: consumed_blocked",
        "Microsoft.Compute/virtualMachines/extensions/write",
        "effective extension write: unverified",
        "92b0c3b1064158684a4b280348c77eeedba6dfc3",
        "30064289707",
        "8585693830",
        "7aae2cff0df757a4b436c5b87507162624813e64bd32946bada8a87e5d7adc22",
        "NotAvailableForSubscription",
        "standardBasv2Family",
        "PR #73",
        "GitHub Pages publication authorized: false",
        "not_observed != false",
    ):
        require(marker in handoff, f"handoff missing {marker!r}")

    print("post-merge PR #92 and PR #93 current-reality validation passed")


if __name__ == "__main__":
    main()
