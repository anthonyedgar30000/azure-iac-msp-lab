# Current project handoff

## Corrected workstream

The active goal is the interactive ServiceTracer Azure demo—not collector replacement and not public-report publication.

```text
GitHub Pages frontend
→ Azure Function demo API
→ existing public Load Balancer TCP 443
→ VPN-01 healthy listener / VPN-02 simulated RADIUS-timeout listener
```

The existing operations collector remains outside this increment.

## Live repository baseline

Observed on `2026-07-23` for draft PR #46:

- repository: `anthonyedgar30000/azure-iac-msp-lab`;
- default branch: `main`;
- live `main` head: `590176f890f590759bb9d9fe518314295c8bad6c`;
- latest merged pull request: PR #45, **Add read-only publication predeployment readiness**;
- active branch: `feat/demo-backends-api`;
- active draft pull request: PR #46, **Deploy demo backends and connect frontend API**;
- no workflow dispatch or Azure mutation is authorized by this repository increment.

Live GitHub, exact-head CI, and fresh scoped Azure evidence remain authoritative.

## Scope correction from the failed broad lifecycle run

Uploaded workflow logs for run `29985391850` showed an attempted broad **Azure lab lifecycle** deploy with:

```text
deploy_demo_backends          = false
deploy_public_report_endpoint = false
```

The run authenticated to Azure and performed reads, then stopped before Bicep What-If because the existing collector VM image differs from the current repository declaration. No collector replacement, backend deployment, API deployment, report deployment, or other Bicep mutation occurred.

```text
broad_lifecycle_collector_drift
!= blocker_for_collector_independent_demo_scope
```

The new workflow does not call `resolve_vm_plan.sh`, does not declare `deployOperationsCollector`, and does not manage `vm-stcollector-mst-dev`.

## Existing dependencies

The scoped template treats the following live resources as dependencies rather than ownership targets:

- resource group `rg-servicetracer-dev-westus2` in `westus2`;
- VNet `vnet-onprem-sim-mst-dev`;
- edge subnet `snet-edge`;
- public load balancer `lb-remote-access-mst-dev`;
- backend pool `be-vpn-gateways`;
- public IP `pip-remote-access-mst-dev`;
- Log Analytics workspace `law-mst-dev`.

The workflow inventories these resources before planning or deployment. Missing or mismatched dependencies fail closed.

## Repository implementation

Declared paths:

- `.github/workflows/ci.yml`;
- `.github/workflows/demo-backend-api.yml`;
- `.project/active-work.json`;
- `.project/handoffs/current-state.md`;
- `demo_api/.funcignore`;
- `demo_api/core.py`;
- `demo_api/function_app.py`;
- `demo_api/host.json`;
- `demo_api/requirements.txt`;
- `docs/app.js`;
- `docs/report-source.json`;
- `docs/runbooks/demo-backend-api.md`;
- `infra/demo-backend-api.bicep`;
- `infra/modules/demo_api.bicep`;
- `infra/scripts/assert_demo_backend_api_what_if.py`;
- `infra/tests/test_demo_backend_api.py`.

The implementation adds:

1. a collector-independent Bicep entrypoint;
2. the existing two-backend synthetic listener module;
3. a Linux Consumption Azure Function and runtime Storage account;
4. workspace-based Application Insights;
5. a bounded Python API;
6. frontend invocation with controlled fixture fallback;
7. scoped What-If/deploy/verify automation;
8. regression tests and a runbook.

## Backend listener contract

Both VMs run the existing HTTPS listener on port `443`:

```text
GET /healthz
GET /transaction?correlation_id=<uuid>
```

- `VPN-01` returns a successful synthetic transaction;
- `VPN-02` returns HTTP `503` with the simulated `radius_response_timeout` boundary;
- the load-balancer probe remains shallow TCP, so both listeners can be probe-healthy while user-function outcomes differ.

## API contract

The Azure Function exposes:

```text
GET  /api/health
POST /api/demo/run
```

Example request:

```json
{
  "attempts": 20
}
```

Controls:

