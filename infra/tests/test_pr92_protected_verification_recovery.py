from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate_pr92_protected_verification_artifact.py"
AUTHORIZATION = (
    ROOT
    / ".project"
    / "authorizations"
    / "pr92-protected-verification-evidence-recovery-20260725.json"
)
WORKFLOW = (
    ROOT
    / ".github"
    / "workflows"
    / "recover-pr92-protected-verification-evidence.yml"
)

spec = importlib.util.spec_from_file_location("pr92_recovery", SCRIPT)
assert spec is not None and spec.loader is not None
recovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recovery)


class PR92ProtectedVerificationRecoveryTests(unittest.TestCase):
    def _run(self, *, conclusion: str = "success", head_sha: str | None = None) -> dict:
        return {
            "id": 30160699999,
            "name": recovery.TARGET_WORKFLOW,
            "event": "push",
            "head_branch": recovery.TARGET_BRANCH,
            "head_sha": head_sha or recovery.TARGET_HEAD,
            "run_attempt": 1,
            "status": "completed",
            "conclusion": conclusion,
            "created_at": "2026-07-25T13:56:31Z",
            "updated_at": "2026-07-25T14:00:00Z",
            "html_url": "https://github.com/example/repo/actions/runs/30160699999",
        }

    def _artifact(self, *, workflow_run_id: int = 30160699999) -> dict:
        return {
            "id": 8620999999,
            "name": (
                "servicetracer-demo-api-extension-write-verify-only-2-"
                f"{workflow_run_id}"
            ),
            "digest": "sha256:example",
            "size_in_bytes": 4096,
            "expired": False,
            "workflow_run": {"id": workflow_run_id},
        }

    def _write_json(self, directory: Path, name: str, value: object) -> None:
        (directory / name).write_text(
            json.dumps(value, indent=2) + "\n", encoding="utf-8"
        )

    def _create_success_artifact(self, directory: Path) -> None:
        resources = [
            {
                "name": f"resource-{index}",
                "type": f"Example.Type/{index}",
                "location": "westus2",
            }
            for index in range(recovery.EXPECTED_RESOURCE_COUNT)
        ]
        health = {
            "status": "healthy",
            "hosting_model": "dedicated_vm_subproject",
        }
        permission = {
            "status": "effective_extension_write_permission_verified",
            "effective_extension_write_permission_verified": True,
            "arm_validation_succeeded": True,
            "extension_only_what_if_accepted": True,
            "azure_mutation_performed": False,
            "application_deployment_performed": False,
            "transaction_replay_performed": False,
            "deployment_authorized": False,
        }
        summary = {
            "status": "effective_extension_write_permission_verified",
            "source_head": recovery.TARGET_HEAD,
            "arm_validation_succeeded": True,
            "extension_only_what_if_accepted": True,
            "resource_count_preserved": recovery.EXPECTED_RESOURCE_COUNT,
            "public_health_preserved": True,
            "azure_mutation_performed": False,
            "application_deployment_performed": False,
            "transaction_replay_performed": False,
            "deployment_authorized": False,
        }
        payloads = {
            "exact-head-ci.json": {
                "status": "success",
                "run_id": recovery.TARGET_CI_RUN,
                "source_head": recovery.TARGET_HEAD,
            },
            "resources-before.json": resources,
            "resources-after.json": list(reversed(resources)),
            "health-before.json": health,
            "health-after.json": health,
            "validation.json": {"properties": {"provisioningState": "Succeeded"}},
            "what-if.json": {"status": "Succeeded", "changes": []},
            "permission-verification.json": permission,
            "summary.json": summary,
        }
        for name, value in payloads.items():
            self._write_json(directory, name, value)

        manifest_lines = []
        for path in sorted(directory.iterdir()):
            if not path.is_file():
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            manifest_lines.append(f"{digest}  evidence/{path.name}")
        (directory / "artifact-manifest.sha256").write_text(
            "\n".join(manifest_lines) + "\n", encoding="utf-8"
        )

    def test_complete_success_artifact_promotes_effective_permission(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            artifact_dir = Path(temporary)
            self._create_success_artifact(artifact_dir)
            result = recovery.inspect_recovery(
                self._run(), self._artifact(), artifact_dir
            )

        self.assertEqual(
            result["status"], "effective_extension_write_permission_verified"
        )
        self.assertTrue(result["effective_extension_write_permission_verified"])
        self.assertTrue(result["arm_validation_succeeded"])
        self.assertTrue(result["extension_only_what_if_accepted"])
        self.assertTrue(result["resource_count_preserved"])
        self.assertTrue(result["public_health_preserved"])
        self.assertTrue(result["inspection"]["manifest_verified"])
        self.assertFalse(result["azure_mutation_performed"])
        self.assertFalse(result["deployment_authorized"])

    def test_failed_or_partial_run_remains_unverified(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            artifact_dir = Path(temporary)
            self._write_json(
                artifact_dir,
                "exact-head-ci.json",
                {
                    "status": "success",
                    "run_id": recovery.TARGET_CI_RUN,
                    "source_head": recovery.TARGET_HEAD,
                },
            )
            result = recovery.inspect_recovery(
                self._run(conclusion="failure"), self._artifact(), artifact_dir
            )

        self.assertEqual(
            result["status"],
            "protected_verification_recovered_permission_unverified",
        )
        self.assertFalse(result["effective_extension_write_permission_verified"])
        self.assertIn(
            "permission-verification.json",
            result["inspection"]["missing_success_files"],
        )
        self.assertFalse(result["deployment_authorized"])

    def test_wrong_source_head_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "head SHA mismatch"):
                recovery.inspect_recovery(
                    self._run(head_sha="0" * 40),
                    self._artifact(),
                    Path(temporary),
                )

    def test_artifact_must_be_bound_to_target_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "not bound to the target run"):
                recovery.inspect_recovery(
                    self._run(),
                    self._artifact(workflow_run_id=30160699998),
                    Path(temporary),
                )

    def test_authorization_is_read_only_and_one_shot(self) -> None:
        authorization = json.loads(AUTHORIZATION.read_text(encoding="utf-8"))
        authority = authorization["authority"]

        self.assertEqual(
            authorization["scope"]["target_source_head"], recovery.TARGET_HEAD
        )
        self.assertEqual(
            authorization["scope"]["expected_exact_head_ci_run"],
            recovery.TARGET_CI_RUN,
        )
        for permitted in (
            "github_actions_metadata_read",
            "historical_artifact_download",
            "local_artifact_integrity_validation",
            "sanitized_summary_artifact_upload",
            "sanitized_pull_request_comment",
        ):
            self.assertTrue(authority[permitted])
        for prohibited in (
            "raw_artifact_republication",
            "workflow_dispatch",
            "workflow_rerun",
            "azure_authentication",
            "azure_query",
            "azure_mutation",
            "rbac_mutation",
            "deployment",
            "transaction_replay",
            "guest_command",
            "network_mutation",
            "cleanup",
            "pull_request_merge",
        ):
            self.assertFalse(authority[prohibited])
        self.assertFalse(authorization["one_shot"]["retry_authorized"])

    def test_workflow_cannot_rerun_or_access_azure(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")

        self.assertIn(
            "agent/recover-pr92-protected-evidence-20260725", workflow
        )
        self.assertIn("actions: read", workflow)
        self.assertIn("issues: write", workflow)
        self.assertIn("gh run download", workflow)
        self.assertIn("sanitized recovery summary", workflow.lower())
        self.assertIn(".authority.workflow_rerun == false", workflow)
        self.assertIn(".authority.azure_authentication == false", workflow)
        self.assertNotIn("azure/login", workflow)
        self.assertNotIn("id-token: write", workflow)
        self.assertNotIn("workflow_dispatch:", workflow)
        self.assertNotIn("gh run rerun", workflow)
        self.assertNotIn("/rerun", workflow)
        self.assertNotIn("/attempts", workflow)
        self.assertNotIn(" az ", workflow)


if __name__ == "__main__":
    unittest.main()
