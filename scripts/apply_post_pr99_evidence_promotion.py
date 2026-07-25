#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_MAIN = "719fe25db340fecbcc24599d6cf3c7ac1eee80dd"
DEPLOYED = "8b3d55c616d8820edd523f77021a35fe24167bd0"
PR99_SOURCE = "4593f63fafe6623dfcd4dc0df92df2ef40a96c55"
PR99_PACKAGE_CI = 30171211077
PR99_EXECUTION_CI = 30171259207
RECOVERY_RUN = 30171257533
HISTORICAL_RUN = 30160680313
HISTORICAL_ARTIFACT = 8620163872
HISTORICAL_DIGEST = "sha256:9da1e4f3b12de2d4702ab3ea8c4b47b0169d4030a3bccf4762e2f1aa81ba5b04"
EVIDENCE_PATH = ".project/evidence/pr92-protected-verification-recovery-30171257533.json"
RECONCILIATION_PATH = ".project/reconciliations/post-pr99-protected-verification-evidence.json"


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def dump(path: str, value: dict) -> None:
    (ROOT / path).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise AssertionError(f"expected exactly one replacement in {path}: {old!r}")
    target.write_text(text.replace(old, new), encoding="utf-8")


def promote_current_reality() -> None:
    current = load(".project/current-reality.json")
    if current["repository_state"]["observed_head"] != "665e051375594d11e58e434231bd06775dbdc560":
        raise AssertionError("unexpected pre-promotion current-reality watermark")

    repo = current["repository_state"]
    repo["observed_head"] = BASE_MAIN
    repo["latest_merged_pull_request"] = 99
    repo["also_merged_pull_requests"] = [97, 98]
    repo["merge_order"] = [98, 97, 99]
    repo["open_pull_requests_observed"] = []
    repo["local_working_tree"] = "not_observed"
    repo["exact_head_ci"].update(
        {
            "pr99_reviewed_package_head": "582e77ffa301e47b9ef003d33474bcd2540f9671",
            "pr99_reviewed_package_ci_run_id": PR99_PACKAGE_CI,
            "pr99_reviewed_package_ci_conclusion": "success",
            "pr99_execution_source_head": PR99_SOURCE,
            "pr99_execution_head_ci_run_id": PR99_EXECUTION_CI,
            "pr99_execution_head_ci_conclusion": "success",
            "pr99_recovery_run_id": RECOVERY_RUN,
            "pr99_recovery_run_conclusion": "failure",
            "pr99_recovery_resolution_step_conclusion": "success",
            "pr99_recovery_comment_step_conclusion": "failure",
            "pr99_recovery_summary_upload_conclusion": "success",
        }
    )
    repo["merge_result_ci"].update(
        {
            "pr98_merge_commit": "84ccfe3d68816efdfbcfa1d52fa563ce00f779d2",
            "pr98_merge_commit_run": "not_observed",
            "pr97_merge_commit": "0a08201e6c667390c006d52c7f2c2a4a56749b7d",
            "pr97_merge_commit_run": "not_observed",
            "pr99_merge_commit": BASE_MAIN,
            "pr99_merge_commit_run": "not_observed",
            "final_combined_main_ci": "not_observed",
        }
    )
    repo["operator_merge_reconciliation"].update(
        {
            "pr99_recorded_agent_merge_authority": False,
            "pr99_human_operator_merge_observed": True,
        }
    )
    repo["operator_merge_reconciliation"]["resolution"] = (
        "The human GitHub merges are accepted as repository reality without retroactively "
        "broadening the earlier agent grants. PR #99 evidence recovery is promoted from its "
        "sanitized artifact even though the nonessential PR-comment step failed."
    )
    repo["claim_boundary"] = (
        "GitHub establishes main at PR #99 merge commit 719fe25. PR #99 exact-head CI passed. "
        "Its recovery workflow resolved and validated the exact historical PR #92 protected run "
        "and artifact, while only the optional PR-comment publication step failed. No workflow "
        "result was observed directly on the final main merge composition."
    )

    anchors = current["evidence_anchors"]
    anchors.update(
        {
            "post_pr99_protected_verification_reconciliation": RECONCILIATION_PATH,
            "pr92_protected_run_id": HISTORICAL_RUN,
            "pr92_protected_artifact_id": HISTORICAL_ARTIFACT,
            "pr92_protected_artifact_name": "servicetracer-demo-api-extension-write-verify-only-2-30160680313",
            "pr92_protected_artifact_digest": HISTORICAL_DIGEST,
            "pr92_protected_artifact_manifest_verified": True,
            "pr99_source_head": PR99_SOURCE,
            "pr99_merge_commit": BASE_MAIN,
            "pr99_package_ci_run_id": PR99_PACKAGE_CI,
            "pr99_execution_ci_run_id": PR99_EXECUTION_CI,
            "pr99_recovery_run_id": RECOVERY_RUN,
            "pr99_recovery_evidence": EVIDENCE_PATH,
        }
    )

    api = current["independent_demo_api"]
    repository = api["repository_reconciliation"]
    repository["main_ahead_by_commits"] = 191
    repository["main_behind_by_commits"] = 0
    repository["pr99_protected_evidence_recovery_merged_into_main"] = True
    repository["interpretation"] = (
        "Current main contains the timeout correction and the durable PR #92 protected evidence "
        "recovery. Effective extension-write permission is verified; the corrected runtime is "
        "still not deployed and the Azure observation remains time-bounded."
    )

    operations = api["security_and_operations"]
    operations["effective_rbac"] = (
        "effective_extension_write_permission_verified_by_protected_arm_validation_and_extension_only_what_if"
    )
    operations["required_extension_write_effective"] = "verified"
    operations["effective_least_privilege_verified"] = False

    resolved = api["resolved_state"]
    resolved["repository_pr99_protected_evidence_recovery_merged"] = True
    resolved["extension_write_permission_verified"] = True
    resolved["protected_verify_only_artifact_inspected"] = True
    resolved["protected_verify_only_historical_run_id"] = HISTORICAL_RUN
    resolved["protected_verify_only_historical_artifact_id"] = HISTORICAL_ARTIFACT
    resolved["corrected_runtime_deployed"] = False
    resolved["operationally_verified"] = False
    resolved["claim_boundary"] = (
        "The original deployment and public API health remain verified and time-bounded. The exact "
        "protected run and artifact now verify extension-write permission without mutation. The "
        "timeout correction remains undeployed; backend success, alert delivery, corrected runtime, "
        "and full service validation remain unresolved."
    )

    rbac = current["rbac_reconciliation"]
    claims = rbac["preserved_source_claims"]
    new_claims = [
        {
            "source": "Protected workflow run 30160680313",
            "claim": "Azure login, ARM validation, extension-only What-If, inventory preservation, public health, and sanitized evidence upload completed successfully.",
            "verification_status": "durably_recovered_and_inspected",
        },
        {
            "source": EVIDENCE_PATH,
            "claim": "Artifact 8620163872 manifest verified with no missing success files; effective extension-write permission verified and Azure mutation false.",
            "verification_status": "repository_promoted_sanitized_evidence",
        },
    ]
    existing_sources = {item["source"] for item in claims}
    claims.extend(item for item in new_claims if item["source"] not in existing_sources)
    rbac_state = rbac["resolved_state"]
    rbac_state["execution_truth"] = "effective_permission_verified_preserving_unobserved_assignment"
    rbac_state["apply_success"] = "assumed_not_evidenced"
    rbac_state["effective_target_identity_permission"] = "verified_for_vm_extension_write"
    rbac_state["protected_verify_only_outcome"] = (
        "run_30160680313_success_artifact_8620163872_manifest_verified"
    )
    rbac_state["deployment_authorized"] = False
    rbac["claim_boundary"] = (
        "Effective Microsoft.Compute/virtualMachines/extensions/write permission is verified by "
        "successful protected ARM validation and accepted extension-only What-If evidence. The role "
        "definition and assignment observations remain supplementary and their absence does not erase "
        "the effective-permission proof. Deployment remains unauthorized."
    )

    shared = current["shared_state_resolution"]
    shared["latest_reconciliation"] = RECONCILIATION_PATH
    distinctions = shared["canonical_distinctions"]
    for marker in (
        "recovery_workflow_red != protected_evidence_failed",
        "effective_permission_verified != deployment_authorized",
    ):
        if marker not in distinctions:
            distinctions.append(marker)

    current["next_gate"] = {
        "operation": "prepare_exact_commit_timeout_correction_deployment_authorization",
        "execution_authorized": False,
        "requirements": [
            "fresh repository and Azure reality synchronization",
            "exact deployment source selection and exact-head CI",
            "fresh cost, quota, target inventory, and runtime preflight",
            "accepted fail-closed extension-only What-If",
            "new identity-bound scope-bound method-bound deployment authorization",
            "rollback, validation, cleanup, and evidence plan",
        ],
        "claim_boundary": (
            "The recovered verification grant and evidence do not renew the consumed deployment grant. "
            "No Azure login, query, mutation, deployment, replay, publication, cleanup, or workflow rerun "
            "is authorized by this reconciliation."
        ),
    }
    dump(".project/current-reality.json", current)


