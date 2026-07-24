# Current project handoff

## Interpretation boundary

This handoff records the latest durable repository and evidence synthesis reviewed on `2026-07-24`. It is not a continuously refreshed GitHub or Azure dashboard.

```text
historical_planner_evidence != current_deployment_state
declared_in_code != deployed_in_azure
deployment_succeeded != service_validated
public_API_healthy != backend_transaction_successful
resource_exists != securely_configured
not_observed != false
not_observed != absent
```

Resolve live GitHub, exact-head CI, current authority, Azure state, cost, RBAC, backup, and dependency health before every consequential operation.

## Repository watermark

```text
repository: anthonyedgar30000/azure-iac-msp-lab
main: 5dfa3b76a9fb975002d9cd702a892a0f678c88c5
latest merged pull request: 82
open pull requests observed before reconciliation: none
local working tree: not observed
```

PR #82 promoted authenticated post-deployment inventory from exact source head `a85970061879ef4a900564d18e9631630e95b11e`. Full CI run `30112308916` and dedicated evidence workflow run `30112309167` passed on that source head. GitHub reported no file-content difference between the tested source head and the final merge commit.

## Preserved planner evidence anchors

The following historical planner anchors remain required evidence and are preserved verbatim:

```text
authorization reconciliation merge: 92b0c3b1064158684a4b280348c77eeedba6dfc3
planner run: 30064289707
planner artifact: 8585693830
planner artifact SHA-256: 7aae2cff0df757a4b436c5b87507162624813e64bd32946bada8a87e5d7adc22
requested candidate: Standard_B2ats_v2 / eastus
restriction: NotAvailableForSubscription
VM family: standardBasv2Family
typed readiness control: PR #73
```

These markers prove preservation of the earlier candidate evidence. They do not describe the later West US 2 deployment.

## Resolved independent ServiceTracer demo API state

The consumed planner run `30064289707` remains valid historical evidence for `eastus` and `Standard_B2ats_v2`. It is not the current deployment view.

Authenticated Azure Cloud Shell evidence captured through `2026-07-24T16:40:36Z` established:

```text
subscription: Azure subscription 1
resource group: rg-st-demo-api-dev-westus2
location: westus2
resources observed: 7
deployment: servicetracer-demo-api-dev
deployment state: Succeeded
deployed source ref: 8b3d55c616d8820edd523f77021a35fe24167bd0
VM: vm-st-demo-api-mst-dev
VM size: Standard_F1als_v7
VM state: VM running
VM provisioning: Succeeded
FQDN: st-demo-api-vm-aeg30000.westus2.cloudapp.azure.com
```

The VM, OS disk, public IP, NIC, NSG, VNet, and Custom Script extension were observed.

Current `main` is 18 commits ahead of the deployed source and zero behind. The observed differences are repository governance, workflow, evidence, validation, test, documentation, and handoff paths.

```text
deployed_source_ref != current_main
workload_source_or_IaC_drift = not_observed
```

## Public runtime evidence

Protected workflow run `30086152352` observed:

```text
public endpoint reachable: true
TLS verified: true
GET /api/health: HTTP 200
health status: healthy
CORS verified: true
transaction protocol verified: true
attempts: 2
successful attempts: 0
failed attempts: 2
observed backend: VPN-02
backend statuses: 503, 503
failure boundary: radius_response
exact root cause claimed: false
```

Therefore:

```text
deployment verified = true
public API verified = true
backend transaction success verified = false
full workload operationally verified = false
```

## Security and operations

```text
VM identity: SystemAssigned
boot diagnostics: enabled
Internet TCP 80: allowed
Internet TCP 443: allowed
resource-group locks: 0
supported resources with diagnostic settings: 0 of 6 queried
metric alerts: 0
action groups: 0
alert delivery verified: false
effective RBAC: not observed
least privilege: not verified
backup: not observed
recovery tested: false
actual cost: not observed
```

The RBAC, backup, and cost gaps are failed or unavailable observations, not absence claims.

## Quota snapshot

At the authenticated capture:

```text
Standard Falsv7 family vCPUs: 1 / 10
Total regional vCPUs: 1 / 10
Standard IPv4 public IPs: 1 / 20
```

Quota is not availability, reservation, cost, or authorization.

## Shared-state resolution

The canonical current synthesis is:

```text
.project/current-reality.json
```

The older East US planner fields in `.project/active-work.json` and `.project/environment-state.json` remain preserved as historical candidate evidence. They must not be read as the current deployment truth.

The authenticated post-deployment event is appended to `.project/deployment-history.jsonl`.

## Current authority

```text
repository reconciliation authorized: true
pull request creation authorized: true
pull request merge authorized: false
workflow dispatch authorized: false
Azure authentication authorized: false
Azure mutation authorized: false
guest commands authorized: false
transaction replay authorized: false
cleanup authorized: false
```

## Next gate

The corrected read-only RBAC, backup, and month-to-date cost follow-up remains prepared but unexecuted. A separate exact authorization is required before Azure authentication or execution.
