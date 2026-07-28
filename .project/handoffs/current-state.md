# Current project handoff

## Interpretation boundary

This handoff records evidence observed through **2026-07-27T22:34:00-04:00**. It is not a continuously refreshed GitHub or Azure dashboard. Query live GitHub state and obtain fresh Azure evidence before any write, merge, dispatch, authentication, or cloud action.

```text
declared_in_code != deployed_in_azure
deployment_succeeded != service_validated
workflow_conclusion != live_service_truth
deployment_succeeded != authority_valid
issue_comment_consumption_record != enforced_single_use
closed_trigger_PR != historical_run_unrerunnable
not_observed != false
```

## Canonical files

```text
state index: .project/state-index.json
current reality: .project/current-reality-v2.json
completion gate: .project/lab-v1-completion-gate-v2.json
latest terminal reconciliation: .project/reconciliations/correlation-identity-run1-terminal-20260727.json
consumed request: .project/deployment-requests/correlation-identity-run1.json
```

## Repository watermark

```text
repository: anthonyedgar30000/azure-iac-msp-lab
observed main: 767a0482cdfff689e430ebe4a5a08fc339f1a291
latest merged PR: #180
PR #180 source: 51286ff49b86e02d69a4169925880d0970a82e36
PR #180 exact-head CI: 30310296654 / success
trigger PR #181: closed without merge
containment branch: agent/quarantine-correlation-replay
local working tree: not observed; connector-backed changes
```

The deployed application source is `0b6b5322f25b3d0289f6c0febdcfd800ea4b909a`. Main is newer because it includes governance workflow, request, and test changes. No newer application implementation was observed.

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
```

The red child conclusions came from legacy or presentation evidence observers. They do not negate the successful ARM deployment, extension convergence, or live API verification.

## Latest Azure evidence

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

## Live service verification

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

## Control incident and containment

The root cause is an **authorization consumption control failure**. The dispatcher wrote a consumed marker to an issue comment but did not consult a durable external single-use ledger before every cloud dispatch. A GitHub Actions rerun reused the original opened-event request snapshot and dispatched a second child run.

Repository-only containment on `agent/quarantine-correlation-replay`:

```text
shared collector workflow: quarantined fail-closed
OIDC permission: absent
Azure environment: absent
Azure commands: absent
consumed one-shot dispatcher: deleted from branch
trigger PR #181: closed without merge
new Azure authority created: false
```

The quarantine is intentionally broad. It blocks `what-if`, `deploy`, and `verify` through the shared collector workflow until a replacement workflow is reviewed with durable replay protection.

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
repository containment and reconciliation: authorized
ordinary pull-request CI: authorized
PR #181 closure without merge: completed
containment PR merge: not separately recorded
workflow dispatch or rerun: unauthorized
Azure authentication, query, or mutation: unauthorized
rollback: unauthorized
cleanup: unauthorized
RBAC mutation: unauthorized
```

## Next gate

Review exact-head CI for the containment pull request. After merge, prove that replaying the historical dispatcher cannot obtain OIDC or execute Azure commands. Do not restore the collector workflow until a durable external consumption ledger, unique immutable request IDs, replay tests, and fresh explicit authority exist.
