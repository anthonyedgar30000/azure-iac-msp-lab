from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import unittest

from lab_factory.azure_preflight import CommandResult, PreflightError, run_lab_preflight


ROOT = Path(__file__).resolve().parents[2]
SUBSCRIPTION = "11111111-1111-1111-1111-111111111111"
TENANT = "22222222-2222-2222-2222-222222222222"
PARAMETERS = {
    "dnsLabel": "stpreflight-test",
    "allowedOrigin": "https://example.invalid",
    "backendTransactionUrl": "https://example.invalid/api/demo/run",
    "adminSshPublicKey": (
        "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAITestOnlyPublicKey "
        "lab-preflight"
    ),
    "sourceRepository": "https://github.com/example/repository.git",
    "sourceRef": "0123456789abcdef0123456789abcdef01234567",
    "installerUri": "https://example.invalid/install.sh",
}


def _response(argv: tuple[str, ...], *, blocked: bool = False):
    if argv[:3] == ("az", "account", "show"):
        return {
            "id": SUBSCRIPTION,
            "tenantId": TENANT,
            "name": "Azure for Students",
            "state": "Enabled",
        }
    if argv[:3] == ("az", "account", "list-locations"):
        return [{"name": "westus2"}]
    if argv[:3] == ("az", "provider", "show"):
        return {"registrationState": "Registered"}
    if argv[:3] == ("az", "vm", "list-skus"):
        restrictions = (
            [
                {
                    "type": "Location",
                    "reasonCode": "NotAvailableForSubscription",
                    "values": ["westus2"],
                }
            ]
            if blocked
            else []
        )
        return [
            {
                "name": "Standard_F1als_v7",
                "family": "standardFalsv7Family",
                "locations": ["westus2"],
                "capabilities": [{"name": "vCPUs", "value": "1"}],
                "restrictions": restrictions,
            }
        ]
    if argv[:3] == ("az", "vm", "list-usage"):
        return [
            {
                "name": {
                    "value": "cores",
                    "localizedValue": "Total Regional vCPUs",
                },
                "currentValue": 0,
                "limit": 10,
            },
            {
                "name": {
                    "value": "standardFalsv7Family",
                    "localizedValue": "Standard Falsv7 Family vCPUs",
                },
                "currentValue": 0,
                "limit": 10,
            },
        ]
    if argv[:3] == ("az", "network", "list-usages"):
        return [
            {
                "name": {
                    "value": "PublicIPAddresses",
                    "localizedValue": "Standard Public IP Addresses",
                },
                "currentValue": 0,
                "limit": 20,
            }
        ]
    if argv[:3] == ("az", "group", "show"):
        return None
    if argv[:3] == ("az", "rest", "--method"):
        return {
            "value": [
                {
                    "actions": ["*"],
                    "notActions": [],
                    "dataActions": [],
                    "notDataActions": [],
                }
            ]
        }
    if argv[:4] == ("az", "policy", "assignment", "list"):
        return []
    if argv[:4] == ("az", "deployment", "sub", "validate"):
        return {"properties": {"provisioningState": "Succeeded"}}
    raise AssertionError(f"unexpected command: {argv}")


class FakeRunner:
    def __init__(self, *, blocked: bool = False):
        self.blocked = blocked
        self.calls: list[tuple[str, ...]] = []

    def __call__(self, argv, timeout_seconds, cwd):
        command = tuple(argv)
        self.calls.append(command)
        payload = _response(command, blocked=self.blocked)
        if command[:3] == ("az", "group", "show") and payload is None:
            return CommandResult(
                command,
                3,
                "",
                "ResourceGroupNotFound: could not be found",
            )
        return CommandResult(command, 0, json.dumps(payload), "")


def prices(location: str, vm_size: str):
    assert location == "westus2"
    assert vm_size == "Standard_F1als_v7"
    return {
        "vm_hourly_cad": 0.02,
        "public_ip_hourly_cad": 0.005,
        "disk_monthly_cad": 2.0,
    }


