#!/usr/bin/env python3
"""Validate canonical repository lifecycle after PR #90 without changing Azure truth."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / ".project/current-reality.json"
HANDOFF = ROOT / ".project/handoffs/current-state.md"
HISTORICAL_RECONCILIATION = ROOT / ".project/reconciliations/post-merge-pr86-pr88-current-reality.json"
RBAC_RECONCILIATION = ROOT / ".project/reconciliations/servicetracer-demo-api-extension-updater-rbac-bootstrap.json"
RBAC_AUTHORIZATION = ROOT / ".project/authorizations/servicetracer-demo-api-extension-updater-rbac-bootstrap-20260725.json"
VERIFY_EXECUTION = ROOT / ".project/executions/servicetracer-demo-api-extension-write-verify-only-20260725.json"
CLEANUP_CONTRACT = ROOT / ".project/contracts/servicetracer-resource-group-boundary-cleanup.json"

CURRENT_MAIN = "8b25ecf1f00a59033955ef67bb3f9b511126f08a"
PR89_SOURCE = "3727b67533eb8043a22895a833223fa00fb70d10"
PR89_MERGE = "39e214a32ebdac61d22d7b130d4c2f1e5d6f4f53"
PR90_SOURCE = "0e5ae4c68801695241eebef4f05967ec38a894ff"
PR90_MERGE = CURRENT_MAIN

HISTORICAL_MAIN = "726c42ea1dddf402a42d8d0c591c660ebc50733f"
PR86_SOURCE = "8df0a5af4b522ceeff16c0d9d1adfc978e66d559"
PR86_MERGE = "67d1aa9c784825e835097f684ddf629727ca5e22"
PR88_SOURCE = "5e05d050cace2210c9b47103fe100eceb759cd0e"
DEPLOYED = "8b3d55c616d8820edd523f77021a35fe24167bd0"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    current = load(CURRENT)
    historical = load(HISTORICAL_RECONCILIATION)
    rbac_reconciliation = load(RBAC_RECONCILIATION)
    rbac_authorization = load(RBAC_AUTHORIZATION)
    verify_execution = load(VERIFY_EXECUTION)
    cleanup_contract = load(CLEANUP_CONTRACT)
    handoff = HANDOFF.read_text(encoding="utf-8")

    repo = current["repository_state"]
    require(repo["observed_head"] == CURRENT_MAIN, "current main watermark mismatch")
    require(repo["latest_merged_pull_request"] == 90, "latest merged PR mismatch")
    require(repo["open_pull_requests_observed"] == [], "open PR observation mismatch")

    ci = repo["exact_head_ci"]
    require(ci["pr86_ci_conclusion"] == "success", "PR #86 exact-head CI lost")
    require(ci["pr88_ci_conclusions"] == ["success", "success", "success"], "PR #88 exact-head CI lost")
    require(ci["pr89_ci_run_id"] == 30145973950, "PR #89 CI run mismatch")
    require(ci["pr89_ci_conclusion"] == "failure", "PR #89 full CI failure was erased")
    require(
        ci["pr89_dedicated_conclusions"] == ["success", "success", "success"],
        "PR #89 dedicated checks changed",
    )
    require(ci["pr90_source_head"] == PR90_SOURCE, "PR #90 source mismatch")
    require(
        ci["pr90_ci_run_ids"] == [30146139826, 30146139825, 30146139830, 30146139832],
        "PR #90 run IDs mismatch",
    )
    require(ci["pr90_ci_conclusions"] == ["success", "success", "success", "success"], "PR #90 CI changed")

    merge_ci = repo["merge_result_ci"]
    require(merge_ci["pr89_merge_commit"] == PR89_MERGE, "PR #89 merge mismatch")
    require(merge_ci["pr90_merge_commit"] == PR90_MERGE, "PR #90 merge mismatch")
    require(merge_ci["pr90_merge_commit_run"] == "not_observed", "PR #90 merge CI fabricated")
    require(merge_ci["final_combined_main_ci"] == "not_observed", "combined main CI fabricated")

    anchors = current["evidence_anchors"]
    require(anchors["pr86_source_head"] == PR86_SOURCE, "PR #86 source mismatch")
    require(anchors["pr86_merge_commit"] == PR86_MERGE, "PR #86 merge mismatch")
    require(anchors["pr88_source_head"] == PR88_SOURCE, "PR #88 source mismatch")
    require(anchors["pr88_merge_commit"] == HISTORICAL_MAIN, "PR #88 merge mismatch")
    require(anchors["pr89_source_head"] == PR89_SOURCE, "PR #89 source mismatch")
    require(anchors["pr89_merge_commit"] == PR89_MERGE, "PR #89 merge mismatch")
    require(anchors["pr89_full_ci_conclusion"] == "failure", "PR #89 failure lost")
    require(anchors["pr90_source_head"] == PR90_SOURCE, "PR #90 source mismatch")
    require(anchors["pr90_merge_commit"] == PR90_MERGE, "PR #90 merge mismatch")
    require(anchors["pr90_source_vs_merge_file_content_difference_observed"] is False, "PR #90 content mismatch")
    require(anchors["pr90_merge_commit_ci_observed"] is False, "PR #90 merge CI fabricated")

    api = current["independent_demo_api"]
    provenance = api["deployment_provenance"]
    require(provenance["deployed_source_ref"] == DEPLOYED, "deployed source mismatch")
    require(provenance["latest_observation_completed_at"] == "2026-07-25T00:47:40Z", "Azure timestamp changed")
    require(provenance["vm_power_state"] == "VM running", "VM state lost")

    repository = api["repository_reconciliation"]
    require(repository["main_ahead_by_commits"] == 146, "commit comparison mismatch")
    require(repository["main_behind_by_commits"] == 0, "behind count mismatch")
    require(repository["rbac_package_merged_into_main"] is True, "RBAC package missing")
    require(repository["cleanup_plan_merged_into_main"] is True, "cleanup plan missing")
    require(repository["handoff_repair_merged_into_main"] is True, "PR #90 repair missing")
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

    rbac = current["rbac_reconciliation"]
    resolved = rbac["resolved_state"]
    require(resolved["execution_truth"] == "conflicting", "RBAC conflict collapsed")
    require(resolved["apply_attempt_asserted"] is True, "asserted attempt lost")
    require(resolved["apply_success"] == "assumed_not_evidenced", "RBAC success fabricated")
    require(resolved["role_definition_observed"] is False, "role definition fabricated")
    require(resolved["role_assignment_observed"] is False, "role assignment fabricated")
    require(resolved["effective_target_identity_permission"] == "unverified", "permission fabricated")
    require(resolved["protected_verify_only_outcome"] == "not_observed", "verify outcome fabricated")
    require(resolved["deployment_authorized"] is False, "deployment authority fabricated")
    require(len(rbac["preserved_source_claims"]) == 4, "RBAC source claims dropped")

    require(
        rbac_reconciliation["current_state"]["azure_rbac_bootstrap_executed"] is False,
        "historical bootstrap record changed",
    )
    require(rbac_authorization["status"] == "authorized_not_consumed", "authorization history changed")
    require("assume" in verify_execution["assumption"].lower(), "assumption boundary lost")

    cleanup = current["resource_group_cleanup"]
    require(cleanup["repository_plan_merged"] is True, "cleanup plan not represented")
    require(cleanup["independent_demo_api_protected"] is True, "independent workload protection lost")
    require(cleanup["dependency_collection_executed"] is False, "dependency collection fabricated")
    require(cleanup["candidate_current_presence"] == "not_freshly_observed", "presence fabricated")
    require(cleanup["candidate_orphan_status"] == "not_established", "orphan status fabricated")
    require(cleanup["azure_cleanup_authorized"] is False, "cleanup authority fabricated")
    require(cleanup["azure_cleanup_performed"] is False, "cleanup fabricated")
    require(len(cleanup["cleanup_candidates"]) == 7, "cleanup candidate count mismatch")
    require(
        cleanup_contract["resource_group_model"]["independent_demo_api"]["protected_from_this_cleanup"] is True,
        "contract protection lost",
    )
    require(
        cleanup_contract["authority"]["resource_graph_query_execution_authorized"] is False,
        "query authority fabricated",
    )

    operations = api["security_and_operations"]
    require(operations["required_extension_write_effective"] == "unverified", "permission state mismatch")
    require(operations["backup_scope"] == "intentionally_out_of_scope_for_lab_v1", "backup scope mismatch")
    require(operations["recovery_services_vault_count"] == 0, "vault observation lost")
    require(operations["other_backup_methods"] == "not_observed", "backup unknown collapsed")
    require(operations["month_to_date_actual_cost"]["currency"] == "CAD", "cost currency mismatch")
    require(
        operations["month_to_date_actual_cost"]["pre_tax_cost"] == 0.734335248846279,
        "cost evidence changed",
    )

    require(historical["baseline"]["main"] == HISTORICAL_MAIN, "historical reconciliation baseline changed")
    require(
        historical["problem"]["classification"]
        == "canonical_shared_state_stale_and_rbac_execution_claims_conflicting_after_pr86_pr88_merge",
        "historical problem classification changed",
    )
    require(historical["problem"]["azure_contradiction"] is False, "false Azure contradiction")
    require(historical["problem"]["rbac_claim_conflict"] is True, "RBAC conflict hidden")

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
        PR89_SOURCE,
        PR89_MERGE,
        PR90_SOURCE,
        PR90_MERGE,
        PR86_SOURCE,
        PR86_MERGE,
        PR88_SOURCE,
        DEPLOYED,
        "RBAC execution truth: conflicting",
        "apply success: assumed_not_evidenced",
        "candidate orphan status: not established",
        "Azure Backup / Recovery Services: intentionally out of scope for Lab v1",
        "Azure authentication authorized: false",
        "92b0c3b1064158684a4b280348c77eeedba6dfc3",
        "30064289707",
        "8585693830",
        "7aae2cff0df757a4b436c5b87507162624813e64bd32946bada8a87e5d7adc22",
        "NotAvailableForSubscription",
        "standardBasv2Family",
        "PR #73",
        "not_observed != false",
    ):
        require(marker in handoff, f"handoff missing {marker!r}")

    print("post-merge PR #90 current-reality validation passed")


if __name__ == "__main__":
    main()
