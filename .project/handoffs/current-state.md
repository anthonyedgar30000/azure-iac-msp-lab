# Current project handoff

## Interpretation boundary

This handoff records repository lifecycle state checked after PR #93 and then PR #92 merged. It preserves the latest durable Azure evidence reviewed on `2026-07-25`; it is not a continuously refreshed GitHub or Azure dashboard.

```text
merged_into_main != deployed_to_VM
checks_green != protected_Azure_artifact_inspected
verification_package_merged != effective_permission_verified
human_operator_merge != prior_agent_merge_authority
repository_RBAC_package != Azure_RBAC_observed
RBAC_apply_asserted != RBAC_apply_succeeded
role_assignment_observed != effective_permission_verified
cleanup_plan_merged != cleanup_query_executed
cleanup_candidate != orphaned_resource
historical_planner_evidence != current_deployment_state
not_observed != false
not_observed != absent
conflicting != false
```

Resolve live GitHub, exact-head CI, authority, Azure state, cost, quota, RBAC, and dependency health before every consequential operation.

## Repository watermark

```text
repository: anthonyedgar30000/azure-iac-msp-lab
main: 665e051375594d11e58e434231bd06775dbdc560
latest merge by time: PR #92
also merged in final main: PR #93
merge order: PR #93, then PR #92
open pull requests observed: none
local working tree: not observed
```

PR #92:

```text
title: Verify effective extension write permission without mutation
reviewed package head: c53093ec5a9c84dbe1abb450a0079e01b2865bda
reviewed package CI: 30160596671 / success
execution source head: 5b5af74d57fb5fd87ece2a34239cc6f29d04b12b
execution-head CI: 30160681565 / success
merge commit: 665e051375594d11e58e434231bd06775dbdc560
operator UI check rollup: all checks passed
named protected verifier run ID: not observed
protected verifier artifact: not observed
effective extension-write permission: unverified
Azure mutation claimed: false
```

PR #93:

```text
title: Decouple PR82 historical validation from handoff prose
source head: eecb5c872f76cb5e51df6f5451d5a61b79d87bba
merge commit: 99dc79c7093fa4cd5655c2d5a65095dd796f9f75
PR 82 historical workflow: 30160683469 / success
CI: 30160683486 / success
Azure action performed: false
```

The PR descriptions recorded `pull_request_merge_authorized: false`. The repository owner subsequently merged both PRs through GitHub. Those merges are accepted as live repository reality and recorded as human operator actions; the earlier agent grants are not retroactively broadened.

No workflow result was observed directly on the final combined main merge composition.

## Preserved repository anchors

```text
PR #90 merge: 8b25ecf1f00a59033955ef67bb3f9b511126f08a
PR #90 source: 0e5ae4c68801695241eebef4f05967ec38a894ff
PR #90 CI: 30146139826, 30146139825, 30146139830, 30146139832 / success

PR #89 merge: 39e214a32ebdac61d22d7b130d4c2f1e5d6f4f53
PR #89 source: 3727b67533eb8043a22895a833223fa00fb70d10
PR #89 full CI: 30145973950 / failure
PR #89 dedicated checks: 30145973957, 30145973961, 30145973948 / success

PR #88 merge: 726c42ea1dddf402a42d8d0c591c660ebc50733f
PR #88 source: 5e05d050cace2210c9b47103fe100eceb759cd0e
PR #88 exact-head CI: 30142555135, 30142555107, 30142555131 / success

PR #86 merge: 67d1aa9c784825e835097f684ddf629727ca5e22
PR #86 source: 8df0a5af4b522ceeff16c0d9d1adfc978e66d559
PR #86 exact-head CI: 30141965628 / success

PR #84 merge: c96d9cbb765a023921fa819cf7d99c957e8ad608
PR #84 source: 5c938a7e07da3a22b27bb5ac5aa52b7ccf22ba37
PR #84 exact-head CI: 30137351716 / success

PR #82 merge: 5dfa3b76a9fb975002d9cd702a892a0f678c88c5
PR #82 source: a85970061879ef4a900564d18e9631630e95b11e
PR #82 CI: 30112308916
```

## Repository-to-runtime boundary

Current `main` is 158 commits ahead of deployed source `8b3d55c616d8820edd523f77021a35fe24167bd0` and zero behind.

```text
deployed_source_ref != current_main
workload_source_or_IaC_drift = observed
repository_timeout_fix_merged = true
deployed_timeout_fix_verified = false
repository_RBAC_package_merged = true
repository_verify_only_attempt_2_merged = true
Azure_RBAC_effectiveness_verified = false
repository_cleanup_plan_merged = true
cleanup_dependency_collection_executed = false
repository_structured_PR82_validator_fix_merged = true
```