- attempts are limited to 2–50;
- the caller cannot supply a target URL;
- the backend target is deployment configuration only;
- every attempt receives a new correlation ID;
- expected HTTP `503` bodies are retained as transaction evidence;
- the response schema is `servicetracer.demo-api-response.v1`;
- `exact_root_cause_claimed` remains `false`;
- device-specific diagnosis and repair remain technician-owned.

The Function disables certificate verification only for the fixed synthetic backend target because backend cloud-init generates short-lived self-signed certificates. The browser uses the Azure Function platform hostname and platform TLS.

## Frontend contract

`docs/report-source.json` provides a default `live_demo_api_url`. The frontend also accepts an `?api=` override.

When **Run incident analysis** is selected:

1. the browser posts 20 attempts to the Function;
2. the Function runs correlated transactions through the public load balancer;
3. the result is validated and rendered;
4. when the API is unavailable, the committed fixture remains usable and the fallback is stated explicitly.

```text
frontend_animation
→ live_API_invocation
→ actual_Azure_transactions
→ bounded_localization
```

## Network and security path

```text
Internet browser
→ HTTPS Azure Function endpoint
→ fixed HTTPS load-balancer public IP target
→ TCP 443 backend pool
→ VPN-01 or VPN-02
```

Security controls:

- Function HTTPS-only and TLS 1.2 minimum;
- exact GitHub Pages CORS origin;
- FTP disabled;
- no caller-controlled proxy target;
- bounded request size by attempt count;
- backend VMs retain Trusted Launch, SSH key authentication, and systemd hardening;
- no new RBAC assignment is required by this design;
- no collector or report-publication resource is declared.

```text
CORS_allowed
!= authenticated_API
```

The anonymous API is intentionally a bounded public demo endpoint. It exposes synthetic transactions only and must not accept customer data, arbitrary URLs, secrets, raw evidence, or privileged actions.

## Cost implications

The dominant recurring cost is two continuously running `Standard_B1s` Linux VMs. Additional resources are a Consumption Function, Standard LRS runtime Storage, and Application Insights using the existing capped Log Analytics workspace.

Current West US 2 CAD pricing and the subscription's remaining credit are not yet captured for this exact scope.

```text
retail_estimate != actual_cost
student_credit_available != zero_cost
```

## Scoped workflow

After merge, use **Actions → Demo backends and API**.

Read-only planning confirmation:

```text
DEMO-BACKEND-API:what-if:rg-servicetracer-dev-westus2:func-st-demo-mst-dev-aeg30000
```

A later deployment, only after separate explicit Azure-mutation authorization, uses:

```text
DEMO-BACKEND-API:deploy:rg-servicetracer-dev-westus2:func-st-demo-mst-dev-aeg30000
```

The What-If classifier rejects:

- `Modify`, `Delete`, and `Replace`;
- unexpected resource types;
- changes to the existing VNet, load balancer, public IP, Log Analytics workspace, or collector VM.

## Required proof

Repository proof:

- `.project/validate.py` passes;
- all ServiceTracer and infrastructure tests pass;
- `infra/main.bicep` still lints/builds;
- `infra/demo-backend-api.bicep` lints/builds;
- final diff is restricted to declared paths.

Operational proof after a separately authorized deployment:

- both backend VMs are provisioned;
- both listener services are active;
- Function health is `healthy`;
- a 20-attempt run observes both backends;
- successful and failed transactions are present;
- VPN-02 has the greater failure rate;
- exact root cause remains unclaimed;
- GitHub Pages renders the live API result.

```text
resource_exists
!= listener_verified
listener_verified
!= API_verified
API_verified
!= frontend_verified
```

## Authority and rollback

Current state:

```text
repository_implementation_authored = true
PR46_open_draft                   = true
PR46_merged                       = false
scoped_workflow_dispatched        = false
Azure_authentication_authorized   = false
Azure_mutation_authorized         = false
backend_or_API_deployed           = false
frontend_live_verified            = false
```

Repository rollback is closing PR #46 or reverting its commits. There is no Azure cleanup for this repository-only increment.

After an authorized deployment, cleanup must remove only the two backend VMs/NICs/disks/availability set and the Function plan/app/runtime Storage/Application Insights resources identified by deployment outputs. Shared network, load balancer, public IP, Log Analytics, collector, and report-publication resources must remain unchanged and be re-verified.
