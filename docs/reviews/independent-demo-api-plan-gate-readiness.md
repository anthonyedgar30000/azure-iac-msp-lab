# Independent ServiceTracer Demo API — Planning Gate Readiness

## Purpose

Promote the newest collector-hosted Azure evidence into durable history, reconcile the active independent architecture, and identify the exact repository gates that must close before a read-only planner dispatch can be requested.

This record does not authorize workflow dispatch, Azure authentication, ARM validation, What-If, deployment, cleanup, guest commands, credential creation, RBAC changes, endpoint promotion, or pull-request merge.

## Live synchronization

Observed during this increment:

- initial observed `main`: `9fd2af042d0ee1be28b61c8e9c26939ee98c319e`;
- concurrent PR #67 merged while the first branch was being prepared;
- current branch base after resynchronization: `524be044dc94e59e42477964162f825d83710cb7`;
- PR #67 normalized `.project/active-work.json` and `.project/environment-state.json`;
- the overlapping first draft PR #69 was closed without merge rather than overwrite PR #67;
- open PR #68 owns the planner workflow and its credential-boundary test;
- no other open PR owns the three paths in this evidence increment.

```text
concurrent_merge_observed != permission_to_overwrite
closed_superseded_PR != failed_objective
open_PR_ownership != permission_to_edit_owned_paths
```

## Repository increments

### PR #63

- title: Use dedicated load balancer for collector demo API;
- source head: `3afdefa3d3d778ead811b10393663a5877c6ab35`;
- merge commit: `46821092a6d196cc08279d3d79b09ae613a09b2a`;
- related deployment run: `30050103888`;
- artifact ID: `8580705301`;
- digest: `sha256:178af7ce60202663ac1d60db31a901dcdcb1641a8dbffc656e8068f91fa2b760`;
- state: repository repair only, historical collector-hosted strategy.

### PR #64

- title: Reconcile partial demo public IP safely;
- source head: `0813b1f75fd66c202db8d609bd6acad9d4dbfbb5`;
- merge commit: `b5055cdfea90ea166b0c25f871a88c1cb2b64bc1`;
- related read-only run: `30053018998`;
- artifact ID: `8581736555`;
- digest: `sha256:be58e1d9e9b3dda587209dfdf25a9b9f19aecf1a4ca4ffe08c9ac66e5c41d277`;
- state: fail-closed reconciliation only, historical collector-hosted strategy.

### PR #65

- title: Create independent ServiceTracer demo API subproject;
- source head: `1be38682bf382bb70a585522d9e8c193beb89937`;
- exact-head CI run: `30055579796`, successful;
- merge commit: `e3364b9cb918bf5aef23eab011d2a168183b3442`;
- state: independent repository workload implemented, Azure state not observed.

### PR #66

- title: Correct independent API VM size and synchronize project handoff;
- source head: `540c19e394e4a13e86ad89327aeb17a3f4cb8f2a`;
- exact-head CI run: `30058073866`, successful;
- merge commit: `9fd2af042d0ee1be28b61c8e9c26939ee98c319e`;
- state: `Standard_B2ats_v2` contract corrected, no Azure operation.

### PR #67

- title: Normalize project state to independent demo API architecture;
- source head: `418cde5dee8ee226ac8272605af76ae6ab6d72de`;
- merge commit: `524be044dc94e59e42477964162f825d83710cb7`;
- state: active-work and environment-state normalized, no Azure operation.

### PR #68

- title: Remove credential creation from independent API planner;
- exact head: `b4f225c71e9d93a27aa74f860e2882c8278cd7bf`;
- exact-head CI run: `30058896278`, successful;
- state: open and unmerged;
- owner scope: planner workflow and `test_plan_credential_boundary.py` only.

PR #68 removes planner-time private-key generation and records `credential_creation_authorized=false`. Until it merges, the planner on `main` still creates an ephemeral SSH key pair to satisfy ARM validation and is not ready for the requested authorization package.

## Active independent architecture

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

Default scope:

