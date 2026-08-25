import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent

ATTEST_SPEC = importlib.util.spec_from_file_location("convergence_attest", HERE / "attest.py")
ATTEST = importlib.util.module_from_spec(ATTEST_SPEC)
assert ATTEST_SPEC.loader is not None
ATTEST_SPEC.loader.exec_module(ATTEST)

WATCHDOG_SPEC = importlib.util.spec_from_file_location(
    "watchdog_attestation", HERE / "watchdog_attestation.py"
)
WATCHDOG = importlib.util.module_from_spec(WATCHDOG_SPEC)
assert WATCHDOG_SPEC.loader is not None
WATCHDOG_SPEC.loader.exec_module(WATCHDOG)


class ConvergenceAttestationTests(unittest.TestCase):
    def setUp(self):
        self.topology = ATTEST.load_json_compatible_yaml(HERE / "topology.yaml")

    def test_all_valid_keeps_all_nodes_valid(self):
        observations = {edge["id"]: ATTEST.VALID for edge in self.topology["edges"]}
        result = ATTEST.evaluate(self.topology, observations)
        self.assertTrue(
            all(state == ATTEST.VALID for state in result["node_states"].values())
        )
        self.assertEqual(result["failures"], [])
        self.assertEqual(result["unknowns"], [])
        self.assertEqual(result["node_failures"], [])
        self.assertEqual(result["node_unknowns"], [])
        self.assertEqual(result["candidate_actions"], [])

    def test_fault_poisons_only_dependent_path(self):
        scenario = ATTEST.load_json_compatible_yaml(
            HERE / "scenarios" / "network-workload-edge-fault.json"
        )
        result = ATTEST.evaluate(self.topology, scenario["edge_observations"])
        self.assertEqual(result["node_states"], scenario["expected"]["node_states"])
        self.assertEqual(
            result["candidate_actions"],
            [{
                "edge": "network-workload",
                "action": scenario["expected"]["candidate_action"],
            }],
        )
        self.assertEqual(result["edge_states"]["network-workload"], ATTEST.FAULTED)

    def test_unrelated_logging_branch_remains_valid(self):
        observations = {
            "root-network": ATTEST.VALID,
            "root-logging": ATTEST.VALID,
            "network-workload": ATTEST.FAULTED,
            "workload-service": ATTEST.VALID,
        }
        result = ATTEST.evaluate(self.topology, observations)
        self.assertEqual(result["node_states"]["logging"], ATTEST.VALID)

    def test_missing_evidence_is_unknown_and_blocks_downstream_trust(self):
        observations = {
            "root-network": ATTEST.VALID,
            "root-logging": ATTEST.VALID,
            "workload-service": ATTEST.VALID,
        }
        result = ATTEST.evaluate(self.topology, observations)
        self.assertEqual(result["edge_states"]["network-workload"], ATTEST.UNKNOWN)
        self.assertEqual(result["node_states"]["workload"], ATTEST.POISONED)
        self.assertEqual(result["node_states"]["service"], ATTEST.POISONED)
        self.assertEqual(result["candidate_actions"], [])
        self.assertEqual(len(result["unknowns"]), 1)

    def test_watchdog_fault_becomes_local_fault_and_poisons_descendant(self):
        scenario = ATTEST.load_json_compatible_yaml(
            HERE / "scenarios" / "watchdog-workload-fault.json"
        )
        binding = scenario["binding"]
        local_attestation = WATCHDOG.wrap_watchdog_classification(
            scenario["watchdog_record"],
            node_id=binding["node_id"],
            evaluation_time=binding["evaluation_time"],
            max_age_seconds=binding["max_age_seconds"],
        )
        self.assertEqual(
            local_attestation["status"], scenario["expected"]["attestation_status"]
        )
        self.assertEqual(local_attestation["source_outcome"], "UNSATISFIED")
        self.assertEqual(local_attestation["source_reason"], "systemd_failed")

        result = ATTEST.evaluate(
            self.topology,
            scenario["edge_observations"],
            WATCHDOG.as_node_observation(local_attestation),
        )
        self.assertEqual(result["node_states"], scenario["expected"]["node_states"])
        self.assertEqual(result["node_failures"][0]["node"], "workload")
        self.assertEqual(result["node_failures"][0]["poisoned_path"], ["service"])
        self.assertEqual(result["node_states"]["logging"], ATTEST.VALID)

    def test_stale_watchdog_success_cannot_restore_trust(self):
        scenario = ATTEST.load_json_compatible_yaml(
            HERE / "scenarios" / "watchdog-workload-fault.json"
        )
        source = dict(scenario["watchdog_record"])
        source["outcome"] = "SATISFIED"
        source["reason"] = "systemd_active"

        local_attestation = WATCHDOG.wrap_watchdog_classification(
            source,
            node_id="workload",
            evaluation_time=200.0,
            max_age_seconds=60.0,
        )
        self.assertEqual(local_attestation["status"], WATCHDOG.UNKNOWN)
        self.assertEqual(
            local_attestation["attestation_reason"], "stale_watchdog_classification"
        )

        result = ATTEST.evaluate(
            self.topology,
            scenario["edge_observations"],
            WATCHDOG.as_node_observation(local_attestation),
        )
        self.assertEqual(result["node_states"]["workload"], ATTEST.UNKNOWN)
        self.assertEqual(result["node_states"]["service"], ATTEST.POISONED)
        self.assertEqual(result["node_states"]["logging"], ATTEST.VALID)


if __name__ == "__main__":
    unittest.main()
