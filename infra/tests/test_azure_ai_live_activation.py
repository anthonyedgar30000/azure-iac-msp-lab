from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/azure-ai-read-only-preflight.yml"
SCRIPT = ROOT / "scripts/azure_ai_read_only_preflight.sh"
ROOT_BICEP = ROOT / "infra/azure-ai-live.bicep"
MODULE_BICEP = ROOT / "infra/modules/azure_ai_openai.bicep"
PARAMETERS = ROOT / "infra/azure-ai-live.dev.bicepparam"
CONTRACT = ROOT / ".project/contracts/azure-ai-live-activation-v1.json"
HANDOFF = ROOT / ".project/handoffs/post-pr193-azure-ai-live-activation-plan.md"
RECONCILIATION = (
    ROOT
    / ".project/reconciliations/post-pr193-azure-ai-live-activation-plan-20260729.json"
)


class AzureAiLiveActivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.root_bicep = ROOT_BICEP.read_text(encoding="utf-8")
        cls.module_bicep = MODULE_BICEP.read_text(encoding="utf-8")
        cls.parameters = PARAMETERS.read_text(encoding="utf-8")
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.handoff = HANDOFF.read_text(encoding="utf-8")
        cls.reconciliation = json.loads(RECONCILIATION.read_text(encoding="utf-8"))

    def test_preflight_is_manual_exact_commit_and_read_only(self) -> None:
        self.assertIn("workflow_dispatch:", self.workflow)
        self.assertNotIn("pull_request:", self.workflow)
        self.assertNotIn("push:", self.workflow)
        self.assertIn("id-token: write", self.workflow)
        self.assertIn("environment: azure-lab", self.workflow)
        self.assertIn("ref: ${{ inputs.reviewed_commit }}", self.workflow)
        self.assertIn(
            "OBSERVE-AZURE-AI:${RESOURCE_GROUP}:${REVIEWED_COMMIT}",
            self.workflow,
        )
        self.assertIn("azure_mutations_authorized:false", self.workflow)
        self.assertIn("role_assignment_authorized:false", self.workflow)
        self.assertIn("model_deployment_authorized:false", self.workflow)
        self.assertIn("model_request_authorized:false", self.workflow)
        self.assertLess(
            self.workflow.index("Verify static workflow, script, and IaC boundaries"),
            self.workflow.index("Log in to Azure with workload identity federation"),
        )

    def test_preflight_queries_subscription_model_quota_capacity_and_rbac(self) -> None:
        self.assertIn('readonly SCRIPT_VERSION="1.0.0"', self.script)
        self.assertIn('account_json="$(az account show --output json)"', self.script)
        self.assertIn("az account list-locations", self.script)
        self.assertIn("az provider show --namespace Microsoft.CognitiveServices", self.script)
        self.assertIn("az cognitiveservices account list --output json", self.script)
        self.assertIn("/models?api-version=2024-10-01", self.script)
        self.assertIn("az cognitiveservices usage list", self.script)
        self.assertIn("az cognitiveservices account list-skus", self.script)
        self.assertIn("/modelCapacities?api-version=2024-10-01", self.script)
        self.assertIn("az role assignment list", self.script)
        self.assertIn("raw_subscription_id_persisted:false", self.script)
        self.assertIn("azure_mutations_performed:false", self.script)

        self.assertNotRegex(
            self.script,
            r"az account show(?:[ \t]|\\\n)+--subscription\b",
        )
        self.assertNotRegex(
            self.script,
            r"az account list-locations(?:[ \t]|\\\n)+--subscription\b",
        )

        forbidden_commands = (
            r"^\s*az\s+group\s+create\b",
            r"^\s*az\s+provider\s+register\b",
            r"^\s*az\s+deployment\b",
            r"^\s*az\s+role\s+assignment\s+create\b",
            r"^\s*az\s+cognitiveservices\s+account\s+create\b",
            r"^\s*az\s+cognitiveservices\s+account\s+deployment\s+create\b",
            r"^\s*az\s+resource\s+(create|update|delete)\b",
        )
        for pattern in forbidden_commands:
            with self.subTest(pattern=pattern):
                self.assertIsNone(re.search(pattern, self.script, re.MULTILINE))

    def test_candidate_regions_and_models_are_explicit(self) -> None:
        self.assertIn("AZURE_AI_CANDIDATE_LOCATIONS: canadaeast,eastus2", self.workflow)
        self.assertIn('"name":"gpt-4.1-mini","version":"2025-04-14"', self.workflow)
        self.assertIn('"name":"gpt-5-mini","version":"2025-08-07"', self.workflow)
        self.assertIn("'canadaeast'", self.root_bicep)
        self.assertIn("'eastus2'", self.root_bicep)
        self.assertIn("param modelName string = 'gpt-4.1-mini'", self.root_bicep)
        self.assertIn("param modelVersion string = '2025-04-14'", self.root_bicep)

    def test_iac_is_fail_closed_and_entra_only(self) -> None:
        self.assertIn("param deployAzureAi bool = false", self.root_bicep)
        self.assertIn("param assignInferenceRole bool = false", self.root_bicep)
        self.assertIn("param deployAzureAi = false", self.parameters)
        self.assertIn("param assignInferenceRole = false", self.parameters)
        self.assertIn("disableLocalAuth: true", self.module_bicep)
        self.assertIn("customSubDomainName: accountName", self.module_bicep)
        self.assertIn("publicNetworkAccess: 'Enabled'", self.module_bicep)
        self.assertIn("versionUpgradeOption: 'NoAutoUpgrade'", self.module_bicep)
        self.assertIn("raiPolicyName: 'Microsoft.Default'", self.module_bicep)
        self.assertIn("5e0bd9bd-7b93-4f28-af87-19fc36ad61bd", self.module_bicep)
        self.assertIn(
            "resource inferenceRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (assignInferenceRole)",
            self.module_bicep,
        )

    def test_repository_contract_does_not_claim_live_azure(self) -> None:
        self.assertEqual(
            self.contract["status"],
            "repository_candidate_preflight_not_dispatched",
        )
        execution = self.contract["execution"]
        for key in (
            "azure_authentication_performed",
            "azure_query_performed",
            "azure_mutation_performed",
            "resource_group_created",
            "openai_account_created",
            "model_deployment_created",
            "role_assignment_created",
            "model_request_performed",
        ):
            self.assertFalse(execution[key], key)

        authority = self.contract["authority"]
        self.assertTrue(authority["repository_changes_authorized"])
        self.assertTrue(authority["ordinary_exact_head_ci_authorized"])
        for key in (
            "pull_request_merge_authorized",
            "workflow_dispatch_authorized",
            "azure_authentication_authorized",
            "azure_query_authorized",
            "azure_mutation_authorized",
            "rbac_mutation_authorized",
            "model_deployment_authorized",
            "model_request_authorized",
        ):
            self.assertFalse(authority[key], key)

    def test_reconciliation_preserves_post_pr193_live_boundary(self) -> None:
        github = self.reconciliation["github_state"]
        self.assertEqual(
            github["observed_main"],
            "2099b6c60268976f95d8b9ebcc20601aa1fce7f1",
        )
        self.assertEqual(github["latest_merged_pull_request"], 193)
        self.assertEqual(github["open_pull_requests_observed"], [])
        self.assertFalse(self.reconciliation["azure_state"]["fresh_query_performed"])
        self.assertFalse(self.reconciliation["activation_state"]["endpoint_live"])
        self.assertIn("provider_on_main != endpoint_live", self.handoff)
        self.assertIn("preflight_passed != deployment_authorized", self.handoff)


if __name__ == "__main__":
    unittest.main()
