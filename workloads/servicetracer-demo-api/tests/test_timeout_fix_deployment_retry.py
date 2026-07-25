from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
RETRY = ROOT / '.github' / 'workflows' / 'servicetracer-demo-api-timeout-fix-deploy-retry.yml'
EVIDENCE = ROOT / '.project' / 'evidence' / 'servicetracer-demo-api-timeout-fix-deployment-blocked-20260724.json'


class TimeoutFixDeploymentRetryTests(unittest.TestCase):
    def test_retry_reads_nested_or_top_level_power_state_null_safely(self):
        source = RETRY.read_text(encoding='utf-8')
        self.assertIn('(.statuses // .instanceView.statuses // [])', source)
        self.assertIn('PowerState/running', source)

    def test_retry_keeps_extension_only_gate_and_no_transaction_replay(self):
        source = RETRY.read_text(encoding='utf-8')
        self.assertIn('assert_extension_update_what_if.py', source)
        self.assertIn('az deployment group what-if', source)
        self.assertIn('az deployment group create', source)
        self.assertNotIn('/api/demo/run', source)
        self.assertNotIn('az role assignment create', source)
        self.assertNotIn('az group delete', source)
        self.assertNotIn('az resource delete', source)
        self.assertNotIn('az vm restart', source)

    def test_retry_has_rollback_and_exact_health_contract(self):
        source = RETRY.read_text(encoding='utf-8')
        self.assertIn('PREVIOUS_TRUSTED_SOURCE_REF', source)
        self.assertIn('rollback_performed:true', source)
        for field in (
            'backend_timeout_seconds==10',
            'max_parallel_transactions==10',
            'max_attempts==50',
            'estimated_max_execution_seconds==50',
        ):
            self.assertIn(field, source)

    def test_temporary_promotion_was_replaced_by_durable_evidence(self):
        self.assertTrue(EVIDENCE.is_file())
        source = EVIDENCE.read_text(encoding='utf-8')
        self.assertIn('consumed_blocked', source)
        self.assertIn('Microsoft.Compute/virtualMachines/extensions/write', source)
        self.assertIn('"azure_resource_mutation_performed": false', source)


if __name__ == '__main__':
    unittest.main()
