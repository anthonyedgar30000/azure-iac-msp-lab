#!/usr/bin/env python3
"""Validate the bounded PR #82 shared-state reconciliation."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / ".project/current-reality.json"
RECONCILIATION = ROOT / ".project/reconciliations/post-merge-pr82-shared-state.json"
HANDOFF = ROOT / ".project/handoffs/current-state.md"
HISTORY = ROOT / ".project/deployment-history.jsonl"
POST_DEPLOYMENT = ROOT / ".project/evidence/servicetracer-demo-api-post-deployment-inventory-20260724T163938Z.json"
PUBLIC_RUNTIME = ROOT / ".project/evidence/servicetracer-demo-api-live-verification-30086152352.json"

MAIN = "5dfa3b76a9fb975002d9cd702a892a0f678c88c5"
SOURCE_HEAD = "a85970061879ef4a900564d18e9631630e95b11e"
DEPLOYED_REF = "8b3d55c616d8820edd523f77021a35fe24167bd0"
EVENT_ID = "independent-demo-api-post-deployment-inventory-20260724T163938Z"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_history() -> list[dict]:
    return [
        json.loads(line)
        for line in HISTORY.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    current = load_json(CURRENT)
    reconciliation = load_json(RECONCILIATION)
    inventory = load_json(POST_DEPLOYMENT)
    runtime = load_json(PUBLIC_RUNTIME)
    handoff = HANDOFF.read_text(encoding="utf-8")
    history = load_history()

    require(current["schema_version"] == "project.current-reality.v1", "unexpected current-reality schema")
    require(current["repository_state"]["observed_head"] == MAIN, "main watermark drifted")
    require(current["repository_state"]["open_pull_requests_observed"] == [], "open PR state must be the bounded observation")
    require(current["evidence_anchors"]["pr82_source_head"] == SOURCE_HEAD, "PR #82 source head mismatch")
    require(current["evidence_anchors"]["pr82_merge_commit"] == MAIN, "PR #82 merge mismatch")
    require(current["evidence_anchors"]["pr82_source_vs_merge_file_content_difference_observed"] is False, "content equivalence boundary regressed")

    api = current["independent_demo_api"]
    provenance = api["deployment_provenance"]
    require(provenance["resource_group"] == "rg-st-demo-api-dev-westus2", "resource-group mismatch")
    require(provenance["location"] == "westus2", "location mismatch")
    require(provenance["vm_size"] == "Standard_F1als_v7", "VM-size mismatch")
    require(provenance["deployed_source_ref"] == DEPLOYED_REF, "deployed source mismatch")
    require(provenance["vm_power_state"] == "VM running", "running state not preserved")
    require(api["resolved_state"]["deployed"] is True, "deployment must be represented")
    require(api["resolved_state"]["public_api_verified"] is True, "public API verification missing")
    require(api["resolved_state"]["backend_transaction_success_verified"] is False, "backend failure boundary collapsed")
    require(api["resolved_state"]["operationally_verified"] is False, "full operational verification fabricated")

    operations = api["security_and_operations"]
    require(operations["effective_rbac"] == "not_observed", "RBAC unknown was collapsed")
    require(operations["backup"] == "not_observed", "backup unknown was collapsed")
    require(operations["actual_cost"] == "not_observed", "cost unknown was collapsed")
    require(operations["recovery_tested"] is False, "recovery test was fabricated")
    require(operations["metric_alert_count"] == 0, "metric-alert observation changed")
    require(operations["action_group_count"] == 0, "action-group observation changed")

    historical = current["historical_planner_evidence"]
    require(historical["run_id"] == 30064289707, "historical planner evidence lost")
    require(historical["preserved"] is True, "historical planner evidence must remain preserved")
    require(historical["current_deployment_view"] is False, "historical planner record must not remain current deployment truth")

    authority = current["authority"]
    for key in (
        "pull_request_merge_authorized",
        "workflow_dispatch_authorized",
        "azure_authentication_authorized",
        "azure_mutations_authorized",
        "guest_commands_authorized",
        "transaction_replay_authorized",
        "cleanup_authorized",
    ):
        require(authority[key] is False, f"{key} must remain false")

    require(reconciliation["baseline"]["main"] == MAIN, "reconciliation main mismatch")
    require(reconciliation["problem"]["classification"] == "shared_state_view_stale", "problem classification changed")
    require(reconciliation["problem"]["azure_contradiction"] is False, "state-view drift became false Azure contradiction")
    require(reconciliation["resolution"]["historical_planner_evidence_preserved"] is True, "planner history not preserved")

    inventory_provenance = inventory["deployment_provenance"]
    require(inventory_provenance["resource_group"]["name"] == provenance["resource_group"], "inventory resource group mismatch")
    require(inventory_provenance["deployment_record"]["source_ref"] == DEPLOYED_REF, "inventory source ref mismatch")
    require(inventory["runtime_control_plane"]["vm"]["power_state"] == "VM running", "inventory VM state mismatch")
    require(inventory["combined_verification"]["actual_cost_observed"] is False, "inventory cost boundary changed")

    runtime_observation = runtime["public_runtime_observation"]
    require(runtime_observation["public_endpoint_reachable"] is True, "runtime reachability mismatch")
    require(runtime["typed_verification"]["public_api_operationally_verified"] is True, "runtime API verification mismatch")
    require(runtime["typed_verification"]["backend_transaction_success_verified"] is False, "runtime backend boundary mismatch")
    require(runtime["typed_verification"]["full_workload_operationally_verified"] is False, "runtime full verification fabricated")

    matching = [event for event in history if event.get("event_id") == EVENT_ID]
    require(len(matching) == 1, "post-deployment history event must appear exactly once")
    require(matching[0]["repository_commit"] == MAIN, "history repository watermark mismatch")
    require(matching[0]["azure_mutations_performed"] is False, "history mutation boundary regressed")

    for required in (
        MAIN,
        "rg-st-demo-api-dev-westus2",
        "Standard_F1als_v7",
        "backend transaction success verified = false",
        "effective RBAC: not observed",
        "Azure authentication authorized: false",
    ):
        require(required in handoff, f"handoff missing {required!r}")

    print("PR #82 shared-state reconciliation validation passed")


if __name__ == "__main__":
    main()
