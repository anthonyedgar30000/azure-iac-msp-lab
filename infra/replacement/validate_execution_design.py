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
EXPECTED_PLANNER_DIGEST = (
    "76f3b44e6e97e906dac6d62eeb212a6bc55265e77271a030b9c45b0cacf55637"
)
EXPECTED_TARGET = "vm-stcollector-mst-dev"
EXPECTED_NIC = "nic-stcollector-mst-dev"
EXPECTED_EVIDENCE_DISK = "disk-stcollector-evidence-mst-dev"
EXPECTED_OS_DISK = "disk-stcollector-os-mst-dev"
EXPECTED_CONFIRMATION = (
    "REPLACE:rg-servicetracer-dev-westus2:vm-stcollector-mst-dev"
)
EXPECTED_ROLLBACK_STATUS = "strategy_selected_design_only"
EXPECTED_ROLLBACK_STRATEGY = "os_disk_snapshot_recreate_canonical_name"
EXPECTED_REVIEW_STATUS = "changes_addressed_re_review_pending"
EXPECTED_ROLLBACK_SNAPSHOT_PREFIX = "snap-stcollector-os-rollback-mst-dev-"
EXPECTED_BINDING_FIELDS = {
    "maintenance_correlation_id",
    "final_evidence_checkpoint_id",
    "final_evidence_checkpoint_sha256",
}
REQUIRED_ROLLBACK_PREFLIGHT = {
    "source OS-disk resource ID",
    "disk size GiB",
    "disk SKU",
    "OS type",
    "Hyper-V generation",
    "security profile and Trusted Launch compatibility",
    "encryption configuration and disk encryption set when present",
    "availability zone when present",
    "network access policy",
    "public network access state",
    "OS-disk delete option",
}
REQUIRED_SNAPSHOT_VERIFICATION = {
    "provisioning state succeeded",
    "source OS-disk resource ID matches",
    "snapshot size matches source disk",
    "Hyper-V generation and OS type are preserved",
    "network access policy is DenyAll",
    "public network access is Disabled",
    "maintenance correlation ID matches the consistency boundary",
    "final evidence checkpoint ID matches the consistency boundary",
    "final evidence checkpoint SHA-256 matches the consistency boundary",
    "execution, owner, and cleanup-deadline tags are present",
    "cleanup deadline is no more than 24 hours after creation",
}
REQUIRED_RECREATION_METADATA = {
    "disk SKU",
    "OS type",
    "Hyper-V generation",
    "security profile and Trusted Launch settings",
    "encryption configuration and disk encryption set when present",
    "availability zone when present",
    "network access policy",
    "public network access state",
    "OS-disk delete option",
}
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


