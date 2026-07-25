from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / '.github/workflows/servicetracer-demo-api-extension-write-verify-only-2.yml'
ASSERTION = ROOT / 'workloads/servicetracer-demo-api/scripts/assert_extension_write_permission_verify_only.py'
AUTH = ROOT / '.project/authorizations/servicetracer-demo-api-extension-write-verify-only-20260725-2.json'


class ExtensionWriteVerifyOnlyAttempt2Tests(unittest.TestCase):
    def test_workflow_is_verify_only_source_bound_and_protected(self) -> None:
        source = WORKFLOW.read_text(encoding='utf-8')
        self.assertIn('environment: azure-api-payg', source)
        self.assertIn('id-token: write', source)
        self.assertIn('fetch-depth: 2', source)
        self.assertIn('.reviewed_package_head == $parent_head', source)
        self.assertIn('az deployment group validate', source)
        self.assertIn('az deployment group what-if', source)
        self.assertIn('assert_extension_write_permission_verify_only.py', source)
        self.assertIn('resource_count_preserved:7', source)
        self.assertIn('azure_mutation_performed:false', source)
        self.assertIn('deployment_authorized:false', source)
        for prohibited in (
            'az deployment group create',
            'az vm extension set',
            'az vm run-command',
            'az vm restart',
            '/api/demo/run',
            'az role assignment create',
            'az role definition create',
            'az group delete',
        ):
            self.assertNotIn(prohibited, source)

    def test_assertion_preserves_authority_boundary(self) -> None:
        source = ASSERTION.read_text(encoding='utf-8')
        self.assertIn("'effective_extension_write_permission_verified': True", source)
        self.assertIn("'azure_mutation_performed': False", source)
        self.assertIn("'application_deployment_performed': False", source)
        self.assertIn("'transaction_replay_performed': False", source)
        self.assertIn("'deployment_authorized': False", source)

    def test_authorization_is_bounded_and_non_renewing(self) -> None:
        record = json.loads(AUTH.read_text(encoding='utf-8'))
        self.assertEqual(record['status'], 'authorized_not_consumed')
        self.assertEqual(record['authorization_source'], 'Explicit governed control message: Proceed authorized')
        self.assertEqual(record['source_binding']['base_commit'], '6c53a78cfcec9dede2d0dbbd5e102b11a90035b1')
        authority = record['authority']
        for permitted in (
            'repository_verification_package',
            'pull_request_creation',
            'azure_login',
            'control_plane_read',
            'arm_validate',
            'arm_what_if',
            'public_health_get',
            'sanitized_evidence_upload',
        ):
            self.assertTrue(authority[permitted])
        for prohibited in (
            'resource_mutation',
            'application_deployment',
            'vm_command',
            'service_restart',
            'transaction_replay',
            'rbac_mutation',
            'network_mutation',
            'pull_request_merge',
            'github_pages_publication',
            'cleanup',
        ):
            self.assertFalse(authority[prohibited])
        self.assertIn('Retry requires new explicit authorization', record['termination'])
        self.assertIn('Verification authorized != deployment authorized', record['claim_boundary'])


if __name__ == '__main__':
    unittest.main()
