from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from lab_factory.cli import main as cli_main


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class LabFactoryCliOptionOrderTests(unittest.TestCase):
    def test_repository_root_is_accepted_after_prepare(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = cli_main(
                [
                    "prepare",
                    "--repository-root",
                    str(REPOSITORY_ROOT),
                    "--profile",
                    "servicetracer-demo-api",
                ]
            )
        self.assertEqual(exit_code, 0, stderr.getvalue())
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["deployment"]["operation"], "prepare_only")
        self.assertEqual(payload["next_gate"], "parameters_required")

    def test_existing_repository_root_order_remains_supported(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            exit_code = cli_main(
                [
                    "--repository-root",
                    str(REPOSITORY_ROOT),
                    "prepare",
                    "--profile",
                    "servicetracer-demo-api",
                ]
            )
        self.assertEqual(exit_code, 0, stderr.getvalue())
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["next_gate"], "parameters_required")


if __name__ == "__main__":
    unittest.main()
