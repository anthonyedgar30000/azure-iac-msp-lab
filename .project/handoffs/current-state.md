# Current project handoff

## Interpretation boundary

This handoff records the latest durable repository and evidence synthesis reviewed on `2026-07-25`. It is not a continuously refreshed GitHub or Azure dashboard.

```text
merged_into_main != deployed_to_VM
deployment_authorized != deployment_possible_with_current_identity
ARM_authorization_failure != Azure_resource_mutation
public_API_healthy != corrected_runtime_deployed
role_assignment_exists != effective_required_action_granted
historical_planner_evidence != current_deployment_state
not_observed != absent
```

Resolve live GitHub, exact-head CI, current authority, Azure state, cost, quota, RBAC, backup, and dependency health before every consequential operation.

## Repository watermark

```text
repository: anthonyedgar30000/azure-iac-msp-lab
main: c96d9cbb765a023921fa819cf7d99c957e8ad608
latest merged pull request: 84
PR #84 source head: 5c938a7e07da3a22b27bb5ac5aa52b7ccf22ba37
PR #84 exact-head CI: 30137351716 / success
open pull requests observed before reconciliation: none
local working tree: not observed
```

GitHub reported no file-content differences between the tested PR #84 source head and merge commit `c96d9cbb765a023921fa819cf7d99c957e8ad608`. The merge commit itself has no separate status checks.

PR #82 remains a preserved historical shared-state anchor:

```text
PR #82 merge: 5dfa3b76a9fb975002d9cd702a892a0f678c88c5
PR #82 source head: a85970061879ef4a900564d18e9631630e95b11e
PR #82 CI: 30112308916
```

## Repository-to-runtime boundary

Current `main` is 83 commits ahead of deployed source `8b3d55c616d8820edd523f77021a35fe24167bd0` and zero behind. Unlike the earlier governance-only drift, current main now contains runtime, installer, frontend, and deployment-control changes.

```text
deployed_source_ref != current_main
workload_source_or_IaC_drift = observed
repository_timeout_fix_merged = true
deployed_timeout_fix_verified = false
```

## Fresh Azure state

The newest protected preflight evidence was observed through `2026-07-25T00:47:40Z`:

```text
subscription: Azure subscription 1
resource group: rg-st-demo-api-dev-westus2
location: westus2
resources observed: 7
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

No Azure resource mutation occurred during either timeout-fix deployment attempt.

## Deployment authorization outcome

Anthony authorized one exact extension-only deployment with post-deployment health verification and rollback on failed verification.

Attempt 1 stopped during preflight because the VM power state was nested under `instanceView.statuses`. The observer was corrected and exact-head CI passed.

Attempt 2 stopped during ARM authorization evaluation because the protected deployment identity lacked:

```text
Microsoft.Compute/virtualMachines/extensions/write
```

Therefore:

```text
deployment grant status: consumed_blocked
What-If result observed: false
deployment step executed: false
Azure resource mutation performed: false
rollback performed: false
```

No RBAC broadening was authorized or performed.

## Public runtime evidence

The API remains healthy, but the corrected runtime is not active. The latest transaction evidence remains the earlier two-attempt sample:

```text
transaction protocol verified: true
attempts: 2
successful attempts: 0
failed attempts: 2
observed backend: VPN-02
backend statuses: 503, 503
failure boundary: radius_response
exact root cause claimed: false
live 20-attempt replay performed: false
full workload operationally verified: false
```

## Frontend state

```text
frontend integration merged into main: true
default data mode: fixture
live API activation: explicit query parameter only
GitHub Pages publication after merge verified: false
corrected live browser rendering verified: false
```

## Security and operations

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
effective required extension write: false
effective least privilege verified: false
Recovery Services vaults observed: 0
other backup methods: not observed
recovery tested: false
```

Zero Recovery Services vaults does not prove every possible backup method is absent.

## Cost and quota

Month-to-date ActualCost observed at the latest preflight:

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

Quota is not availability, reservation, cost, or authorization.

## Preserved planner evidence

The earlier protected planner run remains valid historical evidence only:

```text
planner run: 30064289707
candidate: Standard_B2ats_v2 / eastus
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
guest commands authorized: false
transaction replay authorized: false
GitHub Pages publication authorized: false
cleanup authorized: false
```

## Next gate

Choose one separately authorized path:

1. use an already-authorized human Azure identity for the same extension-only deployment while preserving What-If, health verification, evidence, and rollback; or
2. design and separately authorize a dedicated least-privilege identity for validation, What-If, and write access only to the existing VM extension scope.

This reconciliation does not authorize either path.
