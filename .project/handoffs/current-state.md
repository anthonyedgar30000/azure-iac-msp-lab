# Current project handoff

## Interpretation boundary

This handoff reflects repository state observed on `2026-07-26T04:43:53-04:00` and the newest durable Azure evidence from collector-hosted demo API What-If run `30192970923`.

```text
declared_in_code != deployed_in_azure
deployment_succeeded != service_validated
resource_exists != securely_configured
RBAC_assignment != effective_least_privilege
monitoring_enabled != alerts_verified
estimated_cost != actual_cost
artifact_verified != deployment_authorized
WhatIf_accepted != service_restored
not_observed != false
source_silence != contradiction
verification_status != truth_value
```

Resolve live GitHub, Azure identity, subscription, cost, quota, locks, dependencies, and authority before every consequential operation.

## Canonical state selection

```text
state index: .project/state-index.json
current reality: .project/current-reality-v2.json
current completion gate: .project/lab-v1-completion-gate-v2.json
legacy PR #92/#93 reality snapshot: .project/current-reality.json
legacy original completion gate: .project/lab-v1-completion-gate.json
```

Legacy filenames remain immutable evidence inputs for historical validators; they are not current operational authority.

## Repository watermark

```text
repository: anthonyedgar30000/azure-iac-msp-lab
main: 9bfff60bd2e1e3bbf5610807df7d970c9bd9f229
latest merge: PR #120
PR #120 source head: 2a2bfa64643e56d304fe075392735ec7155c05ed
PR #120 exact-head CI: 30194713992 / success
open pull requests observed: none
local working tree: not observed
merge-commit CI: not observed
```

PR #120 promotes the exact run-16 workflow and artifact evidence. It does not authorize deployment.

## Exact collector What-If evidence

```text
workflow: Collector-hosted demo API
run number: 16
run ID: 30192970923
run attempt: 1
job ID: 89769401839
operation: what-if
reviewed source: 8de1f61f8a0ea06dcf94b94c798edde2aace357d
artifact ID: 8629191915
artifact digest: sha256:57fe05c113d0fefc86437a4aa247b920dc6a02680a1c2bfe8e67873fe7612e6e
manifest payloads verified: 29 / 29
Azure mutation: false
deployment step: skipped
runtime verification: skipped
transaction replay: not performed
```

## Captured collector Azure state

```text
subscription: Azure for Students
subscription, tenant, and principal IDs: SHA-256 fingerprints only
resource group: rg-servicetracer-dev-westus2
location: westus2
collector VM: vm-stcollector-mst-dev
collector VM size: Standard_B2ats_v2
collector VM state: running
collector private IP: 10.20.40.10
load balancer: lb-st-demo-api-mst-dev / Succeeded
backend pool: be-st-demo-api / zero addresses
VM extension: servicetracer-demo-api / Failed
resource locks: none
readiness blockers: none
```

The evidence was captured at `2026-07-26T07:33:03Z`. It is time-bounded and not a continuously refreshed Azure dashboard.

## Accepted Azure plan

```text
24 Ignore
3 Modify
3 NoChange
0 Create
0 Delete
0 Replace
```

Approved modifications are limited to:

1. Rerun the exact `Microsoft.Azure.Extensions / CustomScript` extension with `forceUpdateTag` bound to `8de1f61f...`.
2. Reconcile the exact existing Standard/Regional load-balancer parent contract.
3. Populate `be-st-demo-api` with one backend named `collector` at `10.20.40.10`.

Explicit `NoChange` targets:

```text
pip-st-demo-api-mst-dev
Allow-Demo-API-HTTP-From-Internet
Allow-Demo-API-HTTPS-From-Internet
```

No collector VM, NIC, base infrastructure, Microsoft.Web resource, create, delete, or replace is proposed.

## Quota, cost, and source boundary

```text
Standard IPv4 public IPs: 2 / 3
load balancers: 2 / 1000
additional public IP required: 0
quota sufficient for accepted no-create plan: true

current billing cost: not observed
remaining Azure for Students credit: not observed
cost delta: not quantified
```

The accepted plan is bound to `8de1f61f8a0ea06dcf94b94c798edde2aace357d`.

Current `main` is `9bfff60bd2e1e3bbf5610807df7d970c9bd9f229`. The intervening changes are repository evidence and validation only, but:

```text
deploying accepted source != deploying current main
```

An exact deployment source decision remains unresolved.

## Lab v1 status

```text
exact What-If and artifact evidence: complete
cost or credit refresh: pending
exact deployment source decision: pending
collector deployment: not performed
post-deployment runtime validation: not performed
20-transaction ServiceTracer scenario: not performed
live browser demonstration: not verified
monitoring and alert delivery: not verified
full evidence lock: incomplete
```

## Historical compatibility anchors

The following historical evidence remains valid only within its original observation boundary:

```text
PR #84 merge: c96d9cbb765a023921fa819cf7d99c957e8ad608
PR #84 source: 5c938a7e07da3a22b27bb5ac5aa52b7ccf22ba37
historical main: 665e051375594d11e58e434231bd06775dbdc560
PR #92 source: 5b5af74d57fb5fd87ece2a34239cc6f29d04b12b
PR #93 source: eecb5c872f76cb5e51df6f5451d5a61b79d87bba
PR #93 merge: 99dc79c7093fa4cd5655c2d5a65095dd796f9f75
independent demo API deployed source: 8b3d55c616d8820edd523f77021a35fe24167bd0
merged_into_main != deployed_to_VM
checks_green != protected_Azure_artifact_inspected
human_operator_merge != prior_agent_merge_authority
missing action: Microsoft.Compute/virtualMachines/extensions/write
deployment grant status: consumed_blocked
effective extension write: unverified
authorization reconciliation merge: 92b0c3b1064158684a4b280348c77eeedba6dfc3
planner run: 30064289707
planner artifact: 8585693830
planner artifact SHA-256: 7aae2cff0df757a4b436c5b87507162624813e64bd32946bada8a87e5d7adc22
restriction: NotAvailableForSubscription
VM family: standardBasv2Family
typed readiness control: PR #73
GitHub Pages publication authorized: false
```

Historical evidence is preserved; it is not allowed to overwrite newer collector evidence.

## Current authority

```text
repository reconciliation authorized: true
draft pull request creation authorized: true
ordinary pull request CI authorized: true
pull request merge authorized: false
workflow dispatch authorized: false
Azure authentication authorized: false
Azure query authorized: false
Azure mutation authorized: false
deployment authorized: false
rollback authorized: false
transaction replay authorized: false
RBAC mutation authorized: false
cleanup authorized: false
```

## Next gate

1. Refresh current Azure for Students credit or billing evidence.
2. Select one exact deployment source.
3. Repeat live preflight and FullResourcePayloads What-If for that exact source.
4. Seek a one-shot, non-renewing deployment grant with rollback and post-deployment verification boundaries.
