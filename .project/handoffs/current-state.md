# Current project handoff

## How to interpret this document

This handoff preserves the accepted architecture, promoted evidence, unresolved gates, and safe next decision boundary. It is not a live GitHub dashboard.

Always query GitHub for:

- current `main` head;
- current branches and open pull requests;
- active write ownership;
- review and merge state;
- CI for the exact commit under evaluation.

```text
promoted_repository_event != current_repository_head
durable_handoff != live_status
```

## Durable repository baseline

The latest substantive implementation promoted into project memory is PR #46, **Deploy demo backends and connect frontend API**:

- source head: `e8358d090c79f1ba8752323e054693a779e7db51`;
- merge commit: `dcc4f75fc051484ba2f6ef633dc92ef80adae224`;
- exact-head CI run: `29990625589`, success.

The latest coordination event promoted into project memory is PR #47, **Reconcile PR46 merge project state**:

- source head: `b1857301f23e26e05d004c1baf0ead62a4011d21`;
- merge commit: `bdee00b203a5628dc5f309a086935075c2098c62`;
- merged at: `2026-07-23T14:21:18Z`;
- exact-head CI run: `30013155576`, success.

These are durable historical facts. They do not claim that either merge commit remains the current GitHub head.

## Repository capability now established

The repository contains the interactive ServiceTracer demo path:

```text
GitHub Pages frontend
→ Azure Function demo API
→ existing public Load Balancer TCP 443
→ VPN-01 healthy listener / VPN-02 simulated RADIUS-timeout listener
```

PR #46 added:

1. a collector-independent Bicep entrypoint;
2. two synthetic VPN backend listener VMs;
3. a Linux Consumption Azure Function and runtime Storage account;
4. workspace-based Application Insights;
5. a bounded Python API;
6. frontend invocation with controlled fixture fallback;
7. scoped `what-if`, `deploy`, and `verify` workflow operations;
8. regression tests and a runbook.

The workflow path is `.github/workflows/demo-backend-api.yml`.

```text
repository_implementation_present = true
workflow_dispatch_observed        = false
Azure_deployment_observed         = false
service_validation_observed       = false
```

## Contracts declared in code

Backend listener contract:

```text
GET /healthz
GET /transaction?correlation_id=<uuid>
```

- VPN-01 returns a successful synthetic transaction.
- VPN-02 returns HTTP `503` with the simulated `radius_response_timeout` boundary.
- Both may remain healthy under the shallow TCP 443 load-balancer probe while user-function outcomes differ.

Function contract:

```text
GET  /api/health
POST /api/demo/run
```

Declared controls include bounded attempts, no caller-controlled target URL, unique correlation IDs, retained expected `503` evidence, `exact_root_cause_claimed: false`, and technician-owned diagnosis.

These are tested repository contracts, not deployed-service proof.

## Azure dependencies to re-resolve

The scoped template references, but does not own:

- resource group `rg-servicetracer-dev-westus2` in `westus2`;
- VNet `vnet-onprem-sim-mst-dev`;
- subnet `snet-edge`;
- public load balancer `lb-remote-access-mst-dev`;
- backend pool `be-vpn-gateways`;
- public IP `pip-remote-access-mst-dev`;
- Log Analytics workspace `law-mst-dev`.

Fresh Azure inventory must confirm each dependency, identifier, region, tag, and configuration before planning or deployment.

## Latest promoted Azure evidence

The newest promoted Azure evidence remains read-only publication planner run `29979955391` for the separate report-publication architecture. It established, at its recorded time:

- successful GitHub OIDC authentication;
- current inventory for that scope;
- ProviderNoRbac validation;
- a four-create What-If;
- zero Modify, Delete, or Replace changes;
- no authorized or performed Azure mutation.

This does not establish current demo-backend/API readiness.

Broad lifecycle run `29985391850` authenticated and captured Azure context, then failed before What-If because the deployed collector image line differs from the repository declaration. It did not deploy or replace the collector, demo backends, API, report resources, or any other Bicep resource.

## Last stored collector baseline

The latest promoted collector evidence, dated `2026-07-21`, records:

- VM size `Standard_B2ats_v2`;
- deployed Canonical Ubuntu 22.04 Jammy image line;
- desired Canonical Ubuntu 24.04 image line;
- 32 GiB Standard SSD evidence disk with detach-on-delete preservation;
- static-address NIC configured for deletion with the VM;
- system-assigned managed identity;
- no visible publication role assignments for that identity;
- OS disk public network access still allowed.

These are time-bounded control-plane observations. They do not prove current guest health, running version, evidence readability, effective permissions, or present Azure state.

## Authority boundary

The default authority remains fail-closed:

```text
demo_workflow_dispatch_authorized = false
demo_Azure_authentication_authorized = false
demo_Azure_mutation_authorized = false
guest_command_authorized = false
```

The existing bounded grant applies only to the read-only existing-collector report-publication planner. It does not authorize the demo-backend/API workflow.

A future demo planning action requires a new explicit, exact-commit-bounded authorization for read-only Azure inventory, ARM validation, and What-If. A later deployment requires a separate mutation authorization.

## Cost, quota, and security gates

Expected recurring cost is dominated by two continuously running `Standard_B1s` Linux VMs. Function Consumption, Standard LRS runtime Storage, and Application Insights add usage-based cost.

Before deployment consideration, capture:

- current West US 2 CAD prices;
- remaining subscription credit;
- VM and regional quota;
- Azure Policy and deny assignments;
- effective identity permissions;
- exact scoped What-If.

Declared security controls include HTTPS-only, TLS 1.2 minimum, exact GitHub Pages CORS, FTP disabled, no caller-controlled proxy target, SSH-key authentication, Trusted Launch, and no collector declaration.

```text
CORS_allowed != authenticated_API
resource_declared != securely_configured
retail_estimate != actual_cost
```

## Required proof sequence

Before any deployment decision:

1. resolve current GitHub head, open PRs, ownership, and exact-head CI;
2. resolve subscription, tenant, resource group, region, and dependencies;
3. capture cost, quota, policy, and effective permission evidence;
4. obtain explicit read-only planning authority;
5. run scoped ARM validation and exact What-If;
6. reject any unexpected Modify, Delete, Replace, or protected-resource change;
7. obtain separate explicit Azure-mutation authority.

After an authorized deployment:

- prove both backend VMs provisioned;
- verify both listener services;
- verify Function health;
- run 20 correlated attempts and observe both backends;
- prove successful and failed transactions;
- confirm VPN-02 has the greater failure rate;
- preserve the bounded root-cause claim;
- verify live GitHub Pages rendering.

```text
resource_exists
!= listener_verified
!= API_verified
!= frontend_verified
```

## Rollback and cleanup

Repository-only state-model changes are rolled back by reverting their commits. They require no Azure cleanup.

After any future authorized demo deployment, cleanup must remove only deployment-output-identified demo backend and Function resources. Shared network, load balancer, public IP, Log Analytics, collector, evidence disk, and report-publication resources must remain unchanged and be re-verified.
