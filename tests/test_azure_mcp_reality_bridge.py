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

    def test_exactly_one_local_read_only_tool_is_admitted(self) -> None:
        admission = self.contract["tool_admission"]
        self.assertEqual(admission["allowed_tool_names"], ["get_current_reality"])
        self.assertEqual(admission["server_mode"], "local_observer_only")
        self.assertEqual(
            admission["tool"]["annotations"],
            {
                "readOnlyHint": True,
                "destructiveHint": False,
                "idempotentHint": True,
                "openWorldHint": True,
            },
        )
        self.assertEqual(admission["tool"]["model_inputs"], [])
        self.assertFalse(admission["tool"]["performs_azure_mutation"])

    def test_second_tool_cannot_be_admitted(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["tool_admission"]["allowed_tool_names"].append("resource_create")
        with self.assertRaises(validator.ContractError):
            validator.validate_contract(changed)

    def test_tool_annotations_cannot_be_weakened(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["tool_admission"]["tool"]["annotations"]["destructiveHint"] = True
        with self.assertRaises(validator.ContractError):
            validator.validate_contract(changed)

    def test_model_cannot_select_azure_scope(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["azure_scope"]["model_supplied_scope_parameters_allowed"] = True
        with self.assertRaises(validator.ContractError):
            validator.validate_contract(changed)

    def test_default_subscription_inference_remains_denied(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["azure_scope"]["default_subscription_inference_allowed"] = True
        with self.assertRaises(validator.ContractError):
            validator.validate_contract(changed)

    def test_remote_endpoint_cannot_be_promoted(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["transport"]["remote_endpoint_deployed"] = True
        changed["transport"]["remote_endpoint_url"] = "https://example.invalid/mcp"
        with self.assertRaises(validator.ContractError):
            validator.validate_contract(changed)

    def test_live_tool_execution_cannot_be_manufactured(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["authentication"]["local_tool_to_azure"]["live_execution_observed"] = True
        with self.assertRaises(validator.ContractError):
            validator.validate_contract(changed)

    def test_azure_openai_mcp_call_cannot_be_manufactured(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["client_paths"]["azure_openai_responses_api"]["mcp_server_configured"] = True
        changed["client_paths"]["azure_openai_responses_api"]["mcp_tool_call_verified"] = True
        with self.assertRaises(validator.ContractError):
            validator.validate_contract(changed)

    def test_azure_mutation_authority_remains_false(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["authority"]["azure_resource_creation_authorized"] = True
        with self.assertRaises(validator.ContractError):
            validator.validate_contract(changed)


if __name__ == "__main__":
    unittest.main()
