# Current project handoff

## Interpretation boundary

This handoff records the durable repository architecture and the newest authenticated Azure evidence reviewed on `2026-07-24`. It is not a live dashboard.

```text
durable_handoff != live_status
declared_in_code != deployed_in_Azure
not_observed != false
read_only_plan != deployment_authorization
resource_group_created != operationally_verified
```

Resolve the live default-branch head, open pull requests, exact-head CI, current Azure context, quota, cost, target resources and dependency state whenever this document is used for a consequential decision.

## Repository synchronization watermark

The active repository architecture is the independent ServiceTracer demo API subproject.

Promoted increments:

- PR #63 repaired the historical collector-hosted path after run `30050103888` failed on Azure Network provider contracts;
- PR #64 repaired the historical public-IP reconciliation after read-only run `30053018998` rejected a Modify fail closed;
- PR #65 created the independent workload, source head `1be38682bf382bb70a585522d9e8c193beb89937`, exact-head CI run `30055579796`, merge commit `e3364b9cb918bf5aef23eab011d2a168183b3442`;
- PR #66 corrected the independent VM-size contract to `Standard_B2ats_v2`, source head `540c19e394e4a13e86ad89327aeb17a3f4cb8f2a`, exact-head CI run `30058073866`, merge commit `9fd2af042d0ee1be28b61c8e9c26939ee98c319e`.

No Azure planning, deployment, cleanup or endpoint promotion was authorized by those repository merges.

## Active independent architecture

```text
GitHub Pages
→ dedicated Standard public IP and DNS
→ dedicated NSG allowing TCP 80/443 only
→ dedicated VNet and subnet
→ dedicated Linux VM
→ Nginx TLS, rate limiting and request-size controls
→ loopback-only Python API
→ existing ServiceTracer HTTPS transaction endpoint as a read-only dependency
```

Default target scope:

```text
resource group: rg-st-demo-api-dev-westus2
VM:             vm-st-demo-api-mst-dev
public IP:      pip-st-demo-api-vm-mst-dev
VNet:           vnet-st-demo-api-mst-dev
VM size:        Standard_B2ats_v2
```

The independent workload must not mutate or install on:

- `vm-stcollector-mst-dev`;
- the collector NIC, disks, extensions, identity or guest OS;
- `vnet-onprem-sim-mst-dev` or any base subnet;
- `nsg-operations-mst-dev`;
- `lb-remote-access-mst-dev`;
- `pip-remote-access-mst-dev`.

The existing ServiceTracer transaction endpoint is a read-only dependency only.

## Independent Azure state

The independent target resource group, VM, VNet, subnet, NSG, NIC, public IP, DNS, TLS, Nginx, loopback API, dependency call, CORS, rate limiting, frontend integration and operational behavior are:

```text
not_observed
```

The repository implementation is merged and exact-source-head CI verified. The independent Azure workload remains unplanned, undeployed and operationally unverified.

```text
repository_implemented
!= read_only_plan_reviewed
!= deployment_authorized
!= deployed
!= service_verified
!= frontend_integration_verified
```

## Read-only planner contract

Workflow:

```text
ServiceTracer demo API subproject plan
.github/workflows/servicetracer-demo-api-subproject-plan.yml
```

The planner:

- runs only from `refs/heads/main`;
- checks out `github.sha` and verifies `HEAD == GITHUB_SHA`;
- accepts no manually entered commit SHA;
- runs independent workload tests before Azure login;
- uses Azure OIDC only for bounded planning;
- captures Azure context, Compute and Network provider registration, VM SKU availability, compute usage, network/public-IP usage, dependency state, target-resource-group state, ARM validation and full What-If;
- permits active changes only inside `rg-st-demo-api-<environment>-<location>`;
- rejects dependency mutation, scope escape, unrelated resource types and every Modify, Delete or Replace;
- uploads manifest-bearing evidence;
- contains no deployment, cleanup, guest-command, RBAC or endpoint-promotion step;
- records `deployment_authorized=false`, `azure_mutations_authorized=false` and `azure_mutations_performed=false`.

The planner is implemented but has not been authorized or dispatched by this handoff.

## Newest authenticated Azure evidence

The newest authenticated Azure evidence reviewed remains historical collector-hosted run `30053018998`:

- exact run head `46821092a6d196cc08279d3d79b09ae613a09b2a`;
- artifact `collector-demo-api-30053018998-1`;
- artifact ID `8581736555`;
- digest `sha256:be58e1d9e9b3dda587209dfdf25a9b9f19aecf1a4ca4ffe08c9ac66e5c41d277`;
- generated at `2026-07-23T23:24:05Z`;
- Azure OIDC, inventory, readiness and ARM validation succeeded;
- What-If proposed `2 Create`, `1 Modify`, `24 Ignore` and `2 NoChange`;
- the public-IP Modify was rejected fail closed;
- `azure_mutations_authorized=false`;
- `azure_mutations_performed=false`;
- `deployment_authorized=false`.

Time-bounded observations included:

- the Azure for Students subscription and expected tenant;
- `vm-stcollector-mst-dev` running privately at `10.20.40.10` with size `Standard_B2ats_v2`;
- existing legacy `pip-st-demo-api-mst-dev` at `20.59.28.146`;
- existing collector-hosted HTTP and HTTPS rules on `nsg-operations-mst-dev`;
- no dedicated collector-hosted load balancer or VM extension;
- no legacy demo child resources under `lb-remote-access-mst-dev`;
- Standard public-IP usage observed at `2/3`.

This evidence is not an independent workload plan and cannot authorize deployment.

## Historical collector-hosted path

The collector-hosted strategy is superseded and retained only as evidence.

Historical anchors remain:

- PR #56 introduced an isolated collector API root;
- PR #58 added the governed persistence controller;
- PR #59 repaired the parent/nested deployment-name collision;
- run `30044644501` accepted an isolated What-If and then failed deployment;
- run `30050103888` later failed on Azure Network provider contracts;
- run `30053018998` later rejected a public-IP Modify fail closed;
- post-failure Azure mutation was not proven where a deployment was attempted;
- a fresh Azure inventory and isolated What-If were required before any retry.

PR #65 superseded that strategy before successful deployment or service verification. Issue #60 is therefore superseded for the active independent architecture.

## Legacy residue boundary

Separate cleanup scopes include:

- `pip-st-demo-api-mst-dev`;
- collector-hosted demo HTTP and HTTPS operations-NSG rules;
- `appi-demo-api-mst-dev`;
- `storfxczr3fewce`;
- synthetic backend VMs;
- any other evidence-backed partial resources.

Do not delete, modify, reuse or declare these resources healthy. Cleanup requires a separate inventory, dependency review, cost review, destructive What-If where applicable, rollback assessment and explicit human authorization.

## Authority state

```text
repository_reconciliation_authorized = true
pull_request_creation_authorized = true
pull_request_merge_authorized = false
workflow_dispatch_authorized = false
Azure_authentication_authorized = false
Azure_WhatIf_authorized = false
Azure_deployment_authorized = false
Azure_cleanup_authorized = false
guest_commands_authorized = false
endpoint_promotion_authorized = false
```

## Safest next gate

After this reconciliation and planner-evidence increment passes exact-head CI and is reviewed, the next action is a separate human decision on merging that repository PR.

After merge, re-resolve the exact `main` SHA and present one exact dispatch package for **ServiceTracer demo API subproject plan**. Planning success must stop at a separate deployment proposal and explicit deployment authorization.
