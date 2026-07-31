from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
CLASSIFIER = ROOT / "workloads" / "servicetracer-demo-api" / "scripts" / "assert_what_if.py"
TARGET = "rg-st-demo-api-dev-westus2"
SUFFIX = "mst-dev"
BASE = f"/subscriptions/x/resourceGroups/{TARGET}/providers"


def load_classifier():
    spec = importlib.util.spec_from_file_location("existing_rg_classifier", CLASSIFIER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def workload_changes() -> list[dict[str, object]]:
    return [
        {
            "changeType": "Create",
            "resourceId": f"{BASE}/Microsoft.Network/publicIPAddresses/pip-st-demo-api-vm-{SUFFIX}",
            "after": {"type": "Microsoft.Network/publicIPAddresses"},
        },
        {
            "changeType": "Create",
            "resourceId": f"{BASE}/Microsoft.Compute/virtualMachines/vm-st-demo-api-{SUFFIX}",
            "after": {"type": "Microsoft.Compute/virtualMachines"},
        },
    ]


class ExistingResourceGroupWhatIfTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.classifier = load_classifier()

    def classify(self, changes: list[dict[str, object]]):
        return self.classifier.classify(
            {"status": "Succeeded", "error": None, "changes": changes},
            target_resource_group=TARGET,
            dependency_resource_group="rg-servicetracer-dev-westus2",
            suffix=SUFFIX,
        )

    def test_omitted_existing_resource_group_is_accepted(self) -> None:
        result = self.classify(workload_changes())
        self.assertEqual(result["target_resource_group_state"], "omitted_existing")
        self.assertEqual(len(result["active_changes"]), 2)

    def test_no_change_existing_resource_group_is_accepted(self) -> None:
        changes = [
            {
                "changeType": "NoChange",
                "resourceId": f"/subscriptions/x/resourceGroups/{TARGET}",
                "before": {"type": "Microsoft.Resources/resourceGroups"},
                "after": {"type": "Microsoft.Resources/resourceGroups"},
            },
            *workload_changes(),
        ]
        result = self.classify(changes)
        self.assertEqual(result["target_resource_group_state"], "existing_no_change")

    def test_resource_group_create_is_still_accepted(self) -> None:
        changes = [
            {
                "changeType": "Create",
                "resourceId": f"/subscriptions/x/resourceGroups/{TARGET}",
                "after": {"type": "Microsoft.Resources/resourceGroups"},
            },
            *workload_changes(),
        ]
        result = self.classify(changes)
        self.assertEqual(result["target_resource_group_state"], "create")

    def test_resource_group_modify_delete_and_replace_remain_rejected(self) -> None:
        for change_type in ("Modify", "Delete", "Replace"):
            changes = [
                {
                    "changeType": change_type,
                    "resourceId": f"/subscriptions/x/resourceGroups/{TARGET}",
                    "after": {"type": "Microsoft.Resources/resourceGroups"},
                },
                *workload_changes(),
            ]
            with self.subTest(change_type=change_type), self.assertRaises(SystemExit):
                self.classify(changes)

    def test_required_workload_creates_are_not_optional(self) -> None:
        with self.assertRaises(SystemExit):
            self.classify(workload_changes()[:-1])


if __name__ == "__main__":
    unittest.main()
