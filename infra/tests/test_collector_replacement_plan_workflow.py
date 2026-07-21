from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
PLAN_WORKFLOW = (
    ROOT / ".github" / "workflows" / "collector-replacement-plan.yml"
).read_text(encoding="utf-8")
DRIFT_SCRIPT = (
    ROOT / "infra" / "scripts" / "check_collector_image_drift.sh"
).read_text(encoding="utf-8")
RESOLVER = (ROOT / "infra" / "scripts" / "resolve_vm_plan.sh").read_text(
    encoding="utf-8"
)


class CollectorReplacementPlanWorkflowTests(unittest.TestCase):
    def test_normal_planner_blocks_image_drift_before_arm_validation(self) -> None:
        self.assertIn("check_collector_image_drift.sh", RESOLVER)
        self.assertIn("--mode guard", RESOLVER)
        self.assertLess(
            RESOLVER.index("check_collector_image_drift.sh"),
            RESOLVER.index("az deployment group validate"),
        )
        self.assertIn("exit 42", DRIFT_SCRIPT)
        self.assertIn("replacement_required", DRIFT_SCRIPT)

    def test_replacement_planner_requires_exact_intent_and_oidc(self) -> None:
        self.assertIn("workflow_dispatch:", PLAN_WORKFLOW)
        self.assertIn("PLAN:${RESOURCE_GROUP}:${vm_name}", PLAN_WORKFLOW)
        self.assertIn('[[ "$CONFIRMATION" == "$expected" ]]', PLAN_WORKFLOW)
        self.assertIn("id-token: write", PLAN_WORKFLOW)
        self.assertIn("uses: azure/login@v2", PLAN_WORKFLOW)
        self.assertIn("environment: azure-lab", PLAN_WORKFLOW)
        self.assertIn("--mode plan", PLAN_WORKFLOW)

    def test_replacement_planner_is_read_only(self) -> None:
        combined = f"{PLAN_WORKFLOW}\n{DRIFT_SCRIPT}"
        forbidden_patterns = (
            r"\baz\s+vm\s+(create|delete|deallocate|start|stop|restart|update)\b",
            r"\baz\s+disk\s+(create|delete|detach|attach|update)\b",
            r"\baz\s+snapshot\s+(create|delete|update)\b",
            r"\baz\s+network\s+nic\s+(create|delete|update)\b",
            r"\baz\s+deployment\s+group\s+create\b",
            r"\baz\s+resource\s+(create|delete|update)\b",
        )
        for pattern in forbidden_patterns:
            self.assertIsNone(re.search(pattern, combined))

        self.assertIn("execution_authorized:false", DRIFT_SCRIPT)
        self.assertIn("execution_performed:false", DRIFT_SCRIPT)
        self.assertIn("azure_mutations_performed:false", DRIFT_SCRIPT)
        self.assertIn("evidence_disk_must_be_preserved:true", DRIFT_SCRIPT)


if __name__ == "__main__":
    unittest.main()
