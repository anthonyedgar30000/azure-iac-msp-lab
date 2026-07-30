# ServiceTracer Demo API — Azure for Students Boundary

## Purpose

Plan the independent ServiceTracer demo API in the existing Azure for Students subscription while keeping the existing ServiceTracer dependency and the proposed workload in separate resource groups.

```text
same_subscription != same_resource_lifecycle
resource_group_isolation != subscription_isolation
ProviderNoRbac_what_if != deployment
```

## Selected boundary

```text
Subscription
  name: Azure for Students
  role: existing dependency plus planning target
  region: westus2

Existing dependency
  resource group: rg-servicetracer-<environment>-westus2
  access: read only for this planner

Proposed workload
  resource group: rg-st-demo-api-<environment>-westus2
  candidate VM size: Standard_F1als_v7
  operation: validation and What-If only
```

The exact subscription and tenant identifiers remain in the protected `azure-lab` GitHub environment. Tokens, private keys, client secrets, federated assertions, and unredacted identifiers must not be committed or written to public evidence.

## Repository workflow contract

```text
workflow: .github/workflows/servicetracer-demo-api-subproject-plan.yml
GitHub environment: azure-lab
subscription boundary: single_subscription
candidate region: westus2
candidate VM size: Standard_F1als_v7
```

Required environment secrets:

```text
AZURE_CLIENT_ID
AZURE_TENANT_ID
AZURE_SUBSCRIPTION_ID
```

The workflow validates the configured subscription and tenant after one workload-identity login. It rejects any region or VM-size input other than the reviewed package and rejects a target resource-group name that equals the dependency resource group.

The workflow does not create GitHub environments, secrets, federated credentials, Azure role assignments, resources, or deployment records.

## Planner sequence

```text
immutable main SHA
→ validate exact westus2 / Standard_F1als_v7 package
→ run repository tests
→ Azure for Students OIDC login
→ verify exact enabled subscription and tenant
→ read existing ServiceTracer dependency endpoint
→ capture providers, policy, quotas, SKU, and target inventory
→ distinguish explicit ResourceGroupNotFound from observation failure
→ fail closed on unknown inventory or readiness failure
→ subscription validation with ProviderNoRbac
→ subscription What-If with ProviderNoRbac
→ classify exact create-only plan
→ upload evidence
→ stop
```

No step authorizes or performs deployment, cleanup, RBAC mutation, credential creation, guest commands, or endpoint promotion.

## Required planning evidence

An acceptable artifact must prove:

- the selected subscription is the configured Azure for Students subscription, Enabled, and tenant-aligned;
- the dependency resource group and public endpoint are readable;
- Microsoft.Compute and Microsoft.Network are registered;
- `Standard_F1als_v7` is observed and unrestricted in `westus2`;
- regional, VM-family, and Standard IPv4 public-IP quota are sufficient;
- the target resource group is explicitly absent or its complete inventory is authoritative;
- ARM validation and What-If used `ProviderNoRbac`;
- the What-If contains only dedicated workload creates;
- the dependency resource group is unchanged;
- `azure_mutations_performed=false`;
- `deployment_authorized=false`.

## Identity and authorization boundary

The workflow uses the established `azure-lab` identity. The commands in this planner are read-only or planning operations, but this does not prove that the identity's effective RBAC is itself read-only. Effective role assignments and least privilege require separate evidence.

A successful planning run consumes only its exact one-attempt authorization. A retry, changed commit, changed parameters, deployment, cleanup, or RBAC change requires new authority.

## Cost gate

This repository correction has no Azure cost delta. A later planning run must capture current quota and subscription context. Current student credit, invoice pricing, taxes, discounts, and actual monthly cost are not verified. The planner's CAD ceiling is not a price assertion or billing control.

## Failure and rollback

Planning failures perform no Azure mutation. Fix the exact blocked condition and obtain fresh authorization before another dispatch.

Repository rollback is a PR revert. Removal of stale Pay-As-You-Go GitHub configuration, federated credentials, secrets, or Azure role assignments is a separate administrative cleanup requiring explicit authorization and verification.

## Deployment gate

A successful read-only planner does not authorize deployment. Deployment requires:

- exact reviewed commit binding;
- accepted protected What-If artifact;
- student-credit and cost acceptance;
- effective write-identity review;
- rollback and cleanup procedure;
- post-deployment health, TLS, dependency, CORS, and browser validation;
- explicit human deployment authorization.
