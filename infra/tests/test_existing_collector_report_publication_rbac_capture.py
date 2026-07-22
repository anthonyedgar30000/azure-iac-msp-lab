from __future__ import annotations

from pathlib import Path
import re
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]
PLANNER_PATH = ROOT / "infra" / "scripts" / "plan_existing_collector_report_publication.sh"
PLANNER = PLANNER_PATH.read_text(encoding="utf-8")


class ExistingCollectorReportPublicationRbacCaptureTests(unittest.TestCase):
    def test_planner_shell_syntax_is_valid(self) -> None:
        subprocess.run(["bash", "-n", str(PLANNER_PATH)], check=True)

    def test_scoped_role_queries_never_use_subscription_all_mode(self) -> None:
        role_query_blocks = re.findall(
            r"az role assignment list \\\n(?:\s+.*\n){1,6}",
            PLANNER,
        )
        self.assertEqual(len(role_query_blocks), 2)
        for block in role_query_blocks:
            self.assertIn("--scope", block)
            self.assertIn("--include-inherited", block)
            self.assertNotIn("--all", block)
        self.assertIsNone(re.search(r"(?m)^\s+--all(?:\s|$)", PLANNER))

    def test_rbac_evidence_is_atomic_nonempty_and_json_validated(self) -> None:
        for expected in (
            'temp_path="$(mktemp "${destination}.partial.XXXXXX")"',
            '[[ ! -s "$temp_path" ]]',
            "'type == $expected_type'",
            'mv -- "$temp_path" "$destination"',
            'capture_json array "$artifact_dir/visible-resource-group-role-assignments-all.json"',
            'capture_json array "$artifact_dir/visible-report-storage-role-assignments-all.json"',
            'capture_json array "$artifact_dir/visible-collector-role-assignments.json"',
        ):
            self.assertIn(expected, PLANNER)

        self.assertNotIn(
            '> "$artifact_dir/visible-resource-group-role-assignments-all.json"',
            PLANNER,
        )
        self.assertNotIn(
            '> "$artifact_dir/visible-report-storage-role-assignments-all.json"',
            PLANNER,
        )

    def test_planner_remains_read_only(self) -> None:
        prohibited = (
            "az deployment group create",
            "az role assignment create",
            "az role assignment delete",
            "az storage account create",
            "az storage account delete",
            "az vm run-command invoke",
            "az vm create",
            "az vm delete",
            "az resource delete",
            "az group create",
            "az group delete",
        )
        for command in prohibited:
            self.assertNotIn(command, PLANNER)


if __name__ == "__main__":
    unittest.main()
