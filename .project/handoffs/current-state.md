# Current project handoff

## Interpretation boundary

This handoff records repository lifecycle state checked after PR #90 merged and preserves the latest durable Azure evidence reviewed on `2026-07-25`.

It is not a continuously refreshed GitHub or Azure dashboard.

```text
merged_into_main != deployed_to_VM
repository_RBAC_package != Azure_RBAC_observed
RBAC_apply_asserted != RBAC_apply_succeeded
role_assignment_observed != effective_permission_verified
cleanup_plan_merged != cleanup_query_executed
cleanup_candidate != orphaned_resource
resource_groups_are_peers != resource_groups_are_nested
out_of_scope != missing_control
historical_planner_evidence != current_deployment_state
not_observed != false
not_observed != absent
conflicting != false
```

Resolve live GitHub, exact-head CI, current authority, Azure state, cost, quota, RBAC, and dependency health before every consequential operation.

## Repository watermark

```text
repository: anthonyedgar30000/azure-iac-msp-lab
main: 8b25ecf1f00a59033955ef67bb3f9b511126f08a
latest merged pull request: 90
open pull requests observed before this reconciliation: none
local working tree: not observed
```

PR #89:

```text
source head: 3727b67533eb8043a22895a833223fa00fb70d10
merge commit: 39e214a32ebdac61d22d7b130d4c2f1e5d6f4f53
full CI: 30145973950 / failure
dedicated reconciliation: 30145973957 / success
PR 82 shared-state: 30145973961 / success
Azure MCP architecture: 30145973948 / success
failure boundary: workflow-observability handoff anchors
Azure action performed: false
```

PR #90:

```text
source head: 0e5ae4c68801695241eebef4f05967ec38a894ff
merge commit: 8b25ecf1f00a59033955ef67bb3f9b511126f08a
CI: 30146139826 / success
PR 86 and PR 88 reconciliation: 30146139825 / success
PR 82 shared-state: 30146139830 / success
Azure MCP architecture: 30146139832 / success
changed path: .project/handoffs/current-state.md
source-to-merge file-content difference observed: false
merge-result CI: not observed
Azure action performed: false
```

`not_observed` is not a CI failure.

## Preserved historical repository anchors

```text
PR #88 merge: 726c42ea1dddf402a42d8d0c591c660ebc50733f
PR #88 source head: 5e05d050cace2210c9b47103fe100eceb759cd0e
PR #88 exact-head CI: 30142555135, 30142555107, 30142555131 / success

PR #86 merge: 67d1aa9c784825e835097f684ddf629727ca5e22
PR #86 source head: 8df0a5af4b522ceeff16c0d9d1adfc978e66d559
PR #86 exact-head CI: 30141965628 / success

PR #84 merge: c96d9cbb765a023921fa819cf7d99c957e8ad608
PR #84 source head: 5c938a7e07da3a22b27bb5ac5aa52b7ccf22ba37
PR #84 exact-head CI: 30137351716 / success

PR #82 merge: 5dfa3b76a9fb975002d9cd702a892a0f678c88c5
PR #82 source head: a85970061879ef4a900564d18e9631630e95b11e
PR #82 CI: 30112308916
```

## Repository-to-runtime boundary

Current `main` is 146 commits ahead of deployed source `8b3d55c616d8820edd523f77021a35fe24167bd0` and zero behind.

```text
deployed_source_ref != current_main
workload_source_or_IaC_drift = observed
repository_timeout_fix_merged = true
deployed_timeout_fix_verified = false
repository_RBAC_package_merged = true
Azure_RBAC_effectiveness_verified = false
repository_cleanup_plan_merged = true
cleanup_dependency_collection_executed = false
repository_handoff_repair_merged = true
```

## Latest Azure evidence

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

No newer Azure inventory, Resource Graph query, deployment, runtime test, RBAC verification, or mutation was observed in PR #89, PR #90, or this repository-only reconciliation.

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

The later RBAC package does not retroactively prove that permission became effective and does not revive deployment authorization.

## RBAC reconciliation

The repository package defines:

```text
role: ServiceTracer Demo API Extension Updater v1
action: Microsoft.Compute/virtualMachines/extensions/write
assignable scope: rg-st-demo-api-dev-westus2
assignment scope: vm-st-demo-api-mst-dev/extensions/servicetracer-demo-api
```

Repository sources conflict:

```text
PR #86 narrative: operator --apply attempt asserted
bootstrap reconciliation: azure_rbac_bootstrap_executed = false
authorization record: authorized_not_consumed
verify-only execution record: bootstrap success assumed pending evidence
```

Canonical resolution:

```text
RBAC execution truth: conflicting
apply attempt asserted: true
apply success: assumed_not_evidenced
role definition observed: false
role assignment observed: false
effective extension write: unverified
protected verify-only outcome: not observed
deployment authorized: false
```

Missing durable evidence does not prove failure or absence.

## Resource-group cleanup boundary

```text
rg-servicetracer-dev-westus2 = core ServiceTracer platform
rg-st-demo-api-dev-westus2 = independent public demo API
relationship = peer operational boundaries, not nested layers
independent demo API protected from cleanup = true
```

Review candidates:

```text
appi-demo-api-mst-dev
storfxczr3fewce
pip-st-demo-api-mst-dev
lb-st-demo-api-mst-dev
nsg-operations-mst-dev/Allow-Demo-API-HTTP-From-Internet
nsg-operations-mst-dev/Allow-Demo-API-HTTPS-From-Internet
vm-stcollector-mst-dev/extensions/servicetracer-demo-api
```

```text
dependency collection executed: false
candidate current presence: not freshly observed
candidate orphan status: not established
cleanup authorized: false
cleanup performed: false
```

## Public runtime evidence

```text
transaction protocol verified: true
attempts: 2
successful attempts: 0
failed attempts: 2
observed backend: VPN-02
backend statuses: 503, 503
failure boundary: radius_response
exact root cause claimed: false
backend transaction success verified: false
live 20-attempt replay performed: false
full workload operationally verified: false
```

## Security, operations, backup, cost, and quota

```text
VM identity: SystemAssigned
boot diagnostics: enabled
Internet TCP 80: allowed
Internet TCP 443: allowed
resource-group locks: 0
diagnostic settings: 0 across 6 supported queried resources
metric alerts: 0
action groups: 0
alert delivery verified: false
inherited roles observed: Owner, Reader, ServiceTracer Demo API What-If Planner v1
effective required extension write: unverified
effective least privilege verified: false
Azure Backup / Recovery Services: intentionally out of scope for Lab v1
Recovery Services vaults observed: 0
other backup methods: not observed
recovery tested: false
```

Month-to-date ActualCost observed at the latest protected preflight:

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

## Preserved planner evidence

The earlier protected planner record remains historical evidence and does not describe the current West US 2 deployment:

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

This reconciliation is repository-only. Its exact branch and two-file initial objective are declared in the pull request; the existing validator must also be updated because it freezes the PR #88 watermark as current.

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

Choose one new, separately authorized, exact-commit read-only observation:

1. protected verify-only observation of effective extension-write permission; or
2. Resource Graph dependency collection for the seven cleanup candidates.

This reconciliation authorizes neither path.