def _text_set(value: Any, field: str) -> set[str]:
    return {_text(item, f"{field}[]") for item in _list(value, field)}


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
        _require_false(activation.get(field), f"activation.{field}")
    _require_true(
        activation.get("promotion_requires_separate_pull_request"),
        "activation.promotion_requires_separate_pull_request",
    )
    reviews = _text_set(
        activation.get("promotion_requires_independent_reviews"),
        "activation.promotion_requires_independent_reviews",
    )
    if reviews != {
        "evidence-quality",
        "operations-and-recovery",
        "security-and-identity",
        "azure-cost",
    }:
        raise DesignValidationError("all four independent review lenses are required")

    evidence = _object(contract.get("evidence_anchor"), "evidence_anchor")
    if evidence.get("planner_run_id") != EXPECTED_PLANNER_RUN:
        raise DesignValidationError("planner run ID does not match promoted evidence")
    if evidence.get("planner_artifact_sha256") != EXPECTED_PLANNER_DIGEST:
        raise DesignValidationError("planner artifact digest does not match promoted evidence")
    _require_false(
        evidence.get("planner_azure_mutations_authorized"),
        "evidence_anchor.planner_azure_mutations_authorized",
    )
    _require_false(
        evidence.get("planner_azure_mutations_performed"),
        "evidence_anchor.planner_azure_mutations_performed",
    )

    target = _object(contract.get("target"), "target")
    if target.get("collector_vm") != EXPECTED_TARGET:
        raise DesignValidationError("unexpected collector VM target")
    if target.get("collector_nic") != EXPECTED_NIC:
        raise DesignValidationError("unexpected collector NIC")
    if target.get("collector_evidence_disk") != EXPECTED_EVIDENCE_DISK:
        raise DesignValidationError("unexpected evidence disk")
    if target.get("collector_os_disk") != EXPECTED_OS_DISK:
        raise DesignValidationError("unexpected canonical collector OS-disk name")
    if target.get("exact_future_confirmation") != EXPECTED_CONFIRMATION:
        raise DesignValidationError("unexpected replacement confirmation phrase")
    if target.get("evidence_mount") != "/var/lib/servicetracer":
        raise DesignValidationError("unexpected evidence mount")

    cost = _object(contract.get("cost_controls"), "cost_controls")
    if cost.get("currency") != "CAD":
        raise DesignValidationError("cost controls must be denominated in CAD")
    if cost.get("review_status") != "conditionally_approved_planning_estimate":
        raise DesignValidationError("cost review must remain planning-only")
    if cost.get("reviewed_planning_estimate") != 4.0:
        raise DesignValidationError("reviewed planning estimate must remain CAD 4")
    if cost.get("renewed_approval_threshold") != 4.0:
        raise DesignValidationError("renewed cost approval threshold must remain CAD 4")
    if cost.get("maximum_declared_temporary_cost") != 10.0:
        raise DesignValidationError("hard temporary cost ceiling must remain CAD 10")
    if cost.get("maximum_snapshots") != 2:
        raise DesignValidationError("the selected rollback requires exactly two snapshots")
    if cost.get("maximum_total_snapshot_gib") != 96:
        raise DesignValidationError("snapshot capacity ceiling must remain 96 GiB")
    if cost.get("maximum_compute_overlap_minutes") != 0:
        raise DesignValidationError("old and rehearsal or replacement compute may not overlap")
    if cost.get("maximum_isolated_restore_rehearsal_compute_hours") != 4:
        raise DesignValidationError("isolated rehearsal compute must be capped at four hours")
    if cost.get("maximum_recovery_resource_retention_hours") != 24:
        raise DesignValidationError("temporary recovery resources must be capped at 24 hours")
    _require_true(
        cost.get("fresh_authenticated_subscription_cost_preflight_required"),
        "cost_controls.fresh_authenticated_subscription_cost_preflight_required",
    )
    _require_true(cost.get("cleanup_owner_required"), "cost_controls.cleanup_owner_required")
    _require_true(
        cost.get("cleanup_deadline_required"), "cost_controls.cleanup_deadline_required"
    )
    _require_false(
        cost.get("azure_budget_or_alert_mutation_allowed"),
        "cost_controls.azure_budget_or_alert_mutation_allowed",
    )

    gates = _text_set(contract.get("required_preflight_gates"), "required_preflight_gates")
    if not any("subscription-specific pricing" in gate for gate in gates):
        raise DesignValidationError("fresh subscription-specific cost preflight is missing")
    if not any("OS-disk identity" in gate and "delete option" in gate for gate in gates):
        raise DesignValidationError("OS-disk recreation metadata is incomplete")

    consistency = _object(contract.get("consistency_boundary"), "consistency_boundary")
    if consistency.get("phase_id") != "quiesce_and_deallocate_source":
        raise DesignValidationError("unexpected consistency-boundary phase")
    actions = _text_set(consistency.get("ordered_actions"), "consistency_boundary.ordered_actions")
    for required in (
        "stop accepting new collector writes",
        "drain in-flight collector writes",
        "flush pending evidence writes to the mounted evidence filesystem",
        "record final evidence checkpoint identifier and SHA-256",
        "record maintenance correlation identifier",
        "verify guest shutdown",
        "deallocate the source VM",
        "verify Azure PowerState/deallocated",
    ):
        if required not in actions:
            raise DesignValidationError(f"consistency boundary is missing: {required}")
    if consistency.get("source_power_state_required") != "PowerState/deallocated":
        raise DesignValidationError("source VM must be deallocated before snapshots")
    for field in (
        "final_evidence_checkpoint_id_required",
        "final_evidence_checkpoint_sha256_required",
        "maintenance_correlation_id_required",
        "both_snapshots_must_share_binding",
    ):
        _require_true(consistency.get(field), f"consistency_boundary.{field}")
    _require_false(
        consistency.get("snapshot_capture_before_boundary_allowed"),
        "consistency_boundary.snapshot_capture_before_boundary_allowed",
    )
    if _text_set(
        consistency.get("snapshot_binding_fields"),
        "consistency_boundary.snapshot_binding_fields",
    ) != EXPECTED_BINDING_FIELDS:
        raise DesignValidationError("snapshot binding fields changed")

    rehearsal = _object(contract.get("isolated_restore_rehearsal"), "isolated_restore_rehearsal")
    if rehearsal.get("phase_id") != "isolated_snapshot_boot_rehearsal":
        raise DesignValidationError("unexpected isolated rehearsal phase")
    if rehearsal.get("required_before_phase") != "remove_old_compute":
        raise DesignValidationError("isolated rehearsal must precede old-compute removal")
    if rehearsal.get("source_snapshot") != "exact verified OS-disk snapshot":
        raise DesignValidationError("isolated rehearsal must use the exact verified snapshot")
    if rehearsal.get("temporary_os_disk_create_option") != "Copy":
        raise DesignValidationError("isolated rehearsal disk must use Copy")
    if rehearsal.get("temporary_vm_os_disk_create_option") != "Attach":
        raise DesignValidationError("isolated rehearsal VM must use Attach")
    if rehearsal.get("security_profile_source") != "recorded source Trusted Launch profile":
        raise DesignValidationError("isolated rehearsal must use the recorded Trusted Launch profile")
    for field in ("source_vm_must_remain_deallocated", "cleanup_required"):
        _require_true(rehearsal.get(field), f"isolated_restore_rehearsal.{field}")
    for field in (
        "production_nic_attached",
        "production_evidence_disk_attached",
        "operational_rollback_proof",
    ):
        _require_false(rehearsal.get(field), f"isolated_restore_rehearsal.{field}")
    if rehearsal.get("maximum_compute_hours") != 4:
        raise DesignValidationError("isolated rehearsal compute cap changed")
    if rehearsal.get("maximum_retention_hours") != 24:
        raise DesignValidationError("isolated rehearsal retention cap changed")
    if _text_set(
        rehearsal.get("required_proof"), "isolated_restore_rehearsal.required_proof"
    ) != REQUIRED_REHEARSAL_PROOF:
        raise DesignValidationError("isolated rehearsal proof requirements changed")

    attachments = _object(
        contract.get("replacement_vm_attachment_contract"),
        "replacement_vm_attachment_contract",
    )
    if attachments.get("nic_resource") != EXPECTED_NIC:
        raise DesignValidationError("replacement NIC resource changed")
    if attachments.get("evidence_disk_resource") != EXPECTED_EVIDENCE_DISK:
        raise DesignValidationError("replacement evidence disk resource changed")
    if attachments.get("os_disk_resource") != EXPECTED_OS_DISK:
        raise DesignValidationError("replacement OS disk resource changed")
    if attachments.get("nic_delete_option") != "Detach":
        raise DesignValidationError("replacement NIC must use deleteOption Detach")
    if attachments.get("evidence_disk_delete_option") != "Detach":
        raise DesignValidationError("replacement evidence disk must use deleteOption Detach")
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
            _require_true(
                phase.get("requires_explicit_authorization"),
                f"phases[{index}].requires_explicit_authorization",
            )
        phase_evidence[phase_id] = _text(
            phase.get("evidence_required"), f"phases[{index}].evidence_required"
        )
    if phase_ids != REQUIRED_PHASE_ORDER:
        raise DesignValidationError("replacement phases are missing or out of order")
    if mutation_ids != MUTATION_PHASES:
        raise DesignValidationError("mutation phase classification changed unexpectedly")
    if "PowerState/deallocated" not in phase_evidence["quiesce_and_deallocate_source"]:
        raise DesignValidationError("quiesce phase must verify deallocation")
    if "same maintenance correlation" not in phase_evidence["create_recovery_points"]:
        raise DesignValidationError("snapshots must share the maintenance binding")
    if "exact snapshot" not in phase_evidence["isolated_snapshot_boot_rehearsal"]:
        raise DesignValidationError("isolated rehearsal must use the exact snapshot")
    if "isolated boot rehearsal" not in phase_evidence["remove_old_compute"]:
        raise DesignValidationError("old compute removal must require isolated boot proof")
    if "deleteOption Detach" not in phase_evidence["deploy_replacement_compute"]:
        raise DesignValidationError("replacement attachments must use Detach")

    rollback = _object(contract.get("rollback"), "rollback")
    rollback_status = _text(rollback.get("status"), "rollback.status")
    if rollback_status != EXPECTED_ROLLBACK_STATUS:
        raise DesignValidationError("rollback must remain selected design-only state")
    _require_true(rollback.get("promotion_blocked"), "rollback.promotion_blocked")
    if rollback.get("strategy_id") != EXPECTED_ROLLBACK_STRATEGY:
        raise DesignValidationError("unexpected rollback strategy")
    if rollback.get("canonical_os_disk_name") != EXPECTED_OS_DISK:
        raise DesignValidationError("rollback must recreate the canonical OS-disk name")
    if rollback.get("snapshot_name_prefix") != EXPECTED_ROLLBACK_SNAPSHOT_PREFIX:
        raise DesignValidationError("unexpected OS-disk snapshot prefix")
    _require_false(
        rollback.get("preserve_old_os_disk_directly"),
        "rollback.preserve_old_os_disk_directly",
    )
    if rollback.get("maximum_os_disk_snapshot_gib") != 64:
        raise DesignValidationError("OS-disk snapshot ceiling must remain 64 GiB")
    if rollback.get("block_if_os_disk_exceeds_snapshot_gib") != 64:
        raise DesignValidationError("OS-disk blocker must remain 64 GiB")
    if _text_set(
        rollback.get("source_preflight_required"), "rollback.source_preflight_required"
    ) != REQUIRED_ROLLBACK_PREFLIGHT:
        raise DesignValidationError("rollback source preflight requirements changed")
    if _text_set(
        rollback.get("snapshot_verification_required"),
        "rollback.snapshot_verification_required",
    ) != REQUIRED_SNAPSHOT_VERIFICATION:
        raise DesignValidationError("snapshot verification requirements changed")

    recreation = _object(rollback.get("recreation_contract"), "rollback.recreation_contract")
    if recreation.get("managed_disk_create_option") != "Copy":
        raise DesignValidationError("snapshot-to-managed-disk operation must use Copy")
    if recreation.get("managed_disk_source") != "exact verified OS-disk snapshot":
        raise DesignValidationError("rollback disk must use the exact verified snapshot")
    if recreation.get("vm_os_disk_create_option") != "Attach":
        raise DesignValidationError("specialized OS disk must be attached to the VM")
    if recreation.get("recreated_os_disk_name") != EXPECTED_OS_DISK:
        raise DesignValidationError("recreated OS disk must use the canonical name")
    if recreation.get("recreated_vm_name") != EXPECTED_TARGET:
        raise DesignValidationError("rollback must recreate the collector VM name")
    if recreation.get("attach_preserved_nic") != EXPECTED_NIC:
        raise DesignValidationError("rollback must attach the preserved NIC")
    if recreation.get("preserved_nic_delete_option") != "Detach":
        raise DesignValidationError("rollback NIC must use deleteOption Detach")
    if recreation.get("attach_preserved_evidence_disk") != EXPECTED_EVIDENCE_DISK:
        raise DesignValidationError("rollback must attach the preserved evidence disk")
    if recreation.get("preserved_evidence_disk_delete_option") != "Detach":
        raise DesignValidationError("rollback evidence disk must use deleteOption Detach")
    for field in (
        "re_read_attachment_delete_options_after_create",
        "verify_attachment_delete_options_before_failed_compute_deletion",
    ):
        _require_true(recreation.get(field), f"rollback.recreation_contract.{field}")
    if _text_set(
        recreation.get("metadata_required"),
        "rollback.recreation_contract.metadata_required",
    ) != REQUIRED_RECREATION_METADATA:
        raise DesignValidationError("rollback recreation metadata requirements changed")
    if _text_set(
        recreation.get("acceptance_required"),
        "rollback.recreation_contract.acceptance_required",
    ) != REQUIRED_ROLLBACK_ACCEPTANCE:
        raise DesignValidationError("rollback acceptance requirements changed")

    _require_false(rollback.get("operationally_tested"), "rollback.operationally_tested")
    if rollback.get("independent_review_status") != EXPECTED_REVIEW_STATUS:
        raise DesignValidationError("rollback must remain pending independent re-review")
    _text(rollback.get("decision"), "rollback.decision")
    _text(rollback.get("before_old_vm_deletion"), "rollback.before_old_vm_deletion")
    _text(rollback.get("after_old_vm_deletion"), "rollback.after_old_vm_deletion")
    _text(rollback.get("evidence_disk_rule"), "rollback.evidence_disk_rule")

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
        "mutation_phase_ids": sorted(mutation_ids),
        "cost_controls": cost,
        "rollback_status": rollback_status,
        "rollback_strategy": EXPECTED_ROLLBACK_STRATEGY,
        "rollback_review_status": EXPECTED_REVIEW_STATUS,
        "canonical_os_disk_name": EXPECTED_OS_DISK,
        "rollback_operationally_tested": False,
        "consistency_boundary_required": True,
        "isolated_snapshot_boot_rehearsal_required": True,
        "production_attachment_delete_option": "Detach",
        "unresolved_blockers": sorted(blockers),
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
        "consistency-bound snapshots, isolated Trusted Launch boot rehearsal, "
        "Copy/Attach separation, Detach-preserved production attachments, "
        "fail-closed and Azure mutations unauthorized"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
