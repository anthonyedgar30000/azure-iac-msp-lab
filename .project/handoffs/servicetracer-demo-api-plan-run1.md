# ServiceTracer demo API planning run 1

## Objective

Authorize exactly one dispatch of the ratified dual-subscription planning workflow from immutable `main`.

This is the first cloud-facing gate toward deployment. It performs authenticated read-only observations, ARM validation, and bounded ARM What-If. It does not deploy or mutate Azure resources.

## Exact workflow

```text
.github/workflows/servicetracer-demo-api-subproject-plan.yml
```

GitHub Environment:

```text
azure-api-payg
```

## Exact inputs

```text
environment: dev
location: westus2
prefix: mst
dependency_resource_group: rg-servicetracer-dev-westus2
dns_label: st-demo-api-vm-aeg30000
allowed_origin: https://anthonyedgar30000.github.io
vm_size: Standard_F1als_v7
maximum_monthly_cost_cad: 25.00
confirmation: PLAN-DEMO-API-SUBPROJECT:dev:st-demo-api-vm-aeg30000
```

## Authority boundary

Authorized once:

- workflow dispatch from `main`;
- OIDC authentication to the existing dependency and target subscriptions;
- read-only dependency, provider, policy, quota, SKU, resource, and price observations;
- ARM validation using `ProviderNoRbac`;
- bounded ARM What-If;
- protected evidence upload.

Not authorized:

- Azure resource creation, update, or deletion;
- deployment execution;
- RBAC or provider-registration mutation;
- secret or network mutation;
- cleanup, rollback, retry, or GitHub Re-run;
- model request, remote MCP hosting, or ChatGPT connection.

```text
planning dispatch authorized != deployment authorized
ARM What-If != Azure mutation
planning ceiling != spend authority
```

## Cost boundary

The **CAD 25.00** value is a planning ceiling used to reject an unsuitable plan. It is not authorization to spend CAD 25.00 and is not an observed Azure cost.

## Consumption and failure

The first authenticated workflow attempt consumes this authorization. Any failure must preserve the protected evidence and stop. A new attempt requires a new authorization record and explicit human instruction.

## Next gate

Review the exact planning artifact, current price and quota observations, target-resource state, ARM validation, and What-If changes. Only then may a separate deployment request authorize resource mutation.