- resource group: `rg-st-demo-api-dev-westus2`;
- VM: `vm-st-demo-api-mst-dev`;
- public IP: `pip-st-demo-api-vm-mst-dev`;
- VNet: `vnet-st-demo-api-mst-dev`;
- VM size: `Standard_B2ats_v2`.

The workload must not mutate or install on the collector, collector NIC or disks, base VNet/subnets, operations NSG, existing remote-access load balancer/public IP, or collector guest OS.

## Independent Azure state

```text
repository_implemented = true
exact_source_head_CI_verified = true
merged = true
read_only_independent_plan_observed = false
target_resource_group_state = not_observed
deployed = false
service_verified = false
frontend_integration_verified = false
operationally_verified = false
```

`not_observed` is not absence, failure, health, or deployment.

## Newest authenticated Azure evidence

Newest reviewed evidence remains historical collector-hosted run `30053018998`:

- head SHA: `46821092a6d196cc08279d3d79b09ae613a09b2a`;
- artifact: `collector-demo-api-30053018998-1`;
- artifact ID: `8581736555`;
- digest: `sha256:be58e1d9e9b3dda587209dfdf25a9b9f19aecf1a4ca4ffe08c9ac66e5c41d277`;
- generated: `2026-07-23T23:24:05Z`;
- Azure OIDC, inventory, readiness, and ARM validation succeeded;
- What-If: `2 Create`, `1 Modify`, `24 Ignore`, `2 NoChange`;
- the public-IP Modify was rejected fail closed;
- deployment and service verification were skipped;
- Azure mutations authorized: false;
- Azure mutations performed: false;
- deployment authorized: false.

Time-bounded observations included the collector running privately, legacy `pip-st-demo-api-mst-dev`, two collector-hosted NSG rules, no dedicated collector-hosted load balancer or extension, and Standard public-IP usage at `2/3`.

This evidence is not an independent workload plan.

## Legacy residue

Separate cleanup scopes remain:

- `pip-st-demo-api-mst-dev`;
- collector-hosted demo HTTP/HTTPS NSG rules;
- `appi-demo-api-mst-dev`;
- `storfxczr3fewce`;
- synthetic backend VMs;
- any other partial resources discovered later.

No cleanup, modification, reuse, or health declaration is authorized.

## Issue #60

Issue #60 requests a historical collector-hosted What-If. PR #65 replaced that architecture with the independent workload. The issue is therefore superseded for the active path and should close as `not_planned`, with its discussion retained as historical evidence.

## Future dispatch package template

This is not yet an authorization request. It becomes eligible only after PR #68 and this evidence PR merge, live `main` is re-resolved, and the merged planner is reverified.

```text
workflow: ServiceTracer demo API subproject plan
ref: main
exact main SHA: <resolve after both merges>
environment: dev
location: westus2
prefix: mst
dependency resource group: rg-servicetracer-dev-westus2
target resource group: rg-st-demo-api-dev-westus2
dns label: st-demo-api-vm-aeg30000
allowed origin: https://anthonyedgar30000.github.io
VM size: Standard_B2ats_v2
maximum monthly cost ceiling: CAD 25.00
confirmation: PLAN-DEMO-API-SUBPROJECT:dev:st-demo-api-vm-aeg30000
```

Future authorized planner operations would be bounded Azure OIDC login, subscription/tenant evidence, provider registration, quota and SKU reads, dependency and target inventory, ARM validation, full What-If, and evidence upload. Azure mutation and deployment would remain false.

## Current authority

```text
repository_evidence_increment = authorized
pull_request_creation = authorized
pull_request_merge = not_authorized
workflow_dispatch = not_authorized
Azure_authentication = not_authorized
Azure_WhatIf = not_authorized
Azure_deployment = not_authorized
Azure_cleanup = not_authorized
guest_commands = not_authorized
credential_creation = not_authorized
endpoint_promotion = not_authorized
```

## Genuine human gate

After exact-head CI and final scope review, explicit human merge authorization is required for:

1. PR #68, the planner credential-boundary correction; and
2. this three-path durable evidence increment.

Only after both merges may the exact read-only planner dispatch package be presented for a separate authorization.
