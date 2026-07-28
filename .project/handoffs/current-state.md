# Current project handoff

## Interpretation boundary

This handoff records repository state observed through **2026-07-28T19:32:58-04:00** and Azure evidence last captured by preserved workflow artifacts. It is not a continuously refreshed GitHub or Azure dashboard. Query live GitHub state and obtain fresh Azure evidence before any write, merge, dispatch, ruleset change, authorization claim, authentication, or cloud action.

```text
declared_in_code != deployed_in_azure
deployment_succeeded != service_validated
workflow_conclusion != live_service_truth
deployment_succeeded != authority_valid
issue_comment_consumption_record != enforced_single_use
closed_trigger_PR != historical_run_unrerunnable
PR_exact_head_CI_success != integrated_main_CI_observed
implementation_merged != control_activated
atomic_claim_workflow_present != protected_ledger_verified
repository_watermark_reconciled != Azure_freshly_observed
main_contains_frontend_implementation != GitHub_Pages_publication_observed
architecture_explained != runtime_proof_manufactured
static_repository_proof != fresh_Azure_observation
not_observed != false
```

## Canonical files

```text
state index: .project/state-index.json
current reality: .project/current-reality-v2.json
completion gate: .project/lab-v1-completion-gate-v2.json
current handoff: .project/handoffs/current-state.md
latest terminal deployment reconciliation: .project/reconciliations/correlation-identity-run1-terminal-20260727.json
containment reconciliation: .project/reconciliations/post-pr182-containment-20260727.json
previous repository reconciliation: .project/reconciliations/post-pr185-repository-watermark-20260728.json
latest repository reconciliation: .project/reconciliations/post-pr187-repository-watermark-20260728.json
consumed request: .project/deployment-requests/correlation-identity-run1.json
replacement authorization design: .project/designs/durable-single-use-authorization-ledger-v1.md
replacement authorization contract: .project/contracts/durable-single-use-authorization-ledger-v1.json
```

## Repository watermark

```text
repository: anthonyedgar30000/azure-iac-msp-lab
observed main: 07f32b59eda11b5a3627d398f1ffca00c8c88e69
latest merged PR: #187
PR #187 exact tested head: 44bc3ab202c2e3d709aa2d9906ef9aba365acfb2
PR #187 CI: 30390614963 / success
current-reality lifecycle: 30390618165 / success
shared-state reconciliation: 30390616682 / success
Azure architecture plan: 30390616307 / success
integrated main CI: not observed
PR #186 implementation head: 138659609b15ef80f6cce12d916e26382ab71205
PR #186 CI: 30389249099 / success
PR #186 merge: 30e312ef5122831a8233835db2f541437a97b125
PR #187 merge: 07f32b59eda11b5a3627d398f1ffca00c8c88e69
trigger PR #181: closed without merge
open pull requests observed: none
local working tree: not observed; connector-backed repository operations
```

PR #186 merged the durable single-use authorization implementation. PR #187 then merged the historical repository reconciliation that had observed PR #186 while it was still open. Therefore the PR #185 reconciliation remains valid for its own time boundary but is no longer current repository truth.

The deployed collector application source remains `0b6b5322f25b3d0289f6c0febdcfd800ea4b909a`. Main is newer because it contains governance containment, repository reconciliations, the authorization-ledger design and implementation, the frontend architecture explainer, and deterministic tests. No newer collector deployment is promoted.

The frontend architecture implementation is present in the repository and its exact PR head passed CI. GitHub Pages publication and browser rendering were not freshly observed, so the repository implementation is not promoted as deployed presentation truth.

## Correlation deployment authority

```text
request: correlation-identity-run1
attempt limit: 1
consumed at: 2026-07-27T22:21:42Z
renewable: false
retry authorized: false
rollback authorized: false
attempts observed: 2
```

Attempt 1 was the authorized consuming attempt. Attempt 2 was an unauthorized replay after consumption.

### Attempt 1

```text
dispatcher run: 30310432132
child deployment run: 30310439500
child artifact: 8670172029
artifact digest: sha256:8917c2adea01c881a7382020bad06dd94288c576141c0d80b865f382c3eecb7b
authority: valid consuming attempt
ARM parent: Succeeded
ARM nested: Succeeded
VM extension: Succeeded
workflow conclusion: failure
failure boundary: legacy CORS and GitHub Pages evidence observer
```

### Attempt 2

```text
dispatcher run: 30310432132 / rerun
child deployment run: 30315658677
child artifact: 8672070574
artifact digest: sha256:8e551e4b770996db41befc6f95b4dd6af08f674ae098e6bcde0d22234a049c8e
authority: invalid unauthorized replay
ARM parent: Succeeded
ARM nested: Succeeded
VM extension: Succeeded
workflow conclusion: failure
failure boundary: presentation evidence observer
```

The red child conclusions came from legacy or presentation evidence observers. They do not negate successful ARM convergence, extension convergence, or the preserved API evidence. They also do not make the unauthorized replay valid.

## Last evidenced Azure state

No fresh Azure query was performed by this reconciliation.

```text
subscription: Azure for Students
subscription and tenant IDs: observed but not promoted
resource group: rg-servicetracer-dev-westus2
region: westus2
collector VM: vm-stcollector-mst-dev
VM size: Standard_B2ats_v2
private IP: 10.20.40.10
power state: running
extension state: Succeeded
extension source: 0b6b5322f25b3d0289f6c0febdcfd800ea4b909a
standard public IPv4 usage: 2 / 3
resource locks: 0
actual cost: not observed
```

