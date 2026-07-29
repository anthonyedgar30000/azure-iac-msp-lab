from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from azure_mcp_reality.config import ConfigurationError, RealitySettings
from azure_mcp_reality.observer import (
    CommandResult,
    ObservationError,
    TOOL_INVENTORY_DIGEST,
    observe_current_reality,
)


SUBSCRIPTION_ID = "11111111-1111-1111-1111-111111111111"
TENANT_ID = "22222222-2222-2222-2222-222222222222"
RESOURCE_GROUP = "rg-demo-eastus"


class FakeRunner:
    def __init__(self, responses: dict[tuple[str, ...], tuple[int, object, str]]):
        self.responses = responses
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, argv, timeout_seconds, cwd):
        key = tuple(argv)
        self.calls.append(key)
        if key not in self.responses:
            raise AssertionError(f"unexpected command: {key}")
        returncode, stdout, stderr = self.responses[key]
        if not isinstance(stdout, str):
            stdout = json.dumps(stdout)
        return CommandResult(key, returncode, stdout, stderr)


def base_responses() -> dict[tuple[str, ...], tuple[int, object, str]]:
    return {
        ("git", "rev-parse", "HEAD"): (0, "a" * 40, ""),
        (
            "git",
            "status",
            "--porcelain=v1",
            "--untracked-files=normal",
        ): (0, "", ""),
        (
            "az",
            "account",
            "show",
            "--subscription",
            SUBSCRIPTION_ID,
            "--output",
            "json",
            "--only-show-errors",
        ): (
            0,
            {
                "id": SUBSCRIPTION_ID,
                "tenantId": TENANT_ID,
                "name": "Azure for Students",
                "state": "Enabled",
            },
            "",
        ),
        (
            "az",
            "group",
            "show",
            "--subscription",
            SUBSCRIPTION_ID,
            "--name",
            RESOURCE_GROUP,
            "--output",
            "json",
            "--only-show-errors",
        ): (
            0,
            {
                "id": f"/subscriptions/{SUBSCRIPTION_ID}/resourceGroups/{RESOURCE_GROUP}",
                "name": RESOURCE_GROUP,
                "location": "eastus",
                "properties": {"provisioningState": "Succeeded"},
                "tags": {"environment": "demo"},
            },
            "",
        ),
        (
            "az",
            "resource",
            "list",
            "--subscription",
            SUBSCRIPTION_ID,
            "--resource-group",
            RESOURCE_GROUP,
            "--output",
            "json",
            "--only-show-errors",
        ): (
            0,
            [
                {
                    "id": (
                        f"/subscriptions/{SUBSCRIPTION_ID}/resourceGroups/"
                        f"{RESOURCE_GROUP}/providers/Microsoft.CognitiveServices/"
                        "accounts/example-openai"
                    ),
                    "name": "example-openai",
                    "type": "Microsoft.CognitiveServices/accounts",
                    "kind": "OpenAI",
                    "location": "eastus",
                    "resourceGroup": RESOURCE_GROUP,
                    "sku": {"name": "S0"},
                    "tags": {"note": "untrusted"},
                }
            ],
            "",
        ),
        (
            "az",
            "cognitiveservices",
            "account",
            "deployment",
            "list",
            "--subscription",
            SUBSCRIPTION_ID,
            "--resource-group",
            RESOURCE_GROUP,
            "--name",
            "example-openai",
            "--output",
            "json",
            "--only-show-errors",
        ): (
            0,
            [
                {
                    "name": "gpt-5-mini",
                    "properties": {
                        "provisioningState": "Succeeded",
                        "model": {
                            "format": "OpenAI",
                            "name": "gpt-5-mini",
                            "version": "2025-08-07",
                        },
                    },
                    "sku": {"name": "GlobalStandard", "capacity": 1},
                }
            ],
            "",
        ),
    }


class RealityObserverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / ".project").mkdir()
        (self.root / ".project" / "state-index.json").write_text(
            json.dumps(
                {
                    "latest_repository_and_mcp_reconciliation": "mcp.json",
                    "latest_successful_azure_mcp_preflight_reconciliation": "preflight.json",
                    "latest_repository_and_azure_ai_reconciliation": "ai.json",
                    "azure_ai_verified_base_url": "https://example.openai.azure.com/openai/v1/",
                    "azure_ai_verified_deployment": "gpt-5-mini",
                    "azure_ai_verified_model_response": True,
                    "azure_ai_mcp_connected": False,
                    "active_deployment_authorization": None,
                    "active_azure_mcp_preflight_authorization": None,
                    "active_azure_ai_activation_authorization": None,
                }
            ),
            encoding="utf-8",
        )
        self.settings = RealitySettings(
            subscription_id=SUBSCRIPTION_ID,
            resource_group=RESOURCE_GROUP,
            repository_root=self.root,
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_settings_require_exact_scope_and_reject_mutation_overrides(self) -> None:
        env = {
            "AZURE_MCP_ALLOWED_SUBSCRIPTION_ID": SUBSCRIPTION_ID,
            "AZURE_MCP_ALLOWED_RESOURCE_GROUP": RESOURCE_GROUP,
            "AZURE_MCP_REPOSITORY_ROOT": str(self.root),
        }
        settings = RealitySettings.from_env(env)
        self.assertEqual(settings.subscription_id, SUBSCRIPTION_ID)
        self.assertEqual(settings.resource_group, RESOURCE_GROUP)

        changed = dict(env)
        changed["AZURE_MCP_ALLOW_MUTATION"] = "1"
        with self.assertRaises(ConfigurationError):
            RealitySettings.from_env(changed)

        changed = dict(env)
        changed.pop("AZURE_MCP_ALLOWED_RESOURCE_GROUP")
        with self.assertRaises(ConfigurationError):
            RealitySettings.from_env(changed)

    def test_observation_is_bounded_redacted_and_digest_bearing(self) -> None:
        runner = FakeRunner(base_responses())
        result = observe_current_reality(
            self.settings,
            runner=runner,
            now=lambda: datetime(2026, 7, 29, 10, 45, tzinfo=timezone.utc),
            correlation_id="11111111-2222-3333-4444-555555555555",
        )

        self.assertEqual(result["observation_status"], "observed")
        self.assertFalse(result["mutations_performed"])
        self.assertFalse(result["secrets_returned"])
        self.assertEqual(result["azure"]["resource_count"], 1)
        self.assertEqual(
            result["azure"]["cognitive_services_accounts"][0]["deployments"][0]["name"],
            "gpt-5-mini",
        )
        encoded = json.dumps(result)
        self.assertNotIn(SUBSCRIPTION_ID, encoded)
        self.assertIn("<subscription>", encoded)
        self.assertEqual(result["tool_inventory_digest"], TOOL_INVENTORY_DIGEST)
        self.assertRegex(result["raw_evidence_digest"], r"^sha256:[0-9a-f]{64}$")

        flattened = [" ".join(call) for call in runner.calls]
        for denied in (
            " create ",
            " update ",
            " delete ",
            " deployment group create",
            " role assignment create",
            " azd up",
        ):
            self.assertNotIn(denied, f" {' '.join(flattened)} ")

    def test_missing_resource_group_is_observed_as_not_present(self) -> None:
        responses = base_responses()
        key = (
            "az",
            "group",
            "show",
            "--subscription",
            SUBSCRIPTION_ID,
            "--name",
            RESOURCE_GROUP,
            "--output",
            "json",
            "--only-show-errors",
        )
        responses[key] = (3, "", "ResourceGroupNotFound")
        runner = FakeRunner(responses)

        result = observe_current_reality(self.settings, runner=runner)

        self.assertEqual(result["observation_status"], "not_present")
        self.assertIsNone(result["azure"]["resource_group"])
        self.assertEqual(result["azure"]["resources"], [])
        self.assertFalse(
            any(call[:3] == ("az", "resource", "list") for call in runner.calls)
        )

    def test_subscription_mismatch_fails_closed(self) -> None:
        responses = base_responses()
        account_key = (
            "az",
            "account",
            "show",
            "--subscription",
            SUBSCRIPTION_ID,
            "--output",
            "json",
            "--only-show-errors",
        )
        responses[account_key][1]["id"] = "33333333-3333-3333-3333-333333333333"
        with self.assertRaises(ObservationError):
            observe_current_reality(self.settings, runner=FakeRunner(responses))

    def test_resource_count_limit_fails_closed(self) -> None:
        responses = base_responses()
        resource_key = (
            "az",
            "resource",
            "list",
            "--subscription",
            SUBSCRIPTION_ID,
            "--resource-group",
            RESOURCE_GROUP,
            "--output",
            "json",
            "--only-show-errors",
        )
        responses[resource_key] = (0, [{"name": "one"}, {"name": "two"}], "")
        settings = RealitySettings(
            subscription_id=SUBSCRIPTION_ID,
            resource_group=RESOURCE_GROUP,
            repository_root=self.root,
            max_resources=1,
        )
        with self.assertRaises(ObservationError):
            observe_current_reality(settings, runner=FakeRunner(responses))


if __name__ == "__main__":
    unittest.main()
