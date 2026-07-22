from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "servicetracer.collector-replacement-execution-design.v1"
REQUIRED_PHASE_ORDER = [
    "validate_authority",
    "guest_and_control_plane_preflight",
    "preserve_delete_options",
    "create_recovery_points",
    "verify_recovery_points",
    "remove_old_compute",
    "verify_preservation_boundary",
    "deploy_replacement_compute",
    "harden_replacement_os_disk",
    "restore_identity_and_rbac",
    "post_change_verification",
    "human_recovery_acceptance",
    "cleanup_temporary_recovery_resources",
]
MUTATION_PHASES = {
    "preserve_delete_options",
    "create_recovery_points",
    "remove_old_compute",
    "deploy_replacement_compute",
    "harden_replacement_os_disk",
    "restore_identity_and_rbac",
    "cleanup_temporary_recovery_resources",
}
EXPECTED_PLANNER_RUN = 29856203054
EXPECTED_PLANNER_DIGEST = (
    "76f3b44e6e97e906dac6d62eeb212a6bc55265e77271a030b9c45b0cacf55637"
)
EXPECTED_TARGET = "vm-stcollector-mst-dev"
EXPECTED_OS_DISK = "disk-stcollector-os-mst-dev"
EXPECTED_CONFIRMATION = (
    "REPLACE:rg-servicetracer-dev-westus2:vm-stcollector-mst-dev"
)
EXPECTED_ROLLBACK_STATUS = "strategy_selected_design_only"
EXPECTED_ROLLBACK_STRATEGY = "os_disk_snapshot_recreate_canonical_name"
EXPECTED_ROLLBACK_SNAPSHOT_PREFIX = "snap-stcollector-os-rollback-mst-dev-"
REQUIRED_ROLLBACK_PREFLIGHT = {
    "source OS-disk resource ID",
    "disk size GiB",
    "OS type",
    "Hyper-V generation",
    "security type and Trusted Launch compatibility",
    "encryption configuration",
    "network access policy",
    "public network access state",
}
REQUIRED_SNAPSHOT_VERIFICATION = {
    "provisioning state succeeded",
    "source OS-disk resource ID matches",
    "snapshot size matches source disk",
    "Hyper-V generation and OS type are preserved",
    "network access policy is DenyAll",
    "public network access is Disabled",
    "execution, owner, and cleanup-deadline tags are present",
    "cleanup deadline is no more than 24 hours after creation",
}
REQUIRED_ROLLBACK_ACCEPTANCE = {
    "prior OS boots under the reviewed security profile",
    "same evidence filesystem UUID is mounted at /var/lib/servicetracer",
    "recent pre-change evidence is readable",
    "collector service and local health endpoint succeed",
    "durable write and restart persistence succeed",
    "NIC, static address, identity, RBAC, and disk access policies match the rollback contract",
}


class DesignValidationError(RuntimeError):
    pass


def _object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DesignValidationError(f"{field} must be an object")
    return value


def _list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise DesignValidationError(f"{field} must be a list")
    return value


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DesignValidationError(f"{field} must be a non-empty string")
    return value.strip()


def _text_set(value: Any, field: str) -> set[str]:
    return {_text(item, f"{field}[]") for item in _list(value, field)}


