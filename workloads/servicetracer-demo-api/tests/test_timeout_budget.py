from __future__ import annotations

import math
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
import unittest

ROOT = Path(__file__).resolve().parents[3]
DEMO_API = ROOT / "demo_api"
INDEPENDENT_INSTALLER = ROOT / "workloads" / "servicetracer-demo-api" / "scripts" / "install.sh"
COLLECTOR_INSTALLER = ROOT / "infra" / "scripts" / "install_collector_demo_api.sh"

sys.path.insert(0, str(DEMO_API))

import core  # noqa: E402
import runtime  # noqa: E402
import standalone_server  # noqa: E402


def shell_constant(source: str, name: str) -> int:
    match = re.search(rf"^{re.escape(name)}='([0-9]+)'$", source, re.MULTILINE)
    if not match:
        raise AssertionError(f"missing numeric shell constant {name}")
    return int(match.group(1))


class DemoApiTimeoutBudgetTests(unittest.TestCase):
    def test_installers_share_a_bounded_timeout_contract(self):
        for installer in (INDEPENDENT_INSTALLER, COLLECTOR_INSTALLER):
            subprocess.run(["bash", "-n", str(installer)], check=True)
            source = installer.read_text(encoding="utf-8")
            backend_timeout = shell_constant(source, "BACKEND_TIMEOUT_SECONDS")
            workers = shell_constant(source, "MAX_PARALLEL_TRANSACTIONS")
            proxy_timeout = shell_constant(source, "PROXY_READ_TIMEOUT_SECONDS")

            expected_worst_case = math.ceil(core.MAX_ATTEMPTS / workers) * backend_timeout
            self.assertEqual(backend_timeout, 10)
            self.assertEqual(workers, 10)
            self.assertEqual(expected_worst_case, 50)
            self.assertGreaterEqual(proxy_timeout - expected_worst_case, 15)
            self.assertIn(
                "proxy_read_timeout ${PROXY_READ_TIMEOUT_SECONDS}s;",
                source,
            )

    def test_server_runtime_matches_installer_budget(self):
        self.assertEqual(runtime.BACKEND_TIMEOUT_SECONDS, 10)
        self.assertEqual(standalone_server.MAX_PARALLEL_TRANSACTIONS, 10)
        self.assertEqual(standalone_server.estimated_max_execution_seconds(), 50)

        server_source = (DEMO_API / "standalone_server.py").read_text(encoding="utf-8")
        for marker in (
            "ThreadPoolExecutor",
            '"estimated_max_execution_seconds"',
            '"max_parallel_transactions"',
            '"backend_timeout_seconds"',
        ):
            self.assertIn(marker, server_source)

    def test_twenty_attempts_execute_with_bounded_parallelism(self):
        original_runner = standalone_server.run_transaction
        original_url = standalone_server.BACKEND_TRANSACTION_URL
        active = 0
        peak = 0
        lock = threading.Lock()

        def fake_runner(_url: str, correlation_id: str) -> dict:
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(peak, active)
            time.sleep(0.02)
            with lock:
                active -= 1
            return {
                "correlation_id": correlation_id,
                "backend": "VPN-01",
                "transaction_status": "successful",
            }

        standalone_server.run_transaction = fake_runner
        standalone_server.BACKEND_TRANSACTION_URL = "https://127.0.0.1/transaction"
        try:
            results = standalone_server.execute_transactions(20)
        finally:
            standalone_server.run_transaction = original_runner
            standalone_server.BACKEND_TRANSACTION_URL = original_url

        self.assertEqual(len(results), 20)
        self.assertGreater(peak, 1)
        self.assertLessEqual(peak, standalone_server.MAX_PARALLEL_TRANSACTIONS)
        self.assertEqual(
            len({item["correlation_id"] for item in results}),
            20,
        )


if __name__ == "__main__":
    unittest.main()
