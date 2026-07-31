# Current project handoff v5

## Interpretation boundary

This is the authoritative repository and evidence handoff selected by `.project/CURRENT.json` after the accepted ServiceTracer plan, one-shot deployment, and operator runtime health checks.

```text
declared_in_code != deployed_in_azure
current_main != deployed_source_ref
deployment_succeeded != service_validated
health_endpoint_verified != transaction_path_verified
public_FQDN_from_VM_guest != external_browser_path
monitoring_enabled != alerts_verified
backup_configured != recovery_tested
planning_ceiling != actual_cost
not_observed != false
```

## Authoritative files

```text
selector: .project/CURRENT.json
current reality: .project/current-reality-v6.json
state index: .project/state-index-v15.json
current handoff: .project/handoffs/current-state-v5.md
repository sync: .project/reconciliations/servicetracer-plan-deploy-runtime-sync-20260731.json
plan evidence: .project/evidence/servicetracer-demo-api-plan-run-30660575435.json
deployment evidence: .project/evidence/servicetracer-demo-api-deployment-run-30661015789.json
```

## Repository watermark

```text
repository: anthonyedgar30000/azure-iac-msp-lab
observed main: 2ad9557e21cddeed6fc9437c8f20c32b387bf2a2
latest merged PR: #260
PR #260 merge commit: 5576f36ee67dc81f7943ddab9d1ab04333142b75
PR #260 source head: 1e3d4cb6e475af19e84cda3fbc61533da7590adb
direct commits after PR #260 observed: 11
open pull requests observed before this sync: none
exact-head CI for current main: not observed
local working tree: not observed through connector
```

## Accepted planning evidence

```text
workflow run: 30660575435 / attempt 1
source: main@ae08e7a72c14ec6deaddd3fa0f8c84b8342e0be3
conclusion: success
artifact: 8805026018
artifact SHA-256: 76911fb3b626786593df022bdfb654c01efde11cd0b3dc1809679c431f11d1f2
subscription: Azure for Students / Enabled
region: westus2
VM size: Standard_F1als_v7
target resource group: rg-st-demo-api-dev-westus2
readiness: ready_for_arm_what_if
What-If: accepted_independent_workload_create_plan
base or dependency modifications: none
planning authority consumed: true
```

The plan authorized no deployment. Deployment was separately authorized afterward.

## One-shot deployment evidence

```text
workflow run: 30661015789 / attempt 1
source: main@ae08e7a72c14ec6deaddd3fa0f8c84b8342e0be3
accepted plan run: 30660575435
conclusion: success
artifact: 8805241142
artifact SHA-256: 80b0819552623c13cfa244ec2d480f7606c2f224516a5d6c9882233fdbe2b478
internal manifest: 45 entries / 0 failures
deployment: servicetracer-demo-api-deploy-30661015789-1
provisioning state: Succeeded
mode: Incremental
cleanup authorized: false
rerun authorized: false
```

Created workload resources:

```text
vm-st-demo-api-mst-dev
vm-st-demo-api-mst-dev/servicetracer-demo-api
nic-st-demo-api-mst-dev
pip-st-demo-api-vm-mst-dev
```

Existing target VNet, NSG, and resource group were passive/no-change dependencies. The existing ServiceTracer dependency resource group was not modified.

## Post-deployment Azure inventory

```text
resource group: rg-st-demo-api-dev-westus2
region: westus2
VM: vm-st-demo-api-mst-dev
VM size: Standard_F1als_v7
VM provisioning: Succeeded
VM power state: VM running
system-assigned identity: present
Custom Script extension: Succeeded
FQDN: st-demo-api-vm-aeg30001.westus2.cloudapp.azure.com
deployed source ref: ae08e7a72c14ec6deaddd3fa0f8c84b8342e0be3
```

## Runtime health evidence

Two Azure Run Command screenshots supplied by the operator establish:

```text
curl http://localhost:8090/api/health
status: healthy
backend_target_configured: true
hosting_model: dedicated_vm_subproject
```

and:

```text
curl -sS https://st-demo-api-vm-aeg30001.westus2.cloudapp.azure.com/api/health
status: healthy
Azure IMDS identity verified: true
resource group: rg-st-demo-api-dev-westus2
VM: vm-st-demo-api-mst-dev
location: westus2
source ref: ae08e7a72c14ec6deaddd3fa0f8c84b8342e0be3
```

The HTTPS command succeeded without an insecure curl flag, supporting certificate-chain acceptance by that guest. Certificate metadata was not captured. Because the command ran from the VM guest, it does not prove the external browser path.

## Repository-to-runtime drift

The running VM reports deployed source `ae08e7a72c14ec6deaddd3fa0f8c84b8342e0be3`, while current `main` is `2ad9557e21cddeed6fc9437c8f20c32b387bf2a2`. Two later repository commits are not proven applied to the VM:

```text
b5bfd616d2f3faab5f692301c4b71c46a6f9557f  Fix demo API health rate limiting
2ad9557e21cddeed6fc9437c8f20c32b387bf2a2  Fix Azure runtime source provenance
```

This is declared-versus-deployed drift, not a failed deployment claim. Applying either fix to the guest requires a separately planned and authorized runtime update; this sync performs no repair or redeployment.

## Service-validation boundary

Established:

```text
ARM deployment succeeded
VM running
extension succeeded
local process health succeeded
public-FQDN HTTPS health succeeded from VM guest
Azure runtime identity matched exact resource group, VM, region, and source commit
```

Still unverified:

```text
GitHub Pages publication
external browser-to-API path
CORS preflight and allowed-origin behavior
POST /api/demo/run response contract
downstream transaction success
monitoring alert delivery
backup configuration and restore test
actual month-to-date cost
remaining Azure for Students credit
cleanup procedure execution
```

## Authority after sync

```text
active ServiceTracer planning authority: none
active ServiceTracer deployment authority: none
active cleanup authority: none
deployment rerun authorized: false
workflow dispatch performed by this sync: false
Azure login/query performed by this sync: false
guest command performed by this sync: false
Azure mutation performed by this sync: false
cleanup or rollback performed by this sync: false
```

## Cost boundary

The deployed VM, disk, public IP, and related resources are cost-bearing while present. The CAD `$25.00` value is the accepted planning ceiling, not a price assertion, budget, invoice, or spend authority. Current cost and remaining student credit were not freshly observed.

## Next gate

First decide whether the two post-deployment installer fixes need a separately planned runtime update. Then perform a separately bounded read-only external validation: confirm GitHub Pages publication and browser health, verify exact CORS behavior, execute one bounded POST transaction, capture the downstream result without claiming an unsupported root cause, and query cost, credit, monitoring, diagnostics, backup, and recovery status. Any repair, rerun, cleanup, or additional Azure mutation requires separate explicit authority.
