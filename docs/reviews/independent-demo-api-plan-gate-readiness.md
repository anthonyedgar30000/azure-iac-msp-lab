# Independent ServiceTracer Demo API — Planning Gate Readiness

## Review purpose

This record synchronizes the repository and promoted Azure evidence before requesting any read-only independent-workload planning authority.

It does not authorize workflow dispatch, Azure authentication, ARM validation, What-If, deployment, cleanup, guest commands, RBAC changes, endpoint promotion, or pull-request merge.

## Live repository observation

Observed on `2026-07-24` before this branch was created:

- repository: `anthonyedgar30000/azure-iac-msp-lab`;
- default branch: `main`;
- observed main commit: `9fd2af042d0ee1be28b61c8e9c26939ee98c319e`;
- latest completed increment: PR #66;
- PR #66 source head: `540c19e394e4a13e86ad89327aeb17a3f4cb8f2a`;
- PR #66 exact-head CI run: `30058073866`, successful;
- no open pull request owned the independent subproject or overlapping paths at branch creation.

```text
observed_main_commit != permanently_current_main
no_open_PR_observed != future_exclusive_ownership
```

Live GitHub must be queried again before merge, planner dispatch, or any later mutation proposal.

## Repository increments promoted by this reconciliation

### PR #63 — collector-hosted dedicated load-balancer repair

- source head: `3afdefa3d3d778ead811b10393663a5877c6ab35`;
- merge commit: `46821092a6d196cc08279d3d79b09ae613a09b2a`;
- related failed deployment run: `30050103888`;
- artifact ID: `8580705301`;
- artifact digest: `sha256:178af7ce60202663ac1d60db31a901dcdcb1641a8dbffc656e8068f91fa2b760`;
- classification: repository repair only, collector-hosted strategy later superseded.

### PR #64 — collector-hosted public-IP reconciliation

- source head: `0813b1f75fd66c202db8d609bd6acad9d4dbfbb5`;
- merge commit: `b5055cdfea90ea166b0c25f871a88c1cb2b64bc1`;
- related read-only run: `30053018998`;
- artifact ID: `8581736555`;
- artifact digest: `sha256:be58e1d9e9b3dda587209dfdf25a9b9f19aecf1a4ca4ffe08c9ac66e5c41d277`;
- classification: fail-closed repository reconciliation only, collector-hosted strategy later superseded.

### PR #65 — independent ServiceTracer demo API subproject

- source head: `1be38682bf382bb70a585522d9e8c193beb89937`;
- exact-head CI run: `30055579796`, successful;
- merge commit: `e3364b9cb918bf5aef23eab011d2a168183b3442`;
- classification: independent repository workload implemented, not planned or deployed in Azure.

### PR #66 — independent VM-size and handoff correction

- source head: `540c19e394e4a13e86ad89327aeb17a3f4cb8f2a`;
- exact-head CI run: `30058073866`, successful;
- merge commit: `9fd2af042d0ee1be28b61c8e9c26939ee98c319e`;
- approved repository default: `Standard_B2ats_v2`;
- classification: repository correction only, no Azure operation.

## Active architecture

```text
GitHub Pages
→ dedicated Standard public IP and DNS
→ dedicated NSG
→ dedicated VNet and subnet
→ dedicated Linux VM
→ Nginx TLS, rate limiting and request-size controls
→ loopback-only Python API
→ existing ServiceTracer HTTPS transaction endpoint as read-only dependency
```

Default independent scope:

- target resource group: `rg-st-demo-api-dev-westus2`;
- VM: `vm-st-demo-api-mst-dev`;
- public IP: `pip-st-demo-api-vm-mst-dev`;
- VNet: `vnet-st-demo-api-mst-dev`;
- candidate VM size: `Standard_B2ats_v2`.

The independent workload may not mutate or install on the collector VM, collector NIC or disks, base ServiceTracer VNet or subnets, operations NSG, remote-access load balancer, remote-access public IP, or collector guest operating system.

## Newest authenticated Azure evidence

