# Current project handoff v6

## Interpretation boundary

This is the authoritative repository and evidence handoff selected by `.project/CURRENT.json` after successful planning, one-shot deployment, guest-origin runtime health checks, and one consumed external browser validation.

```text
declared_in_code != deployed_in_azure
current_main != deployed_source_ref
deployment_succeeded != service_validated
external_browser_path_verified != permanent_service_availability
HTTP_200_API_response != downstream_transaction_success
all_observed_transactions_on_VPN-02 != stable_backend_localization
radius_response_boundary != exact_root_cause
frontend_guarded_output != raw_API_boundary_consistency
monitoring_enabled != alerts_verified
backup_configured != recovery_tested
planning_ceiling != actual_cost
not_observed != false
```

## Authoritative files

```text
selector: .project/CURRENT.json
current reality: .project/current-reality-v7.json
state index: .project/state-index-v16.json
current handoff: .project/handoffs/current-state-v6.md
repository sync: .project/reconciliations/servicetracer-external-evidence-sync-20260801.json
plan evidence: .project/evidence/servicetracer-demo-api-plan-run-30660575435.json
deployment evidence: .project/evidence/servicetracer-demo-api-deployment-run-30661015789.json
external validation evidence: .project/evidence/servicetracer-external-path-run-30693434244.json
external validation authority: .project/authorizations/servicetracer-external-validation-20260801.json
```

## Repository watermark

```text
repository: anthonyedgar30000/azure-iac-msp-lab
observed main: e67869e98d8c26c6525fa25e08cae1af6f5be73d
latest merged PR: #263
PR #263 merge commit: e67869e98d8c26c6525fa25e08cae1af6f5be73d
PR #263 final source head: 83b68d4836b36ffd0db3254121eb4fe3b8ce3e80
open pull requests observed before this sync: none
PR-head CI: success
merge-commit CI: not observed
local working tree: not observed through connector
```

## Deployment and runtime identity retained

The previously promoted deployment facts remain established:

```text
plan run: 30660575435 / success
deployment run: 30661015789 / success
resource group: rg-st-demo-api-dev-westus2
region: westus2
VM: vm-st-demo-api-mst-dev
VM size: Standard_F1als_v7
VM state at deployment evidence: running
Custom Script extension: Succeeded
FQDN: st-demo-api-vm-aeg30001.westus2.cloudapp.azure.com
deployed source ref: ae08e7a72c14ec6deaddd3fa0f8c84b8342e0be3
```

Current `main` is newer than the deployed source. These repository commits are still not proven installed on the VM:

```text
b5bfd616d2f3faab5f692301c4b71c46a6f9557f
2ad9557e21cddeed6fc9437c8f20c32b387bf2a2
```

## Consumed external browser validation

```text
pull request: #263
authorized PR head: 0ca222703585f6e0403957f096f424d0d2a22b91
successful workflow run: 30693434244 / attempt 1
workflow conclusion: success
GitHub synthetic merge checkout: 150a4b5d895b2be426180540316e8588520545c3
artifact: 8816461373
artifact digest: sha256:f162c7a266c35146d827e05cb8b70db6d0438599149e99affe5cbfb5f18d4b6a
artifact manifest: 17 entries verified
observed at: 2026-08-01T09:17:23.919Z
```

The successful live attempt used GitHub's synthetic pull-request merge checkout rather than the literal PR head. The workflow run and artifact metadata bind the attempt to PR head `0ca222...`, and `main` was unchanged during the attempt. This variance is explicit. The merged workflow now checks out the exact PR head and refuses network work when authority is inactive or consumed.

## External path established

Hosted Chrome verified the real published console and live API path:

```text
GitHub Pages publication: verified
frontend rendered: verified
fixture fallback used: false
browser TLS: verified
health GET: HTTP 200 / healthy
allowed-origin CORS preflight: HTTP 204
bounded POST /api/demo/run: HTTP 200
response header/body request ID match: verified
request ID: 9a205247-5dc0-4505-a774-bc697694bd9d
disallowed origin: HTTP 403 / origin_not_allowed
```

Azure runtime identity in the browser-observed health and transaction payload matched:

```text
resource group: rg-st-demo-api-dev-westus2
VM: vm-st-demo-api-mst-dev
location: westus2
hosting model: dedicated_vm_subproject
source ref: ae08e7a72c14ec6deaddd3fa0f8c84b8342e0be3
```

## Bounded downstream sample

The one authorized POST requested 20 synthetic transactions:

```text
attempts: 20
successful: 0
failed: 20
transport errors: 0
VPN-01 observed transactions: 0
VPN-02 observed transactions: 20
HTTP status: 503 for all 20
failure boundary: radius_response for all 20
```

Every transaction showed the same bounded stage sequence:

```text
tcp_established: 90 ms
tls_completed: 318 ms
radius_request_sent: 20 ms
radius_response_timeout: 15000 ms
retries: 3
```

This proves that the API completed the request and returned structured application-level failure evidence. It does not prove a permanent routing condition, an infrastructure defect, a RADIUS server cause, or any exact root cause.

## Localization and evidence-boundary finding

The sample contained no VPN-01 comparison traffic. Therefore stable backend localization was not established.

The frontend behaved correctly:

```text
finding: Repeat the bounded sample before localizing
suspect: Not established
comparison: Not established
boundary: Not established
technician workflow: hidden
exact root cause presented: no
```

The raw API payload nevertheless reported:

```text
suspect_backend: VPN-02
healthy_comparison_backend: VPN-02
service_tracer_stops_at: VPN-02
stable localization: false
```

This is recorded as an unresolved **potential API evidence-boundary defect**. The frontend guard prevented the unsupported boundary from being presented to the operator, but the API report builder should return an unresolved investigation boundary whenever comparison evidence is absent.

A browser-console 404 was also observed. The failed resource was not identified, so it is a separate low-confidence frontend defect candidate rather than evidence that the application failed.

## Authority after promotion

```text
active planning authority: none
active deployment authority: none
active external-validation authority: none
active cleanup authority: none
external validation attempt consumed: true
external validation retry authorized: false
manual workflow dispatch authorized: false
another live POST authorized: false
Azure login/query performed by this sync: false
Azure mutation performed by this sync: false
repair or redeployment performed by this sync: false
cleanup or rollback performed by this sync: false
```

## Still unobserved

```text
downstream successful transaction
actual month-to-date Azure cost
remaining Azure for Students credit
current quota after deployment
monitoring alert delivery
diagnostic-settings effectiveness
backup configuration
restore test
disaster-recovery test
whether the two post-deployment installer fixes are applied to the VM
cleanup execution
```

## Next gate

Plan a repository-only correction to the API report builder so inconclusive samples return an unresolved investigation boundary, and add deterministic regression coverage for no-comparison traffic. Do not redeploy or execute another live POST without separate explicit authority.

Azure cost, credit, quota, monitoring, diagnostics, backup, and recovery need a separately bounded read-only observation when an Azure connector is available. Repair, runtime update, rollback, and cleanup remain separately authorized operations.
