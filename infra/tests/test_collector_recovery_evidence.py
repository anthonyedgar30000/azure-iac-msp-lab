from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "infra" / "recovery" / "collector-recovery-evidence-contract.json"
VALIDATOR_PATH = ROOT / "infra" / "recovery" / "validate_recovery_evidence.py"
ZERO_SUBSCRIPTION = "00000000-0000-0000-0000-000000000000"
RESOURCE_GROUP = "rg-servicetracer-dev-westus2"
VM_ID = (
    f"/subscriptions/{ZERO_SUBSCRIPTION}/resourceGroups/{RESOURCE_GROUP}"
    "/providers/Microsoft.Compute/virtualMachines/vm-stcollector-mst-dev"
)
NIC_ID = (
    f"/subscriptions/{ZERO_SUBSCRIPTION}/resourceGroups/{RESOURCE_GROUP}"
    "/providers/Microsoft.Network/networkInterfaces/nic-stcollector-mst-dev"
)
EVIDENCE_DISK_ID = (
    f"/subscriptions/{ZERO_SUBSCRIPTION}/resourceGroups/{RESOURCE_GROUP}"
    "/providers/Microsoft.Compute/disks/disk-stcollector-evidence-mst-dev"
)
OS_DISK_ID = (
    f"/subscriptions/{ZERO_SUBSCRIPTION}/resourceGroups/{RESOURCE_GROUP}"
    "/providers/Microsoft.Compute/disks/disk-stcollector-os-mst-dev"
)
SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64


class CollectorRecoveryEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import importlib.util
        import sys

        sys.path.insert(0, str(VALIDATOR_PATH.parent))
        spec = importlib.util.spec_from_file_location(
            "collector_recovery_evidence_validator", VALIDATOR_PATH
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("unable to load recovery evidence validator")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls.validate_contract = staticmethod(module.validate_contract)
        cls.validate_package = staticmethod(module.validate_evidence_package)
        cls.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def _target(self) -> dict:
        return {
            "resource_group": RESOURCE_GROUP,
            "collector_vm": "vm-stcollector-mst-dev",
            "collector_vm_resource_id": VM_ID,
            "collector_nic_resource_id": NIC_ID,
            "collector_evidence_disk_resource_id": EVIDENCE_DISK_ID,
            "collector_os_disk_resource_id": OS_DISK_ID,
            "evidence_mount": "/var/lib/servicetracer",
        }

    def _record(
        self,
        record_id: str,
        record_type: str,
        phase_id: str,
        *,
        status: str = "passed",
        exit_status: int = 0,
        target_resource_id: str = VM_ID,
        command_identity: str = "guest.preflight.collect",
        details: dict | None = None,
        before_state: dict | None = None,
        after_state: dict | None = None,
        redactions: list | None = None,
        observed_at: str = "2026-07-22T18:00:00Z",
        evidence_sha256: str = SHA_A,
    ) -> dict:
        return {
            "record_id": record_id,
            "record_type": record_type,
            "phase_id": phase_id,
            "observed_at": observed_at,
            "command_identity": command_identity,
            "exit_status": exit_status,
            "status": status,
            "target_resource_id": target_resource_id,
            "before_state": before_state or {"state": "unknown"},
            "after_state": after_state or {"state": "observed"},
            "evidence_sha256": evidence_sha256,
            "summary": f"{record_type} evidence",
            "details": details or {"source": "synthetic-test-fixture"},
            "redactions": redactions or [],
        }

    def _claims(self, **overrides: str) -> dict:
        claims = {
            "snapshot_recoverability": "not_claimed",
            "trusted_launch_bootability": "not_claimed",
            "rollback": "not_claimed",
            "recovery": "not_claimed",
        }
        claims.update(overrides)
        return claims

    def _package(
        self,
        phases: list[str],
        records: list[dict],
        *,
        package_status: str = "complete",
        claims: dict | None = None,
    ) -> dict:
        return {
            "schema_version": "servicetracer.collector-recovery-evidence.v1",
            "package_id": "pkg-20260722-0001",
            "generated_at": "2026-07-22T18:05:00Z",
            "maintenance_correlation_id": "MNT-20260722-0001",
            "target": self._target(),
            "declared_phase_ids": phases,
            "package_status": package_status,
            "records": records,
            "claims": claims or self._claims(),
            "claim_boundary": (
                "Synthetic test evidence validates structure only and does not authorize "
                "or prove Azure recovery."
            ),
        }

    def _complete_preflight_package(self) -> dict:
        phase = "guest_and_control_plane_preflight"
        records = [
            self._record(
                "rec-guest-0001",
                "guest_preflight",
                phase,
                target_resource_id=VM_ID,
                command_identity="guest.preflight.collect",
                details={
                    "service_state": "active",
                    "health_status": "healthy",
                    "mount": "/var/lib/servicetracer",
                    "filesystem_uuid": "11111111-2222-3333-4444-555555555555",
                    "recent_evidence_readable": True,
                },
            ),
            self._record(
                "rec-azure-0001",
                "azure_control_plane_preflight",
                phase,
                target_resource_id=NIC_ID,
                command_identity="azure.control-plane.observe",
                details={
                    "vm_power_state": "PowerState/running",
                    "nic_delete_option": "Delete",
                    "evidence_disk_delete_option": "Detach",
                    "os_disk_public_network_access": "Enabled",
                    "observed_role_assignments": [],
                },
                evidence_sha256=SHA_B,
            ),
            self._record(
                "rec-cleanup-0001",
                "cleanup_commitment",
                phase,
                target_resource_id=VM_ID,
                command_identity="recovery.cleanup.commitment",
                details={
                    "owner": "Anthony Edgar",
                    "deadline": "2026-07-23T18:00:00Z",
                    "maximum_retention_hours": 24,
                    "approved_cost_ceiling_cad": 10.0,
                },
                evidence_sha256=SHA_C,
            ),
        ]
        return self._package([phase], records)

    def _complete_rollback_package(self) -> dict:
        rollback_phase = "rollback_recovery"
        acceptance_phase = "human_recovery_acceptance"
        records = [
            self._record(
                "rec-op-rollback-0001",
                "operation_attempt",
                rollback_phase,
                command_identity="rollback.execute.synthetic",
                details={"operation": "synthetic rollback fixture"},
            ),
            self._record(
                "rec-state-rollback-0001",
                "state_observation",
                rollback_phase,
                command_identity="rollback.state.observe",
                details={"power_state": "PowerState/running"},
                evidence_sha256=SHA_B,
            ),
            self._record(
                "rec-guest-rollback-0001",
                "guest_preflight",
                rollback_phase,
                command_identity="rollback.guest.verify",
                details={"service_state": "active", "health_status": "healthy"},
                evidence_sha256=SHA_C,
            ),
            self._record(
                "rec-azure-rollback-0001",
                "azure_control_plane_preflight",
                rollback_phase,
                target_resource_id=NIC_ID,
                command_identity="rollback.azure.verify",
                details={"nic_delete_option": "Detach"},
            ),
            self._record(
                "rec-integrity-rollback-0001",
                "integrity_verification",
                rollback_phase,
                target_resource_id=EVIDENCE_DISK_ID,
                command_identity="rollback.integrity.verify",
                details={"recent_evidence_readable": True, "filesystem_uuid_matches": True},
                evidence_sha256=SHA_B,
            ),
            self._record(
                "rec-decision-rollback-0001",
                "decision",
                rollback_phase,
                command_identity="rollback.decision.record",
                details={
                    "decision": "rollback_completed",
                    "reason": "synthetic fixture",
                    "authority": "test-only",
                    "safe_next_step": "none",
                    "rollback_required": False,
                },
                evidence_sha256=SHA_C,
            ),
            self._record(
                "rec-human-accept-0001",
                "decision",
                acceptance_phase,
                command_identity="human.acceptance.record",
                details={
                    "decision": "accepted",
                    "reason": "all synthetic checks passed",
                    "authority": "test-only",
                    "safe_next_step": "none",
                    "rollback_required": False,
                },
            ),
        ]
        return self._package(
            [rollback_phase, acceptance_phase],
            records,
            claims=self._claims(rollback="verified"),
        )

    def test_contract_is_design_only_and_fail_closed(self) -> None:
        result = self.validate_contract(self.contract)
        self.assertTrue(result["contract_valid"])
        self.assertEqual(result["state"], "design_only")
        self.assertFalse(result["active_workflow_present"])
        self.assertFalse(result["dispatch_authorized"])
        self.assertFalse(result["azure_authentication_authorized"])
        self.assertFalse(result["azure_mutations_authorized"])

    def test_complete_preflight_package_validates_for_declared_scope(self) -> None:
        result = self.validate_package(self._complete_preflight_package(), self.contract)
        self.assertTrue(result["package_valid"])
        self.assertTrue(result["complete_for_declared_scope"])
        self.assertEqual(result["missing_evidence_by_phase"], {})
        self.assertEqual(result["verified_claims"], [])
        self.assertFalse(result["authority_granted"])
        self.assertFalse(result["azure_mutations_authorized"])

    def test_incomplete_package_reports_missing_evidence_without_overstating_completeness(self) -> None:
        package = self._complete_preflight_package()
        package["package_status"] = "incomplete"
        package["records"] = package["records"][:-1]
        result = self.validate_package(package, self.contract)
        self.assertFalse(result["complete_for_declared_scope"])
        self.assertEqual(
            result["missing_evidence_by_phase"],
            {"guest_and_control_plane_preflight": ["cleanup_commitment"]},
        )

    def test_complete_package_rejects_missing_declared_phase_evidence(self) -> None:
        package = self._complete_preflight_package()
        package["records"] = package["records"][:-1]
        with self.assertRaises(Exception):
            self.validate_package(package, self.contract)

    def test_nested_secret_like_field_is_rejected(self) -> None:
        package = self._complete_preflight_package()
        package["records"][0]["details"]["client_secret"] = "not-a-real-secret"
        with self.assertRaises(Exception):
            self.validate_package(package, self.contract)

    def test_forbidden_credential_prefix_is_rejected(self) -> None:
        package = self._complete_preflight_package()
        package["records"][0]["details"]["header"] = "Bearer fake-value"
        with self.assertRaises(Exception):
            self.validate_package(package, self.contract)

    def test_logical_command_identity_rejects_raw_shell_command(self) -> None:
        package = self._complete_preflight_package()
        package["records"][0]["command_identity"] = "az vm show --name vm-stcollector-mst-dev"
        with self.assertRaises(Exception):
            self.validate_package(package, self.contract)

    def test_resource_id_outside_target_boundary_is_rejected(self) -> None:
        package = self._complete_preflight_package()
        package["records"][0]["target_resource_id"] = (
            f"/subscriptions/{ZERO_SUBSCRIPTION}/resourceGroups/other-rg"
            "/providers/Microsoft.Compute/virtualMachines/other-vm"
        )
        with self.assertRaises(Exception):
            self.validate_package(package, self.contract)

    def test_non_utc_timestamp_is_rejected(self) -> None:
        package = self._complete_preflight_package()
        package["records"][0]["observed_at"] = "2026-07-22T14:00:00-04:00"
        with self.assertRaises(Exception):
            self.validate_package(package, self.contract)

    def test_redaction_marker_requires_digest_metadata(self) -> None:
        package = self._complete_preflight_package()
        package["records"][0]["details"]["sensitive_value"] = "[REDACTED]"
        with self.assertRaises(Exception):
            self.validate_package(package, self.contract)

    def test_redaction_marker_with_digest_metadata_is_accepted(self) -> None:
        package = self._complete_preflight_package()
        package["records"][0]["details"]["sensitive_value"] = "[REDACTED]"
        package["records"][0]["redactions"] = [
            {
                "field_path": "details.sensitive_value",
                "marker": "[REDACTED]",
                "original_sha256": SHA_A,
            }
        ]
        result = self.validate_package(package, self.contract)
        self.assertTrue(result["package_valid"])

    def test_oversized_nested_collection_is_rejected(self) -> None:
        package = self._complete_preflight_package()
        package["records"][0]["details"]["items"] = list(range(129))
        with self.assertRaises(Exception):
            self.validate_package(package, self.contract)

    def test_duplicate_record_ids_are_rejected(self) -> None:
        package = self._complete_preflight_package()
        package["records"][1]["record_id"] = package["records"][0]["record_id"]
        with self.assertRaises(Exception):
            self.validate_package(package, self.contract)

    def test_failed_package_requires_terminal_decision(self) -> None:
        phase = "rollback_recovery"
        package = self._package(
            [phase],
            [
                self._record(
                    "rec-failed-op-0001",
                    "operation_attempt",
                    phase,
                    status="failed",
                    exit_status=1,
                    command_identity="rollback.synthetic.failure",
                )
            ],
            package_status="failed",
        )
        with self.assertRaises(Exception):
            self.validate_package(package, self.contract)

    def test_failed_package_with_terminal_decision_is_valid_but_incomplete(self) -> None:
        phase = "rollback_recovery"
        records = [
            self._record(
                "rec-failed-op-0001",
                "operation_attempt",
                phase,
                status="failed",
                exit_status=1,
                command_identity="rollback.synthetic.failure",
            ),
            self._record(
                "rec-failed-decision-0001",
                "decision",
                phase,
                status="failed",
                exit_status=1,
                command_identity="rollback.failure.decision",
                details={
                    "decision": "abort",
                    "reason": "synthetic operation failed",
                    "authority": "test-only",
                    "safe_next_step": "preserve evidence and request review",
                    "rollback_required": True,
                },
            ),
        ]
        package = self._package([phase], records, package_status="failed")
        result = self.validate_package(package, self.contract)
        self.assertTrue(result["package_valid"])
        self.assertFalse(result["complete_for_declared_scope"])

    def test_verified_claim_without_required_phases_is_rejected(self) -> None:
        package = self._complete_preflight_package()
        package["claims"]["rollback"] = "verified"
        with self.assertRaises(Exception):
            self.validate_package(package, self.contract)

    def test_verified_rollback_claim_requires_complete_evidence_and_human_acceptance(self) -> None:
        result = self.validate_package(self._complete_rollback_package(), self.contract)
        self.assertEqual(result["verified_claims"], ["rollback"])
        self.assertTrue(result["complete_for_declared_scope"])

    def test_verified_rollback_claim_rejects_missing_human_acceptance(self) -> None:
        package = self._complete_rollback_package()
        package["records"] = [
            record
            for record in package["records"]
            if record["phase_id"] != "human_recovery_acceptance"
        ]
        package["package_status"] = "incomplete"
        with self.assertRaises(Exception):
            self.validate_package(package, self.contract)

    def test_unknown_record_field_is_rejected(self) -> None:
        package = self._complete_preflight_package()
        package["records"][0]["stdout"] = "raw output"
        with self.assertRaises(Exception):
            self.validate_package(package, self.contract)


if __name__ == "__main__":
    unittest.main()