## Latest durable Azure evidence

The newest durable protected observation remains time-bounded through `2026-07-25T00:47:40Z`:

```text
subscription: Azure subscription 1
resource group: rg-st-demo-api-dev-westus2
location: westus2
resources observed: 7
deployment: servicetracer-demo-api-dev / Succeeded
deployed source: 8b3d55c616d8820edd523f77021a35fe24167bd0
VM: vm-st-demo-api-mst-dev
VM size: Standard_F1als_v7
VM state: VM running
VM provisioning: Succeeded
Custom Script extension provisioning: Succeeded
FQDN: st-demo-api-vm-aeg30000.westus2.cloudapp.azure.com
public GET /api/health: HTTP 200 / healthy
health contract: pre-timeout-fix contract
corrected timeout fields observed: false
```

No fresh Azure inventory, Resource Graph query, RBAC query, runtime test, deployment, or mutation was performed by this repository reconciliation.

## Historical timeout-fix deployment outcome

```text
deployment grant status: consumed_blocked
attempts: 2
missing action at attempt time: Microsoft.Compute/virtualMachines/extensions/write
What-If result observed: false
deployment step executed: false
Azure resource mutation performed: false
rollback performed: false
```

Green checks on PR #92 do not retroactively deploy the fix or renew deployment authorization.

## RBAC reconciliation

```text
role: ServiceTracer Demo API Extension Updater v1
action: Microsoft.Compute/virtualMachines/extensions/write
assignable scope: rg-st-demo-api-dev-westus2
assignment scope: vm-st-demo-api-mst-dev/extensions/servicetracer-demo-api
PR #86 operator --apply attempt asserted: true
apply success: assumed_not_evidenced
role definition observed: false
role assignment observed: false
PR #92 check rollup: passed
exact protected run and artifact: not observed
effective extension write: unverified
deployment authorized: false
```

The check rollup is retained as evidence without being promoted into the missing protected What-If assessment.

## Runtime and operations boundaries

```text
backend transaction success verified: false
live 20-attempt replay performed: false
full workload operationally verified: false
metric alerts observed: 0
action groups observed: 0
alert delivery verified: false
effective least privilege verified: false
Azure Backup / Recovery Services: intentionally out of scope for Lab v1
Recovery Services vaults observed: 0
other backup methods: not observed
recovery tested: false
```

Month-to-date ActualCost at the latest protected preflight:

```text
total: CAD 0.734335248846279
VM: CAD 0.648600227898012
public IP: CAD 0.0606791966666666
disk: CAD 0.0250558242816
```

Usage may lag and is not a final invoice or forecast.

```text
Total regional vCPUs: 1 / 10
Standard IPv4 public IPs: 1 / 20
Falsv7 family quota: not returned by the latest filtered query
```

## Resource-group cleanup boundary

```text
rg-servicetracer-dev-westus2 = core ServiceTracer platform
rg-st-demo-api-dev-westus2 = independent public demo API
relationship = peer operational boundaries, not nested layers
independent demo API protected from cleanup = true
dependency collection executed: false
candidate current presence: not freshly observed
candidate orphan status: not established
cleanup authorized: false
cleanup performed: false
```

## Preserved planner evidence

```text
authorization reconciliation merge: 92b0c3b1064158684a4b280348c77eeedba6dfc3
planner run: 30064289707
planner artifact: 8585693830
planner artifact SHA-256: 7aae2cff0df757a4b436c5b87507162624813e64bd32946bada8a87e5d7adc22
candidate: Standard_B2ats_v2 / eastus
restriction: NotAvailableForSubscription
VM family: standardBasv2Family
typed readiness control: PR #73
status: readiness rejected before ARM validation and What-If
current deployment view: false
```

## Current authority

```text
repository reconciliation authorized: true
pull request creation authorized: true
pull request merge authorized: false
workflow dispatch authorized: false
Azure authentication authorized: false
Azure mutation authorized: false
Azure RBAC mutation authorized: false
Resource Graph query authorized: false
guest commands authorized: false
transaction replay authorized: false
GitHub Pages publication authorized: false
cleanup authorized: false
```

## Next gate

Recover and inspect the exact existing PR #92 protected verifier run and artifact if possible. A new Azure verification attempt, deployment, RBAC change, replay, cleanup, publication, workflow rerun, or PR merge requires separate explicit authorization.
