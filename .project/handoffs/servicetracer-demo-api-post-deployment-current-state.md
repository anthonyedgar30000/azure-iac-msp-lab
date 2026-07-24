# ServiceTracer demo API authenticated post-deployment handoff

## Interpretation boundary

This handoff promotes an authenticated, read-only Azure control-plane inventory captured in Cloud Shell at `2026-07-24T16:39:38Z`–`2026-07-24T16:40:36Z`.

```text
declared_in_code != deployed_in_azure
deployment_succeeded != service_validated
resource_exists != securely_configured
RBAC_assignment != effective_least_privilege
monitoring_enabled != alerts_verified
backup_configured != recovery_tested
estimated_cost != actual_cost
not_observed != absent
```

The capture performed Azure authentication and read-only control-plane queries. It performed no Azure mutation, guest command, transaction replay, deployment, or cleanup.

## Evidence anchor

```text
capture channel: operator-authenticated Azure Cloud Shell
archive: servicetracer-post-deployment-inventory-evidence.zip
archive SHA-256: 95512590ba39a6ef68a78ececf525268af49ba18f2f5d9a582adff4aff85fca0
archive size: 18409 bytes
manifest entries: 21
manifest hashes verified: true
raw archive committed: false
promoted record: .project/evidence/servicetracer-demo-api-post-deployment-inventory-20260724T163938Z.json
```

This is operator-captured evidence, not an independently protected GitHub Actions artifact. The repository stores the sanitized digest, exact manifest hashes, and typed interpretation.

## Azure deployment provenance verified

```text
subscription: Azure subscription 1
subscription ID: hashed only
tenant ID: hashed only
resource group: rg-st-demo-api-dev-westus2
location: westus2
resource count: 7
deployment: servicetracer-demo-api-dev
deployment state: Succeeded
deployment timestamp: 2026-07-24T09:28:47.774684+00:00
deployed source ref: 8b3d55c616d8820edd523f77021a35fe24167bd0
VM: vm-st-demo-api-mst-dev
VM size: Standard_F1als_v7
VM state: VM running
VM provisioning: Succeeded
FQDN: st-demo-api-vm-aeg30000.westus2.cloudapp.azure.com
```

The VM, OS disk, public IP, NIC, NSG, VNet, and Custom Script extension were observed. The public IP FQDN matched the expected endpoint.

## Repository versus deployment

At promotion start, repository `main` was:

```text
e20ef494fe93806085d2b983cde2c58a504ab217
```

GitHub reported that `main` was nine commits ahead of the deployed source ref and zero behind. The changed paths were limited to public-runtime workflows, `.project` evidence/history/handoff, a validator, and tests.

```text
deployed_source_ref != current_main
workload_source_or_IaC_drift = not_observed
```

This is observed governance/evidence advancement, not observed workload-content drift.

## Network and identity

```text
public IP allocation: Static
public IP SKU: Standard Regional IPv4
VNet: vnet-st-demo-api-mst-dev / 10.30.0.0/24
subnet: snet-api / 10.30.0.0/27
VM private IP: 10.30.0.4
NSG inbound Internet TCP 80: allowed
NSG inbound Internet TCP 443: allowed
VM identity: SystemAssigned
```

Port 80 exposure is observed. Whether it is required for redirect or certificate automation was not guest-validated.

## Monitoring and operational controls

```text
boot diagnostics: enabled
supported resources queried for diagnostic settings: 6
supported resources with zero diagnostic settings: 6
metric alerts: 0
action groups: 0
resource-group locks: 0
alert delivery tested: false
```

No Azure Monitor diagnostic settings, metric alerts, or action groups were observed for the supported resource types queried.

```text
boot_diagnostics_enabled != operational_monitoring_configured
alert_objects_absent != alert_delivery_tested
```

## Incomplete observations and collector defects

### RBAC

```text
query status: observation_failed
effective RBAC: not_observed
least privilege: not_verified
```

Cause: the collector combined `--all` with a scoped role-assignment query.

### Cost

```text
query status: observation_failed
actual cost: not_observed
```

Cause: the Cost Management query grouped by unsupported `Currency`.

### Backup and recovery

```text
backup: not_observed
backup absent: not established
recovery tested: false
```

Cause: the collector required an already-installed Resource Graph extension and intentionally did not install it.

These collection defects do not erase the successfully observed deployment facts.

## Quota snapshot

```text
Standard Falsv7 family vCPUs: 1 / 10
Total regional vCPUs: 1 / 10
Standard IPv4 public IPs: 1 / 20
```

## Combined runtime state

The prior public-runtime record and this authenticated control-plane inventory together establish:

```text
deployment provenance = verified
public endpoint identity = verified
VM and networking existence = verified
VM control-plane state = running
ARM deployment success = verified
public API health, TLS, and CORS = verified by prior evidence
transaction protocol = verified by prior evidence
backend transaction success = false in the prior bounded sample

guest OS/service state = not directly verified
effective RBAC = not_observed
diagnostic monitoring = not configured for supported queried resources
alerts = not configured
backup = not_observed
recovery = not tested
actual cost = not_observed
```

## Authority

```text
repository evidence promotion authorized = true
pull request creation authorized = true
pull request merge authorized = false
corrected read-only follow-up execution authorized = false
Azure mutations authorized = false
```

## Next gate

Review and merge this repository-only promotion. A separate authorization is required to execute the corrected read-only RBAC, backup, and cost follow-up.
