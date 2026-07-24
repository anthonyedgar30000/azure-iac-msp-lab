# Implementation status

## State model

This document is a durable implementation summary, not a live GitHub or Azure dashboard.

```text
implemented != CI_verified != deployed != operationally_verified
deployment_failed != no_Azure_mutation
not_observed != false
resource_exists != service_healthy
```

Live repository, CI, Azure, cost, quota, and local working-tree state must be queried before consequential decisions.

## Repository implementation

Implemented and exact-source-head CI verified:

- repository-native workflow observability and six canonical ServiceTracer workstreams;
- segmented Azure network, Standard Load Balancer, Log Analytics, collector VM, evidence disk, identity, and lifecycle IaC;
- deterministic ServiceTracer collection, evidence, transaction, localization, containment, handoff, report, and operator-console capabilities;
- bounded publication planning and execution workflows;
- synthetic VPN backend infrastructure and transaction contracts;
- collector replacement and recovery designs;
- governed persistence controls;
- retired legacy Microsoft.Web demo path;
- historical collector-hosted demo API path and its fail-closed evidence;
- independent ServiceTracer demo API subproject under `workloads/servicetracer-demo-api`.

PR #65 changed the active demo API architecture from collector-hosted deployment to an independent workload boundary. Its exact source head `1be38682bf382bb70a585522d9e8c193beb89937` passed CI run `30055579796` and merged as `e3364b9cb918bf5aef23eab011d2a168183b3442`.

A distinct post-merge CI observation was not found. That does not negate the exact-head CI evidence.

## Independent demo API architecture

```text
GitHub Pages
→ dedicated public IP and DNS
→ dedicated NSG with TCP 80/443 only
→ dedicated VNet, subnet, NIC, and Linux VM
→ Nginx TLS and rate limiting
→ loopback-only Python API
→ fixed HTTPS dependency on existing ServiceTracer transaction endpoint
```

Default resource group:

```text
rg-st-demo-api-dev-westus2
```

The workload does not own or mutate the collector VM, operations NSG, base VNet, remote-access load balancer, collector disks, collector identity, or collector extensions.

## VM sizing

The approved default for the independent API host is:

```text
Standard_B2ats_v2
```

`Standard_B1s` belongs to the older synthetic-backend planning context and is not the approved independent API default.

The planner must still refresh:

- SKU availability in West US 2;
- relevant compute-family quota;
- Standard public-IP quota;
- exact cost context;
- remaining Azure for Students credit.

## Planning workflow

The repository contains one read-only independent-workload planner:

```text
.github/workflows/servicetracer-demo-api-subproject-plan.yml
```

It is bound to `main` and immutable `github.sha`, accepts no manually entered commit SHA, authenticates through GitHub OIDC, gathers scoped Azure evidence, runs subscription validation and What-If, uploads a manifest-bound artifact, and stops.

```text
planning_workflow_present = true
planning_workflow_dispatched = not_observed
Azure_mutation_authorized = false
deployment_workflow_present = false
```

## Azure resources observed

### Existing ServiceTracer environment

Time-bounded authenticated evidence has observed:

- `rg-servicetracer-dev-westus2` in `westus2`;
- `vm-stcollector-mst-dev` running at private IP `10.20.40.10`;
- collector size `Standard_B2ats_v2`;
- no collector public IP;
- synthetic backend VMs at the control-plane boundary;
- partial Microsoft.Web residue;
- partial collector-hosted API residue after failed deployment attempts.

Current guest health, ServiceTracer version, evidence readability, backend listeners, transaction behavior, TLS, CORS, browser integration, effective RBAC, policy, actual cost, and remaining credit are not established.

### Independent workload

These independent resources are declared in code but not yet observed in Azure:

- `rg-st-demo-api-dev-westus2`;
- `vnet-st-demo-api-mst-dev`;
- `nsg-st-demo-api-mst-dev`;
- `pip-st-demo-api-vm-mst-dev`;
- `nic-st-demo-api-mst-dev`;
- `vm-st-demo-api-mst-dev`;
- the VM extension and public service endpoint.

```text
declared_in_code != deployed_in_Azure
not_observed != absent
```

## Quota and cost boundary

The newest inspected authenticated evidence observed Standard public-IP usage at 2 of 3 in West US 2. The independent workload requires one additional Standard public IP, which would consume the last slot if that observation remains current.

That evidence is time-bounded. Quota must be refreshed before deployment, and deployment requires explicit acceptance of zero remaining headroom or a separate quota/cleanup strategy.

The workflow's CAD ceiling is a human planning boundary, not a computed price. Current invoice cost and remaining student credit remain unobserved.

## Historical collector-hosted path

The collector-hosted API path remains useful operational evidence:

- broad What-If detected unsafe base-infrastructure modifications;
- isolated What-If later passed;
- deployment failed on a parent/nested deployment-name collision;
- later attempts exposed partial public-IP and NSG state;
- fail-closed controls prevented unreviewed mutation;
- the lifecycle coupling motivated the independent subproject.

This history does not authorize retry or cleanup.

## Current readiness verdict

```text
independent_subproject_implemented = true
exact_source_head_CI_passed = true
vm_size_contract_corrected = pending_PR_merge
independent_Azure_plan_current = false
independent_Azure_deployed = not_observed
independent_service_verified = false
Azure_deployment_authorized = false
legacy_cleanup_authorized = false
```

The next safe gate is one fresh read-only independent-workload planner run from `main` after the VM-size correction is merged and the live repository head is re-resolved.