def promote_gate() -> None:
    gate = load(".project/lab-v1-completion-gate.json")
    gate["decision_status"] = "merged_repository_authority_active"
    criteria = {
        item["criterion_id"]: item
        for item in gate["priority_order"][0]["exit_criteria"]
    }
    criteria["p0-protected-verification-evidence"]["current_status"] = (
        "satisfied_run_30160680313_artifact_8620163872_recovered_and_inspected"
    )
    criteria["p0-effective-extension-permission"]["current_status"] = (
        "satisfied_effective_extension_write_permission_verified"
    )
    gate["evidence_inputs"].update(
        {
            "protected_verification_historical_run": HISTORICAL_RUN,
            "protected_verification_artifact_id": HISTORICAL_ARTIFACT,
            "protected_verification_artifact_digest": HISTORICAL_DIGEST,
            "protected_verification_recovery_run": RECOVERY_RUN,
            "protected_verification_recovery_evidence": EVIDENCE_PATH,
            "post_pr99_reconciliation": RECONCILIATION_PATH,
        }
    )
    gate["evidence_inputs"]["claim_boundary"] = (
        "The recovered protected run and sanitized artifact satisfy the protected-evidence and "
        "effective-extension-permission criteria without Azure mutation. The corrected runtime "
        "deployment and all later criteria remain unresolved."
    )
    gate["next_gate"] = {
        "operation": "prepare_exact_commit_timeout_correction_deployment_authorization",
        "execution_authorized": False,
        "claim_boundary": (
            "Permission verification does not renew or manufacture deployment authority. A new exact "
            "deployment grant is required after fresh preflight and reviewed What-If evidence."
        ),
    }
    dump(".project/lab-v1-completion-gate.json", gate)


