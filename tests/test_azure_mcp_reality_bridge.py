from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "scripts" / "validate_azure_mcp_reality_bridge.py"
CONTRACT_PATH = ROOT / ".project" / "contracts" / "azure-mcp-reality-bridge.json"

spec = importlib.util.spec_from_file_location("azure_mcp_contract_validator", VALIDATOR_PATH)
assert spec and spec.loader
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class AzureMcpRealityBridgeContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_repository_contract_is_valid(self) -> None:
        validator.validate_contract(copy.deepcopy(self.contract))

    def test_selected_architecture_remains_unimplemented(self) -> None:
        self.assertEqual(
            self.contract["client_paths"]["selection"]["selected_client_path"],
            "openai_responses_api",
        )
        self.assertFalse(self.contract["client_paths"]["selection"]["configured"])
        self.assertEqual(self.contract["hosting"]["selected_service"], "azure_container_apps")
        self.assertFalse(self.contract["hosting"]["deployed"])
        self.assertEqual(
            self.contract["authentication"]["server_to_azure"]["selected_model"],
            "managed_identity_shared_service_identity",
        )
        self.assertFalse(self.contract["authentication"]["server_to_azure"]["implemented"])

    def test_azure_authentication_cannot_be_pre_authorized(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["authority"]["azure_authentication_authorized"] = True
        with self.assertRaises(validator.ContractError):
            validator.validate_contract(changed)

    def test_openai_execution_cannot_be_pre_authorized(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["client_paths"]["openai_responses_api"]["api_execution_authorized"] = True
        with self.assertRaises(validator.ContractError):
            validator.validate_contract(changed)

    def test_tool_cannot_be_pre_admitted_without_inventory_evidence(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["tool_admission"]["allowed_tool_names"] = ["subscription_list"]
        with self.assertRaises(validator.ContractError):
            validator.validate_contract(changed)

    def test_namespace_cannot_be_pre_admitted(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["tool_admission"]["namespace_allowlist"] = ["subscription"]
        with self.assertRaises(validator.ContractError):
            validator.validate_contract(changed)

    def test_endpoint_cannot_be_promoted_without_deployment_evidence(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["transport"]["remote_endpoint_deployed"] = True
        changed["transport"]["endpoint_url"] = "https://example.invalid/mcp"
        with self.assertRaises(validator.ContractError):
            validator.validate_contract(changed)

    def test_default_subscription_inference_remains_denied(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["azure_scope"]["default_subscription_inference_allowed"] = True
        with self.assertRaises(validator.ContractError):
            validator.validate_contract(changed)

    def test_cloud_shell_preflight_is_not_execution_authority(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["cloud_shell_package"]["preflight_execution_authorized"] = True
        with self.assertRaises(validator.ContractError):
            validator.validate_contract(changed)


if __name__ == "__main__":
    unittest.main()
