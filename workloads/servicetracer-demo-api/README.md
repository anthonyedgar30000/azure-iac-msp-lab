# ServiceTracer Demo API — Independent Azure Workload

## Purpose

This directory is the authoritative deployment boundary for the independent ServiceTracer demo API workload. It owns a dedicated resource group, VNet, subnet, NSG, public IP, NIC, Linux VM, managed identity, installer, planning evidence, rollback, and cleanup procedure.

It consumes the existing ServiceTracer HTTPS transaction endpoint as a read-only dependency. It does not install on, reconfigure, or share the lifecycle of the collector.

```text
subproject != separate product
shared_subscription != shared_resource_lifecycle
backend_dependency != mutation_authority
what_if_accepted != deployment_authorized
```

## Ratified single-subscription planning boundary

```text
Azure for Students
├── rg-servicetracer-dev-westus2
│   └── existing ServiceTracer HTTPS endpoint (read only)
└── future rg-st-demo-api-dev-westus2
    ├── vnet-st-demo-api-mst-dev
    ├── nsg-st-demo-api-mst-dev
    ├── pip-st-demo-api-vm-mst-dev
    ├── nic-st-demo-api-mst-dev
    └── vm-st-demo-api-mst-dev
```

The existing dependency and proposed workload remain isolated by resource group and workload-specific naming while using the same Azure for Students subscription. The planner uses the protected GitHub environment `azure-lab`, one workload-identity login, and `ProviderNoRbac` ARM validation.

The workflow's command set is planning-only. The effective RBAC assigned to the `azure-lab` identity may be broader than the commands used by this workflow, so successful authentication does not by itself prove effective least privilege.

## Intended application path

```text
GitHub Pages
→ HTTPS
→ dedicated Standard public IP and Azure DNS label
→ dedicated NSG allowing TCP 80/443 only
→ dedicated Linux VM
→ Nginx TLS termination and rate limiting
→ loopback-only Python API on 127.0.0.1:8090
→ fixed ServiceTracer HTTPS transaction dependency
→ synthetic VPN-01 / VPN-02 backends
```

## Approved read-only planning candidate

The reconciled defaults are:

```text
region: westus2
VM size: Standard_F1als_v7
```

Historical Cloud Shell observations on `2026-07-24` reported an unrestricted `Standard_F1als_v7` record and sufficient regional, family, and Standard IPv4 public-IP quota in `westus2`. Those observations were not captured by the corrected single-subscription workflow and must be refreshed before they can support a new planning decision.

```text
manual_cloud_shell_observation != protected_workflow_artifact
sku_unrestricted != quota_reserved
candidate_selected != deployment_authorized
estimated_cost != actual_cost
```

The next protected planner must refresh provider, policy, SKU, quota, subscription state, and target resource-group inventory before ARM What-If. Current invoice-level pricing, remaining student credit, and the candidate's actual monthly cost remain unverified.

## Identity and permissions

The VM receives a system-assigned managed identity but no Azure role assignment in the initial workload.

The planner uses the existing `azure-lab` workload-identity contract:

- `AZURE_CLIENT_ID`;
- `AZURE_TENANT_ID`;
- `AZURE_SUBSCRIPTION_ID` for Azure for Students;
- `ProviderNoRbac` for subscription validation and What-If.

It reads the existing dependency resource group and evaluates a distinct target resource group in the same subscription. No second subscription, target identity, or Pay-As-You-Go environment is part of the current design.

The exact effective role-assignment scope must be captured separately before it can be claimed as verified least privilege. The VM has no inbound SSH rule. The planner uses a public-only ARM placeholder and creates no private credential.

## Network and security controls

- Dedicated `/24` VNet and `/27` subnet.
- Inbound TCP 80 and 443 only from the `Internet` service tag.
- No inbound SSH rule.
- Standard, static, Regional IPv4 public IP.
- Nginx is the only public listener.
- Python binds to loopback.
- CORS allows one exact HTTPS origin.
- The backend URL is deployment configuration, not caller input.
- The service runs as an unprivileged account with systemd hardening.

## Cost, policy, and quota implications

The workload would add one Linux VM, one managed OS disk, one Standard public IP, and outbound data usage to Azure for Students. That could consume student credit and quota, but this repository correction performs no Azure operation and creates no cost delta.

The planner captures subscription context, providers, inherited policy, regional compute usage, VM-family quota, public-IP quota, SKU restrictions, target inventory, ARM validation, and What-If evidence. The `maximum_monthly_cost_cad` input is a human ceiling only; it is not a computed price, student-credit check, or billing control.

## Deployment method

The active planning workflow is:

```text
.github/workflows/servicetracer-demo-api-subproject-plan.yml
```

It is a read-only planner. It runs from immutable `main`, validates the exact `westus2` / `Standard_F1als_v7` package, logs into Azure for Students once, reads the existing dependency, captures target evidence in the same subscription, classifies readiness, runs `ProviderNoRbac` validation and What-If, uploads evidence, and stops.

It contains no deployment command.

## Validation

```bash
python .project/validate.py
python -m unittest discover -s workloads/servicetracer-demo-api/tests -v
python -m unittest discover -s infra/tests -v
az bicep lint --file workloads/servicetracer-demo-api/infra/main.bicep
az bicep build --file workloads/servicetracer-demo-api/infra/main.bicep
bash -n workloads/servicetracer-demo-api/scripts/install.sh
```

An accepted plan may contain only creates for the dedicated workload scope. Any Modify, Delete, Replace, dependency-resource mutation, scope escape, unobserved target inventory, unavailable SKU, or insufficient quota is blocking.

## Failure, rollback, and cleanup

Planning failures perform no Azure mutation. Repository rollback is a PR revert.

A failed future deployment must capture deployment operations and post-failure inventory; failure cannot be treated as proof of zero partial mutation.

Cleanup is separately authorized and must delete only the dedicated workload resource group after endpoint withdrawal, consumer checks, cost capture, and deletion verification.