def write_reconciliation() -> None:
    record = {
        "schema_version": "project.post-pr99-protected-verification-reconciliation.v1",
        "recorded_on": "2026-07-25",
        "repository": "anthonyedgar30000/azure-iac-msp-lab",
        "baseline": {
            "main": BASE_MAIN,
            "latest_merged_pull_request": 99,
            "open_pull_requests_observed": [],
            "local_working_tree": "not_observed",
            "deployed_source_ref": DEPLOYED,
            "main_ahead_by_commits": 191,
            "main_behind_by_commits": 0,
        },
        "pull_request_99": {
            "source_head": PR99_SOURCE,
            "merge_commit": BASE_MAIN,
            "reviewed_package_ci_run": PR99_PACKAGE_CI,
            "execution_head_ci_run": PR99_EXECUTION_CI,
            "ci_conclusions": ["success", "success"],
            "recovery_run": RECOVERY_RUN,
            "recovery_run_conclusion": "failure",
            "historical_resolution_step_conclusion": "success",
            "comment_publication_step_conclusion": "failure",
            "sanitized_summary_upload_conclusion": "success",
            "interpretation": (
                "The recovery workflow is red only because the nonessential PR-comment publication "
                "step failed. Historical evidence resolution, validation, and sanitized upload succeeded."
            ),
        },
        "protected_evidence": {
            "historical_run_id": HISTORICAL_RUN,
            "historical_run_conclusion": "success",
            "source_head": "5b5af74d57fb5fd87ece2a34239cc6f29d04b12b",
            "artifact_id": HISTORICAL_ARTIFACT,
            "artifact_digest": HISTORICAL_DIGEST,
            "manifest_verified": True,
            "missing_success_files": [],
            "arm_validation_succeeded": True,
            "extension_only_what_if_accepted": True,
            "resource_count_preserved": True,
            "public_health_preserved": True,
            "effective_extension_write_permission_verified": True,
            "azure_mutation_performed": False,
            "deployment_authorized": False,
            "repository_evidence": EVIDENCE_PATH,
        },
        "resolved_state": {
            "p0_protected_verification_evidence": "satisfied",
            "p0_effective_extension_permission": "satisfied",
            "p0_timeout_correction_deployment": "repository_merged_not_deployed",
            "corrected_runtime_deployed": False,
            "deployment_authorized": False,
        },
        "azure_boundary": {
            "fresh_azure_authentication_performed": False,
            "fresh_azure_query_performed": False,
            "fresh_runtime_test_performed": False,
            "azure_mutation_performed": False,
            "latest_promoted_azure_observation": "2026-07-25T00:47:40Z",
        },
        "canonical_distinctions": [
            "recovery_workflow_red != protected_evidence_failed",
            "effective_permission_verified != deployment_authorized",
            "repository_evidence_promoted != corrected_runtime_deployed",
            "RBAC_assignment != effective_permission_proof",
            "not_observed != false",
        ],
        "authority": {
            "repository_reconciliation": True,
            "pull_request_creation": True,
            "pull_request_merge": False,
            "workflow_dispatch_or_rerun": False,
            "azure_authentication": False,
            "azure_query": False,
            "azure_mutation": False,
            "deployment": False,
            "rbac_mutation": False,
            "transaction_replay": False,
            "cleanup": False,
        },
        "next_gate": "Prepare a new exact-commit timeout-correction deployment authorization after fresh preflight; do not inherit or renew the consumed historical deployment grant.",
    }
    dump(RECONCILIATION_PATH, record)


