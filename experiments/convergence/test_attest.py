import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("convergence_attest", HERE / "attest.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ConvergenceAttestationTests(unittest.TestCase):
    def setUp(self):
        self.topology = MODULE.load_json_compatible_yaml(HERE / "topology.yaml")

    def test_all_valid_keeps_all_nodes_valid(self):
        observations = {edge["id"]: MODULE.VALID for edge in self.topology["edges"]}
        result = MODULE.evaluate(self.topology, observations)
        self.assertTrue(
            all(state == MODULE.VALID for state in result["node_states"].values())
        )
        self.assertEqual(result["failures"], [])
        self.assertEqual(result["unknowns"], [])
        self.assertEqual(result["candidate_actions"], [])

    def test_fault_poisons_only_dependent_path(self):
        scenario = MODULE.load_json_compatible_yaml(
            HERE / "scenarios" / "network-workload-edge-fault.json"
        )
        result = MODULE.evaluate(self.topology, scenario["edge_observations"])
        self.assertEqual(result["node_states"], scenario["expected"]["node_states"])
        self.assertEqual(
            result["candidate_actions"],
            [{
                "edge": "network-workload",
                "action": scenario["expected"]["candidate_action"],
            }],
        )
        self.assertEqual(result["edge_states"]["network-workload"], MODULE.FAULTED)

    def test_unrelated_logging_branch_remains_valid(self):
        observations = {
            "root-network": MODULE.VALID,
            "root-logging": MODULE.VALID,
            "network-workload": MODULE.FAULTED,
            "workload-service": MODULE.VALID,
        }
        result = MODULE.evaluate(self.topology, observations)
        self.assertEqual(result["node_states"]["logging"], MODULE.VALID)

    def test_missing_evidence_is_unknown_and_blocks_downstream_trust(self):
        observations = {
            "root-network": MODULE.VALID,
            "root-logging": MODULE.VALID,
            "workload-service": MODULE.VALID,
        }
        result = MODULE.evaluate(self.topology, observations)
        self.assertEqual(result["edge_states"]["network-workload"], MODULE.UNKNOWN)
        self.assertEqual(result["node_states"]["workload"], MODULE.POISONED)
        self.assertEqual(result["node_states"]["service"], MODULE.POISONED)
        self.assertEqual(result["candidate_actions"], [])
        self.assertEqual(len(result["unknowns"]), 1)


if __name__ == "__main__":
    unittest.main()