def validate_contract(contract: dict[str, Any]) -> dict[str, Any]:
    if contract.get("schema_version") != SCHEMA_VERSION:
        raise DesignValidationError("unsupported schema_version")
    if contract.get("state") != "design_only":
        raise DesignValidationError("the replacement contract must remain design_only")

    activation = _object(contract.get("activation"), "activation")
    candidate_workflow = _text(
        activation.get("candidate_workflow"), "activation.candidate_workflow"
    )
    active_workflow = _text(
        activation.get("active_workflow"), "activation.active_workflow"
    )
    if not candidate_workflow.startswith("infra/workflow-designs/"):
        raise DesignValidationError("candidate workflow must remain outside .github/workflows")
    if active_workflow != ".github/workflows/collector-replacement-execution.yml":
        raise DesignValidationError("unexpected active workflow promotion path")
    for field in (
        "active_workflow_present",
        "dispatch_authorized",
        "azure_mutations_authorized",
    ):
        if activation.get(field) is not False:
            raise DesignValidationError(f"activation.{field} must be false")
    if activation.get("promotion_requires_separate_pull_request") is not True:
        raise DesignValidationError("promotion must require a separate pull request")

    reviews = _text_set(
        activation.get("promotion_requires_independent_reviews"),
        "activation.promotion_requires_independent_reviews",
    )
    required_reviews = {
        "evidence-quality",
        "operations-and-recovery",
        "security-and-identity",
        "azure-cost",
    }
    if reviews != required_reviews:
        raise DesignValidationError("all four independent review lenses are required")

    evidence = _object(contract.get("evidence_anchor"), "evidence_anchor")
    if evidence.get("planner_run_id") != EXPECTED_PLANNER_RUN:
        raise DesignValidationError("planner run ID does not match promoted evidence")
    if evidence.get("planner_artifact_sha256") != EXPECTED_PLANNER_DIGEST:
        raise DesignValidationError("planner artifact digest does not match promoted evidence")
    if evidence.get("planner_azure_mutations_authorized") is not False:
        raise DesignValidationError("planner mutations must remain unauthorized")
    if evidence.get("planner_azure_mutations_performed") is not False:
        raise DesignValidationError("planner must record no Azure mutations")

    target = _object(contract.get("target"), "target")
    if target.get("collector_vm") != EXPECTED_TARGET:
        raise DesignValidationError("unexpected collector VM target")
    if target.get("collector_os_disk") != EXPECTED_OS_DISK:
        raise DesignValidationError("unexpected canonical collector OS-disk name")
    if target.get("exact_future_confirmation") != EXPECTED_CONFIRMATION:
        raise DesignValidationError("unexpected replacement confirmation phrase")
    if target.get("evidence_mount") != "/var/lib/servicetracer":
        raise DesignValidationError("unexpected evidence mount")

    cost = _object(contract.get("cost_controls"), "cost_controls")
    if cost.get("currency") != "CAD":
        raise DesignValidationError("cost ceiling must be denominated in CAD")
    max_cost = cost.get("maximum_declared_temporary_cost")
    if not isinstance(max_cost, (int, float)) or isinstance(max_cost, bool):
        raise DesignValidationError("temporary cost ceiling must be numeric")
    if max_cost <= 0 or max_cost > 10:
        raise DesignValidationError(
            "temporary cost ceiling must be greater than 0 and at most CAD 10"
        )
    if cost.get("maximum_snapshots") != 2:
        raise DesignValidationError(
            "the selected rollback requires exactly two recovery snapshots"
        )
    if cost.get("maximum_total_snapshot_gib") != 96:
        raise DesignValidationError("snapshot capacity ceiling must remain 96 GiB")
    if cost.get("maximum_compute_overlap_minutes") != 0:
        raise DesignValidationError("overlapping old and replacement compute is prohibited")
    retention = cost.get("maximum_recovery_resource_retention_hours")
    if (
        not isinstance(retention, int)
        or isinstance(retention, bool)
        or retention <= 0
        or retention > 24
    ):
        raise DesignValidationError(
            "recovery resources must be retained for between 1 and 24 hours"
        )
    if cost.get("azure_budget_or_alert_mutation_allowed") is not False:
        raise DesignValidationError("the execution path must not modify budgets or alerts")

    gates = [
        _text(item, "required_preflight_gates[]")
        for item in _list(contract.get("required_preflight_gates"), "required_preflight_gates")
    ]
    if len(gates) < 9:
        raise DesignValidationError("preflight gate set is incomplete")
    if not any("OS-disk identity" in gate for gate in gates):
        raise DesignValidationError("OS-disk recreation metadata is missing from preflight")

    phases = _list(contract.get("phases"), "phases")
    phase_ids: list[str] = []
    observed_mutation_phases: set[str] = set()
    phase_evidence: dict[str, str] = {}
    for index, phase_value in enumerate(phases):
        phase = _object(phase_value, f"phases[{index}]")
        phase_id = _text(phase.get("phase_id"), f"phases[{index}].phase_id")
        phase_ids.append(phase_id)
        mutation = phase.get("mutation")
        if not isinstance(mutation, bool):
            raise DesignValidationError(f"phases[{index}].mutation must be boolean")
        if mutation:
            observed_mutation_phases.add(phase_id)
            if phase.get("requires_explicit_authorization") is not True:
                raise DesignValidationError(
                    f"mutation phase {phase_id} requires explicit authorization"
                )
        phase_evidence[phase_id] = _text(
            phase.get("evidence_required"), f"phases[{index}].evidence_required"
        )

    if phase_ids != REQUIRED_PHASE_ORDER:
        raise DesignValidationError("replacement phases are missing or out of order")
    if observed_mutation_phases != MUTATION_PHASES:
        raise DesignValidationError("mutation phase classification changed unexpectedly")
    if "both snapshots" not in phase_evidence["remove_old_compute"]:
        raise DesignValidationError(
            "old compute removal must require both recovery snapshots"
        )
    if "canonical OS-disk name" not in phase_evidence["deploy_replacement_compute"]:
        raise DesignValidationError(
            "replacement deployment must retain the canonical OS-disk name"
        )

    rollback = _object(contract.get("rollback"), "rollback")
    rollback_status = _text(rollback.get("status"), "rollback.status")
    if rollback_status != EXPECTED_ROLLBACK_STATUS:
        raise DesignValidationError("rollback must remain selected design-only state")
    if rollback.get("promotion_blocked") is not True:
        raise DesignValidationError("workflow promotion must remain blocked")
    if rollback.get("strategy_id") != EXPECTED_ROLLBACK_STRATEGY:
        raise DesignValidationError("unexpected rollback strategy")
    if rollback.get("canonical_os_disk_name") != EXPECTED_OS_DISK:
        raise DesignValidationError("rollback must recreate the canonical OS-disk name")
    if rollback.get("snapshot_name_prefix") != EXPECTED_ROLLBACK_SNAPSHOT_PREFIX:
        raise DesignValidationError("unexpected OS-disk rollback snapshot prefix")
    if rollback.get("preserve_old_os_disk_directly") is not False:
        raise DesignValidationError(
            "the selected strategy must use a verified snapshot, not direct disk retention"
        )
    max_os_snapshot = rollback.get("maximum_os_disk_snapshot_gib")
    if (
        not isinstance(max_os_snapshot, int)
        or isinstance(max_os_snapshot, bool)
        or max_os_snapshot <= 0
        or max_os_snapshot > 64
    ):
        raise DesignValidationError("OS-disk snapshot ceiling must be 1 through 64 GiB")
    if rollback.get("block_if_os_disk_exceeds_snapshot_gib") != max_os_snapshot:
        raise DesignValidationError("OS-disk size blocker must equal the snapshot ceiling")
    if _text_set(
        rollback.get("source_preflight_required"),
        "rollback.source_preflight_required",
    ) != REQUIRED_ROLLBACK_PREFLIGHT:
        raise DesignValidationError("rollback source preflight requirements changed")
    if _text_set(
        rollback.get("snapshot_verification_required"),
        "rollback.snapshot_verification_required",
    ) != REQUIRED_SNAPSHOT_VERIFICATION:
        raise DesignValidationError("OS-disk snapshot verification requirements changed")

    recreation = _object(rollback.get("recreation_contract"), "rollback.recreation_contract")
    if recreation.get("os_disk_create_option") != "Copy":
        raise DesignValidationError("rollback OS disk must be copied from the snapshot")
    if recreation.get("os_disk_source") != "verified OS-disk snapshot":
        raise DesignValidationError("rollback OS-disk source must be the verified snapshot")
    if recreation.get("recreated_os_disk_name") != EXPECTED_OS_DISK:
        raise DesignValidationError("recreated OS disk must use the canonical name")
    if recreation.get("recreated_vm_name") != EXPECTED_TARGET:
        raise DesignValidationError("rollback must recreate the prior collector VM name")
    if recreation.get("attach_preserved_nic") != target.get("collector_nic"):
        raise DesignValidationError("rollback must attach the preserved collector NIC")
    if recreation.get("attach_preserved_evidence_disk") != target.get(
        "collector_evidence_disk"
    ):
        raise DesignValidationError("rollback must attach the preserved evidence disk")
    _text(recreation.get("identity_rule"), "rollback.recreation_contract.identity_rule")
    if _text_set(
        recreation.get("acceptance_required"),
        "rollback.recreation_contract.acceptance_required",
    ) != REQUIRED_ROLLBACK_ACCEPTANCE:
        raise DesignValidationError("rollback acceptance requirements changed")

    if rollback.get("operationally_tested") is not False:
        raise DesignValidationError(
            "repository design tests cannot claim operational rollback verification"
        )
    if rollback.get("independent_review_status") != "pending":
        raise DesignValidationError("independent rollback review must remain pending")
    _text(rollback.get("decision"), "rollback.decision")
    _text(rollback.get("before_old_vm_deletion"), "rollback.before_old_vm_deletion")
    _text(rollback.get("after_old_vm_deletion"), "rollback.after_old_vm_deletion")
    _text(rollback.get("evidence_disk_rule"), "rollback.evidence_disk_rule")

    blockers = [
        _text(item, "unresolved_blockers[]")
        for item in _list(contract.get("unresolved_blockers"), "unresolved_blockers")
    ]
    if "operational proof of the selected OS-disk snapshot recreation rollback" not in blockers:
        raise DesignValidationError("operational rollback proof must remain unresolved")
    if "rollback mechanism and canonical OS-disk naming" in blockers:
        raise DesignValidationError("the selected rollback decision was not reconciled")

    return {
        "schema_version": "servicetracer.collector-replacement-design-validation.v1",
        "design_valid": True,
        "design_state": "fail_closed",
        "candidate_workflow": candidate_workflow,
        "active_workflow": active_workflow,
        "dispatch_authorized": False,
        "azure_mutations_authorized": False,
        "promotion_ready": False,
        "evidence_anchor": {
            "planner_run_id": EXPECTED_PLANNER_RUN,
            "planner_artifact_sha256": EXPECTED_PLANNER_DIGEST,
        },
        "target": {
            "collector_vm": EXPECTED_TARGET,
            "collector_os_disk": EXPECTED_OS_DISK,
            "exact_future_confirmation": EXPECTED_CONFIRMATION,
        },
        "phase_order": phase_ids,
        "mutation_phase_ids": sorted(observed_mutation_phases),
        "cost_controls": cost,
        "unresolved_blockers": blockers,
        "rollback_status": rollback_status,
        "rollback_strategy": EXPECTED_ROLLBACK_STRATEGY,
        "canonical_os_disk_name": EXPECTED_OS_DISK,
        "rollback_operationally_tested": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate and render the fail-closed collector replacement design."
    )
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if not isinstance(contract, dict):
        raise DesignValidationError("contract root must be an object")
    result = validate_contract(contract)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        "collector replacement execution design validated: "
        "snapshot rollback selected, fail-closed, non-dispatchable, "
        "Azure mutations unauthorized"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
