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
    "quiesce_and_deallocate_source",
    "create_recovery_points",
    "verify_recovery_points",
    "isolated_snapshot_boot_rehearsal",
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
    "quiesce_and_deallocate_source",
    "create_recovery_points",
    "isolated_snapshot_boot_rehearsal",
    "remove_old_compute",
    "deploy_replacement_compute",
    "harden_replacement_os_disk",
    "restore_identity_and_rbac",
    "cleanup_temporary_recovery_resources",
}
EXPECTED_PLANNER_RUN = 29856203054
EXPECTED_PLANNER_DIGEST = "76f3b44e6e97e906dac6d62eeb212a6bc55265e77271a030b9c45b0cacf55637"
EXPECTED_TARGET = "vm-stcollector-mst-dev"
EXPECTED_NIC = "nic-stcollector-mst-dev"
EXPECTED_EVIDENCE_DISK = "disk-stcollector-evidence-mst-dev"
EXPECTED_OS_DISK = "disk-stcollector-os-mst-dev"
EXPECTED_CONFIRMATION = "REPLACE:rg-servicetracer-dev-westus2:vm-stcollector-mst-dev"
EXPECTED_ROLLBACK_STATUS = "strategy_selected_design_only"
EXPECTED_ROLLBACK_STRATEGY = "os_disk_snapshot_recreate_canonical_name"
EXPECTED_REVIEW_STATUS = "changes_addressed_re_review_pending"
EXPECTED_ROLLBACK_SNAPSHOT_PREFIX = "snap-stcollector-os-rollback-mst-dev-"
EXPECTED_BINDING_FIELDS = {
    "maintenance_correlation_id",
    "final_evidence_checkpoint_id",
    "final_evidence_checkpoint_sha256",
}
EXPECTED_CONSISTENCY_ACTIONS = [
    "stop accepting new collector writes",
    "drain in-flight collector writes",
    "flush pending evidence writes to the mounted evidence filesystem",
    "record final evidence checkpoint identifier and SHA-256",
    "record maintenance correlation identifier",
    "stop the collector service",
    "verify guest shutdown",
    "deallocate the source VM",
    "verify Azure PowerState/deallocated",
]
REQUIRED_REHEARSAL_PROOF = {
    "temporary disk source is the exact verified OS-disk snapshot",
    "temporary VM uses the recorded Trusted Launch security profile",
    "specialized OS disk is attached with create option Attach",
    "prior OS boots",
    "VM Guest State and vTPM viability are proven",
    "bounded guest health evidence succeeds",
    "production NIC is not attached",
    "production evidence disk is not attached",
}
REHEARSAL_TEARDOWN_EVIDENCE = [
    "isolated rehearsal VM is deallocated after proof capture",
    "temporary rehearsal VM and isolated NIC are removed before replacement compute",
    "only approved snapshots and temporary recovery disks may remain",
]
REQUIRED_ROLLBACK_PREFLIGHT = {
    "source OS-disk resource ID", "disk size GiB", "disk SKU", "OS type",
    "Hyper-V generation", "security profile and Trusted Launch compatibility",
    "encryption configuration and disk encryption set when present",
    "availability zone when present", "network access policy",
    "public network access state", "OS-disk delete option",
}
REQUIRED_SNAPSHOT_VERIFICATION = {
    "provisioning state succeeded", "source OS-disk resource ID matches",
    "snapshot size matches source disk", "Hyper-V generation and OS type are preserved",
    "network access policy is DenyAll", "public network access is Disabled",
    "maintenance correlation ID matches the consistency boundary",
    "final evidence checkpoint ID matches the consistency boundary",
    "final evidence checkpoint SHA-256 matches the consistency boundary",
    "execution, owner, and cleanup-deadline tags are present",
    "cleanup deadline is no more than 24 hours after creation",
}
REQUIRED_RECREATION_METADATA = {
    "disk SKU", "OS type", "Hyper-V generation",
    "security profile and Trusted Launch settings",
    "encryption configuration and disk encryption set when present",
    "availability zone when present", "network access policy",
    "public network access state", "OS-disk delete option",
}
REQUIRED_ROLLBACK_ACCEPTANCE = {
    "prior OS boots under the reviewed security profile",
    "same evidence filesystem UUID is mounted at /var/lib/servicetracer",
    "recent pre-change evidence is readable",
    "collector service and local health endpoint succeed",
    "durable write and restart persistence succeed",
    "NIC, static address, identity, RBAC, and disk access policies match the rollback contract",
    "NIC and evidence disk are re-read with deleteOption Detach before any failed-compute deletion",
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


def _text_list(value: Any, field: str) -> list[str]:
    return [_text(item, f"{field}[]") for item in _list(value, field)]


def _text_set(value: Any, field: str) -> set[str]:
    return set(_text_list(value, field))


def _require_true(value: Any, field: str) -> None:
    if value is not True:
        raise DesignValidationError(f"{field} must be true")


def _require_false(value: Any, field: str) -> None:
    if value is not False:
        raise DesignValidationError(f"{field} must be false")


def validate_contract(contract: dict[str, Any]) -> dict[str, Any]:
    if contract.get("schema_version") != SCHEMA_VERSION:
        raise DesignValidationError("unsupported schema_version")
    if contract.get("state") != "design_only":
        raise DesignValidationError("the replacement contract must remain design_only")

    activation = _object(contract.get("activation"), "activation")
    candidate_workflow = _text(activation.get("candidate_workflow"), "activation.candidate_workflow")
    active_workflow = _text(activation.get("active_workflow"), "activation.active_workflow")
    if not candidate_workflow.startswith("infra/workflow-designs/"):
        raise DesignValidationError("candidate workflow must remain outside .github/workflows")
    if active_workflow != ".github/workflows/collector-replacement-execution.yml":
        raise DesignValidationError("unexpected active workflow promotion path")
    for field in ("active_workflow_present", "dispatch_authorized", "azure_mutations_authorized"):
        _require_false(activation.get(field), f"activation.{field}")
    _require_true(activation.get("promotion_requires_separate_pull_request"), "activation.promotion_requires_separate_pull_request")
    if _text_set(activation.get("promotion_requires_independent_reviews"), "activation.promotion_requires_independent_reviews") != {
        "evidence-quality", "operations-and-recovery", "security-and-identity", "azure-cost"
    }:
        raise DesignValidationError("all four independent review lenses are required")

    evidence = _object(contract.get("evidence_anchor"), "evidence_anchor")
    if evidence.get("planner_run_id") != EXPECTED_PLANNER_RUN:
        raise DesignValidationError("planner run ID does not match promoted evidence")
    if evidence.get("planner_artifact_sha256") != EXPECTED_PLANNER_DIGEST:
        raise DesignValidationError("planner artifact digest does not match promoted evidence")
    _require_false(evidence.get("planner_azure_mutations_authorized"), "evidence_anchor.planner_azure_mutations_authorized")
    _require_false(evidence.get("planner_azure_mutations_performed"), "evidence_anchor.planner_azure_mutations_performed")

    target = _object(contract.get("target"), "target")
    expected_target_values = {
        "collector_vm": EXPECTED_TARGET,
        "collector_nic": EXPECTED_NIC,
        "collector_evidence_disk": EXPECTED_EVIDENCE_DISK,
        "collector_os_disk": EXPECTED_OS_DISK,
        "evidence_mount": "/var/lib/servicetracer",
        "exact_future_confirmation": EXPECTED_CONFIRMATION,
    }
    for field, expected in expected_target_values.items():
        if target.get(field) != expected:
            raise DesignValidationError(f"unexpected target field: {field}")

    cost = _object(contract.get("cost_controls"), "cost_controls")
    expected_cost_values = {
        "currency": "CAD", "review_status": "conditionally_approved_planning_estimate",
        "reviewed_planning_estimate": 4.0, "renewed_approval_threshold": 4.0,
        "maximum_declared_temporary_cost": 10.0, "maximum_snapshots": 2,
        "maximum_total_snapshot_gib": 96, "maximum_compute_overlap_minutes": 0,
        "maximum_isolated_restore_rehearsal_compute_hours": 4,
        "maximum_recovery_resource_retention_hours": 24,
    }
    for field, expected in expected_cost_values.items():
        if cost.get(field) != expected:
            raise DesignValidationError(f"cost control changed: {field}")
    for field in ("fresh_authenticated_subscription_cost_preflight_required", "cleanup_owner_required", "cleanup_deadline_required"):
        _require_true(cost.get(field), f"cost_controls.{field}")
    _require_false(cost.get("azure_budget_or_alert_mutation_allowed"), "cost_controls.azure_budget_or_alert_mutation_allowed")

    gates = _text_set(contract.get("required_preflight_gates"), "required_preflight_gates")
    if not any("subscription-specific pricing" in gate for gate in gates):
        raise DesignValidationError("fresh subscription-specific cost preflight is missing")
    if not any("OS-disk identity" in gate and "delete option" in gate for gate in gates):
        raise DesignValidationError("OS-disk recreation metadata is incomplete")

    consistency = _object(contract.get("consistency_boundary"), "consistency_boundary")
    if consistency.get("phase_id") != "quiesce_and_deallocate_source":
        raise DesignValidationError("unexpected consistency-boundary phase")
    actions = _text_list(consistency.get("ordered_actions"), "consistency_boundary.ordered_actions")
    if actions != EXPECTED_CONSISTENCY_ACTIONS:
        raise DesignValidationError("consistency boundary actions are missing, duplicated, or out of order")
    if consistency.get("source_power_state_required") != "PowerState/deallocated":
        raise DesignValidationError("source VM must be deallocated before snapshots")
    for field in ("final_evidence_checkpoint_id_required", "final_evidence_checkpoint_sha256_required", "maintenance_correlation_id_required", "both_snapshots_must_share_binding"):
        _require_true(consistency.get(field), f"consistency_boundary.{field}")
    _require_false(consistency.get("snapshot_capture_before_boundary_allowed"), "consistency_boundary.snapshot_capture_before_boundary_allowed")
    if _text_set(consistency.get("snapshot_binding_fields"), "consistency_boundary.snapshot_binding_fields") != EXPECTED_BINDING_FIELDS:
        raise DesignValidationError("snapshot binding fields changed")

    rehearsal = _object(contract.get("isolated_restore_rehearsal"), "isolated_restore_rehearsal")
    expected_rehearsal_values = {
        "phase_id": "isolated_snapshot_boot_rehearsal",
        "required_before_phase": "remove_old_compute",
        "source_snapshot": "exact verified OS-disk snapshot",
        "temporary_os_disk_create_option": "Copy",
        "temporary_vm_os_disk_create_option": "Attach",
        "security_profile_source": "recorded source Trusted Launch profile",
        "maximum_compute_hours": 4,
        "maximum_retention_hours": 24,
    }
    for field, expected in expected_rehearsal_values.items():
        if rehearsal.get(field) != expected:
            raise DesignValidationError(f"isolated rehearsal contract changed: {field}")
    for field in ("source_vm_must_remain_deallocated", "cleanup_required"):
        _require_true(rehearsal.get(field), f"isolated_restore_rehearsal.{field}")
    for field in ("production_nic_attached", "production_evidence_disk_attached", "operational_rollback_proof"):
        _require_false(rehearsal.get(field), f"isolated_restore_rehearsal.{field}")
    if _text_set(rehearsal.get("required_proof"), "isolated_restore_rehearsal.required_proof") != REQUIRED_REHEARSAL_PROOF:
        raise DesignValidationError("isolated rehearsal proof requirements changed")

    attachments = _object(contract.get("replacement_vm_attachment_contract"), "replacement_vm_attachment_contract")
    if attachments.get("nic_resource") != EXPECTED_NIC or attachments.get("evidence_disk_resource") != EXPECTED_EVIDENCE_DISK or attachments.get("os_disk_resource") != EXPECTED_OS_DISK:
        raise DesignValidationError("replacement attachment resource changed")
    if attachments.get("nic_delete_option") != "Detach" or attachments.get("evidence_disk_delete_option") != "Detach":
        raise DesignValidationError("replacement production attachments must use deleteOption Detach")
    for field in ("verify_after_vm_create", "verify_before_failed_compute_deletion"):
        _require_true(attachments.get(field), f"replacement_vm_attachment_contract.{field}")

    phases = _list(contract.get("phases"), "phases")
    phase_ids: list[str] = []
    mutation_ids: set[str] = set()
    phase_evidence: dict[str, str] = {}
    for index, phase_value in enumerate(phases):
        phase = _object(phase_value, f"phases[{index}]")
        phase_id = _text(phase.get("phase_id"), f"phases[{index}].phase_id")
        phase_ids.append(phase_id)
        mutation = phase.get("mutation")
        if not isinstance(mutation, bool):
            raise DesignValidationError(f"phases[{index}].mutation must be boolean")
        if mutation:
            mutation_ids.add(phase_id)
            _require_true(phase.get("requires_explicit_authorization"), f"phases[{index}].requires_explicit_authorization")
        phase_evidence[phase_id] = _text(phase.get("evidence_required"), f"phases[{index}].evidence_required")
    if phase_ids != REQUIRED_PHASE_ORDER:
        raise DesignValidationError("replacement phases are missing or out of order")
    if mutation_ids != MUTATION_PHASES:
        raise DesignValidationError("mutation phase classification changed unexpectedly")
    required_evidence_fragments = {
        "quiesce_and_deallocate_source": "PowerState/deallocated",
        "create_recovery_points": "same maintenance correlation",
        "isolated_snapshot_boot_rehearsal": "source VM remains deallocated",
        "remove_old_compute": "isolated boot rehearsal",
        "verify_preservation_boundary": "rehearsal evidence",
        "deploy_replacement_compute": "deleteOption Detach",
        "cleanup_temporary_recovery_resources": "deletion proof before deadline",
    }
    for phase_id, fragment in required_evidence_fragments.items():
        if fragment not in phase_evidence[phase_id]:
            raise DesignValidationError(f"{phase_id} evidence must include: {fragment}")

    # The immutable contract already sets zero compute overlap and requires cleanup.
    # This validator makes the transition consequence explicit: the rehearsal compute
    # boundary must be gone before replacement compute begins, while approved recovery
    # snapshots/disks may remain until final acceptance.
    rehearsal_index = phase_ids.index("isolated_snapshot_boot_rehearsal")
    replacement_index = phase_ids.index("deploy_replacement_compute")
    if rehearsal_index >= replacement_index:
        raise DesignValidationError("replacement compute cannot precede the isolated rehearsal")

    rollback = _object(contract.get("rollback"), "rollback")
    rollback_status = _text(rollback.get("status"), "rollback.status")
    if rollback_status != EXPECTED_ROLLBACK_STATUS:
        raise DesignValidationError("rollback must remain selected design-only state")
    _require_true(rollback.get("promotion_blocked"), "rollback.promotion_blocked")
    if rollback.get("strategy_id") != EXPECTED_ROLLBACK_STRATEGY or rollback.get("canonical_os_disk_name") != EXPECTED_OS_DISK or rollback.get("snapshot_name_prefix") != EXPECTED_ROLLBACK_SNAPSHOT_PREFIX:
        raise DesignValidationError("rollback identity changed")
    _require_false(rollback.get("preserve_old_os_disk_directly"), "rollback.preserve_old_os_disk_directly")
    if rollback.get("maximum_os_disk_snapshot_gib") != 64 or rollback.get("block_if_os_disk_exceeds_snapshot_gib") != 64:
        raise DesignValidationError("OS-disk snapshot ceiling changed")
    if _text_set(rollback.get("source_preflight_required"), "rollback.source_preflight_required") != REQUIRED_ROLLBACK_PREFLIGHT:
        raise DesignValidationError("rollback source preflight requirements changed")
    if _text_set(rollback.get("snapshot_verification_required"), "rollback.snapshot_verification_required") != REQUIRED_SNAPSHOT_VERIFICATION:
        raise DesignValidationError("snapshot verification requirements changed")

    recreation = _object(rollback.get("recreation_contract"), "rollback.recreation_contract")
    expected_recreation_values = {
        "managed_disk_create_option": "Copy", "managed_disk_source": "exact verified OS-disk snapshot",
        "vm_os_disk_create_option": "Attach", "recreated_os_disk_name": EXPECTED_OS_DISK,
        "recreated_vm_name": EXPECTED_TARGET, "attach_preserved_nic": EXPECTED_NIC,
        "preserved_nic_delete_option": "Detach", "attach_preserved_evidence_disk": EXPECTED_EVIDENCE_DISK,
        "preserved_evidence_disk_delete_option": "Detach",
    }
    for field, expected in expected_recreation_values.items():
        if recreation.get(field) != expected:
            raise DesignValidationError(f"rollback recreation contract changed: {field}")
    for field in ("re_read_attachment_delete_options_after_create", "verify_attachment_delete_options_before_failed_compute_deletion"):
        _require_true(recreation.get(field), f"rollback.recreation_contract.{field}")
    if _text_set(recreation.get("metadata_required"), "rollback.recreation_contract.metadata_required") != REQUIRED_RECREATION_METADATA:
        raise DesignValidationError("rollback recreation metadata requirements changed")
    if _text_set(recreation.get("acceptance_required"), "rollback.recreation_contract.acceptance_required") != REQUIRED_ROLLBACK_ACCEPTANCE:
        raise DesignValidationError("rollback acceptance requirements changed")

    _require_false(rollback.get("operationally_tested"), "rollback.operationally_tested")
    if rollback.get("independent_review_status") != EXPECTED_REVIEW_STATUS:
        raise DesignValidationError("rollback must remain pending independent re-review")
    for field in ("decision", "before_old_vm_deletion", "after_old_vm_deletion", "evidence_disk_rule"):
        _text(rollback.get(field), f"rollback.{field}")

    blockers = _text_set(contract.get("unresolved_blockers"), "unresolved_blockers")
    for required in (
        "operational proof of the selected OS-disk snapshot recreation rollback",
        "fake-Azure-CLI-tested recovery-point and isolated-rehearsal implementation",
        "fresh authenticated subscription-specific cost and quota preflight",
        "renewed independent operations-and-recovery approval",
    ):
        if required not in blockers:
            raise DesignValidationError(f"required unresolved blocker missing: {required}")

    return {
        "schema_version": "servicetracer.collector-replacement-design-validation.v1",
        "design_valid": True,
        "design_state": "fail_closed",
        "candidate_workflow": candidate_workflow,
        "active_workflow": active_workflow,
        "dispatch_authorized": False,
        "azure_mutations_authorized": False,
        "promotion_ready": False,
        "evidence_anchor": {"planner_run_id": EXPECTED_PLANNER_RUN, "planner_artifact_sha256": EXPECTED_PLANNER_DIGEST},
        "target": {"collector_vm": EXPECTED_TARGET, "collector_os_disk": EXPECTED_OS_DISK, "exact_future_confirmation": EXPECTED_CONFIRMATION},
        "phase_order": phase_ids,
        "mutation_phase_ids": sorted(mutation_ids),
        "cost_controls": cost,
        "rollback_status": rollback_status,
        "rollback_strategy": EXPECTED_ROLLBACK_STRATEGY,
        "rollback_review_status": EXPECTED_REVIEW_STATUS,
        "canonical_os_disk_name": EXPECTED_OS_DISK,
        "rollback_operationally_tested": False,
        "consistency_boundary_required": True,
        "consistency_actions_exact_order": EXPECTED_CONSISTENCY_ACTIONS,
        "isolated_snapshot_boot_rehearsal_required": True,
        "rehearsal_compute_deallocated_before_replacement": True,
        "rehearsal_temporary_compute_removed_before_replacement": True,
        "rehearsal_teardown_before_phase": "deploy_replacement_compute",
        "rehearsal_teardown_evidence_required": REHEARSAL_TEARDOWN_EVIDENCE,
        "approved_temporary_recovery_artifacts_may_remain": ["verified OS-disk snapshot", "verified evidence-disk snapshot", "approved temporary recovery disk"],
        "production_attachment_delete_option": "Detach",
        "unresolved_blockers": sorted(blockers),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and render the fail-closed collector replacement design.")
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    contract = json.loads(args.contract.read_text(encoding="utf-8"))
    if not isinstance(contract, dict):
        raise DesignValidationError("contract root must be an object")
    result = validate_contract(contract)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "collector replacement execution design validated: exact ordered quiescence, "
        "consistency-bound snapshots, isolated Trusted Launch boot rehearsal, mandatory "
        "rehearsal teardown before replacement compute, Copy/Attach separation, "
        "Detach-preserved production attachments, fail-closed and Azure mutations unauthorized"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