The newest authenticated evidence reviewed remains collector-hosted read-only run `30053018998`:

- exact run head: `46821092a6d196cc08279d3d79b09ae613a09b2a`;
- artifact: `collector-demo-api-30053018998-1`;
- artifact ID: `8581736555`;
- artifact digest: `sha256:be58e1d9e9b3dda587209dfdf25a9b9f19aecf1a4ca4ffe08c9ac66e5c41d277`;
- generated: `2026-07-23T23:24:05Z`;
- Azure OIDC, inventory, readiness and ARM validation succeeded;
- What-If proposed `2 Create`, `1 Modify`, `24 Ignore`, `2 NoChange`;
- the public-IP Modify was rejected fail closed;
- deployment and service verification were skipped;
- `azure_mutations_authorized=false`;
- `azure_mutations_performed=false`;
- `deployment_authorized=false`.

Observed legacy residue included `pip-st-demo-api-mst-dev` and two collector-hosted demo rules on `nsg-operations-mst-dev`. This evidence is not the independent-workload plan and cannot be used as deployment authority.

## Independent workload state

```text
repository_implemented = true
exact_source_head_CI_verified = true
merged = true
independent_Azure_plan_observed = false
target_resource_group_state = not_observed
deployed = false
service_verified = false
frontend_integration_verified = false
operationally_verified = false
```

`not_observed` must not be collapsed into absent, failed, healthy, or deployed.

## Planner verification checklist

The repository planner is required to:

- run only from `refs/heads/main`;
- check out `github.sha`;
- verify `git rev-parse HEAD == GITHUB_SHA`;
- accept no manually entered commit SHA;
- run independent subproject tests before Azure login;
- authenticate through Azure OIDC only for bounded planning;
- record subscription and tenant evidence without exposing secrets;
- verify Compute and Network provider registration;
- capture compute usage and network/public-IP usage;
- reject a VM SKU with active restrictions;
- capture dependency resource-group and public-endpoint state;
- capture target-resource-group existence and all existing target resources;
- perform subscription ARM validation and full What-If;
- reject dependency-resource mutation;
- reject active changes outside the independent target resource group;
- reject unrelated resource types;
- reject every unexpected `Modify`, `Delete`, or `Replace`;
- produce checksum and JSON evidence manifests;
- record exact run, attempt, dispatch SHA, ref, artifact name and generated time;
- record explicit cost limitations rather than infer an Azure price;
- record `deployment_authorized=false`;
- record `azure_mutations_authorized=false`;
- record `azure_mutations_performed=false`;
- contain no deployment step.

## Exact future dispatch package template

This package is informational until the repository increment is reviewed and merged, live `main` is re-resolved, and Anthony explicitly authorizes the planner dispatch.

```text
workflow: ServiceTracer demo API subproject plan
ref: main
exact main SHA: <resolve after merge>
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

Authorized Azure operations in that future planner would be bounded read-only inventory, provider/SKU/quota checks, ARM validation, and ARM What-If. Azure resource mutation and deployment would remain false.

## Legacy cleanup boundary

The following remain separate evidence-backed cleanup scopes:

- `pip-st-demo-api-mst-dev`;
- two collector-hosted demo NSG rules;
- `appi-demo-api-mst-dev`;
- `storfxczr3fewce`;
- synthetic backend VMs;
- any other partial resources found by a future authorized inventory.

No deletion, modification, reuse or health claim is authorized by this review.

## Current authority

```text
repository_changes_on_owned_branch = authorized
pull_request_creation = authorized
pull_request_merge = not_authorized
workflow_dispatch = not_authorized
Azure_authentication = not_authorized
Azure_WhatIf = not_authorized
Azure_deployment = not_authorized
Azure_cleanup = not_authorized
guest_commands = not_authorized
endpoint_promotion = not_authorized
```

## Next genuine human gate

After exact-head CI and final scope review, stop for explicit authorization to merge the repository reconciliation and planner-evidence PR.

Only after that merge may the live `main` SHA be resolved and the exact read-only planner dispatch package be presented for a separate human authorization.
