from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class ExternalValidationEvidenceSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.selector = json.loads(
            (ROOT / '.project/CURRENT.json').read_text(encoding='utf-8')
        )
        cls.reality = json.loads(
            (ROOT / '.project/current-reality-v7.json').read_text(encoding='utf-8')
        )
        cls.index = json.loads(
            (ROOT / '.project/state-index-v16.json').read_text(encoding='utf-8')
        )
        cls.evidence = json.loads(
            (
                ROOT
                / '.project/evidence/servicetracer-external-path-run-30693434244.json'
            ).read_text(encoding='utf-8')
        )
        cls.reconciliation = json.loads(
            (
                ROOT
                / '.project/reconciliations/servicetracer-external-evidence-sync-20260801.json'
            ).read_text(encoding='utf-8')
        )
        cls.authorization = json.loads(
            (
                ROOT
                / '.project/authorizations/servicetracer-external-validation-20260801.json'
            ).read_text(encoding='utf-8')
        )
        cls.handoff = (
            ROOT / '.project/handoffs/current-state-v6.md'
        ).read_text(encoding='utf-8')

    def test_selector_promotes_external_validation_state(self) -> None:
        self.assertEqual(
            self.selector['authoritative_current_reality'],
            '.project/current-reality-v7.json',
        )
        self.assertEqual(
            self.selector['authoritative_state_index'],
            '.project/state-index-v16.json',
        )
        self.assertEqual(
            self.selector['authoritative_handoff'],
            '.project/handoffs/current-state-v6.md',
        )
        self.assertEqual(
            self.selector['latest_servicetracer_external_validation_evidence'],
            '.project/evidence/servicetracer-external-path-run-30693434244.json',
        )
        self.assertIsNone(
            self.selector['active_servicetracer_external_validation_authorization']
        )

    def test_external_artifact_is_exact_and_manifest_verified(self) -> None:
        source = self.evidence['source']
        artifact = self.evidence['artifact']
        self.assertEqual(source['workflow_run_id'], 30693434244)
        self.assertEqual(source['workflow_run_attempt'], 1)
        self.assertEqual(source['workflow_conclusion'], 'success')
        self.assertEqual(artifact['artifact_id'], 8816461373)
        self.assertEqual(
            artifact['digest'],
            'sha256:f162c7a266c35146d827e05cb8b70db6d0438599149e99affe5cbfb5f18d4b6a',
        )
        self.assertTrue(artifact['internal_manifest_verified'])
        self.assertEqual(artifact['internal_manifest_entries'], 17)
        self.assertEqual(
            artifact['selected_file_sha256']['frontend-external-path.png'],
            '056a8a9f56692d5f55d56311dd6d78f2a6a9a4da775168ed71aab2951ff3c6af',
        )

    def test_browser_tls_cors_and_runtime_identity_are_verified(self) -> None:
        frontend = self.evidence['frontend_observation']
        contract = self.evidence['api_contract_observation']
        self.assertTrue(frontend['github_pages_publication_verified'])
        self.assertTrue(frontend['hosted_chrome_render_verified'])
        self.assertFalse(frontend['fixture_fallback_used'])
        self.assertEqual(contract['health_http_status'], 200)
        self.assertEqual(contract['allowed_origin_preflight_http_status'], 204)
        self.assertEqual(contract['transaction_http_status'], 200)
        self.assertTrue(contract['browser_tls_verified'])
        self.assertTrue(contract['request_header_and_body_ids_matched'])
        identity = contract['azure_host']
        self.assertTrue(identity['verified'])
        self.assertEqual(identity['resource_group'], 'rg-st-demo-api-dev-westus2')
        self.assertEqual(identity['vm_name'], 'vm-st-demo-api-mst-dev')
        self.assertEqual(identity['location'], 'westus2')
        self.assertEqual(
            identity['source_ref'],
            'ae08e7a72c14ec6deaddd3fa0f8c84b8342e0be3',
        )
        denied = contract['disallowed_origin']
        self.assertEqual(denied['http_status'], 403)
        self.assertEqual(denied['error'], 'origin_not_allowed')
        self.assertTrue(denied['fail_closed_verified'])

    def test_bounded_sample_does_not_invent_localization(self) -> None:
        sample = self.evidence['bounded_transaction_sample']
        self.assertEqual(sample['attempts'], 20)
        self.assertEqual(sample['successful_transactions'], 0)
        self.assertEqual(sample['failed_transactions'], 20)
        self.assertEqual(sample['transport_errors'], 0)
        self.assertEqual(sample['backend_counts'], {'VPN-01': 0, 'VPN-02': 20})
        self.assertEqual(sample['failure_boundary_counts'], {'radius_response': 20})
        self.assertFalse(sample['comparison_backend_observed'])
        self.assertFalse(sample['stable_backend_localization'])
        self.assertFalse(sample['exact_root_cause_claimed'])
        self.assertFalse(sample['downstream_transaction_success_verified'])
        frontend = self.evidence['frontend_observation']
        self.assertEqual(frontend['rendered_suspect'], 'Not established')
        self.assertEqual(frontend['rendered_comparison'], 'Not established')
        self.assertEqual(frontend['rendered_boundary'], 'Not established')
        self.assertTrue(frontend['technician_workflow_hidden'])

    def test_raw_api_boundary_defect_remains_open(self) -> None:
        assessment = self.evidence['evidence_boundary_assessment']
        self.assertEqual(
            assessment['status'],
            'potential_api_evidence_boundary_defect_unresolved',
        )
        self.assertEqual(assessment['raw_api_service_tracer_stops_at'], 'VPN-02')
        self.assertFalse(assessment['raw_api_stable_localization'])
        self.assertTrue(assessment['raw_api_comparison_backend_equals_suspect'])
        self.assertTrue(
            assessment['frontend_guard_prevented_unsupported_localization']
        )
        self.assertFalse(assessment['unsupported_root_cause_presented_to_operator'])

    def test_authority_is_consumed_and_sync_is_repository_only(self) -> None:
        authority = self.authorization['authorization']
        self.assertEqual(authority['status'], 'consumed_success')
        self.assertFalse(authority['active_for_one_attempt'])
        self.assertTrue(authority['attempt_consumed'])
        self.assertFalse(authority['retry_authorized'])
        self.assertFalse(authority['manual_dispatch_authorized'])
        sync_authority = self.reconciliation['authority']
        for field in (
            'workflow_dispatch_or_rerun_by_this_sync',
            'external_live_post_by_this_sync',
            'azure_authentication_or_query_by_this_sync',
            'arm_what_if_by_this_sync',
            'guest_command_by_this_sync',
            'azure_mutation_by_this_sync',
            'rbac_mutation',
            'deployment',
            'repair',
            'redeployment',
            'rollback',
            'cleanup',
        ):
            self.assertFalse(sync_authority[field], field)

    def test_current_reality_preserves_unknowns_and_next_gate(self) -> None:
        service = self.reality['domain_state']['servicetracer_demo_api']
        self.assertTrue(service['external_browser_path_verified'])
        self.assertTrue(service['cors_verified'])
        self.assertTrue(service['transaction_post_verified'])
        self.assertFalse(service['downstream_transaction_success_verified'])
        self.assertFalse(service['stable_backend_localization_verified'])
        self.assertTrue(service['potential_api_evidence_boundary_defect'])
        self.assertTrue(service['unidentified_browser_console_404_observed'])
        unknowns = self.reality['freshness_and_unknowns']
        self.assertFalse(unknowns['actual_azure_cost_freshly_observed'])
        self.assertFalse(unknowns['monitoring_alert_delivery_freshly_verified'])
        self.assertEqual(
            self.reality['next_gate']['operation'],
            'repository_only_api_evidence_boundary_correction_planning',
        )
        self.assertIn('another live POST authorized: false', self.handoff)


if __name__ == '__main__':
    unittest.main()
