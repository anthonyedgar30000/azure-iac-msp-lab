from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github" / "workflows" / "collector-demo-api.yml"


class CollectorDemoApiCorsCrlfVerificationTests(unittest.TestCase):
    def test_workflow_normalizes_crlf_before_exact_origin_match(self) -> None:
        source = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            "tr -d '\\r' < \"$ARTIFACT_DIR/cors-headers.txt\" > \"$ARTIFACT_DIR/cors-headers-normalized.txt\"",
            source,
        )
        self.assertIn(
            "grep -Fxi \"Access-Control-Allow-Origin: ${ALLOWED_ORIGIN}\" \"$ARTIFACT_DIR/cors-headers-normalized.txt\"",
            source,
        )
        self.assertNotIn(
            "grep -Eiq \"^access-control-allow-origin: ${ALLOWED_ORIGIN}\\r?$\"",
            source,
        )

    def test_real_http_crlf_header_survives_normalization_and_exact_match(self) -> None:
        origin = "https://anthonyedgar30000.github.io"
        raw = (
            "HTTP/1.1 204 No Content\r\n"
            f"Access-Control-Allow-Origin: {origin}\r\n"
            "Access-Control-Allow-Methods: POST, OPTIONS\r\n"
        ).encode()

        normalized = subprocess.run(
            ["tr", "-d", "\r"],
            input=raw,
            capture_output=True,
            check=True,
        ).stdout
        self.assertNotIn(b"\r", normalized)

        matched = subprocess.run(
            ["grep", "-Fxi", f"Access-Control-Allow-Origin: {origin}"],
            input=normalized,
            capture_output=True,
            check=False,
        )
        self.assertEqual(matched.returncode, 0, matched.stderr.decode())


if __name__ == "__main__":
    unittest.main()