def write_handoff() -> None:
    text = f"""# Current project handoff

## Interpretation boundary

This handoff records repository and evidence state after PR #99 merged. The newest Azure inventory and runtime observation remains time-bounded through `2026-07-25T00:47:40Z`; this is not a continuously refreshed dashboard.

```text
merged_into_main != deployed_to_VM
recovery_workflow_red != protected_evidence_failed
effective_permission_verified != deployment_authorized
repository_evidence_promoted != corrected_runtime_deployed
RBAC_assignment != effective_permission_proof
monitoring_enabled != alerts_verified
estimated_cost != actual_cost
not_observed != false
```

## Repository watermark

```text
repository: anthonyedgar30000/azure-iac-msp-lab
main observed before this reconciliation branch: {BASE_MAIN}
latest merged pull request: #99
open pull requests observed before branch creation: none
local working tree: not observed
deployed source: {DEPLOYED}
main ahead of deployed source: 191 commits
main behind deployed source: 0 commits
```

## PR #99 and recovered protected evidence

```text
PR #99 source: {PR99_SOURCE}
PR #99 merge: {BASE_MAIN}
reviewed package CI: {PR99_PACKAGE_CI} / success
execution-head CI: {PR99_EXECUTION_CI} / success
recovery workflow: {RECOVERY_RUN} / failure
historical-resolution step: success
sanitized-summary upload: success
PR-comment publication: failure
```

The red recovery check is limited to the optional PR-comment step. The exact historical protected run and artifact were resolved and validated successfully.

```text
historical protected run: {HISTORICAL_RUN} / success
historical source: 5b5af74d57fb5fd87ece2a34239cc6f29d04b12b
artifact: {HISTORICAL_ARTIFACT}
artifact digest: {HISTORICAL_DIGEST}
manifest verified: true
missing success files: none
ARM validation: success
extension-only What-If: accepted
resource inventory preserved: true
public health preserved: true
Azure mutation performed: false
deployment authorized: false
```

Repository-promoted sanitized evidence:

`{EVIDENCE_PATH}`

## Lab v1 P0 status

```text
p0-protected-verification-evidence: satisfied
p0-effective-extension-permission: satisfied
p0-timeout-correction-deployment: repository merged, not deployed
p0-runtime-contract: corrected contract unverified
p0-servicetracer-scenario: not performed
p0-browser-demonstration: not verified
p0-evidence-lock: incomplete
```

## Latest durable Azure evidence

```text
subscription: Azure subscription 1
resource group: rg-st-demo-api-dev-westus2
location: westus2
resources observed: 7
deployment: servicetracer-demo-api-dev / Succeeded
VM: vm-st-demo-api-mst-dev
VM size: Standard_F1als_v7
VM state: VM running
public GET /api/health: HTTP 200 / healthy
health contract: pre-timeout-fix contract
corrected timeout fields observed: false
backend transaction success verified: false
full workload operationally verified: false
```

No fresh Azure authentication, inventory, Resource Graph query, RBAC query, runtime request, deployment, transaction replay, or mutation was performed by this reconciliation.

## Security and operations

```text
effective Microsoft.Compute/virtualMachines/extensions/write: verified
role definition observation: not promoted
role assignment observation: not promoted
effective least privilege across identities: not verified
metric alerts observed: 0
action groups observed: 0
alert delivery verified: false
backup scope: intentionally out of scope for Lab v1
recovery tested: false
```

Effective extension-write permission is proven by protected ARM validation and accepted extension-only What-If, not by assuming a role assignment.

## Cost and quota boundary

Latest promoted ActualCost observation:

```text
total: CAD 0.734335248846279
observed at: 2026-07-25T00:47:40Z
Total regional vCPUs: 1 / 10
Standard IPv4 public IPs: 1 / 20
Falsv7 family quota: not returned by the filtered query
```

Usage may lag and is not a final invoice or forecast.

## Cleanup and optional capability boundaries

```text
cleanup dependency collection executed: false
cleanup candidate orphan status: not established
cleanup authorized: false
Stategraph architecture status: accepted optional capability
Stategraph current priority: Design For
Stategraph execution authority: false
```

## Current authority

```text
repository reconciliation authorized: true
pull request creation authorized: true
pull request merge authorized: false
workflow dispatch or rerun authorized: false
Azure authentication authorized: false
Azure query authorized: false
Azure mutation authorized: false
deployment authorized: false
RBAC mutation authorized: false
transaction replay authorized: false
cleanup authorized: false
```

## Next gate

Prepare a new exact-commit timeout-correction deployment authorization only after fresh repository and Azure synchronization, exact-head CI, reviewed fail-closed What-If, cost and quota preflight, rollback design, and evidence planning.

The consumed historical deployment grant is not renewed by successful permission verification.
"""
    (ROOT / ".project/handoffs/current-state.md").write_text(text, encoding="utf-8")