class LabFactoryAzurePreflightTests(unittest.TestCase):
    def test_passed_preflight_is_read_only_sanitized_and_deterministic(self):
        runner = FakeRunner()
        now = lambda: datetime(2026, 7, 30, 2, 0, tzinfo=timezone.utc)
        first = run_lab_preflight(
            expected_subscription_id=SUBSCRIPTION,
            profile_id="servicetracer-demo-api",
            environment="test",
            ttl_hours=8,
            cost_ceiling_cad=5.0,
            parameters=PARAMETERS,
            repository_root=ROOT,
            runner=runner,
            price_fetcher=prices,
            now=now,
            request_id="lab-preflight-001",
        )
        second = run_lab_preflight(
            expected_subscription_id=SUBSCRIPTION,
            profile_id="servicetracer-demo-api",
            environment="test",
            ttl_hours=8,
            cost_ceiling_cad=5.0,
            parameters=PARAMETERS,
            repository_root=ROOT,
            runner=FakeRunner(),
            price_fetcher=prices,
            now=now,
            request_id="lab-preflight-001",
        )

        self.assertEqual(first, second)
        self.assertEqual(first["status"], "passed")
        self.assertEqual(first["next_gate"], "what_if_review_required")
        self.assertFalse(first["execution"]["azure_mutations_performed"])
        self.assertFalse(first["execution"]["arm_what_if_performed"])
        self.assertFalse(first["execution"]["deployment_authorized"])
        self.assertTrue(first["cost"]["ceiling_accepted"])
        self.assertTrue(first["template_validation"]["passed"])
        self.assertTrue(
            first["permissions"]["sufficient_for_candidate_deployment"]
        )
        self.assertFalse(first["permissions"]["least_privilege_verified"])

        serialized = json.dumps(first, sort_keys=True)
        self.assertNotIn(SUBSCRIPTION, serialized)
        self.assertNotIn(TENANT, serialized)
        for value in PARAMETERS.values():
            self.assertNotIn(value, serialized)

        observed_commands = [" ".join(command) for command in runner.calls]
        self.assertTrue(
            any("deployment sub validate" in command for command in observed_commands)
        )
        self.assertFalse(
            any(
                "what-if" in command
                or " create " in command
                or " delete " in command
                for command in observed_commands
            )
        )

    def test_sku_restriction_blocks_without_mutation(self):
        result = run_lab_preflight(
            expected_subscription_id=SUBSCRIPTION,
            profile_id="servicetracer-demo-api",
            environment="test",
            ttl_hours=8,
            cost_ceiling_cad=5.0,
            parameters=PARAMETERS,
            repository_root=ROOT,
            runner=FakeRunner(blocked=True),
            price_fetcher=prices,
            request_id="lab-preflight-002",
        )
        self.assertEqual(result["status"], "blocked")
        self.assertIn("vm_sku_not_available", result["blockers"])
        self.assertEqual(result["next_gate"], "preflight_remediation_required")
        self.assertFalse(result["execution"]["deployment_authorized"])

    def test_subscription_mismatch_fails_closed_before_other_queries(self):
        class MismatchRunner(FakeRunner):
            def __call__(self, argv, timeout_seconds, cwd):
                command = tuple(argv)
                self.calls.append(command)
                return CommandResult(
                    command,
                    0,
                    json.dumps(
                        {
                            "id": "33333333-3333-3333-3333-333333333333",
                            "tenantId": TENANT,
                            "name": "wrong",
                            "state": "Enabled",
                        }
                    ),
                    "",
                )

        runner = MismatchRunner()
        with self.assertRaisesRegex(PreflightError, "exact allowlist"):
            run_lab_preflight(
                expected_subscription_id=SUBSCRIPTION,
                profile_id="servicetracer-demo-api",
                environment="test",
                ttl_hours=8,
                cost_ceiling_cad=5.0,
                parameters=PARAMETERS,
                repository_root=ROOT,
                runner=runner,
                price_fetcher=prices,
            )
        self.assertEqual(len(runner.calls), 1)

    def test_workflow_and_contract_preserve_the_read_only_boundary(self):
        workflow = (
            ROOT / ".github/workflows/lab-factory-read-only-preflight.yml"
        ).read_text(encoding="utf-8")
        cli = (
            ROOT / "scripts/run_lab_factory_azure_preflight.py"
        ).read_text(encoding="utf-8")
        core = (ROOT / "lab_factory/azure_preflight.py").read_text(
            encoding="utf-8"
        )
        contract = json.loads(
            (
                ROOT
                / ".project/contracts/lab-factory-read-only-preflight-v1.json"
            ).read_text(encoding="utf-8")
        )

        self.assertIn("workflow_dispatch:", workflow)
        self.assertNotIn("pull_request:", workflow)
        self.assertNotIn("push:", workflow)
        self.assertIn("id-token: write", workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn("environment: azure-lab", workflow)
        self.assertRegex(
            core,
            r'"az",\s*"deployment",\s*"sub",\s*"validate"',
        )
        for forbidden in (
            "az deployment sub create",
            "az deployment sub what-if",
            "az group create",
            "az provider register",
            "az role assignment create",
            "az group delete",
        ):
            self.assertNotIn(forbidden, workflow)
            self.assertNotIn(forbidden, cli)
        self.assertFalse(contract["authority"]["arm_what_if"])
        self.assertFalse(contract["authority"]["azure_mutation"])
        self.assertFalse(contract["authority"]["deployment"])
        self.assertEqual(contract["cost"]["currency"], "CAD")
        self.assertEqual(
            contract["repository_baseline"]["main"],
            "0b6fa63d86ae52119b63ef6c9421c8d13215cb59",
        )


if __name__ == "__main__":
    unittest.main()
