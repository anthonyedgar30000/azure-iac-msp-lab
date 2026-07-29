from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path

from .observer import CommandResult, _default_runner


Executor = Callable[[Sequence[str], int, Path], CommandResult]


def build_active_subscription_runner(
    executor: Executor = _default_runner,
) -> Executor:
    """Adapt the account-context command to Azure CLI 2.88 compatibility.

    Azure CLI 2.88 rejects ``az account show --subscription``. The observer still
    receives an explicitly configured subscription UUID and validates the active
    account result against it. All resource-scoped commands retain their explicit
    ``--subscription`` argument.
    """

    def runner(
        argv: Sequence[str],
        timeout_seconds: int,
        cwd: Path,
    ) -> CommandResult:
        command = tuple(argv)
        if command[:4] == ("az", "account", "show", "--subscription"):
            if len(command) < 8:
                raise ValueError("unexpected Azure account command shape")
            command = (
                "az",
                "account",
                "show",
                *command[5:],
            )
        return executor(command, timeout_seconds, cwd)

    return runner


active_subscription_runner = build_active_subscription_runner()