def patch_recovery_workflow_and_test() -> None:
    workflow = ".github/workflows/recover-pr92-protected-verification-evidence.yml"
    replace_once(
        workflow,
        "      - name: Publish sanitized recovery result to the pull request\n        env:\n",
        "      - name: Publish sanitized recovery result to the pull request\n        continue-on-error: true\n        env:\n",
    )
    old_lookup = """          owner=\"${GITHUB_REPOSITORY%%/*}\"\n          pr_number=\"$(gh api -X GET \"repos/${GITHUB_REPOSITORY}/pulls\" \\\n            -f state=open \\\n            -f head=\"${owner}:${GITHUB_REF_NAME}\" \\\n            -F per_page=10 \\\n            --jq 'if length == 1 then .[0].number else error(\"expected exactly one open recovery PR\") end')\"\n          jq -n --rawfile body /tmp/recovery-comment.md '{body:$body}' \\\n            | gh api -X POST \"repos/${GITHUB_REPOSITORY}/issues/${pr_number}/comments\" --input - >/dev/null\n"""
    new_lookup = """          pr_number=\"$(gh api -X GET \\\n            -H \"Accept: application/vnd.github+json\" \\\n            \"repos/${GITHUB_REPOSITORY}/commits/${GITHUB_SHA}/pulls\" \\\n            --jq '.[0].number // empty')\"\n          if [[ -z \"$pr_number\" ]]; then\n            echo \"No associated pull request found; the sanitized artifact remains authoritative.\"\n            exit 0\n          fi\n          jq -n --rawfile body /tmp/recovery-comment.md '{body:$body}' \\\n            | gh api -X POST \"repos/${GITHUB_REPOSITORY}/issues/${pr_number}/comments\" --input - >/dev/null\n"""
    replace_once(workflow, old_lookup, new_lookup)

    test_path = "infra/tests/test_pr92_protected_verification_recovery.py"
    replace_once(
        test_path,
        '        self.assertIn("sanitized recovery summary", workflow.lower())\n',
        '        self.assertIn("sanitized recovery summary", workflow.lower())\n'
        '        self.assertIn("continue-on-error: true", workflow)\n'
        '        self.assertIn("commits/${GITHUB_SHA}/pulls", workflow)\n'
        '        self.assertNotIn("expected exactly one open recovery PR", workflow)\n',
    )


def patch_gate_document() -> None:
    path = "docs/lab-v1-completion-gate.md"
    insert_after = "The machine-readable authority is [`.project/lab-v1-completion-gate.json`](../.project/lab-v1-completion-gate.json).\n"
    status = """

## Current completion status

As of the PR #99 evidence promotion:

```text
p0-protected-verification-evidence = satisfied
p0-effective-extension-permission = satisfied
p0-timeout-correction-deployment = repository_merged_not_deployed
```

Protected run `30160680313` and artifact `8620163872` were recovered and integrity-checked. The accepted extension-only ARM validation and What-If establish effective extension-write permission without Azure mutation. This does not authorize deployment.
"""
    replace_once(path, insert_after, insert_after + status)
    old_next = """## Next gate\n\nReview and merge this bounded scope decision.\n\nAfter merge, the first operational gate is:\n\n> Inspect and promote the exact existing PR #92 protected verify-only run and artifact.\n\nIf that result cannot be recovered, any replacement verification attempt requires new explicit authorization.\n"""
    new_next = """## Next gate\n\nPrepare a new exact-commit timeout-correction deployment authorization. Before any deployment, refresh repository and Azure reality, select the exact source, require exact-head CI, review fail-closed extension-only What-If evidence, confirm cost and quota, and define validation, rollback, cleanup, and evidence capture.\n\n```text\neffective_permission_verified != deployment_authorized\nconsumed_deployment_grant != renewed_deployment_grant\n```\n"""
    replace_once(path, old_next, new_next)


