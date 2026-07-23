from __future__ import annotations

from pathlib import Path
import py_compile
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]
INFRA = ROOT / "infra"
PLAN_VERIFIER_PATH = INFRA / "scripts" / "verify_existing_collector_publication_plan.py"
EXECUTOR_PATH = INFRA / "scripts" / "execute_existing_collector_report_publication.sh"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "existing-collector-report-publication.yml"


class ExistingCollectorReportPublicationTests(unittest.TestCase):
    def test_promoted_publication_files_are_present_and_parse(self) -> None:
        self.assertTrue(WORKFLOW_PATH.is_file())
        self.assertTrue(PLAN_VERIFIER_PATH.is_file())
        self.assertTrue(EXECUTOR_PATH.is_file())
        py_compile.compile(str(PLAN_VERIFIER_PATH), doraise=True)
        subprocess.run(
            ["bash", "-n", str(EXECUTOR_PATH)],
            check=True,
            capture_output=True,
            text=True,
        )


if __name__ == "__main__":
    unittest.main()
