from __future__ import annotations

from pathlib import Path
import unittest

from azure_mcp_reality.azure_cli_compat import build_active_subscription_runner
from azure_mcp_reality.observer import CommandResult


SUBSCRIPTION_ID = "11111111-1111-1111-1111-111111111111"


class RecordingExecutor:
    def __init__(self) -> None:
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, argv, timeout_seconds, cwd):
        command = tuple(argv)
        self.calls.append(command)
        return CommandResult(command, 0, "{}", "")


class ActiveSubscriptionCompatibilityTests(unittest.TestCase):
    def test_account_show_drops_only_unsupported_subscription_argument(self) -> None:
        executor = RecordingExecutor()
        runner = build_active_subscription_runner(executor)

        result = runner(
            (
                "az",
                "account",
                "show",
                "--subscription",
                SUBSCRIPTION_ID,
                "--output",
                "json",
                "--only-show-errors",
            ),
            30,
            Path("."),
        )

        self.assertEqual(
            executor.calls,
            [
                (
                    "az",
                    "account",
                    "show",
                    "--output",
                    "json",
                    "--only-show-errors",
                )
            ],
        )
        self.assertNotIn("--subscription", result.argv)

    def test_resource_scoped_commands_keep_exact_subscription(self) -> None:
        executor = RecordingExecutor()
        runner = build_active_subscription_runner(executor)
        command = (
            "az",
            "group",
            "show",
            "--subscription",
            SUBSCRIPTION_ID,
            "--name",
            "rg-ai-msp-dev-eastus",
            "--output",
            "json",
            "--only-show-errors",
        )

        runner(command, 30, Path("."))

        self.assertEqual(executor.calls, [command])

    def test_unexpected_account_command_shape_fails_closed(self) -> None:
        runner = build_active_subscription_runner(RecordingExecutor())
        with self.assertRaises(ValueError):
            runner(
                ("az", "account", "show", "--subscription", SUBSCRIPTION_ID),
                30,
                Path("."),
            )


if __name__ == "__main__":
    unittest.main()
