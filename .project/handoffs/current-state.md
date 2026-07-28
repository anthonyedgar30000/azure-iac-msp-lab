# Current project handoff

## Interpretation boundary

This handoff records repository state observed through **2026-07-27T23:33:20-04:00** and Azure evidence last captured by preserved workflow artifacts. It is not a continuously refreshed GitHub or Azure dashboard. Query live GitHub state and obtain fresh Azure evidence before any write, merge, dispatch, authentication, or cloud action.

```text
declared_in_code != deployed_in_azure
deployment_succeeded != service_validated
workflow_conclusion != live_service_truth
deployment_succeeded != authority_valid
issue_comment_consumption_record != enforced_single_use
closed_trigger_PR != historical_run_unrerunnable
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
post-containment repository reconciliation: .project/reconciliations/post-pr182-containment-20260727.json
consumed request: .project/deployment-requests/correlation-identity-run1.json
replacement authorization design: .project/designs/durable-single-use-authorization-ledger-v1.md
```

## Repository watermark

```text
repository: anthonyedgar30000/azure-iac-msp-lab
observed main: 516cc45972725f494815449f55f02f96727afbde
latest merged PR: #182
PR #182 exact tested head: 5e544794243f814bca19210e65943995f4f6b2de
PR #182 CI: 30324033493 / success
current-reality lifecycle: 30324033482 / success
shared-state reconciliation: 30324033498 / success
Azure architecture plan: 30324033472 / success
trigger PR #181: closed without merge
open pull requests observed: none
local working tree: not observed; connector-backed repository operations
```

The deployed application source remains `0b6b5322f25b3d0289f6c0febdcfd800ea4b909a`. Main is newer because it contains governance containment, state reconciliation, and tests. No newer application implementation was observed.

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

## Current authority

```text
repository reconciliation and design: authorized
ordinary pull-request CI: authorized
workflow dispatch or rerun: unauthorized
Azure authentication, query, or mutation: unauthorized
rollback: unauthorized
cleanup: unauthorized
RBAC mutation: unauthorized
```

## Next gate

Review `.project/designs/durable-single-use-authorization-ledger-v1.md`. The proposed design uses a separate no-OIDC claim job and an atomic, protected, first-writer-wins Git reference as the durable consumption ledger. The collector workflow remains quarantined. Implementation and any Azure restoration require fresh explicit non-renewing authority.
