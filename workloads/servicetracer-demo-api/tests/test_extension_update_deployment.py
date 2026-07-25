from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[3]
WORKLOAD = ROOT / 'workloads' / 'servicetracer-demo-api'
BICEP = WORKLOAD / 'infra' / 'update-existing-extension.bicep'
PARSER = WORKLOAD / 'scripts' / 'assert_extension_update_what_if.py'
WORKFLOW = ROOT / '.github' / 'workflows' / 'servicetracer-demo-api-timeout-fix-deploy.yml'


def load_parser():
    spec = importlib.util.spec_from_file_location('extension_what_if', PARSER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ExtensionUpdateDeploymentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = load_parser()
        cls.expected = (
            '/subscriptions/sub/resourceGroups/rg-st-demo-api-dev-westus2/'
            'providers/Microsoft.Compute/virtualMachines/vm-st-demo-api-mst-dev/'
            'extensions/servicetracer-demo-api'
        )

    def test_bicep_targets_only_existing_extension(self):
        source = BICEP.read_text(encoding='utf-8')
        self.assertIn("resource vm 'Microsoft.Compute/virtualMachines@2024-07-01' existing", source)
        self.assertIn("resource installExtension 'Microsoft.Compute/virtualMachines/extensions@2024-07-01'", source)
        self.assertIn("forceUpdateTag: forceUpdateTag", source)
        self.assertNotIn('Microsoft.Network/', source)
        self.assertNotIn("resource vm 'Microsoft.Compute/virtualMachines@2024-07-01' =", source)

    def test_parser_accepts_exact_extension_modify(self):
        result = self.parser.assess(
            {'status': 'Succeeded', 'changes': [{'resourceId': self.expected, 'changeType': 'Modify'}]},
            self.expected,
        )
        self.assertEqual(result['status'], 'accepted_extension_only_modify')
        self.assertEqual(result['material_change_count'], 1)

    def test_parser_rejects_scope_escape(self):
        with self.assertRaises(ValueError):
            self.parser.assess(
                {'status': 'Succeeded', 'changes': [{'resourceId': self.expected, 'changeType': 'Modify'}, {'resourceId': '/subscriptions/sub/resourceGroups/other/providers/Microsoft.Network/networkSecurityGroups/x', 'changeType': 'Modify'}]},
                self.expected,
            )

    def test_parser_rejects_delete(self):
        with self.assertRaises(ValueError):
            self.parser.assess(
                {'status': 'Succeeded', 'changes': [{'resourceId': self.expected, 'changeType': 'Delete'}]},
                self.expected,
            )

    def test_workflow_is_bounded_when_present(self):
        if not WORKFLOW.exists():
            self.skipTest('deployment workflow is added in the next bounded commit')
        source = WORKFLOW.read_text(encoding='utf-8')
        self.assertIn('assert_extension_update_what_if.py', source)
        self.assertIn('az deployment group what-if', source)
        self.assertIn('az deployment group create', source)
        self.assertNotIn('/api/demo/run', source)
        self.assertNotIn('az role assignment create', source)
        self.assertNotIn('az group delete', source)
        self.assertNotIn('az resource delete', source)
        self.assertNotIn('az vm restart', source)

    def test_python_compiles(self):
        subprocess.run(['python', '-m', 'py_compile', str(PARSER)], check=True)


if __name__ == '__main__':
    unittest.main()
