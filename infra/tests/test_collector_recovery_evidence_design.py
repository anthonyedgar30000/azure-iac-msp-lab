from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "infra" / "recovery-evidence" / "collector-recovery-evidence-contract.json"
VALIDATOR_PATH = ROOT / "infra" / "recovery-evidence" / "validate_recovery_evidence.py"


class CollectorRecoveryEvidenceDesignTests(unittest.TestCase):
    def setUp(self) -> None:
        self.namespace: dict[str, object] = {"__name__": "collector_recovery_evidence_validator"}
        exec(VALIDATOR_PATH.read_text(encoding="utf-8"), self.namespace)
        self.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        self.schemas = {
            key: json.loads((ROOT / value["path"]).read_text(encoding="utf-8"))
            for key, value in self.contract["schemas"].items()
        }
        self.bundle = self.namespace["build_design_fixture"](self.contract)  # type: ignore[operator]

    def _validate_contract(self, contract: dict | None = None, schemas: dict | None = None) -> dict:
        return self.namespace["validate_contract"](  # type: ignore[operator]
            contract if contract is not None else self.contract,
            schemas if schemas is not None else self.schemas,
        )

    def _validate_bundle(self, bundle: dict | None = None, contract: dict | None = None) -> dict:
        return self.namespace["validate_bundle"](  # type: ignore[operator]
            bundle if bundle is not None else self.bundle,
            contract if contract is not None else self.contract,
        )

    def test_design_contract_and_all_five_schemas_validate(self) -> None:
        result = self._validate_contract()
        self.assertTrue(result["design_valid"])
        self.assertEqual(result["design_state"], "fail_closed_design_only")
        self.assertEqual(result["schema_count"], 5)
        self.assertFalse(result["azure_authentication_authorized"])
        self.assertFalse(result["azure_mutations_authorized"])
        self.assertFalse(result["runtime_execution_authorized"])

    def test_schema_documents_are_closed_and_pinned_to_contract_ids(self) -> None:
        for key, schema in self.schemas.items():
            with self.subTest(schema=key):
                self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
                self.assertEqual(schema["$id"], self.contract["schemas"][key]["schema_id"])
                self.assertFalse(schema["additionalProperties"])
                self.assertEqual(
                    schema["properties"]["schema_version"]["const"],
                    self.contract["schemas"][key]["schema_version"],
                )

    def test_valid_design_fixture_has_exact_observation_coverage(self) -> None:
        result = self._validate_bundle()
        self.assertTrue(result["bundle_valid"])
        self.assertEqual(result["guest_record_count"], 8)
        self.assertEqual(result["azure_record_count"], 16)
        self.assertEqual(result["evidence_identity_count"], 24)
        self.assertEqual(result["failure_record_count"], 0)
        self.assertEqual(result["rollback_record_count"], 0)
        self.assertFalse(result["runtime_execution_authorized"])
        self.assertFalse(result["azure_mutations_authorized"])

    def test_validator_rejects_missing_guest_observation_kind(self) -> None:
        modified = copy.deepcopy(self.bundle)
        modified["guest_preflight"].pop()
        with self.assertRaises(Exception):
            self._validate_bundle(modified)

    def test_validator_rejects_missing_azure_observation_kind(self) -> None:
        modified = copy.deepcopy(self.bundle)
        modified["azure_control_plane_preflight"].pop()
        with self.assertRaises(Exception):
            self._validate_bundle(modified)

    def test_validator_rejects_duplicate_evidence_identity(self) -> None:
        modified = copy.deepcopy(self.bundle)
        modified["azure_control_plane_preflight"][0]["evidence_id"] = modified["guest_preflight"][0]["evidence_id"]
        with self.assertRaises(Exception):
            self._validate_bundle(modified)

    def test_validator_rejects_correlation_mismatch(self) -> None:
        modified = copy.deepcopy(self.bundle)
        modified["guest_preflight"][0]["correlation"]["maintenance_correlation_id"] = "maint-different-correlation"
        with self.assertRaises(Exception):
            self._validate_bundle(modified)

    def test_validator_rejects_target_mismatch(self) -> None:
        modified = copy.deepcopy(self.bundle)
        modified["azure_control_plane_preflight"][0]["target"]["resource_id_sha256"] = "f" * 64
        with self.assertRaises(Exception):
            self._validate_bundle(modified)

    def test_validator_rejects_stale_evidence(self) -> None:
        modified = copy.deepcopy(self.bundle)
        modified["guest_preflight"][0]["guest_observation"]["freshness_seconds"] = 901
        with self.assertRaises(Exception):
            self._validate_bundle(modified)

    def test_validator_rejects_success_with_nonzero_exit_code(self) -> None:
        modified = copy.deepcopy(self.bundle)
        modified["guest_preflight"][0]["result"]["exit_code"] = 1
        modified["guest_preflight"][0]["command"]["exit_code"] = 1
        with self.assertRaises(Exception):
            self._validate_bundle(modified)

    def test_validator_rejects_command_result_exit_code_mismatch(self) -> None:
        modified = copy.deepcopy(self.bundle)
        modified["azure_control_plane_preflight"][0]["command"]["exit_code"] = 2
        with self.assertRaises(Exception):
            self._validate_bundle(modified)

    def test_validator_rejects_preflight_state_mutation(self) -> None:
        modified = copy.deepcopy(self.bundle)
        modified["guest_preflight"][0]["state"]["changed"] = True
        with self.assertRaises(Exception):
            self._validate_bundle(modified)

    def test_validator_rejects_azure_mutation_authorization(self) -> None:
        modified = copy.deepcopy(self.bundle)
        modified["azure_control_plane_preflight"][0]["authority"]["azure_mutations_authorized"] = True
        with self.assertRaises(Exception):
            self._validate_bundle(modified)

    def test_validator_rejects_sanitized_record_without_resource_digest(self) -> None:
        modified = copy.deepcopy(self.bundle)
        del modified["guest_preflight"][0]["target"]["resource_id_sha256"]
        with self.assertRaises(Exception):
            self._validate_bundle(modified)

    def test_validator_rejects_exact_resource_id_in_sanitized_record(self) -> None:
        modified = copy.deepcopy(self.bundle)
        modified["guest_preflight"][0]["target"]["resource_id"] = "/subscriptions/not-for-repository/resourceGroups/example/providers/Microsoft.Compute/virtualMachines/example"
        with self.assertRaises(Exception):
            self._validate_bundle(modified)

    def test_validator_rejects_unredacted_secret_marker(self) -> None:
        modified = copy.deepcopy(self.bundle)
        modified["azure_control_plane_preflight"][0]["command"]["arguments_redacted"].append("client_secret=unsafe")
        with self.assertRaises(Exception):
            self._validate_bundle(modified)

    def test_validator_requires_failure_record_for_failed_preflight(self) -> None:
        modified = copy.deepcopy(self.bundle)
        record = modified["guest_preflight"][0]
        record["result"]["status"] = "failure"
        record["result"]["exit_code"] = 4
        record["command"]["exit_code"] = 4
        with self.assertRaises(Exception):
            self._validate_bundle(modified)

    def test_validator_rejects_rollback_success_without_authorized_runtime_evidence(self) -> None:
        modified = copy.deepcopy(self.bundle)
        modified["rollbacks"].append(
            {
                "evidence_class": "rollback_outcome",
                "authority": {
                    "read_only": True,
                    "azure_authentication_authorized": False,
                    "azure_mutations_authorized": False,
                    "execution_authorization_reference": None,
                },
                "rollback": {"outcome": "succeeded", "operationally_tested": True},
            }
        )
        with self.assertRaises(Exception):
            self._validate_bundle(modified)

    def test_contract_rejects_enabling_azure_authentication(self) -> None:
        modified = copy.deepcopy(self.contract)
        modified["activation"]["azure_authentication_authorized"] = True
        with self.assertRaises(Exception):
            self._validate_contract(modified)

    def test_contract_rejects_raw_private_repository_promotion(self) -> None:
        modified = copy.deepcopy(self.contract)
        modified["redaction_contract"]["raw_private_repository_promotion_allowed"] = True
        with self.assertRaises(Exception):
            self._validate_contract(modified)

    def test_contract_rejects_schema_id_drift(self) -> None:
        modified_schemas = copy.deepcopy(self.schemas)
        modified_schemas["guest_preflight"]["$id"] = "https://example.invalid/guest.json"
        with self.assertRaises(Exception):
            self._validate_contract(schemas=modified_schemas)

    def test_contract_rejects_open_schema_objects(self) -> None:
        modified_schemas = copy.deepcopy(self.schemas)
        modified_schemas["bundle"]["additionalProperties"] = True
        with self.assertRaises(Exception):
            self._validate_contract(schemas=modified_schemas)

    def test_cli_emits_valid_design_and_bundle_summary(self) -> None:
        completed = subprocess.run(
            ["python", str(VALIDATOR_PATH), "--root", str(ROOT)],
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["design"]["design_valid"])
        self.assertTrue(payload["bundle"]["bundle_valid"])
        self.assertFalse(payload["bundle"]["runtime_execution_authorized"])


if __name__ == "__main__":
    unittest.main()
