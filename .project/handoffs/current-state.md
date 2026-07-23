# Current project handoff

## Authoritative scope

The active goal remains the interactive ServiceTracer Azure demo:

```text
GitHub Pages frontend
→ Azure Function demo API
→ existing public Load Balancer TCP 443
→ VPN-01 healthy listener / VPN-02 simulated RADIUS-timeout listener
```

The operations collector and the separate public-report publication path remain outside this increment.

## Live repository baseline

Observed on `2026-07-23`:

- repository: `anthonyedgar30000/azure-iac-msp-lab`;
- default branch: `main`;
- live `main` head before this reconciliation branch: `dcc4f75fc051484ba2f6ef633dc92ef80adae224`;
- PR #46, **Deploy demo backends and connect frontend API**, is merged;
- PR #46 source head: `e8358d090c79f1ba8752323e054693a779e7db51`;
- PR #46 exact-head CI run `29990625589`: success;
- active branch: `agent/reconcile-pr46-merge-state`;
- active draft pull request: PR #47, **Reconcile PR46 merge project state**.

Live GitHub, exact-head CI, and fresh scoped Azure evidence remain authoritative.

## Active reconciliation increment

PR #47 is repository-state reconciliation only.

Permitted paths:

- `.project/active-work.json`;
- `.project/handoffs/current-state.md`.

Its purpose is to record that PR #46 merged while preserving every unproven operational claim as false or unobserved.

```text
PR46_merged                       = true
demo_backend_api_workflow_on_main = true

scoped_workflow_dispatched        = false
Azure_mutation_authorized         = false
demo_backends_deployed            = false
demo_API_deployed                 = false
frontend_live_verified            = false
```

No workflow dispatch, Azure login, Azure read, Azure mutation, RBAC change, deployment, guest command, listener test, API call, browser test, or report publication is authorized by PR #47.

## Repository implementation now present on main

PR #46 added:

1. a collector-independent Bicep entrypoint for the demo backends and API;
2. two synthetic VPN backend listener VMs;
3. a Linux Consumption Azure Function and runtime Storage account;
4. workspace-based Application Insights;
5. a bounded Python API;
6. frontend invocation with controlled fixture fallback;
7. scoped What-If, deploy, and verify automation;
8. regression tests and a runbook.

The scoped workflow is `.github/workflows/demo-backend-api.yml` and supports `what-if`, `deploy`, and `verify` only after separately authorized manual dispatch.

## Backend and API contracts

Backend listener contract:

```text
GET /healthz
GET /transaction?correlation_id=<uuid>
```

- VPN-01 returns a successful synthetic transaction;
- VPN-02 returns HTTP `503` with the simulated `radius_response_timeout` boundary;
- both may remain healthy under the shallow TCP 443 load-balancer probe while user-function outcomes differ.

Function API contract:

```text
GET  /api/health
POST /api/demo/run
```

Controls include bounded attempts, no caller-controlled target URL, unique correlation IDs, retained expected `503` evidence, `exact_root_cause_claimed: false`, and technician-owned diagnosis.

These are repository declarations and tested contracts, not deployed-service proof.

## Existing Azure dependencies

The scoped template references but does not own:

- resource group `rg-servicetracer-dev-westus2` in `westus2`;
- VNet `vnet-onprem-sim-mst-dev`;
- subnet `snet-edge`;
- public load balancer `lb-remote-access-mst-dev`;
- backend pool `be-vpn-gateways`;
- public IP `pip-remote-access-mst-dev`;
- Log Analytics workspace `law-mst-dev`.

Fresh inventory must confirm every dependency before scoped planning or deployment. Repository declarations do not prove that the resources still exist or still match the expected identifiers, region, tags, or configuration.

## Latest accessible Azure evidence

### Read-only publication planner

Run `29979955391` completed successfully for the separate report-publication architecture. It proved Azure OIDC login, current inventory at that time, ProviderNoRbac validation, and a four-create What-If with no Modify, Delete, or Replace changes. It authorized and performed no Azure mutation.

This evidence does not establish current demo-backend/API state.

### Broad lifecycle attempt

Run `29985391850` targeted the collector-owning lifecycle scope. It authenticated and captured Azure context, then failed before What-If because the deployed collector image line differs from the repository declaration.

```text
broad_lifecycle_collector_drift
!= scoped_demo_backends_API_plan
```

The run did not deploy or replace the collector, demo backends, API, report resources, or any other Bicep resource.

## Last stored collector baseline

The most recent repository-promoted environment evidence, dated `2026-07-21`, records:

- collector VM size `Standard_B2ats_v2`;
- deployed image line Canonical Ubuntu 22.04 Jammy;
- desired image line Canonical Ubuntu 24.04;
- a 32 GiB Standard SSD evidence disk with detach-on-delete preservation;
- a static-address collector NIC configured for deletion with the VM;
- a system-assigned managed identity;
- no visible publication role assignments for that principal;
- an OS disk still allowing public network access.

These are time-bounded control-plane observations. Guest health, running version, evidence readability, effective permissions, and current Azure state require fresh verification.

## Security and network boundary

Intended path:

```text
Internet browser
→ HTTPS Azure Function endpoint
→ fixed HTTPS load-balancer public IP target
→ TCP 443 backend pool
→ VPN-01 or VPN-02
```

Declared controls include HTTPS-only, TLS 1.2 minimum, exact GitHub Pages CORS, FTP disabled, no caller-controlled proxy target, SSH-key authentication, Trusted Launch, and no collector resource declaration.

```text
CORS_allowed != authenticated_API
resource_declared != securely_configured
```

The anonymous Function endpoint is a bounded public synthetic-demo surface and must not accept customer data, arbitrary URLs, credentials, raw evidence, or privileged actions.

## Cost and quota boundary

The expected dominant recurring cost is two continuously running `Standard_B1s` Linux VMs. Function Consumption, Standard LRS runtime Storage, and Application Insights add usage-based cost.

Current West US 2 CAD pricing, remaining student credit, subscription quota, Azure Policy allowance, and actual expected monthly cost have not been captured for this exact scope.

```text
retail_estimate != actual_cost
student_credit_available != zero_cost
```

These remain deployment gates.

## Required proof before deployment consideration

Repository proof for PR #47:

- `.project/validate.py` passes;
- CI passes on the exact PR head;
- final diff is restricted to the two declared `.project/` paths.

Separate operational proof before any deployment decision:

- current subscription and tenant context;
- current resource-group and regional inventory;
- dependency existence and identifiers;
- current cost, quota, policy, and effective permission evidence;
- scoped ARM validation and exact What-If;
- zero unexpected Modify, Delete, or Replace changes;
- separately explicit Azure-mutation authorization.

Post-deployment proof, only after authorization:

- both backend VMs provisioned;
- both listener services active;
- Function health reports healthy;
- a 20-attempt run observes both backends;
- successful and failed transactions are present;
- VPN-02 has the greater failure rate;
- exact root cause remains unclaimed;
- GitHub Pages renders the live API result.

```text
resource_exists
!= listener_verified
!= API_verified
!= frontend_verified
```

## Failure, rollback, and cleanup

For PR #47, failure means keeping the PR draft, inspecting the exact project-state or scope failure, and patching only the two permitted files.

Repository rollback is closing PR #47 without merge or reverting its commits. No Azure cleanup applies because this increment performs no Azure operation.

After any future authorized demo deployment, cleanup must remove only deployment-output-identified demo backend and Function resources. Shared network, load balancer, public IP, Log Analytics, collector, evidence disk, and report-publication resources must remain unchanged and be re-verified.
