# Current project handoff

## Interpretation boundary

This handoff records durable repository architecture and the newest authenticated Azure evidence reviewed on `2026-07-24`. It is not a live GitHub or Azure dashboard.

```text
durable_handoff != live_status
declared_in_code != deployed_in_Azure
not_observed != false
read_only_plan != deployment_authorization
resource_exists != service_healthy
```

Resolve the live default-branch head, open pull requests, branch ownership, exact-head CI, Azure subscription context, quotas, costs, target resources, and dependency state before every consequential decision.

## Repository synchronization watermark

At the start of this bounded evidence increment, live `main` was observed at:

```text
524be044dc94e59e42477964162f825d83710cb7
```

That commit merged PR #67, which normalized `.project/active-work.json` and `.project/environment-state.json` to the independent API architecture.

The active repository strategy was established and corrected through:

- PR #63: collector-hosted dedicated load-balancer repair after run `30050103888`;
- PR #64: collector-hosted public-IP reconciliation after read-only run `30053018998`;
- PR #65: independent ServiceTracer demo API subproject, source head `1be38682bf382bb70a585522d9e8c193beb89937`, exact-head CI run `30055579796`, merge `e3364b9cb918bf5aef23eab011d2a168183b3442`;
- PR #66: `Standard_B2ats_v2` correction, source head `540c19e394e4a13e86ad89327aeb17a3f4cb8f2a`, exact-head CI run `30058073866`, merge `9fd2af042d0ee1be28b61c8e9c26939ee98c319e`;
- PR #67: durable project-state normalization, source head `418cde5dee8ee226ac8272605af76ae6ab6d72de`, merge `524be044dc94e59e42477964162f825d83710cb7`.

No Azure planning, deployment, cleanup, or endpoint promotion was authorized by those merges.

## Concurrent planner ownership

Open PR #68 owns exactly:

- `.github/workflows/servicetracer-demo-api-subproject-plan.yml`;
- `workloads/servicetracer-demo-api/tests/test_plan_credential_boundary.py`.

Its objective is to remove planner-time SSH credential generation and replace it with public-only placeholder data. Its exact head `b4f225c71e9d93a27aa74f860e2882c8278cd7bf` passed CI run `30058896278`.

PR #68 is not merged. Other conversations remain review-only on those paths unless ownership is explicitly transferred.

```text
CI_success != merge_authorization
open_PR_ownership != permission_to_overwrite
planner_fix_present_on_branch != planner_fix_present_on_main
```

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
- the collector NIC, disks, extensions, identity, or guest OS;
- `vnet-onprem-sim-mst-dev` or any base subnet;
- `nsg-operations-mst-dev`;
- `lb-remote-access-mst-dev`;
- `pip-remote-access-mst-dev`.

The existing ServiceTracer transaction endpoint is a read-only dependency only.

## Independent Azure state

The target resource group, VM, VNet, subnet, NSG, NIC, public IP, DNS, TLS, Nginx, loopback API, dependency call, CORS, rate limiting, frontend integration, and operational behavior are:

```text
not_observed
```

The independent workload is repository-implemented and exact-source-head CI verified. It remains unplanned, undeployed, and operationally unverified in Azure.

```text
repository_implemented
!= read_only_plan_reviewed
!= deployment_authorized
!= deployed
!= service_verified
!= frontend_integration_verified
```

## Planner authority and readiness

The intended workflow is:

```text
ServiceTracer demo API subproject plan
.github/workflows/servicetracer-demo-api-subproject-plan.yml
```

On merged `main@524be044dc94e59e42477964162f825d83710cb7`, the planner remains main-bound, dispatch-SHA-bound, test-before-login, OIDC-based, read-only, manifest-bearing, and deployment-free. However, it still contains planner-time SSH key generation. PR #68 is the active bounded correction for that credential boundary.

Therefore the read-only dispatch package must not be presented as ready until:

1. PR #68 is independently reviewed and explicitly authorized for merge;
2. PR #68 is merged without scope expansion;
3. live `main` is re-resolved;
4. the exact merged planner is reverified;
5. a separate human explicitly authorizes one planner dispatch.

## Newest authenticated Azure evidence

The newest authenticated Azure evidence reviewed remains historical collector-hosted run `30053018998`:

- exact run head: `46821092a6d196cc08279d3d79b09ae613a09b2a`;
- artifact: `collector-demo-api-30053018998-1`;
- artifact ID: `8581736555`;
- artifact digest: `sha256:be58e1d9e9b3dda587209dfdf25a9b9f19aecf1a4ca4ffe08c9ac66e5c41d277`;
- generated at: `2026-07-23T23:24:05Z`;
- Azure OIDC, inventory, readiness, and ARM validation succeeded;
- What-If proposed `2 Create`, `1 Modify`, `24 Ignore`, and `2 NoChange`;
- the public-IP Modify was rejected fail closed;
- deployment and service verification were skipped;
- `azure_mutations_authorized=false`;
- `azure_mutations_performed=false`;
- `deployment_authorized=false`.

Time-bounded observations included:

- expected Azure for Students subscription and tenant;
- collector VM running privately at `10.20.40.10` with size `Standard_B2ats_v2`;
- legacy `pip-st-demo-api-mst-dev` at `20.59.28.146`;
- collector-hosted HTTP and HTTPS rules on `nsg-operations-mst-dev`;
- no dedicated collector-hosted load balancer or VM extension;
- no legacy demo child resources under `lb-remote-access-mst-dev`;
- Standard public-IP usage observed at `2/3`.

This evidence is not an independent workload plan and cannot authorize deployment.

## Historical collector-hosted path

The collector-hosted strategy is superseded and retained as evidence.

Required historical anchors remain:

- PR #56 introduced an isolated collector API root;
- PR #58 added the governed persistence controller;
- PR #59 repaired the parent/nested deployment-name collision;
- run `30044644501` accepted an isolated What-If and then failed deployment;
- run `30050103888` later failed on Azure Network provider contracts;
- run `30053018998` later rejected a public-IP Modify fail closed;
- failed deployment did not prove zero partial mutation;
- a fresh Azure inventory and isolated What-If were required before any retry.

PR #65 superseded that strategy before successful deployment or service verification. Issue #60 is superseded for the active independent architecture.

## Legacy residue boundary

Separate evidence-backed cleanup scopes include:

- `pip-st-demo-api-mst-dev`;
- collector-hosted demo HTTP and HTTPS NSG rules;
- `appi-demo-api-mst-dev`;
- `storfxczr3fewce`;
- synthetic backend VMs;
- any other partial resources found by future authorized inventory.

Do not delete, modify, reuse, or declare these resources healthy. Cleanup requires a separate inventory, dependency review, cost review, destructive What-If where applicable, rollback assessment, and explicit human authorization.

## Current authority

```text
repository_evidence_increment_authorized = true
pull_request_creation_authorized = true
pull_request_merge_authorized = false
workflow_dispatch_authorized = false
Azure_authentication_authorized = false
Azure_WhatIf_authorized = false
Azure_deployment_authorized = false
Azure_cleanup_authorized = false
guest_commands_authorized = false
credential_creation_authorized = false
endpoint_promotion_authorized = false
```

## Safest next gate

After this evidence-only PR passes exact-head CI and scope review, the genuine human gate is explicit merge authorization for:

1. PR #68, the planner credential-boundary correction; and
2. this non-overlapping durable evidence/handoff increment.

After both are merged, re-resolve the exact `main` SHA and present the separate read-only planner dispatch package. Planning success must stop at a separate deployment proposal and explicit deployment authorization.
