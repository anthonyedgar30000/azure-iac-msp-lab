from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = (
    ROOT
    / ".github"
    / "workflows"
    / "one-shot-tls-accept-loop-deploy-run3.yml"
)
AUTHORITY = (
    ROOT
    / ".project"
    / "change-requests"
    / "tls-accept-loop-deploy-run3-20260727.json"
)


class TlsAcceptLoopDeployRun3WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))

    def test_trigger_is_one_shot_main_push_and_reruns_fail_before_azure_login(self) -> None:
        self.assertIn("name: One-shot TLS accept-loop Azure deployment run 3", self.workflow)
        self.assertIn("push:", self.workflow)
        self.assertIn("- main", self.workflow)
        self.assertIn(
            "- .github/workflows/one-shot-tls-accept-loop-deploy-run3.yml",
            self.workflow,
        )
        self.assertNotIn("workflow_dispatch:", self.workflow)
        attempt_gate = self.workflow.index('[[ "$GITHUB_RUN_ATTEMPT" == \'1\' ]]')
        azure_login = self.workflow.index("uses: azure/login@v2")
        self.assertLess(attempt_gate, azure_login)

    def test_proven_repair_and_sidecar_evidence_are_required(self) -> None:
        for required in (
            "AUTHORIZED_REPAIR: aa493def60866f3d9452899b131bc2f35cd68bdf",
            "SIDECAR_PROOF_SOURCE: 681a7b25b7b5a14b4daabd9ea06d66c0f648f16f",
            "af076e5101a0dd9b95962f476306d80800be0926bebf5ccfd44c980a9608be78",
            "test_vpn_backend_tls_accept_loop.py",
            "test_vpn01_guest_local_sidecar_workflow.py",
            "authorization_issue=169",
        ):
            self.assertIn(required, self.workflow)

    def test_rollout_is_vpn01_first_and_probe_gated_before_vpn02(self) -> None:
        vpn01 = self.workflow.index("Deploy and locally validate VPN-01 production canary")
        probe_gate = self.workflow.index("Wait for VPN-01 Azure TCP probe health")
        vpn02 = self.workflow.index("Deploy and locally validate VPN-02")
        both_probes = self.workflow.index("Wait for both Azure TCP probes to report healthy")
        transactions = self.workflow.index("Validate bounded public transaction contrast")
        self.assertLess(vpn01, probe_gate)
        self.assertLess(probe_gate, vpn02)
        self.assertLess(vpn02, both_probes)
        self.assertLess(both_probes, transactions)

    def test_guest_deployment_has_named_readiness_and_failure_checkpoints(self) -> None:
        for checkpoint in (
            "preflight-required-files",
            "backup-current-production",
            "render-and-verify-new-files",
            "install-production-files",
            "daemon-reload-and-restart-once",
            "service-active",
            "service-enabled",
            "listener-present",
            "loopback-health",
            "private-ip-health",
            "raw-probes-connected",
            "https-survives-raw-probes",
            "private-ip-survives-raw-probes",
            "listener-queue-below-backlog",
            "verify-installed-hashes",
            "verify-unchanged-security-boundary",
            "CHECKPOINT_FAIL",
        ):
            self.assertIn(checkpoint, self.workflow)

    def test_local_regression_and_rollback_are_bounded(self) -> None:
        for required in (
            "RAW_PROBES_CONNECTED count=12",
            "SERVICETRACER_PRODUCTION_DEPLOYMENT_SUCCESS",
            "SERVICETRACER_ROLLBACK_PERFORMED",
            "failed_checkpoint=",
            "rollback=verified",
            "backend.py.before",
            "service.before",
            "systemctl restart \"$service\"",
        ):
            self.assertIn(required, self.workflow)

    def test_only_expected_production_files_are_replaced(self) -> None:
        self.assertIn("backend_path='/opt/servicetracer-demo/backend.py'", self.workflow)
        self.assertIn(
            "unit_path='/etc/systemd/system/servicetracer-demo-backend.service'",
            self.workflow,
        )
        self.assertIn("cert-key-before.sha256", self.workflow)
        self.assertIn("ufw-before.txt", self.workflow)
        self.assertIn("cmp -s", self.workflow)

    def test_no_forbidden_azure_or_guest_mutations(self) -> None:
        forbidden = (
            "az vm restart",
            "az vm deallocate",
            "az vm resize",
            "az vm create",
            "az deployment",
            "az network lb update",
            "az network lb probe",
            "az network nsg",
            "az role assignment",
            "ufw allow",
            "ufw delete",
            "ufw enable",
            "ufw disable",
            "apt-get",
            "apt install",
        )
        for command in forbidden:
            self.assertNotIn(command, self.workflow)

    def test_cost_quota_and_evidence_contract_is_present(self) -> None:
        for required in (
            "az vm list-usage",
            "regional-compute-usage.json",
            "recurring_cost_delta_CAD:0",
            "quota_delta:\"none\"",
            "tls-accept-loop-deploy-run3-evidence",
            "retention-days: 30",
        ):
            self.assertIn(required, self.workflow)

    def test_authority_is_finite_and_nonrenewing(self) -> None:
        self.assertEqual(
            self.authority["status"], "authorized_one_shot_production_execution"
        )
        execution = self.authority["execution"]
        self.assertTrue(execution["one_shot_push_authorized"])
        self.assertTrue(execution["workflow_execution_authorized"])
        self.assertTrue(execution["first_run_attempt_only"])
        self.assertFalse(execution["rerun_authorized"])
        self.assertFalse(execution["automatic_retry_authorized"])
        self.assertEqual(
            self.authority["cost_and_quota"]["expected_recurring_cost_delta_CAD"],
            0,
        )


if __name__ == "__main__":
    unittest.main()
