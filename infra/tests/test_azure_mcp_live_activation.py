from __future__ import annotations

from datetime import datetime, timezone
import unittest
from pathlib import Path

from infra.scripts.authority_claim_v2 import ClaimContext, calculate_request_digest, validate_request

ROOT = Path(__file__).resolve().parents[2]
PARAMS = ROOT / "infra/azure-mcp-live/main.bicepparam"
CONTAINER = ROOT / "infra/azure-mcp-live/modules/container-app.bicep"
MAIN = ROOT / "infra/azure-mcp-live/main.bicep"
DEPLOY = ROOT / ".github/workflows/azure-mcp-live-deploy.yml"
CLAIM = ROOT / ".github/workflows/durable-authorization-claim-v2.yml"


class AzureMcpLiveActivationTests(unittest.TestCase):
    def test_runtime_is_digest_pinned_scale_to_zero_and_read_only(self) -> None:
        params = PARAMS.read_text(encoding="utf-8")
        container = CONTAINER.read_text(encoding="utf-8")
        self.assertRegex(params, r"azure-mcp@sha256:[0-9a-f]{64}")
        self.assertIn("minReplicas: 0", container)
        self.assertIn("maxReplicas: 1", container)
        self.assertIn("'--read-only'", container)
        self.assertIn("'namespace'", container)
        for namespace in ("'group'", "'compute'", "'monitor'"):
            self.assertIn(namespace, params)
        self.assertNotIn("azure-mcp:latest", params)

    def test_least_privilege_scope_is_target_resource_group(self) -> None:
        main = MAIN.read_text(encoding="utf-8")
        self.assertIn("scope: targetRg", main)
        self.assertIn("rg-servicetracer-dev-westus2", PARAMS.read_text(encoding="utf-8"))
        self.assertNotIn("scope: subscription()", main)

    def test_deployment_claims_before_oidc_and_rejects_reruns(self) -> None:
        deploy = DEPLOY.read_text(encoding="utf-8")
        self.assertLess(
            deploy.index("uses: ./.github/workflows/durable-authorization-claim-v2.yml"),
            deploy.index("uses: azure/login@v2"),
        )
        self.assertIn('[[ "$GITHUB_RUN_ATTEMPT" == 1 ]]', deploy)
        self.assertIn("DEPLOY-AZURE-MCP-LIVE", deploy)
        self.assertIn("az deployment sub what-if", deploy)
        self.assertIn("az deployment sub create", deploy)
        self.assertIn("authenticated_tool_call_verified:false", deploy)

    def test_v2_claim_has_no_commit_self_reference(self) -> None:
        claim = CLAIM.read_text(encoding="utf-8")
        self.assertIn("git diff --name-only", claim)
        verifier = (ROOT / "infra/scripts/authority_claim_v2.py").read_text(encoding="utf-8")
        self.assertNotIn('"authorization_commit"', verifier)

    def test_example_v2_request_digest_and_authority(self) -> None:
        request = {
            "schema_version": "project.deployment-authorization-request.v2",
            "request_id": "019c0f1e-5a00-7000-8000-000000000001",
            "request_digest": "",
            "status": "authorized_unconsumed",
            "active": True,
            "issued_at": "2026-07-29T03:30:00Z",
            "valid_until": "2026-07-30T03:30:00Z",
            "reviewed_source": "a" * 40,
            "repository": "anthonyedgar30000/azure-iac-msp-lab",
            "workflow": {
                "path": ".github/workflows/azure-mcp-live-deploy.yml",
                "operation": "deploy-azure-mcp-live",
                "environment": "dev",
            },
            "target": {
                "subscription": "Azure for Students",
                "tenant": "sha256:" + "b" * 64,
                "resource_group": "rg-azure-mcp-dev-westus2",
                "location": "westus2",
                "scope_hash": "sha256:" + "c" * 64,
            },
            "authority": {
                "attempt_limit": 1,
                "renewable": False,
                "transferable": False,
                "automatic_retry_authorized": False,
                "rollback_authorized": False,
                "cleanup_authorized": False,
                "provider_registration_authorized": True,
                "resource_group_mutation_authorized": True,
                "rbac_mutation_authorized": True,
                "entra_application_mutation_authorized": True,
                "deployment_authorized": True,
                "verification_authorized": True,
            },
            "authorized_identity": {
                "repository": "anthonyedgar30000/azure-iac-msp-lab",
                "actor_path": "github-actions/reusable-workflow-v2",
            },
            "human_authority": {
                "authority": "user",
                "instruction": "Fix",
                "interpretation": "Deploy one bounded hardened endpoint.",
            },
        }
        request["request_digest"] = calculate_request_digest(request)
        context = ClaimContext(
            request["repository"],
            request["repository"]
            + "/.github/workflows/azure-mcp-live-deploy.yml@refs/heads/main",
            datetime(2026, 7, 29, 3, 31, tzinfo=timezone.utc),
        )
        outputs = validate_request(request, context)
        self.assertEqual(outputs["rbac_mutation_authorized"], "true")
        self.assertTrue(outputs["claim_ref"].endswith(request["request_id"]))


if __name__ == "__main__":
    unittest.main()
