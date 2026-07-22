from __future__ import annotations

import copy
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "infra" / "replacement" / "collector-replacement-contract.json"
VALIDATOR_PATH = ROOT / "infra" / "replacement" / "validate_execution_design.py"
CANDIDATE_WORKFLOW_PATH = ROOT / "infra" / "workflow-designs" / "collector-replacement-execution.yml"
ACTIVE_WORKFLOW_PATH = ROOT / ".github" / "workflows" / "collector-replacement-execution.yml"
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
EXPECTED_TEARDOWN_REMOVE_RESOURCES = {
    "temporary rehearsal VM",
    "temporary isolated NIC",
}
EXPECTED_RETAINED_ARTIFACTS = {
    "verified OS-disk snapshot",
    "verified evidence-disk snapshot",
    "approved temporary recovery disk",
}


class CollectorReplacementExecutionDesignTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        self.workflow = CANDIDATE_WORKFLOW_PATH.read_text(encoding="utf-8")

    def _validate(self, contract: dict) -> dict:
        namespace: dict[str, object] = {
            "__name__": "collector_replacement_execution_design_validator"
        }
        exec(VALIDATOR_PATH.read_text(encoding="utf-8"), namespace)
        return namespace["validate_contract"](contract)  # type: ignore[operator]

    def test_candidate_is_not_an_active_github_workflow(self) -> None:
        self.assertTrue(CANDIDATE_WORKFLOW_PATH.is_file())
        self.assertFalse(ACTIVE_WORKFLOW_PATH.exists())
        self.assertEqual(
            self.contract["activation"]["candidate_workflow"],
            "infra/workflow-designs/collector-replacement-execution.yml",
        )
        self.assertFalse(self.contract["activation"]["active_workflow_present"])

    def test_workflow_design_fails_closed_before_azure_authentication(self) -> None:
        self.assertLess(
            self.workflow.index("Fail closed before Azure authentication or mutation"),
            self.workflow.index("Candidate replacement phase contract"),
        )
        self.assertIn("DESIGN_ONLY_BLOCKER: 'true'", self.workflow)
        self.assertIn("exit 64", self.workflow)
        self.assertNotIn("uses: azure/login@", self.workflow)

    def test_candidate_contains_no_azure_mutation_commands(self) -> None:
        for forbidden in (
            "az vm delete",
            "az vm deallocate",
            "az snapshot create",
            "az disk create",
            "az disk update",
            "az resource update",
            "az deployment group create",
            "az role assignment create",
            "az network nic delete",
        ):
            self.assertNotIn(forbidden, self.workflow)

    def test_candidate_phase_contract_matches_authoritative_contract_order(self) -> None:
        workflow_phase_ids = re.findall(r"run:\s+echo\s+([a-z0-9_]+)", self.workflow)
        contract_phase_ids = [phase["phase_id"] for phase in self.contract["phases"]]
        self.assertEqual(workflow_phase_ids, contract_phase_ids)

    def test_contract_validates_as_fail_closed_and_not_promotion_ready(self) -> None:
        result = self._validate(self.contract)
        self.assertEqual(
            self.contract["schema_version"],
            "servicetracer.collector-replacement-execution-design.v2",
        )
        self.assertTrue(result["design_valid"])
        self.assertEqual(result["design_state"], "fail_closed")
        self.assertFalse(result["dispatch_authorized"])
        self.assertFalse(result["azure_mutations_authorized"])
        self.assertFalse(result["promotion_ready"])
        self.assertEqual(result["rollback_status"], "strategy_selected_design_only")
        self.assertEqual(
            result["rollback_review_status"],
            "contract_amendment_re_review_pending",
        )
        self.assertFalse(result["rollback_operationally_tested"])

    def test_contract_is_pinned_to_promoted_planner_evidence(self) -> None:
        result = self._validate(self.contract)
        self.assertEqual(result["evidence_anchor"]["planner_run_id"], 29856203054)
        self.assertEqual(
            result["evidence_anchor"]["planner_artifact_sha256"],
            "76f3b44e6e97e906dac6d62eeb212a6bc55265e77271a030b9c45b0cacf55637",
        )
        self.assertEqual(
            result["target"]["exact_future_confirmation"],
            "REPLACE:rg-servicetracer-dev-westus2:vm-stcollector-mst-dev",
        )

    def test_quiesce_and_deallocate_precedes_both_snapshots(self) -> None:
        result = self._validate(self.contract)
        phases = result["phase_order"]
        self.assertLess(
            phases.index("quiesce_and_deallocate_source"),
            phases.index("create_recovery_points"),
        )
        boundary = self.contract["consistency_boundary"]
        self.assertEqual(boundary["source_power_state_required"], "PowerState/deallocated")
        self.assertTrue(boundary["both_snapshots_must_share_binding"])
        self.assertFalse(boundary["snapshot_capture_before_boundary_allowed"])
        self.assertEqual(
            set(boundary["snapshot_binding_fields"]),
            {
                "maintenance_correlation_id",
                "final_evidence_checkpoint_id",
                "final_evidence_checkpoint_sha256",
            },
        )

    def test_quiesce_actions_are_exact_and_ordered(self) -> None:
        result = self._validate(self.contract)
        self.assertEqual(
            self.contract["consistency_boundary"]["ordered_actions"],
            EXPECTED_CONSISTENCY_ACTIONS,
        )
        self.assertEqual(
            result["consistency_actions_exact_order"],
            EXPECTED_CONSISTENCY_ACTIONS,
        )

    def test_validator_rejects_reordered_quiesce_actions(self) -> None:
        modified = copy.deepcopy(self.contract)
        actions = modified["consistency_boundary"]["ordered_actions"]
        actions[2], actions[7] = actions[7], actions[2]
        with self.assertRaises(Exception):
            self._validate(modified)

    def test_validator_rejects_missing_collector_service_stop(self) -> None:
        modified = copy.deepcopy(self.contract)
        modified["consistency_boundary"]["ordered_actions"].remove(
            "stop the collector service"
        )
        with self.assertRaises(Exception):
            self._validate(modified)

    def test_validator_rejects_snapshot_capture_before_consistency_boundary(self) -> None:
        modified = copy.deepcopy(self.contract)
        modified["consistency_boundary"]["snapshot_capture_before_boundary_allowed"] = True
        with self.assertRaises(Exception):
            self._validate(modified)

    def test_validator_rejects_missing_checkpoint_binding(self) -> None:
        modified = copy.deepcopy(self.contract)
        modified["consistency_boundary"]["snapshot_binding_fields"].remove(
            "final_evidence_checkpoint_sha256"
        )
        with self.assertRaises(Exception):
            self._validate(modified)

    def test_isolated_exact_snapshot_boot_rehearsal_precedes_teardown_and_old_compute_removal(self) -> None:
        result = self._validate(self.contract)
        phases = result["phase_order"]
        self.assertLess(
            phases.index("isolated_snapshot_boot_rehearsal"),
            phases.index("teardown_isolated_rehearsal"),
        )
        self.assertLess(
            phases.index("teardown_isolated_rehearsal"),
            phases.index("remove_old_compute"),
        )
        rehearsal = self.contract["isolated_restore_rehearsal"]
        self.assertEqual(rehearsal["source_snapshot"], "exact verified OS-disk snapshot")
        self.assertEqual(rehearsal["temporary_os_disk_create_option"], "Copy")
        self.assertEqual(rehearsal["temporary_vm_os_disk_create_option"], "Attach")
        self.assertTrue(rehearsal["source_vm_must_remain_deallocated"])
        self.assertFalse(rehearsal["production_nic_attached"])
        self.assertFalse(rehearsal["production_evidence_disk_attached"])
        self.assertFalse(rehearsal["operational_rollback_proof"])

    def test_rehearsal_teardown_is_contract_backed_before_old_compute_removal(self) -> None:
        result = self._validate(self.contract)
        teardown = self.contract["rehearsal_teardown"]
        self.assertEqual(teardown["phase_id"], "teardown_isolated_rehearsal")
        self.assertEqual(teardown["required_before_phase"], "remove_old_compute")
        self.assertEqual(
            teardown["rehearsal_vm_power_state_required"],
            "PowerState/deallocated",
        )
        self.assertEqual(set(teardown["remove_resources"]), EXPECTED_TEARDOWN_REMOVE_RESOURCES)
        self.assertEqual(
            set(teardown["allowed_retained_artifacts"]),
            EXPECTED_RETAINED_ARTIFACTS,
        )
        self.assertFalse(teardown["unapproved_retained_artifacts_allowed"])
        self.assertEqual(teardown["maximum_running_compute_overlap_minutes"], 0)
        self.assertTrue(result["rehearsal_compute_deallocated_before_replacement"])
        self.assertTrue(result["rehearsal_temporary_compute_removed_before_replacement"])
        self.assertEqual(result["rehearsal_teardown_before_phase"], "remove_old_compute")
        self.assertEqual(
            set(result["approved_temporary_recovery_artifacts_may_remain"]),
            EXPECTED_RETAINED_ARTIFACTS,
        )

    def test_validator_rejects_rehearsal_compute_overlap(self) -> None:
        modified = copy.deepcopy(self.contract)
        modified["cost_controls"]["maximum_compute_overlap_minutes"] = 1
        with self.assertRaises(Exception):
            self._validate(modified)
        modified = copy.deepcopy(self.contract)
        modified["rehearsal_teardown"]["maximum_running_compute_overlap_minutes"] = 1
        with self.assertRaises(Exception):
            self._validate(modified)

    def test_validator_rejects_missing_rehearsal_cleanup_boundary(self) -> None:
        modified = copy.deepcopy(self.contract)
        modified["isolated_restore_rehearsal"]["cleanup_required"] = False
        with self.assertRaises(Exception):
            self._validate(modified)

    def test_validator_rejects_missing_rehearsal_deallocation_requirement(self) -> None:
        modified = copy.deepcopy(self.contract)
        modified["rehearsal_teardown"]["rehearsal_vm_power_state_required"] = "PowerState/running"
        with self.assertRaises(Exception):
            self._validate(modified)

    def test_validator_rejects_missing_temporary_compute_removal_requirement(self) -> None:
        modified = copy.deepcopy(self.contract)
        modified["rehearsal_teardown"]["remove_resources"].remove(
            "temporary isolated NIC"
        )
        with self.assertRaises(Exception):
            self._validate(modified)

    def test_validator_rejects_teardown_boundary_after_replacement_deployment(self) -> None:
        modified = copy.deepcopy(self.contract)
        modified["rehearsal_teardown"]["required_before_phase"] = (
            "cleanup_temporary_recovery_resources"
        )
        with self.assertRaises(Exception):
            self._validate(modified)

    def test_validator_rejects_unapproved_retained_artifact(self) -> None:
        modified = copy.deepcopy(self.contract)
        modified["rehearsal_teardown"]["allowed_retained_artifacts"].append(
            "temporary rehearsal VM"
        )
        with self.assertRaises(Exception):
            self._validate(modified)
        modified = copy.deepcopy(self.contract)
        modified["rehearsal_teardown"]["unapproved_retained_artifacts_allowed"] = True
        with self.assertRaises(Exception):
            self._validate(modified)

    def test_validator_rejects_missing_teardown_phase(self) -> None:
        modified = copy.deepcopy(self.contract)
        modified["phases"] = [
            phase
            for phase in modified["phases"]
            if phase["phase_id"] != "teardown_isolated_rehearsal"
        ]
        with self.assertRaises(Exception):
            self._validate(modified)

    def test_validator_rejects_non_exact_rehearsal_snapshot(self) -> None:
        modified = copy.deepcopy(self.contract)
        modified["isolated_restore_rehearsal"]["source_snapshot"] = "latest snapshot"
        with self.assertRaises(Exception):
            self._validate(modified)

    def test_validator_rejects_production_attachment_during_rehearsal(self) -> None:
        for field in ("production_nic_attached", "production_evidence_disk_attached"):
            modified = copy.deepcopy(self.contract)
            modified["isolated_restore_rehearsal"][field] = True
            with self.assertRaises(Exception):
                self._validate(modified)

    def test_rollback_separates_copy_from_attach(self) -> None:
        result = self._validate(self.contract)
        recreation = self.contract["rollback"]["recreation_contract"]
        self.assertEqual(
            result["rollback_strategy"],
            "os_disk_snapshot_recreate_canonical_name",
        )
        self.assertEqual(recreation["managed_disk_create_option"], "Copy")
        self.assertEqual(recreation["vm_os_disk_create_option"], "Attach")
        self.assertEqual(
            recreation["managed_disk_source"],
            "exact verified OS-disk snapshot",
        )
        self.assertEqual(
            recreation["recreated_os_disk_name"],
            "disk-stcollector-os-mst-dev",
        )

    def test_validator_rejects_from_image_for_snapshot_restore(self) -> None:
        modified = copy.deepcopy(self.contract)
        modified["rollback"]["recreation_contract"]["managed_disk_create_option"] = (
            "FromImage"
        )
        with self.assertRaises(Exception):
            self._validate(modified)

    def test_validator_rejects_missing_attach_semantics(self) -> None:
        modified = copy.deepcopy(self.contract)
        modified["rollback"]["recreation_contract"]["vm_os_disk_create_option"] = (
            "FromImage"
        )
        with self.assertRaises(Exception):
            self._validate(modified)

    def test_validator_rejects_recreation_metadata_drift(self) -> None:
        modified = copy.deepcopy(self.contract)
        modified["rollback"]["recreation_contract"]["metadata_required"].remove(
            "disk SKU"
        )
        with self.assertRaises(Exception):
            self._validate(modified)

    def test_replacement_and_rollback_preserve_production_attachments(self) -> None:
        replacement = self.contract["replacement_vm_attachment_contract"]
        rollback = self.contract["rollback"]["recreation_contract"]
        self.assertEqual(replacement["nic_delete_option"], "Detach")
        self.assertEqual(replacement["evidence_disk_delete_option"], "Detach")
        self.assertTrue(replacement["verify_after_vm_create"])
        self.assertTrue(replacement["verify_before_failed_compute_deletion"])
        self.assertEqual(rollback["preserved_nic_delete_option"], "Detach")
        self.assertEqual(rollback["preserved_evidence_disk_delete_option"], "Detach")
        self.assertTrue(rollback["re_read_attachment_delete_options_after_create"])
        self.assertTrue(rollback["verify_attachment_delete_options_before_failed_compute_deletion"])

    def test_validator_rejects_delete_semantics_for_preserved_attachments(self) -> None:
        for object_name, field in (
            ("replacement_vm_attachment_contract", "nic_delete_option"),
            ("replacement_vm_attachment_contract", "evidence_disk_delete_option"),
        ):
            modified = copy.deepcopy(self.contract)
            modified[object_name][field] = "Delete"
            with self.assertRaises(Exception):
                self._validate(modified)
        for field in (
            "preserved_nic_delete_option",
            "preserved_evidence_disk_delete_option",
        ):
            modified = copy.deepcopy(self.contract)
            modified["rollback"]["recreation_contract"][field] = "Delete"
            with self.assertRaises(Exception):
                self._validate(modified)

    def test_cost_controls_preserve_reviewed_boundary(self) -> None:
        cost = self.contract["cost_controls"]
        self.assertEqual(cost["currency"], "CAD")
        self.assertEqual(cost["reviewed_planning_estimate"], 4.0)
        self.assertEqual(cost["renewed_approval_threshold"], 4.0)
        self.assertEqual(cost["maximum_declared_temporary_cost"], 10.0)
        self.assertEqual(cost["maximum_snapshots"], 2)
        self.assertEqual(cost["maximum_total_snapshot_gib"], 96)
        self.assertEqual(cost["maximum_compute_overlap_minutes"], 0)
        self.assertEqual(cost["maximum_isolated_restore_rehearsal_compute_hours"], 4)
        self.assertEqual(cost["maximum_recovery_resource_retention_hours"], 24)
        self.assertTrue(cost["fresh_authenticated_subscription_cost_preflight_required"])
        self.assertFalse(cost["azure_budget_or_alert_mutation_allowed"])

    def test_every_mutation_phase_requires_explicit_authorization(self) -> None:
        for phase in self.contract["phases"]:
            if phase["mutation"]:
                self.assertTrue(
                    phase["requires_explicit_authorization"],
                    phase["phase_id"],
                )

    def test_validator_rejects_authorization_in_design_branch(self) -> None:
        modified = copy.deepcopy(self.contract)
        modified["activation"]["azure_mutations_authorized"] = True
        with self.assertRaises(Exception):
            self._validate(modified)

    def test_validator_rejects_false_operational_verification_claim(self) -> None:
        modified = copy.deepcopy(self.contract)
        modified["rollback"]["operationally_tested"] = True
        with self.assertRaises(Exception):
            self._validate(modified)

    def test_validator_rejects_missing_required_phase(self) -> None:
        modified = copy.deepcopy(self.contract)
        modified["phases"] = [
            phase
            for phase in modified["phases"]
            if phase["phase_id"] != "isolated_snapshot_boot_rehearsal"
        ]
        with self.assertRaises(Exception):
            self._validate(modified)

    def test_cli_renders_deterministic_non_authorizing_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "design-validation.json"
            result = subprocess.run(
                [
                    "python",
                    str(VALIDATOR_PATH),
                    "--contract",
                    str(CONTRACT_PATH),
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            rendered = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(
                rendered["schema_version"],
                "servicetracer.collector-replacement-design-validation.v2",
            )
            self.assertTrue(rendered["design_valid"])
            self.assertFalse(rendered["dispatch_authorized"])
            self.assertFalse(rendered["azure_mutations_authorized"])
            self.assertFalse(rendered["promotion_ready"])
            self.assertTrue(rendered["consistency_boundary_required"])
            self.assertTrue(rendered["isolated_snapshot_boot_rehearsal_required"])
            self.assertTrue(rendered["rehearsal_compute_deallocated_before_replacement"])
            self.assertTrue(
                rendered["rehearsal_temporary_compute_removed_before_replacement"]
            )
            self.assertEqual(
                rendered["rehearsal_teardown_before_phase"],
                "remove_old_compute",
            )
            self.assertEqual(rendered["production_attachment_delete_option"], "Detach")
            self.assertFalse(rendered["rollback_operationally_tested"])


if __name__ == "__main__":
    unittest.main()
