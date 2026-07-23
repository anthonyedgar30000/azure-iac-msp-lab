from __future__ import annotations

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "collector-demo-api.yml"
ISOLATED_ROOT = ROOT / "infra" / "collector-demo-api.bicep"


class CollectorDemoApiDeploymentNameTests(unittest.TestCase):
    def test_parent_and_nested_arm_deployment_names_are_distinct(self) -> None:
        workflow_lines = WORKFLOW.read_text(encoding="utf-8").splitlines()
        isolated_root = ISOLATED_ROOT.read_text(encoding="utf-8")

        parent_name = None
        for index, line in enumerate(workflow_lines):
            if "az deployment group create" not in line:
                continue
            for candidate in workflow_lines[index + 1 : index + 6]:
                match = re.search(r'--name "([^"]+)"', candidate)
                if match:
                    parent_name = match.group(1)
                    break
            if parent_name:
                break

        nested_match = re.search(
            r"module collectorDemoApi .*?= \{.*?name: '([^']+)'",
            isolated_root,
            re.DOTALL,
        )

        self.assertIsNotNone(parent_name)
        self.assertIsNotNone(nested_match)
        nested_name = nested_match.group(1)
        normalized_parent_name = parent_name.replace(
            "${LAB_ENVIRONMENT}", "${environment}"
        )

        self.assertEqual(parent_name, "collector-demo-api-${LAB_ENVIRONMENT}")
        self.assertEqual(
            nested_name, "collector-demo-api-resources-${environment}"
        )
        self.assertNotEqual(normalized_parent_name, nested_name)


if __name__ == "__main__":
    unittest.main()
