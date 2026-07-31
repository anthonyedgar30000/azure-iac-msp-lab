from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]

class PostDeploymentRuntimeSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.selector = json.loads((ROOT / '.project/CURRENT.json').read_text(encoding='utf-8'))
        cls.reality = json.loads((ROOT / '.project/current-reality-v6.json').read_text(encoding='utf-8'))
        cls.index = json.loads((ROOT / '.project/state-index-v15.json').read_text(encoding='utf-8'))
        cls.plan = json.loads((ROOT / '.project/evidence/servicetracer-demo-api-plan-run-30660575435.json').read_text(encoding='utf-8'))
        cls.deploy = json.loads((ROOT / '.project/evidence/servicetracer-demo-api-deployment-run-30661015789.json').read_text(encoding='utf-8'))
        cls.recon = json.loads((ROOT / '.project/reconciliations/servicetracer-plan-deploy-runtime-sync-20260731.json').read_text(encoding='utf-8'))
        cls.handoff = (ROOT / '.project/handoffs/current-state-v5.md').read_text(encoding='utf-8')

    def test_selector_promotes_post_deployment_state(self) -> None:
        self.assertEqual(self.selector['authoritative_current_reality'], '.project/current-reality-v6.json')
        self.assertEqual(self.selector['authoritative_state_index'], '.project/state-index-v15.json')
        self.assertEqual(self.selector['authoritative_handoff'], '.project/handoffs/current-state-v5.md')
        self.assertIsNone(self.selector['active_servicetracer_planning_authorization'])
        self.assertIsNone(self.selector['active_deployment_authorization'])
        self.assertIsNone(self.selector['active_cleanup_authorization'])

    def test_plan_and_deployment_artifacts_are_exact(self) -> None:
        self.assertEqual(self.plan['source']['workflow_run_id'], 30660575435)
        self.assertEqual(self.plan['source']['head_sha'], 'ae08e7a72c14ec6deaddd3fa0f8c84b8342e0be3')
        self.assertEqual(self.plan['artifact']['sha256'], '76911fb3b626786593df022bdfb654c01efde11cd0b3dc1809679c431f11d1f2')
        self.assertEqual(self.plan['what_if']['status'], 'accepted_independent_workload_create_plan')
        self.assertEqual(self.deploy['source']['workflow_run_id'], 30661015789)
        self.assertEqual(self.deploy['artifact']['sha256'], '80b0819552623c13cfa244ec2d480f7606c2f224516a5d6c9882233fdbe2b478')
        self.assertTrue(self.deploy['artifact']['internal_manifest_verified'])
        self.assertEqual(self.deploy['artifact']['internal_manifest_entries'], 45)
        self.assertEqual(self.deploy['deployment']['provisioning_state'], 'Succeeded')
        service = self.reality['domain_state']['servicetracer_demo_api']
        self.assertFalse(service['repository_head_matches_deployed_source_ref'])
        self.assertEqual(service['undeployed_repository_commits'], ['b5bfd616d2f3faab5f692301c4b71c46a6f9557f', '2ad9557e21cddeed6fc9437c8f20c32b387bf2a2'])

    def test_runtime_health_and_identity_are_bounded(self) -> None:
        runtime = self.deploy['runtime_evidence']
        self.assertEqual(runtime['local_process_health']['status'], 'healthy')
        public = runtime['public_fqdn_health_from_vm_guest']
        self.assertEqual(public['status'], 'healthy')
        self.assertTrue(public['azure_host']['verified'])
        self.assertEqual(public['azure_host']['resource_group'], 'rg-st-demo-api-dev-westus2')
        self.assertEqual(public['azure_host']['vm_name'], 'vm-st-demo-api-mst-dev')
        self.assertEqual(public['azure_host']['location'], 'westus2')
        self.assertEqual(public['azure_host']['source_ref'], 'ae08e7a72c14ec6deaddd3fa0f8c84b8342e0be3')
        self.assertFalse(runtime['external_browser_path_verified'])
        self.assertFalse(runtime['cors_verified'])
        self.assertFalse(runtime['transaction_post_verified'])

    def test_no_operational_authority_remains(self) -> None:
        self.assertTrue(all(value is None for value in self.index['active_authorizations'].values()))
        authority = self.recon['authority']
        for field in (
            'workflow_dispatch_or_rerun_by_this_sync', 'azure_authentication_or_query_by_this_sync',
            'guest_command_by_this_sync', 'arm_what_if_by_this_sync', 'azure_mutation_by_this_sync',
            'deployment', 'cleanup', 'rollback',
        ):
            self.assertFalse(authority[field], field)
        self.assertTrue(self.deploy['authorization']['attempt_consumed'])
        self.assertFalse(self.deploy['authorization']['rerun_authorized'])
        self.assertFalse(self.deploy['authorization']['cleanup_authorized'])

    def test_handoff_preserves_next_gate(self) -> None:
        self.assertIn('deployment_succeeded != service_validated', self.handoff)
        self.assertIn('public_FQDN_from_VM_guest != external_browser_path', self.handoff)
        self.assertIn('GitHub Pages publication', self.handoff)
        self.assertIn('POST /api/demo/run', self.handoff)
        self.assertIn('actual month-to-date cost', self.handoff)

if __name__ == '__main__':
    unittest.main()
