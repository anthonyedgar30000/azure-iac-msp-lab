# Current project handoff

## Interpretation boundary

This handoff records repository state observed through **2026-07-28T00:55:38-04:00** and Azure evidence last captured by preserved workflow artifacts. It is not a continuously refreshed GitHub or Azure dashboard. Query live GitHub state and obtain fresh Azure evidence before any write, merge, dispatch, authentication, or cloud action.

```text
declared_in_code != deployed_in_azure
deployment_succeeded != service_validated
workflow_conclusion != live_service_truth
deployment_succeeded != authority_valid
issue_comment_consumption_record != enforced_single_use
closed_trigger_PR != historical_run_unrerunnable
repository_watermark_reconciled != Azure_freshly_observed
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
latest repository reconciliation: .project/reconciliations/post-pr183-repository-watermark-20260728.json
consumed request: .project/deployment-requests/correlation-identity-run1.json
replacement authorization design: .project/designs/durable-single-use-authorization-ledger-v1.md
```

## Repository watermark

```text
repository: anthonyedgar30000/azure-iac-msp-lab
observed main: db74fc764f93a972344dae35ed906e8128f51eb8
latest merged PR: #183
PR #183 exact tested head: 52ab387418e77aed0cd23a2d827b359a8ae0ac40
PR #183 CI: 30326878347 / success
current-reality lifecycle: 30326878314 / success
shared-state reconciliation: 30326878316 / success
Azure architecture plan: 30326878319 / success
merge-commit PR-triggered CI: not observed
trigger PR #181: closed without merge
open pull requests observed: none
local working tree: not observed; connector-backed repository operations
```

The deployed application source remains `0b6b5322f25b3d0289f6c0febdcfd800ea4b909a`. Main is newer because it contains governance containment, post-containment reconciliation, the authorization-ledger design, canonical state, and tests. No newer application implementation was observed.

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
browser DOM refresh: pending user observation
```

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

PR #183 then reconciled that containment into canonical state and documented the proposed durable single-use authorization ledger. The design is proposed, not implemented; the collector workflow remains quarantined.

## Lab v1 gate

```text
exact source deployed: true
runtime contract verified: true
20-transaction scenario verified: true
browser rendering verified: false
monitoring and alert delivery verified: false
effective least privilege verified: false
fresh actual cost observed: false
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
ordinary pull-request CI: authorized
pull-request merge: unauthorized
workflow dispatch or rerun: unauthorized
Azure authentication, query, or mutation: unauthorized
rollback: unauthorized
cleanup: unauthorized
RBAC mutation: unauthorized
```

## Next gate

Review `.project/designs/durable-single-use-authorization-ledger-v1.md`. The proposed design uses a separate no-OIDC claim job and an atomic, protected, first-writer-wins Git reference as the durable consumption ledger. The collector workflow remains quarantined. Implementation and any Azure restoration require fresh explicit non-renewing authority.