def write_validator() -> None:
    content = '''#!/usr/bin/env python3
"""Validate canonical project reality after PR #99 evidence promotion.

The file name is retained for workflow compatibility.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / ".project/current-reality.json"
HANDOFF = ROOT / ".project/handoffs/current-state.md"
LATEST = ROOT / ".project/reconciliations/post-pr99-protected-verification-evidence.json"
EVIDENCE = ROOT / ".project/evidence/pr92-protected-verification-recovery-30171257533.json"
GATE = ROOT / ".project/lab-v1-completion-gate.json"
WORKFLOW = ROOT / ".github/workflows/recover-pr92-protected-verification-evidence.yml"

MAIN = "719fe25db340fecbcc24599d6cf3c7ac1eee80dd"
DEPLOYED = "8b3d55c616d8820edd523f77021a35fe24167bd0"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    current = load(CURRENT)
    latest = load(LATEST)
    evidence = load(EVIDENCE)
    gate = load(GATE)
    handoff = HANDOFF.read_text(encoding="utf-8")
    workflow = WORKFLOW.read_text(encoding="utf-8")

    repo = current["repository_state"]
    require(repo["observed_head"] == MAIN, "main watermark mismatch")
    require(repo["latest_merged_pull_request"] == 99, "latest PR mismatch")
    require(repo["merge_order"] == [98, 97, 99], "merge order mismatch")
    require(repo["open_pull_requests_observed"] == [], "open PR observation mismatch")
    require(repo["local_working_tree"] == "not_observed", "local state fabricated")

    ci = repo["exact_head_ci"]
    require(ci["pr99_execution_source_head"] == "4593f63fafe6623dfcd4dc0df92df2ef40a96c55", "PR99 source mismatch")
    require(ci["pr99_reviewed_package_ci_run_id"] == 30171211077, "PR99 package CI mismatch")
    require(ci["pr99_execution_head_ci_run_id"] == 30171259207, "PR99 execution CI mismatch")
    require(ci["pr99_recovery_run_id"] == 30171257533, "recovery run mismatch")
    require(ci["pr99_recovery_resolution_step_conclusion"] == "success", "evidence resolution lost")
    require(ci["pr99_recovery_comment_step_conclusion"] == "failure", "comment failure erased")
    require(ci["pr99_recovery_summary_upload_conclusion"] == "success", "summary upload lost")

    anchors = current["evidence_anchors"]
    require(anchors["pr92_protected_run_id"] == 30160680313, "historical run missing")
    require(anchors["pr92_protected_artifact_id"] == 8620163872, "artifact missing")
    require(anchors["pr92_protected_artifact_manifest_verified"] is True, "manifest not verified")

    api = current["independent_demo_api"]
    require(api["deployment_provenance"]["deployed_source_ref"] == DEPLOYED, "deployed source changed")
    require(api["repository_reconciliation"]["main_ahead_by_commits"] == 191, "ahead count mismatch")
    require(api["repository_reconciliation"]["timeout_fix_deployed"] is False, "deployment fabricated")
    require(api["runtime"]["health_contract"] == "pre_timeout_fix_contract", "runtime boundary changed")
    require(api["runtime"]["corrected_timeout_fields_observed"] is False, "corrected runtime fabricated")

    resolved = api["resolved_state"]
    require(resolved["protected_verify_only_artifact_inspected"] is True, "artifact inspection lost")
    require(resolved["extension_write_permission_verified"] is True, "permission proof lost")
    require(resolved["corrected_runtime_deployed"] is False, "deployment fabricated")
    require(resolved["operationally_verified"] is False, "operation fabricated")

    rbac = current["rbac_reconciliation"]["resolved_state"]
    require(rbac["apply_success"] == "assumed_not_evidenced", "historical apply claim rewritten")
    require(rbac["effective_target_identity_permission"] == "verified_for_vm_extension_write", "permission state mismatch")
    require(rbac["deployment_authorized"] is False, "deployment authority fabricated")

    require(evidence["target"]["workflow_run_id"] == 30160680313, "evidence run mismatch")
    require(evidence["target"]["run_conclusion"] == "success", "historical run not successful")
    require(evidence["artifact"]["id"] == 8620163872, "evidence artifact mismatch")
    require(evidence["inspection"]["manifest_verified"] is True, "manifest verification missing")
    require(evidence["inspection"]["missing_success_files"] == [], "success files missing")
    require(evidence["effective_extension_write_permission_verified"] is True, "permission not verified")
    require(evidence["azure_mutation_performed"] is False, "Azure mutation fabricated")
    require(evidence["deployment_authorized"] is False, "deployment authority fabricated")

    p0 = {item["criterion_id"]: item for item in gate["priority_order"][0]["exit_criteria"]}
    require(p0["p0-protected-verification-evidence"]["current_status"].startswith("satisfied_"), "protected evidence gate open")
    require(p0["p0-effective-extension-permission"]["current_status"].startswith("satisfied_"), "permission gate open")
    require(p0["p0-timeout-correction-deployment"]["current_status"] == "repository_merged_not_deployed", "deployment gate changed")
    require(gate["next_gate"]["execution_authorized"] is False, "next gate authority fabricated")

    require(latest["resolved_state"]["p0_protected_verification_evidence"] == "satisfied", "reconciliation mismatch")
    require(latest["resolved_state"]["p0_effective_extension_permission"] == "satisfied", "reconciliation mismatch")
    require(latest["azure_boundary"]["azure_mutation_performed"] is False, "Azure mutation fabricated")

    require("continue-on-error: true" in workflow, "comment publication remains blocking")
    require("commits/${GITHUB_SHA}/pulls" in workflow, "associated PR lookup missing")
    require("expected exactly one open recovery PR" not in workflow, "fragile PR lookup remains")

    for key in (
        "pull_request_merge_authorized",
        "workflow_dispatch_authorized",
        "azure_authentication_authorized",
        "azure_mutations_authorized",
        "azure_rbac_mutations_authorized",
        "resource_graph_query_authorized",
        "guest_commands_authorized",
        "transaction_replay_authorized",
        "github_pages_publication_authorized",
        "cleanup_authorized",
    ):
        require(current["authority"][key] is False, f"{key} must remain false")

    for marker in (
        MAIN,
        DEPLOYED,
        "historical protected run: 30160680313 / success",
        "artifact: 8620163872",
        "recovery_workflow_red != protected_evidence_failed",
        "effective_permission_verified != deployment_authorized",
        "health contract: pre-timeout-fix contract",
        "total: CAD 0.734335248846279",
        "deployment authorized: false",
    ):
        require(marker in handoff, f"handoff missing {marker!r}")

    print("post-PR99 protected-evidence current-reality validation passed")


if __name__ == "__main__":
    main()
'''
    (ROOT / "scripts/validate_post_merge_pr86_pr88_current_reality.py").write_text(content, encoding="utf-8")


