from __future__ import annotations

import copy
from datetime import datetime, timezone
import importlib.util
import json
import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "infra/scripts/authority_claim.py"
WORKFLOW = ROOT / ".github/workflows/durable-authorization-claim-v1.yml"
FIXTURE = ROOT / "infra/tests/fixtures/durable_authorization_request_v1.json"
DESIGN = ROOT / ".project/designs/durable-single-use-authorization-ledger-v1.md"
CONTRACT = ROOT / ".project/contracts/durable-single-use-authorization-ledger-v1.json"

SPEC = importlib.util.spec_from_file_location("authority_claim", SCRIPT)
assert SPEC and SPEC.loader
authority_claim = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = authority_claim
SPEC.loader.exec_module(authority_claim)


REPOSITORY = "anthonyedgar30000/azure-iac-msp-lab"
AUTHORIZATION_COMMIT = "a" * 40
CALLER_WORKFLOW_REF = (
    f"{REPOSITORY}/.github/workflows/example-authorized-caller.yml@"
    "refs/heads/main"
)
NOW = datetime(2026, 7, 28, 18, 0, tzinfo=timezone.utc)


class DurableAuthorizationClaimTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.design = DESIGN.read_text(encoding="utf-8")
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    def validate(self, request: dict | None = None) -> dict[str, str]:
        return authority_claim.validate_request(
            request or copy.deepcopy(self.fixture),
            authority_claim.ClaimContext(
                repository=REPOSITORY,
                authorization_commit=AUTHORIZATION_COMMIT,
                caller_workflow_ref=CALLER_WORKFLOW_REF,
                now=NOW,
            ),
        )

    def test_valid_request_produces_exact_claim_ref_and_outputs(self) -> None:
        outputs = self.validate()
        self.assertEqual(
            outputs["claim_ref"],
            "refs/tags/authority-consumed/018f22e2-79b0-7cc3-8c4d-9b7a12345678",
        )
        self.assertEqual(outputs["authorization_commit"], AUTHORIZATION_COMMIT)
        self.assertEqual(outputs["reviewed_source"], "b" * 40)
        self.assertEqual(
            outputs["caller_workflow_path"],
            ".github/workflows/example-authorized-caller.yml",
        )
        self.assertEqual(outputs["scope_hash"], "sha256:" + "c" * 64)

    def test_canonical_digest_rejects_any_content_change(self) -> None:
        request = copy.deepcopy(self.fixture)
        request["target"]["resource_group"] = "rg-tampered"
        with self.assertRaisesRegex(
            authority_claim.ClaimValidationError,
            "request_digest",
        ):
            self.validate(request)

    def test_expired_inactive_and_consumed_requests_fail_closed(self) -> None:
        expired = copy.deepcopy(self.fixture)
        expired["valid_until"] = "2026-07-28T17:00:00Z"
        expired["request_digest"] = authority_claim.calculate_request_digest(expired)
        with self.assertRaisesRegex(authority_claim.ClaimValidationError, "not active"):
            self.validate(expired)

        inactive = copy.deepcopy(self.fixture)
        inactive["active"] = False
        inactive["request_digest"] = authority_claim.calculate_request_digest(inactive)
        with self.assertRaisesRegex(authority_claim.ClaimValidationError, "active must"):
            self.validate(inactive)

        consumed = copy.deepcopy(self.fixture)
        consumed["status"] = "consumed"
        consumed["request_digest"] = authority_claim.calculate_request_digest(consumed)
        with self.assertRaisesRegex(authority_claim.ClaimValidationError, "status"):
            self.validate(consumed)

    def test_source_commit_repository_and_workflow_mismatches_fail(self) -> None:
        cases = [
            ("authorization_commit", "d" * 40, "authorization_commit"),
            ("repository", "other/repository", "repository"),
        ]
        for field, value, message in cases:
            request = copy.deepcopy(self.fixture)
            request[field] = value
            request["request_digest"] = authority_claim.calculate_request_digest(request)
            with self.subTest(field=field), self.assertRaisesRegex(
                authority_claim.ClaimValidationError,
                message,
            ):
                self.validate(request)

        request = copy.deepcopy(self.fixture)
        request["workflow"]["path"] = ".github/workflows/other.yml"
        request["request_digest"] = authority_claim.calculate_request_digest(request)
        with self.assertRaisesRegex(
            authority_claim.ClaimValidationError,
            "caller workflow",
        ):
            self.validate(request)

    def test_authority_flags_and_uuidv7_are_strict(self) -> None:
        request = copy.deepcopy(self.fixture)
        request["authority"]["automatic_retry_authorized"] = True
        request["request_digest"] = authority_claim.calculate_request_digest(request)
        with self.assertRaisesRegex(
            authority_claim.ClaimValidationError,
            "automatic_retry_authorized",
        ):
            self.validate(request)

        request = copy.deepcopy(self.fixture)
        request["request_id"] = "550e8400-e29b-41d4-a716-446655440000"
        request["request_digest"] = authority_claim.calculate_request_digest(request)
        with self.assertRaisesRegex(authority_claim.ClaimValidationError, "UUIDv7"):
            self.validate(request)

    def test_unknown_fields_fail_closed(self) -> None:
        request = copy.deepcopy(self.fixture)
        request["authority"]["retry_count"] = 0
        request["request_digest"] = authority_claim.calculate_request_digest(request)
        with self.assertRaisesRegex(authority_claim.ClaimValidationError, "unknown"):
            self.validate(request)

    def test_workflow_is_reusable_no_oidc_and_atomic_create_only(self) -> None:
        workflow = self.workflow
        self.assertIn("workflow_call:", workflow)
        self.assertNotIn("workflow_dispatch:", workflow)
        self.assertIn("contents: write", workflow)
        self.assertIn("id-token: none", workflow)
        self.assertNotIn("id-token: write", workflow)
        self.assertIn("github.workflow_ref", workflow)
        self.assertIn("GH_TOKEN: ${{ github.token }}", workflow)
        self.assertIn("ref: ${{ github.sha }}", workflow)
        self.assertIn('"repos/$GITHUB_REPOSITORY/git/refs"', workflow)
        self.assertIn('git cat-file -e "${reviewed_source}^{commit}"', workflow)
        self.assertIn('git merge-base --is-ancestor "$reviewed_source" "$GITHUB_SHA"', workflow)
        self.assertIn("--method POST", workflow)
        self.assertNotIn("--method PATCH", workflow)
        self.assertNotIn("--method DELETE", workflow)
        self.assertNotIn("force=true", workflow)
        self.assertNotIn("azure/login", workflow)
        self.assertNotIn("az login", workflow)
        self.assertNotIn("az deployment", workflow)
        self.assertNotIn("gh workflow run", workflow)
        self.assertNotIn("gh run rerun", workflow)

    def test_replay_failure_is_classified_before_any_cloud_path(self) -> None:
        workflow = self.workflow
        atomic_create = workflow.index("Atomically create the consumption reference")
        replay_error = workflow.index("already consumed; replay or duplicate")
        evidence = workflow.index("Verify durable claim and assemble evidence")
        self.assertLess(atomic_create, replay_error)
        self.assertLess(replay_error, evidence)
        self.assertIn("exit 1", workflow[atomic_create:evidence])

    def test_contract_records_merge_while_activation_and_azure_remain_blocked(self) -> None:
        contract = self.contract
        self.assertEqual(
            contract["status"],
            "implementation_merged_not_activated",
        )
        self.assertTrue(contract["activation"]["merged_to_main"])
        self.assertFalse(contract["activation"]["ruleset_configured"])
        self.assertFalse(contract["activation"]["ruleset_independently_inspected"])
        self.assertFalse(contract["activation"]["live_claim_test_performed"])
        self.assertFalse(contract["activation"]["concurrent_claim_test_performed"])
        self.assertFalse(contract["activation"]["collector_workflow_restored"])
        self.assertFalse(contract["activation"]["azure_execution_enabled"])
        self.assertFalse(contract["authority"]["repository_ruleset_mutation"])
        self.assertFalse(contract["authority"]["tag_claim_execution"])
        self.assertFalse(contract["authority"]["azure_authentication"])
        self.assertFalse(contract["authority"]["workflow_dispatch"])
        self.assertEqual(contract["merge"]["pull_request"], 186)
        self.assertEqual(
            contract["merge"]["merge_commit"],
            "30e312ef5122831a8233835db2f541437a97b125",
        )
        self.assertIn("merged, not activated", self.design.lower())


if __name__ == "__main__":
    unittest.main()
