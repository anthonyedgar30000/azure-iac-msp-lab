# Current project handoff

## Interpretation boundary

This handoff records durable repository and evidence claims reviewed on `2026-07-24`. It is not a live GitHub or Azure dashboard.

```text
readiness_rejected != workflow_mechanism_failed
planner_dispatched != ARM_WhatIf_completed
Azure_authentication_succeeded != deployment_authorized
not_observed != false
resource_exists != service_healthy
```

Resolve live GitHub, exact-head CI, current authorization, costs, target resources, and dependency state before every consequential operation.

## Repository synchronization watermark

The newest observed default-branch commit before this evidence-promotion branch was created was:

```text
92b0c3b1064158684a4b280348c77eeedba6dfc3
```

It merged PR #72 after PR #73 had merged. No open pull request was observed when ownership was established.

## Current repository architecture

The independent application architecture remains:

```text
GitHub Pages
→ dedicated Standard public IP and DNS
→ dedicated NSG
→ dedicated VNet and subnet
→ dedicated Linux VM
→ Nginx TLS, rate limiting, and request-size controls
→ loopback-only Python API
→ existing ServiceTracer HTTPS transaction endpoint as a read-only dependency
```

Repository anchors:

- PR #65 application source head `1be38682bf382bb70a585522d9e8c193beb89937`, CI `30055579796`, merge `e3364b9cb918bf5aef23eab011d2a168183b3442`;
- PR #71 dual-subscription source head `5b54fc63542836f42a530c5f644b97ccdd1020a7`, CI `30061331939`;
- expanded planner merge `84a527a248964c907172b9af5ca3d5fab991c96d`;
- PR #73 typed-readiness source head `0b0c0eb650ca0da3bb0f8e0143fcc8a0e3c50f7d`, CI `30067704269`, merge `b395f32a08965a7a9602ccdbd25e79a765b42a7b`.

The planner uses `azure-api-payg`, separate dependency and target OIDC identities, and `ProviderNoRbac`. It contains no deployment command and creates no credential.

## Human authorization resolution

Anthony Edgar explicitly authorized one exact read-only planner run with:

```text
MAIN: 323b3892c6efd598231037f23281d49608ceb570
environment: dev
location: eastus
prefix: mst
dependency resource group: rg-servicetracer-dev-westus2
target resource group: rg-st-demo-api-dev-eastus
DNS label: st-demo-api-vm-aeg30000
allowed origin: https://anthonyedgar30000.github.io
VM size: Standard_B2ats_v2
maximum monthly cost ceiling: CAD 25.00
confirmation: PLAN-DEMO-API-SUBPROJECT:dev:st-demo-api-vm-aeg30000
Azure mutations: false
deployment: false
```

That authorization ratified the dual-subscription architecture and administrative prerequisites for this one run. It is consumed and does not authorize another dispatch.

## Planner run evidence

Workflow run:

```text
run ID: 30064289707
attempt: 1
dispatch SHA: 323b3892c6efd598231037f23281d49608ceb570
artifact ID: 8585693830
artifact name: servicetracer-demo-api-subproject-plan-30064289707-1
artifact digest: sha256:7aae2cff0df757a4b436c5b87507162624813e64bd32946bada8a87e5d7adc22
generated at: 2026-07-24T03:29:44Z
```

Observed successful stages:

- immutable `main` checkout and SHA verification;
- repository tests before Azure login;
- dependency-subscription OIDC login;
- existing ServiceTracer dependency resource group and public endpoint read;
- target-subscription OIDC login;
- target subscription observed Enabled and tenant-aligned;
- `Microsoft.Compute` observed Registered;
- `Microsoft.Network` observed Registered;
- inherited policy, compute quota, network quota, and requested-SKU evidence captured;
- manifest-bearing artifact uploaded.

No secret, token, tenant ID, subscription ID, or credential is persisted in this handoff.

## Exact readiness rejection

For `Standard_B2ats_v2` in `eastus`, Azure returned:

```text
matching SKU records: 1
unrestricted SKU records: 0
restriction reason: NotAvailableForSubscription
VM family: standardBasv2Family
family vCPU quota: 0 of 0
total regional vCPU quota: 0 of 10
Standard IPv4 public-IP quota: 0 of 20
```

The GitHub job conclusion was `failure` because the workflow intentionally exited nonzero at the readiness assertion.

The correct interpretation is:

```text
workflow_mechanism_failed = false
Azure_authentication_failed = false
dependency_access_failed = false
requested_candidate_ready = false
ARM_validation_performed = false
What_If_performed = false
Azure_mutations_performed = false
deployment_authorized = false
```

The old workflow exited before querying `rg-st-demo-api-dev-eastus`. Therefore its existence is:

```text
not_observed
```

It must not be recorded as absent. PR #73 now distinguishes explicit `ResourceGroupNotFound` from authorization, throttling, transient, or other observation failures.

## Cost and quota boundary

The artifact proves time-bounded quota and restriction facts only. It does not prove:

- alternate VM-size availability;
- another region’s availability;
- retail or invoice cost;
- reserved quota;
- target-resource-group absence;
- an accepted ARM What-If;
- deployment readiness.

`standardBSFamily` had quota 0 of 10, but that does not establish that any particular BS-family size is available or under the CAD 25 ceiling.

## Independent workload state

```text
repository_implemented = true
architecture_ratified_for_consumed_run = true
planner_dispatched = true
readiness_accepted = false
target_resource_group_observed = false
ARM_validation_performed = false
What_If_performed = false
deployment_authorized = false
deployed = false
service_verified = false
frontend_integration_verified = false
operationally_verified = false
```

## Legacy residue boundary

Separate cleanup scopes remain:

- `pip-st-demo-api-mst-dev`;
- collector-hosted HTTP and HTTPS operations-NSG rules;
- `appi-demo-api-mst-dev`;
- `storfxczr3fewce`;
- synthetic backend VMs;
- any later evidence-backed residue.

Do not delete, modify, reuse, or declare them healthy.

## Current authority

```text
repository_reconciliation_authorized = true
pull_request_creation_authorized = true
pull_request_merge_authorized = false
workflow_dispatch_authorized = false
Azure_authentication_authorized = false
Azure_WhatIf_authorized = false
Azure_mutations_authorized = false
Azure_deployment_authorized = false
Azure_cleanup_authorized = false
guest_commands_authorized = false
endpoint_promotion_authorized = false
```

## Safest next gate

Choose one evidence-informed candidate VM size and region, then prepare a fresh exact-SHA read-only planner authorization package.

Current evidence narrows the decision:

- do not reuse `Standard_B2ats_v2` in `eastus` without quota or availability change evidence;
- `standardBasv2Family` is blocked at 0 of 0;
- total regional vCPU and Standard public-IP quota have headroom;
- `standardBSFamily` quota is 0 of 10;
- candidate-specific availability and cost remain unobserved.

A new size, region, commit, rerun, Azure login, ARM validation, or What-If requires new explicit authorization. Planning success still would not authorize deployment.