def write_current_reality_tests() -> None:
    content = '''from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PostMergeCurrentRealityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = json.loads((ROOT / ".project/current-reality.json").read_text(encoding="utf-8"))
        self.reconciliation = json.loads((ROOT / ".project/reconciliations/post-pr99-protected-verification-evidence.json").read_text(encoding="utf-8"))
        self.evidence = json.loads((ROOT / ".project/evidence/pr92-protected-verification-recovery-30171257533.json").read_text(encoding="utf-8"))

    def test_validator_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/validate_post_merge_pr86_pr88_current_reality.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("validation passed", result.stdout)

    def test_repository_watermark_reaches_pr99(self) -> None:
        repo = self.state["repository_state"]
        self.assertEqual(repo["observed_head"], "719fe25db340fecbcc24599d6cf3c7ac1eee80dd")
        self.assertEqual(repo["latest_merged_pull_request"], 99)
        self.assertEqual(repo["merge_order"], [98, 97, 99])
        self.assertEqual(repo["open_pull_requests_observed"], [])

    def test_recovered_artifact_establishes_effective_permission(self) -> None:
        resolved = self.state["independent_demo_api"]["resolved_state"]
        self.assertTrue(resolved["protected_verify_only_artifact_inspected"])
        self.assertTrue(resolved["extension_write_permission_verified"])
        self.assertFalse(resolved["corrected_runtime_deployed"])

        self.assertEqual(self.evidence["target"]["workflow_run_id"], 30160680313)
        self.assertEqual(self.evidence["artifact"]["id"], 8620163872)
        self.assertTrue(self.evidence["inspection"]["manifest_verified"])
        self.assertEqual(self.evidence["inspection"]["missing_success_files"], [])
        self.assertTrue(self.evidence["effective_extension_write_permission_verified"])
        self.assertFalse(self.evidence["azure_mutation_performed"])
        self.assertFalse(self.evidence["deployment_authorized"])

    def test_red_recovery_run_preserves_successful_core_evidence(self) -> None:
        pr99 = self.reconciliation["pull_request_99"]
        self.assertEqual(pr99["recovery_run_conclusion"], "failure")
        self.assertEqual(pr99["historical_resolution_step_conclusion"], "success")
        self.assertEqual(pr99["comment_publication_step_conclusion"], "failure")
        self.assertEqual(pr99["sanitized_summary_upload_conclusion"], "success")

    def test_repository_and_runtime_remain_separate(self) -> None:
        api = self.state["independent_demo_api"]
        self.assertEqual(api["repository_reconciliation"]["main_ahead_by_commits"], 191)
        self.assertFalse(api["repository_reconciliation"]["timeout_fix_deployed"])
        self.assertEqual(api["runtime"]["health_contract"], "pre_timeout_fix_contract")
        self.assertFalse(api["runtime"]["corrected_timeout_fields_observed"])
        self.assertFalse(api["runtime"]["full_workload_operationally_verified"])

    def test_reconciliation_preserves_azure_boundary(self) -> None:
        azure = self.reconciliation["azure_boundary"]
        self.assertFalse(azure["fresh_azure_authentication_performed"])
        self.assertFalse(azure["fresh_azure_query_performed"])
        self.assertFalse(azure["fresh_runtime_test_performed"])
        self.assertFalse(azure["azure_mutation_performed"])

    def test_no_execution_authority_was_manufactured(self) -> None:
        authority = self.state["authority"]
        for key in (
            "pull_request_merge_authorized",
            "workflow_dispatch_authorized",
            "azure_authentication_authorized",
            "azure_mutations_authorized",
            "azure_rbac_mutations_authorized",
            "resource_graph_query_authorized",
            "guest_commands_authorized",
            "transaction_replay_authorized",
            "github_pages_publication_authorized",
            "cleanup_authorized",
        ):
            self.assertFalse(authority[key], key)


if __name__ == "__main__":
    unittest.main()
'''
    (ROOT / "tests/test_post_merge_pr86_pr88_current_reality.py").write_text(content, encoding="utf-8")