## Last evidenced live service state

```text
health: healthy
hosting model: collector_vm_systemd
Azure host identity: verified
deployed source: exact reviewed source
12 health requests: passed
CORS preflight: HTTP 204
analysis POST: HTTP 200
request header/body identity: verified
transactions: 20
successful / failed: 10 / 10
exact root cause claimed: false
browser DOM refresh: pending direct observation
fresh runtime observation during this reconciliation: false
```

## Frontend architecture state

```text
repository implementation: merged in PR #185
exact tested source: 36bbd5ab1ef3c579c43ad2df589f44362feced37
exact-head CI: 30359529916 / success
GitHub Pages publication freshly observed: false
browser architecture rendering freshly verified: false
Azure collector runtime change claimed: false
```

## Durable authorization implementation state

```text
implementation PR: #186 / merged
exact tested source: 138659609b15ef80f6cce12d916e26382ab71205
exact-head CI: 30389249099 / success
merge commit: 30e312ef5122831a8233835db2f541437a97b125
reusable workflow on main: true
claim job id-token permission: none
atomic create-reference contract: present
protected tag ruleset configured: false
ruleset independently inspected: false
live first claim tested: false
live replay rejection tested: false
concurrent exactly-one-claimant proof: false
collector workflow restored: false
Azure execution enabled: false
operationally verified: false
```

The implementation is merged but not activated. A repository file and green exact-head CI establish implementation truth; they do not establish repository-settings truth or live race behaviour.

## Control incident and merged containment

The root cause is an **authorization consumption control failure** under the canonical **Authorization Consumption Principle**. The dispatcher wrote a consumed marker to an issue comment but did not consult a durable external single-use ledger before every dispatch. A GitHub Actions rerun reused the original opened-event request snapshot.

PR #182 merged the repository-only containment:

```text
shared collector workflow: quarantined fail-closed on main
OIDC permission: absent
Azure environment: absent
Azure login: absent
Azure commands: absent
terminal behavior: reject and exit 1
consumed one-shot dispatcher: deleted from main
trigger PR #181: closed without merge
new Azure authority created: false
```

Static repository proof establishes that a replay can no longer obtain Azure OIDC or execute Azure commands through the current child workflow. This is not a fresh Azure runtime observation.

PR #186 added the replacement authorization implementation without restoring Azure execution. PR #187 reconciled the repository through PR #185 at its historical boundary. This handoff supersedes that watermark by recording both merges while preserving all activation blockers.

## Lab v1 gate

```text
exact source deployed: true
runtime contract verified: true
20-transaction scenario verified: true
frontend architecture source and CI verified: true
GitHub Pages publication and browser rendering verified: false
monitoring and alert delivery verified: false
effective least privilege verified: false
fresh actual cost observed: false
authorization implementation merged: true
authorization ruleset and live claim behaviour verified: false
deployment automation safely available: false / quarantined
```

## Historical compatibility anchors

The following markers remain only so durable historical validators can reproduce their original observation boundaries. They do not override the current terminal or repository reconciliation.

```text
legacy canonical main: 665e051375594d11e58e434231bd06775dbdc560
PR #92 source: 5b5af74d57fb5fd87ece2a34239cc6f29d04b12b
PR #93 source: eecb5c872f76cb5e51df6f5451d5a61b79d87bba
PR #93 merge: 99dc79c7093fa4cd5655c2d5a65095dd796f9f75
independent demo deployed source: 8b3d55c616d8820edd523f77021a35fe24167bd0
checks_green != protected_Azure_artifact_inspected
human_operator_merge != prior_agent_merge_authority
deployment grant status: consumed_blocked
missing action: Microsoft.Compute/virtualMachines/extensions/write
effective extension write: unverified
authorization reconciliation merge: 92b0c3b1064158684a4b280348c77eeedba6dfc3
independent planner run: 30064289707
independent planner artifact: 8585693830
independent planner digest: 7aae2cff0df757a4b436c5b87507162624813e64bd32946bada8a87e5d7adc22
independent SKU restriction: NotAvailableForSubscription
independent VM family: standardBasv2Family
typed readiness control: PR #73
GitHub Pages publication authorized: false
not_observed != false
preserved verified preflight: .project/reconciliations/collector-provenance-preflight-run1-artifact-promotion-20260726.json
prior run-19 reconciliation: .project/reconciliations/collector-provenance-deployment-run19-20260726.json
```

## Current authority

```text
repository watermark reconciliation: authorized
pull-request creation: authorized
ordinary pull-request CI: authorized
pull-request merge: unauthorized
workflow dispatch or rerun: unauthorized
repository ruleset mutation: unauthorized
authorization tag claim execution: unauthorized
Azure authentication, query, or mutation: unauthorized
rollback: unauthorized
cleanup: unauthorized
RBAC mutation: unauthorized
```

## Next gate

Review this repository-only reconciliation through ordinary pull-request CI. Merge requires fresh explicit authority. Protected-tag ruleset configuration, first-claim testing, replay testing, concurrent-claim testing, and any repository-settings change each require separate fresh authority. The collector workflow remains quarantined. Separately observe GitHub Pages and browser rendering before claiming that the architecture explainer is publicly deployed. Any Azure restoration requires fresh explicit non-renewing authority.
