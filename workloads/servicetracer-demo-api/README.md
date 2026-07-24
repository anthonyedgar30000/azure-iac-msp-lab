# ServiceTracer Demo API — Independent Azure Workload

## Purpose

This directory is the authoritative boundary for deploying the ServiceTracer demo API as an independent workload inside the Azure IaC MSP Lab.

The workload owns its own Azure resource group, virtual network, subnet, network security group, public IP, network interface, Linux VM, managed identity, runtime installation, planning evidence, validation, rollback, and cleanup procedure.

It consumes ServiceTracer through one declared HTTPS dependency. It does not install on, reconfigure, or share the lifecycle of the ServiceTracer collector.

```text
subproject != separate product
shared_repository != shared_runtime_lifecycle
backend_dependency != mutation_authority
what_if_accepted != deployment_authorized
```

## Dual-subscription architecture

The active planning design separates the existing dependency from the future API deployment target:

```text
Azure for Students dependency subscription
└── rg-servicetracer-dev-westus2
    └── existing ServiceTracer HTTPS endpoint (read only)

Dedicated Azure Plan target subscription
└── rg-st-demo-api-dev-<region>
    ├── vnet-st-demo-api-mst-dev
    ├── nsg-st-demo-api-mst-dev
    ├── pip-st-demo-api-vm-mst-dev
    ├── nic-st-demo-api-mst-dev
    └── vm-st-demo-api-mst-dev
```

```text
dependency_subscription != target_subscription
billing_plan != deployment_context
Reader_assignment != mutation_authority
ProviderNoRbac_what_if != deployment
```

The planner uses the isolated GitHub environment `azure-api-payg`, not the shared `azure-lab` environment.

## Intended application path

```text
GitHub Pages
→ HTTPS
→ dedicated Standard public IP and Azure DNS label
→ dedicated NSG allowing TCP 80/443 only
→ dedicated Linux VM
→ Nginx TLS termination and rate limiting
→ loopback-only Python API on 127.0.0.1:8090
→ configured ServiceTracer HTTPS transaction dependency
→ synthetic VPN-01 / VPN-02 backends
```

## Canonical boundary

The subproject must never target these existing base resources for mutation:

- `vm-stcollector-mst-dev`;
- `nsg-operations-mst-dev`;
- `vnet-onprem-sim-mst-dev`;
- `lb-remote-access-mst-dev`;
- the collector NIC, evidence disk, extensions, or managed identity.

The existing remote-access public endpoint is read only and becomes the fixed backend transaction URL. The API caller cannot supply an arbitrary target.

## VM sizing contract

The default planning and IaC size is:

```text
Standard_B2ats_v2
```

This size matches the latest working Azure-observed compute contract used in the lab. The earlier `Standard_B1s` default was inherited from the synthetic backend workload and is not the approved default for this independent API host.

```text
observed_working_size != guaranteed_current_availability
configured_default != quota_reserved
```

The planner refreshes target-subscription SKU restrictions and Total Regional vCPU quota before ARM What-If. It fails closed when no unrestricted SKU record exists or the target region cannot accommodate the required cores.

## Identity and permissions

The VM receives a system-assigned managed identity but no Azure role assignment in the initial workload.

The read-only planner uses two separate OIDC identities in the protected `azure-api-payg` GitHub environment:

- dependency identity: Reader on `rg-servicetracer-dev-westus2` in the dependency subscription;
- target identity: Reader on the selected Azure Plan subscription.

ARM validation and What-If use `ProviderNoRbac`, so the planner checks provider-backed resource validity with read permissions instead of granting the planning identities deployment permissions.

The VM has no inbound SSH rule. Administration must use a separately governed Azure control-plane method. The planner supplies a public-only ARM placeholder and creates no usable private credential.

## Network and security controls

- A dedicated `/24` VNet and `/27` subnet isolate the workload.
- The subnet NSG permits only inbound TCP 80 and 443 from the `Internet` service tag.
- No inbound SSH rule is declared.
- The VM public IP is Standard, static, Regional, and uses `VirtualNetworkInherited` DDoS mode.
- Nginx is the only public application listener.
- The Python API binds to loopback and limits request bodies to 4 KiB.
- CORS is restricted to one exact HTTPS origin.
- The API backend URL is deployment configuration, not caller input.
- The service runs as an unprivileged system account with systemd hardening.

## Cost, policy, and quota implications

The workload adds one Linux VM, one managed OS disk, one Standard public IP, and outbound data usage in the selected Azure Plan subscription.

The planner captures target subscription state, inherited policy assignments, providers, regional compute usage, network usage, SKU restrictions, target inventory, and ARM What-If evidence. The human `maximum_monthly_cost_cad` input is a planning ceiling only; it is not a computed price or spending limit.

```text
estimated_cost != actual_cost
quota_observed != quota_reserved
Azure_Plan != unlimited_quota
```

## Deployment method

The only active workflow for this workload is:

```text
.github/workflows/servicetracer-demo-api-subproject-plan.yml
```

It runs only from `refs/heads/main`, checks out the immutable dispatch SHA from `github.sha`, validates the dual-subscription secret contract, runs tests before Azure login, reads the dependency subscription, switches to a separate target identity, captures target evidence, validates the subscription-scope Bicep with `ProviderNoRbac`, runs an exact What-If, classifies the result, uploads evidence, and stops.

The workflow deliberately has no user-entered commit field and no deployment command. GitHub environment creation, secret population, federated credentials, and RBAC are manual prerequisites documented in:

```text
docs/runbooks/servicetracer-demo-api-payg-subscription-boundary.md
```

## Validation commands

```bash
python -m unittest discover -s workloads/servicetracer-demo-api/tests -v
az bicep lint --file workloads/servicetracer-demo-api/infra/main.bicep
az bicep build --file workloads/servicetracer-demo-api/infra/main.bicep
bash -n workloads/servicetracer-demo-api/scripts/install.sh
```

An accepted plan must create only the dedicated target resource group and its declared resources. Any Modify, Delete, Replace, dependency-resource mutation, collector reference, unrelated resource type, unavailable SKU, or insufficient target regional-core quota is blocking.

## Failure, rollback, and cleanup

Planning failures perform no Azure mutation. Repository rollback is a PR revert.

A later failed deployment must capture subscription and resource-group deployment operations plus target inventory. It must not infer zero partial mutation from a failed command.

Cleanup is a separate destructive decision. Delete only the dedicated workload resource group after consumer checks, endpoint withdrawal, cost capture, and deletion verification. Cleanup of legacy collector-hosted, Microsoft.Web, or synthetic-backend residue remains outside this subproject.
