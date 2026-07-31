from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SELECTOR = ROOT / '.project/CURRENT.json'
REALITY = ROOT / '.project/current-reality-v5.json'
INDEX = ROOT / '.project/state-index-v14.json'
HANDOFF = ROOT / '.project/handoffs/current-state-v4.md'
SYNC = ROOT / '.project/reconciliations/post-pr253-student-subscription-sync-20260730.json'
WORKFLOW = ROOT / '.github/workflows/servicetracer-demo-api-subproject-plan.yml'

MAIN = 'af4b050ab18110882e3551f66c69eb2b73a73f7b'
PR253_SOURCE = '161c447a445d86364719d3d414ac6c7f6628e7b8'


class PostPr253StudentSubscriptionSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.selector = json.loads(SELECTOR.read_text(encoding='utf-8'))
        cls.reality = json.loads(REALITY.read_text(encoding='utf-8'))
        cls.index = json.loads(INDEX.read_text(encoding='utf-8'))
        cls.handoff = HANDOFF.read_text(encoding='utf-8')
        cls.sync = json.loads(SYNC.read_text(encoding='utf-8'))
        cls.workflow = WORKFLOW.read_text(encoding='utf-8')

    def test_post_pr253_state_is_preserved_as_historical(self) -> None:
        self.assertEqual(self.reality['repository_state']['observed_main'], MAIN)
        self.assertEqual(self.reality['repository_state']['latest_merged_pull_request'], 253)
        self.assertEqual(self.reality['repository_state']['latest_merged_source_head'], PR253_SOURCE)
        self.assertNotEqual(self.selector['authoritative_current_reality'], '.project/current-reality-v5.json')
        records = {item['path']: item for item in self.selector['compatibility_records']}
        self.assertIn('.project/current-reality-v5.json', records)
        self.assertIn('.project/state-index-v14.json', records)
        self.assertIn('.project/handoffs/current-state-v4.md', records)

    def test_historical_planner_boundary_remains_exact(self) -> None:
        state = self.reality['domain_state']['azure_lab_factory_lite']
        self.assertEqual(state['github_environment'], 'azure-lab')
        self.assertEqual(state['subscription_boundary'], 'single_subscription')
        self.assertEqual(state['subscription_intent'], 'Azure for Students only')
        self.assertFalse(state['corrected_planner_dispatch_verified'])
        self.assertFalse(state['deployment_capability'])
        for marker in ('environment: azure-lab', 'AZURE_CLIENT_ID', 'AZURE_TENANT_ID', 'AZURE_SUBSCRIPTION_ID', 'ProviderNoRbac'):
            self.assertIn(marker, self.workflow)
        self.assertNotIn('az deployment sub create', self.workflow)
        self.assertEqual(self.workflow.count('uses: azure/login@v2'), 1)

    def test_historical_authorities_remain_consumed(self) -> None:
        historical = self.reality['domain_state']['servicetracer_planning_run1_historical']
        self.assertTrue(historical['authority_consumed'])
        self.assertFalse(historical['rerun_authorized'])
        self.assertTrue(all(value is None for value in self.index['active_authorizations'].values()))
        authority = self.sync['authority']
        self.assertFalse(authority['deployment'])
        self.assertFalse(authority['cleanup'])
        self.assertFalse(authority['rollback'])

    def test_historical_handoff_is_not_rewritten(self) -> None:
        self.assertIn(f'observed main: {MAIN}', self.handoff)
        self.assertIn('latest merged PR: #253', self.handoff)
        self.assertIn('corrected planner has not been dispatched', self.handoff)


if __name__ == '__main__':
    unittest.main()
