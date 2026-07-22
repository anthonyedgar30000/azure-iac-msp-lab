from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "infra" / "replacement" / "collector-replacement-contract.json"
VALIDATOR_PATH = ROOT / "infra" / "replacement" / "validate_execution_design.py"
CANDIDATE_WORKFLOW_PATH = (
    ROOT / "infra" / "workflow-designs" / "collector-replacement-execution.yml"
)
ACTIVE_WORKFLOW_PATH = (
    ROOT / ".github" / "workflows" / "collector-replacement-execution.yml"
)


class CollectorReplacementExecutionDesignTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        self.workflow = CANDIDATE_WORKFLOW_PATH.read_text(encoding="utf-8")

    def _validate(self, contract: dict) -> dict:
        namespace: dict[str, object] = {
            "__name__": "collector_replacement_execution_design_validator"
        }
        exec(VALIDATOR_PATH.read_text(encoding="utf-8"), namespace)
        validator = namespace["validate_contract"]
        return validator(contract)  # type: ignore[operator]

    def test_candidate_is_not_an_active_github_workflow(self) -> None:
        self.assertTrue(CANDIDATE_WORKFLOW_PATH.is_file())
        self.assertFalse(ACTIVE_WORKFLOW_PATH.exists())
        self.assertEqual(
            self.contract["activation"]["candidate_workflow"],
            "infra/workflow-designs/collector-replacement-execution.yml",
        )
        self.assertFalse(self.contract["activation"]["active_workflow_present"])

    def test_workflow_design_fails_closed_before_azure_authentication(self) -> None:
        blocker = self.workflow.index("Fail closed before Azure authentication or mutation")
        candidate = self.workflow.index("Candidate replacement phase contract")
        self.assertLess(blocker, candidate)
        self.assertIn("DESIGN_ONLY_BLOCKER: 'true'", self.workflow)
        self.assertIn("exit 64", self.workflow)
        self.assertNotIn("uses: azure/login@", self.workflow)

    def test_candidate_contains_no_azure_mutation_commands(self) -> None:
        for forbidden in (
            "az vm delete",
            "az vm deallocate",
            "az snapshot create",
            "az disk update",
            "az resource update",
            "az deployment group create",
            "az role assignment create",
            "az network nic delete",
        ):
            self.assertNotIn(forbidden, self.workflow)

    def test_contract_validates_as_fail_closed_and_not_promotion_ready(self) -> None:
        result = self._validate(self.contract)
        self.assertTrue(result["design_valid"])
        self.assertEqual(result["design_state"], "fail_closed")
        self.assertFalse(result["dispatch_authorized"])
        self.assertFalse(result["azure_mutations_authorized"])
        self.assertFalse(result["promotion_ready"])
        self.assertEqual(result["rollback_status"], "strategy_selected_design_only")
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

    def test_snapshot_rollback_preserves_canonical_os_disk_name(self) -> None:
        result = self._validate(self.contract)
        rollback = self.contract["rollback"]
        recreation = rollback["recreation_contract"]
        self.assertEqual(
            result["rollback_strategy"],
            "os_disk_snapshot_recreate_canonical_name",
        )
        self.assertEqual(
            result["canonical_os_disk_name"], "disk-stcollector-os-mst-dev"
        )
        self.assertEqual(
            recreation["recreated_os_disk_name"], "disk-stcollector-os-mst-dev"
        )
        self.assertEqual(recreation["os_disk_create_option"], "Copy")
        self.assertFalse(rollback["preserve_old_os_disk_directly"])

    def test_selected_rollback_remains_unverified_and_review_pending(self) -> None:
        rollback = self.contract["rollback"]
        self.assertFalse(rollback["operationally_tested"])
        self.assertEqual(rollback["independent_review_status"], "pending")
        self.assertTrue(rollback["promotion_blocked"])
        self.assertIn(
            "operational proof of the selected OS-disk snapshot recreation rollback",
            self.contract["unresolved_blockers"],
        )

    def test_phase_order_places_both_recovery_points_before_old_compute_removal(self) -> None:
        result = self._validate(self.contract)
        phases = result["phase_order"]
        self.assertLess(
            phases.index("create_recovery_points"), phases.index("remove_old_compute")
        )
        self.assertLess(
            phases.index("verify_recovery_points"), phases.index("remove_old_compute")
        )
        self.assertLess(
            phases.index("verify_preservation_boundary"),
            phases.index("deploy_replacement_compute"),
        )
        self.assertLess(
            phases.index("post_change_verification"),
            phases.index("human_recovery_acceptance"),
        )
        self.assertLess(
            phases.index("human_recovery_acceptance"),
            phases.index("cleanup_temporary_recovery_resources"),
        )
        remove_phase = next(
            phase
            for phase in self.contract["phases"]
            if phase["phase_id"] == "remove_old_compute"
        )
        self.assertIn("both snapshots", remove_phase["evidence_required"])

    def test_every_mutation_phase_requires_explicit_authorization(self) -> None:
        for phase in self.contract["phases"]:
            if phase["mutation"]:
                self.assertTrue(
                    phase["requires_explicit_authorization"], phase["phase_id"]
                )

    def test_cost_controls_fit_evidence_and_os_disk_snapshot_ceiling(self) -> None:
        cost = self.contract["cost_controls"]
        rollback = self.contract["rollback"]
        self.assertEqual(cost["currency"], "CAD")
        self.assertLessEqual(cost["maximum_declared_temporary_cost"], 10)
        self.assertEqual(cost["maximum_snapshots"], 2)
        self.assertEqual(cost["maximum_total_snapshot_gib"], 96)
        self.assertEqual(rollback["maximum_os_disk_snapshot_gib"], 64)
        self.assertEqual(cost["maximum_compute_overlap_minutes"], 0)
        self.assertLessEqual(cost["maximum_recovery_resource_retention_hours"], 24)
        self.assertFalse(cost["azure_budget_or_alert_mutation_allowed"])

    def test_validator_rejects_authorization_in_design_branch(self) -> None:
        modified = copy.deepcopy(self.contract)
        modified["activation"]["azure_mutations_authorized"] = True
        with self.assertRaises(Exception):
            self._validate(modified)

    def test_validator_rejects_cost_ceiling_above_policy_limit(self) -> None:
        modified = copy.deepcopy(self.contract)
        modified["cost_controls"]["maximum_declared_temporary_cost"] = 25
        with self.assertRaises(Exception):
            self._validate(modified)

    def test_validator_rejects_missing_recovery_phase(self) -> None:
        modified = copy.deepcopy(self.contract)
        modified["phases"] = [
            phase
            for phase in modified["phases"]
            if phase["phase_id"] != "verify_recovery_points"
        ]
        with self.assertRaises(Exception):
            self._validate(modified)

    def test_validator_rejects_canonical_os_disk_name_drift(self) -> None:
        modified = copy.deepcopy(self.contract)
        modified["rollback"]["canonical_os_disk_name"] = "disk-stcollector-os-temp"
        with self.assertRaises(Exception):
            self._validate(modified)

    def test_validator_rejects_direct_old_os_disk_preservation(self) -> None:
        modified = copy.deepcopy(self.contract)
        modified["rollback"]["preserve_old_os_disk_directly"] = True
        with self.assertRaises(Exception):
            self._validate(modified)

    def test_validator_rejects_false_operational_verification_claim(self) -> None:
        modified = copy.deepcopy(self.contract)
        modified["rollback"]["operationally_tested"] = True
        with self.assertRaises(Exception):
            self._validate(modified)

    def test_validator_rejects_weakened_snapshot_verification(self) -> None:
        modified = copy.deepcopy(self.contract)
        modified["rollback"]["snapshot_verification_required"].remove(
            "source OS-disk resource ID matches"
        )
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
            self.assertTrue(rendered["design_valid"])
            self.assertFalse(rendered["dispatch_authorized"])
            self.assertFalse(rendered["azure_mutations_authorized"])
            self.assertFalse(rendered["promotion_ready"])
            self.assertEqual(
                rendered["rollback_strategy"],
                "os_disk_snapshot_recreate_canonical_name",
            )
            self.assertFalse(rendered["rollback_operationally_tested"])


if __name__ == "__main__":
    unittest.main()
