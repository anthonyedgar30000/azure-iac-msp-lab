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

## Intended architecture

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

Default resource scope:

```text
subscription
└── rg-st-demo-api-dev-westus2
    ├── vnet-st-demo-api-mst-dev
    ├── nsg-st-demo-api-mst-dev
    ├── pip-st-demo-api-vm-mst-dev
    ├── nic-st-demo-api-mst-dev
    └── vm-st-demo-api-mst-dev
```

## Canonical boundary

The subproject must never target these existing base resources for mutation:

- `vm-stcollector-mst-dev`;
- `nsg-operations-mst-dev`;
- `vnet-onprem-sim-mst-dev`;
- `lb-remote-access-mst-dev`;
- the collector NIC, evidence disk, extensions, or managed identity.

The existing remote-access public endpoint is read only and is converted into the fixed backend transaction URL. The API caller cannot supply an arbitrary target.

## Identity and permissions

The VM receives a system-assigned managed identity but no Azure role assignment in the initial workload. Deployment uses GitHub OIDC through the protected `azure-lab` environment. The planning workflow has Azure read, ARM validation, and What-If authority only.

The VM has no inbound SSH rule. Administration must use a separately governed Azure control-plane method. A generated public key is still required by the Linux provisioning contract, but possession of that key does not create a network path.

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

## Cost and quota implications

The workload adds one small Linux VM, one managed OS disk, one Standard public IP, and outbound data usage. Exact West US 2 CAD cost, remaining Azure for Students credit, VM-family quota, and public-IP quota must be refreshed in the planning artifact before deployment authorization.

```text
estimated_cost != actual_cost
quota_observed != quota_reserved
```

## Deployment method

The only active workflow in this increment is:

```text
.github/workflows/servicetracer-demo-api-subproject-plan.yml
```

It runs only from `refs/heads/main`, checks out the immutable dispatch SHA from `github.sha`, captures Azure context and quota, validates the subscription-scope Bicep, runs an exact What-If, classifies the result, uploads evidence, and stops.

The workflow deliberately has no user-entered commit field. This removes stale-SHA transcription as an operational failure mode.

No deploy workflow is authorized by this increment.

## Validation commands

```bash
python -m unittest discover -s workloads/servicetracer-demo-api/tests -v
az bicep lint --file workloads/servicetracer-demo-api/infra/main.bicep
az bicep build --file workloads/servicetracer-demo-api/infra/main.bicep
bash -n workloads/servicetracer-demo-api/scripts/install.sh
```

An accepted plan must create only the dedicated resource group and the resources listed above. Any Modify, Delete, Replace, dependency-resource mutation, collector reference, or unrelated resource type is blocking.

## Expected outputs

- target resource-group name;
- VM and public-IP resource IDs;
- public FQDN;
- health and run URLs;
- exact What-If assessment with `deployment_authorized: false`;
- evidence manifest binding the artifact to the dispatch SHA.

## Failure and rollback behavior

Planning failures perform no Azure mutation. Repository rollback is a PR revert.

A later failed deployment must capture subscription and resource-group deployment operations plus target inventory. It must not infer zero partial mutation from a failed command.

## Cleanup and decommissioning

Cleanup is a separate destructive decision. The intended order is:

1. withhold the frontend endpoint;
2. verify no consumers depend on the API;
3. delete the dedicated workload resource group;
4. verify the resource group and public IP no longer exist;
5. capture final cost and deletion evidence;
6. retain sanitized deployment and validation records.

Cleanup of legacy collector-hosted or Microsoft.Web residue is outside this subproject.
