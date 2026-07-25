from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "azure_resource_graph_semantic_inventory.py"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "azure-resource-graph-sample.json"
CONTRACT_PATH = ROOT / ".project" / "contracts" / "azure-resource-graph-semantic-inventory.json"

spec = importlib.util.spec_from_file_location("arg_inventory", MODULE_PATH)
assert spec and spec.loader
inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory)


class AzureResourceGraphSemanticInventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        self.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def test_contract_is_valid_and_execution_remains_unauthorized(self) -> None:
        inventory.validate_contract(copy.deepcopy(self.contract))
        self.assertFalse(self.contract["query_package"]["query_execution_authorized"])
        self.assertFalse(self.contract["authority"]["azure_authentication_authorized"])
        self.assertFalse(self.contract["authority"]["azure_resource_mutation_authorized"])

    def test_fixture_normalizes_to_microscopic_ip_configuration_node(self) -> None:
        graph = inventory.normalize(copy.deepcopy(self.payload))
        node_by_id = {node["id"]: node for node in graph["nodes"]}
        ipconfig_id = (
            "/subscriptions/11111111-1111-1111-1111-111111111111/"
            "resourcegroups/rg-demo/providers/microsoft.network/networkinterfaces/"
            "nic-demo/ipconfigurations/ipconfig1"
        )
        self.assertIn(ipconfig_id, node_by_id)
        self.assertEqual(node_by_id[ipconfig_id]["attributes"]["private_ip_address"], "10.20.40.10")
        self.assertEqual(node_by_id[ipconfig_id]["attributes"]["private_ip_allocation_method"], "Static")

    def test_expected_relationships_are_materialized(self) -> None:
        graph = inventory.normalize(copy.deepcopy(self.payload))
        relationships = {
            (edge["source"], edge["relationship"], edge["target"])
            for edge in graph["edges"]
        }
        vm_id = "/subscriptions/11111111-1111-1111-1111-111111111111/resourcegroups/rg-demo/providers/microsoft.compute/virtualmachines/vm-demo"
        nic_id = "/subscriptions/11111111-1111-1111-1111-111111111111/resourcegroups/rg-demo/providers/microsoft.network/networkinterfaces/nic-demo"
        subnet_id = "/subscriptions/11111111-1111-1111-1111-111111111111/resourcegroups/rg-demo/providers/microsoft.network/virtualnetworks/vnet-demo/subnets/snet-ops"
        ipconfig_id = f"{nic_id}/ipconfigurations/ipconfig1"
        self.assertIn((vm_id, "attached_to", nic_id), relationships)
        self.assertIn((nic_id, "contains", ipconfig_id), relationships)
        self.assertIn((ipconfig_id, "connected_to", subnet_id), relationships)

    def test_output_is_deterministic(self) -> None:
        first = inventory.normalize(copy.deepcopy(self.payload))
        reordered = copy.deepcopy(self.payload)
        reordered["results"]["resources"].reverse()
        reordered["results"]["vm_attachments"].reverse()
        second = inventory.normalize(reordered)
        self.assertEqual(first, second)
        self.assertEqual(first["graph_digest"], second["graph_digest"])

    def test_scope_mismatch_fails_closed(self) -> None:
        changed = copy.deepcopy(self.payload)
        changed["results"]["resources"][0]["subscriptionId"] = "22222222-2222-2222-2222-222222222222"
        with self.assertRaises(inventory.InventoryError):
            inventory.normalize(changed)

    def test_truncated_query_without_continuation_evidence_fails_closed(self) -> None:
        changed = copy.deepcopy(self.payload)
        changed["metadata"]["query_complete"] = False
        with self.assertRaises(inventory.InventoryError):
            inventory.normalize(changed)

    def test_sensitive_key_marker_fails_closed(self) -> None:
        changed = copy.deepcopy(self.payload)
        changed["metadata"]["client_secret"] = "redacted-but-forbidden"
        with self.assertRaises(inventory.InventoryError):
            inventory.normalize(changed)

    def test_query_execution_cannot_be_pre_authorized(self) -> None:
        changed = copy.deepcopy(self.contract)
        changed["query_package"]["query_execution_authorized"] = True
        with self.assertRaises(inventory.InventoryError):
            inventory.validate_contract(changed)


if __name__ == "__main__":
    unittest.main()
