from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github" / "workflows" / "servicetracer-demo-api-subproject-deploy.yml"


class ServiceTracerDeploymentWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = WORKFLOW.read_text(encoding="utf-8")

    def test_deployment_is_separate_and_manual(self) -> None:
        self.assertIn("workflow_dispatch:", self.source)
        self.assertIn("approved_plan_run_id:", self.source)
        self.assertIn("approved_plan_commit:", self.source)
        self.assertIn("environment: azure-lab", self.source)

    def test_authority_is_commit_and_plan_evidence_bound(self) -> None:
        self.assertIn('ref: ${{ inputs.approved_plan_commit }}', self.source)
        self.assertIn('run-id: ${{ inputs.approved_plan_run_id }}', self.source)
        self.assertIn("artifact-manifest.sha256", self.source)
        self.assertIn("verify_downloaded_plan_manifest.sh", self.source)
        self.assertIn("DEPLOY-DEMO-API-SUBPROJECT", self.source)

    def test_real_ssh_public_key_is_required_before_login(self) -> None:
        secret = "SERVICETRACER_DEMO_API_ADMIN_SSH_PUBLIC_KEY"
        self.assertIn(secret, self.source)
        validation = self.source.split("Validate bounded deployment authority before Azure login", 1)[1].split("Download accepted planning evidence", 1)[0]
        self.assertIn("ssh-(ed25519|rsa)", validation)

    def test_fresh_what_if_precedes_single_deployment(self) -> None:
        what_if = self.source.index("az deployment sub what-if")
        create = self.source.index("az deployment sub create")
        self.assertLess(what_if, create)
        self.assertEqual(self.source.count("az deployment sub create"), 1)
        self.assertIn("assert_what_if.py", self.source)

    def test_no_cleanup_or_unbounded_remote_execution(self) -> None:
        for forbidden in (
            "az group delete",
            "az resource delete",
            "az vm run-command",
            "az deployment group create",
        ):
            self.assertNotIn(forbidden, self.source)

    def test_failure_evidence_is_always_captured(self) -> None:
        self.assertIn("Capture deployment operations and post-deployment inventory", self.source)
        self.assertIn("az deployment operation sub list", self.source)
        self.assertIn("post-deployment-resources.json", self.source)
        self.assertIn("if: always()", self.source)


if __name__ == "__main__":
    unittest.main()
