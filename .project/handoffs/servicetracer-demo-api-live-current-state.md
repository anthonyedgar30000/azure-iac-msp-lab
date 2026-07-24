# ServiceTracer demo API live-verification handoff

## Interpretation boundary

This handoff promotes protected public-runtime evidence from PR #80. It does not claim authenticated Azure control-plane provenance.

```text
public_endpoint_reachable != Azure_deployment_provenance_observed
API_healthy != backend_transaction_successful
transaction_protocol_verified != root_cause_determined
load_balancer_probe_healthy != full_application_transaction_healthy
not_observed != absent
```

## Repository and evidence anchors

```text
base main: 8b3d55c616d8820edd523f77021a35fe24167bd0
PR: 80
source head: 9212437bf2155434c035b50a8d32b39fcc046182
tested PR merge SHA: ebf90d9752146cb3a8f8a7f7a386add0b69cbe0c
final merge commit: 76279db80458b098b063e428bc7dabf9c1f9edce
live-verification CI: 30086152352
full CI: 30086152445
artifact ID: 8593782051
artifact digest: sha256:2bd876dfd7e707994218ea347887816df03cff03ba5cb45b60e96cf082c83ad7
artifact expiration: 2026-08-23T10:26:22Z
```

GitHub reported no file-content changes between the tested PR merge tree and the final merge commit. Their commit ancestry differs, so this is content equivalence, not commit identity.

## Public runtime verified

At `2026-07-24T10:26:15Z`, the external GitHub-hosted runner observed:

```text
endpoint: https://st-demo-api-vm-aeg30000.westus2.cloudapp.azure.com
public endpoint reachable = true
TLS verified = true
GET /api/health = HTTP 200
health status = healthy
health schema = servicetracer.demo-api-health.v1
CORS preflight = HTTP 204
allowed origin = https://anthonyedgar30000.github.io
POST /api/demo/run = HTTP 200
transaction response schema = servicetracer.demo-api-response.v1
transaction protocol verified = true
Azure mutations performed by verification = false
```

## Backend outcome preserved separately

The bounded sample contained two transactions:

```text
attempts = 2
successful attempts = 0
failed attempts = 2
observed backends = VPN-02
VPN-01 observed attempts = 0
VPN-02 observed attempts = 2
backend HTTP status = 503, 503
failure boundary = radius_response
exact root cause claimed = false
stable backend-specific localization = false
```

ServiceTracer returned valid diagnostic evidence and stopped at the technician investigation boundary. The sample does not prove VPN-01 health, does not establish a stable VPN-02-specific cause, and does not establish successful end-user transactions.

## Typed verification state

```text
public_API_operationally_verified = true
health_contract_verified = true
TLS_verified = true
CORS_verified = true
transaction_protocol_verified = true
backend_transaction_success_verified = false
full_workload_operationally_verified = false
frontend_integration_verified = false
```

## Azure control-plane provenance

The verification workflow used no Azure login and performed no Azure administrative query.

```text
hosting subscription = not_observed
tenant = not_observed
resource group = not_observed
VM resource = not_observed
deployed VM SKU = not_observed
deployment correlation = not_observed
deployed source commit = not_observed
effective RBAC = not_observed
cost = not_observed
backup = not_observed
monitoring and alerts = not_observed
```

These values must not be interpreted as absent.

## Shared-state boundary

The older `.project/active-work.json`, `.project/environment-state.json`, and primary handoff preserve a different protected planner evidence stream. This increment does not overwrite them.

```text
older planner evidence preserved = true
public runtime evidence promoted = true
shared planner state replaced = false
```

The scoped evidence record is:

```text
.project/evidence/servicetracer-demo-api-live-verification-30086152352.json
```

## Current authority

```text
repository evidence promotion authorized = true
pull request creation authorized = true
pull request merge authorized = false
Azure authentication authorized = false
Azure mutation authorized = false
deployment authorized = false
cleanup authorized = false
```

## Next gate

Capture a separately authorized authenticated post-deployment Azure inventory and reconcile it against this public-runtime evidence and an exact repository commit. That gate should observe subscription and tenant fingerprints, resource group, VM SKU, public IP/DNS identity, deployed source identity, deployment record, cost, monitoring, alerts, backup, and recovery state without mutating Azure.