def write_gate_tests() -> None:
    content = '''from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
GATE_PATH = ROOT / ".project" / "lab-v1-completion-gate.json"
DOCUMENT_PATH = ROOT / "docs" / "lab-v1-completion-gate.md"

EXPECTED_P0_IDS = {
    "p0-protected-verification-evidence",
    "p0-effective-extension-permission",
    "p0-timeout-correction-deployment",
    "p0-runtime-contract",
    "p0-servicetracer-scenario",
    "p0-browser-demonstration",
    "p0-evidence-lock",
}

FALSE_OPERATIONAL_AUTHORITY = {
    "pull_request_merge",
    "workflow_dispatch_or_rerun",
    "azure_authentication",
    "azure_query",
    "azure_mutation",
    "deployment",
    "rbac_mutation",
    "guest_command",
    "transaction_replay",
    "endpoint_publication",
    "cleanup",
}


class LabV1CompletionGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.gate = json.loads(GATE_PATH.read_text(encoding="utf-8"))
        cls.document = DOCUMENT_PATH.read_text(encoding="utf-8")

    def test_gate_is_active_repository_authority(self) -> None:
        self.assertEqual(self.gate["schema_version"], "project.lab-v1-completion-gate.v1")
        self.assertEqual(self.gate["project"], "ServiceTracer — Governed Azure Operations Lab")
        self.assertEqual(self.gate["decision_status"], "merged_repository_authority_active")

    def test_priority_order_and_p0_ids_are_preserved(self) -> None:
        priorities = self.gate["priority_order"]
        self.assertEqual([item["priority"] for item in priorities], ["P0", "P1", "P2"])
        self.assertEqual({item["criterion_id"] for item in priorities[0]["exit_criteria"]}, EXPECTED_P0_IDS)

    def test_first_two_p0_criteria_are_satisfied_without_deployment(self) -> None:
        p0 = {item["criterion_id"]: item for item in self.gate["priority_order"][0]["exit_criteria"]}
        self.assertTrue(p0["p0-protected-verification-evidence"]["current_status"].startswith("satisfied_"))
        self.assertTrue(p0["p0-effective-extension-permission"]["current_status"].startswith("satisfied_"))
        self.assertEqual(p0["p0-timeout-correction-deployment"]["current_status"], "repository_merged_not_deployed")

    def test_scope_freeze_and_backup_exclusion_remain(self) -> None:
        scope = self.gate["scope_control"]
        self.assertFalse(scope["parallel_feature_expansion_allowed"])
        self.assertFalse(scope["new_workload_allowed"])
        self.assertFalse(scope["new_governance_abstraction_allowed"])
        exclusion = self.gate["priority_order"][1]["explicit_exclusion"]
        self.assertEqual(exclusion["backup_and_recovery_services"], "intentionally_out_of_scope_for_lab_v1")

    def test_operational_authority_remains_false(self) -> None:
        authority = self.gate["authority"]
        for field in FALSE_OPERATIONAL_AUTHORITY:
            with self.subTest(field=field):
                self.assertFalse(authority[field])
        self.assertFalse(self.gate["next_gate"]["execution_authorized"])

    def test_evidence_and_human_document_are_aligned(self) -> None:
        evidence = self.gate["evidence_inputs"]
        self.assertEqual(evidence["protected_verification_historical_run"], 30160680313)
        self.assertEqual(evidence["protected_verification_artifact_id"], 8620163872)
        for marker in (
            "p0-protected-verification-evidence = satisfied",
            "p0-effective-extension-permission = satisfied",
            "p0-timeout-correction-deployment = repository_merged_not_deployed",
            "effective_permission_verified != deployment_authorized",
            "Prepare a new exact-commit timeout-correction deployment authorization",
        ):
            self.assertIn(marker, self.document)


if __name__ == "__main__":
    unittest.main()
'''
    (ROOT / "infra/tests/test_lab_v1_completion_gate.py").write_text(content, encoding="utf-8")


def remove_temporary_files() -> None:
    for path in (
        ROOT / ".github/workflows/apply-post-pr99-evidence-promotion.yml",
        ROOT / "scripts/apply_post_pr99_evidence_promotion.py",
    ):
        path.unlink(missing_ok=True)


def main() -> None:
    evidence = load(EVIDENCE_PATH)
    if not (
        evidence["effective_extension_write_permission_verified"] is True
        and evidence["inspection"]["manifest_verified"] is True
        and evidence["inspection"]["missing_success_files"] == []
        and evidence["azure_mutation_performed"] is False
        and evidence["deployment_authorized"] is False
    ):
        raise AssertionError("promoted evidence does not satisfy fail-closed requirements")

    promote_current_reality()
    promote_gate()
    write_reconciliation()
    write_handoff()
    patch_recovery_workflow_and_test()
    patch_gate_document()
    write_validator()
    write_current_reality_tests()
    write_gate_tests()
    remove_temporary_files()
    print("post-PR99 protected evidence promotion applied")


if __name__ == "__main__":
    main()
