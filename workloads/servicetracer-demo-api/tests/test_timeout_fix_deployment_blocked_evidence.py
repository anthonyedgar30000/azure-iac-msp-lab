from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / '.project' / 'evidence' / 'servicetracer-demo-api-timeout-fix-deployment-blocked-20260724.json'
RECONCILIATION = ROOT / '.project' / 'reconciliations' / 'servicetracer-demo-api-timeout-fix-deployment-blocked.json'


class TimeoutFixDeploymentBlockedEvidenceTests(unittest.TestCase):
    def test_evidence_preserves_no_mutation_and_missing_permission(self):
        evidence = json.loads(EVIDENCE.read_text(encoding='utf-8'))
        self.assertEqual(evidence['authorization']['final_status'], 'consumed_blocked')
        self.assertEqual(evidence['attempts'][1]['missing_action'], 'Microsoft.Compute/virtualMachines/extensions/write')
        self.assertFalse(evidence['attempts'][1]['azure_resource_mutation_performed'])
        self.assertFalse(evidence['attempts'][1]['deployment_performed'])
        self.assertFalse(evidence['resolved_state']['azure_deployment_succeeded'])
        self.assertFalse(evidence['resolved_state']['deployed_timeout_fix_verified'])
        self.assertFalse(evidence['resolved_state']['live_twenty_attempt_replay_performed'])

    def test_reconciliation_keeps_rbac_and_replay_separate(self):
        record = json.loads(RECONCILIATION.read_text(encoding='utf-8'))
        self.assertEqual(record['result'], 'blocked_before_mutation')
        self.assertFalse(record['grant']['rbac_mutation_authorized'])
        self.assertFalse(record['grant']['transaction_replay_authorized'])
        self.assertFalse(record['attempt_2']['azure_mutation_performed'])
        self.assertFalse(record['failure_and_rollback']['rollback_performed'])
        self.assertFalse(record['next_gate']['execution_authorized'])

    def test_public_health_is_not_collapsed_into_deployed_fix(self):
        record = json.loads(RECONCILIATION.read_text(encoding='utf-8'))
        truth = record['current_truth']
        self.assertTrue(truth['public_health_verified'])
        self.assertTrue(truth['repository_timeout_fix_ready'])
        self.assertFalse(truth['deployed_timeout_fix_verified'])
        self.assertFalse(truth['corrected_health_contract_observed'])


if __name__ == '__main__':
    unittest.main()
