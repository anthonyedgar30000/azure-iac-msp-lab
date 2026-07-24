# ServiceTracer Demo API — Pay-As-You-Go Subscription Boundary

## Purpose

Plan the independent ServiceTracer demo API in a dedicated Pay-As-You-Go subscription while preserving the Azure for Students ServiceTracer environment as a read-only dependency source.

```text
dependency_subscription != deployment_target_subscription
functional_access_observed != least_privilege_verified
ProviderNoRbac_what_if != deployment
```

## Selected boundary

```text
Dependency
  subscription: Azure for Students
  resource group: rg-servicetracer-dev-westus2
  role: read-only ServiceTracer dependency

Target
  subscription: Azure subscription 1
  subscription fingerprint: `sha256:262d05105062731302e7121dd53aed5f97bf644e86f84aa6d86efd322b4f5104`
  offer observed: PayAsYouGo_2014-09-01
  spending limit observed: Off
  tenant fingerprint: `sha256:26ba6e04f1a9cde8b97b64734498f4cbe81d5dcbf7b0f451d81570817c2967bc`
  region: westus2
  future resource group: rg-st-demo-api-dev-westus2
  candidate VM size: Standard_F1als_v7
```

The public repository records only SHA-256 fingerprints for subscription and tenant identifiers. Exact identifiers remain in protected GitHub environment secrets and protected workflow evidence. Tokens, private keys, client secrets, and federated assertion material must never be recorded.

## Repository workflow contract

```text
workflow: .github/workflows/servicetracer-demo-api-subproject-plan.yml
GitHub environment: azure-api-payg
candidate region: westus2
candidate VM size: Standard_F1als_v7
```

Required environment secrets:

```text
AZURE_TENANT_ID
AZURE_DEPENDENCY_CLIENT_ID
AZURE_DEPENDENCY_SUBSCRIPTION_ID
AZURE_TARGET_CLIENT_ID
AZURE_TARGET_SUBSCRIPTION_ID
```

The workflow fails closed if the client IDs or subscription IDs are not distinct. It also rejects any region or VM-size input other than the reviewed package.

## Observed administrative reality

Protected run `30064289707` at commit `323b3892c6efd598231037f23281d49608ceb570` proved:

- the `azure-api-payg` environment resolved the required secret contract;
- dependency OIDC login succeeded;
- dependency resource-group and public-IP reads succeeded;
- target OIDC login succeeded;
- target provider, policy, compute-usage, network-usage, and SKU reads began successfully;
- the target context was Enabled and tenant-aligned;
- no deployment or Azure mutation was authorized;
- ARM What-If was skipped because the old `eastus` / `Standard_B2ats_v2` package was blocked.

Artifact:

```text
name: servicetracer-demo-api-subproject-plan-30064289707-1
artifact ID: 8585693830
digest: sha256:7aae2cff0df757a4b436c5b87507162624813e64bd32946bada8a87e5d7adc22
```

This proves functional authentication and read access for that run. It does not prove the exact effective Reader scopes or continued access at a later time.

## West US 2 candidate evidence

The human-observed Cloud Shell checks on `2026-07-24` reported:

```text
Total Regional vCPUs:                 0 / 10
Standard Falsv7 Family vCPUs:         0 / 10
Standard IPv4 Public IP addresses:    0 / 20
Standard_F1als_v7 restrictions:       []
vCPUs / memory:                       1 / 2 GiB
PremiumIO:                            True
```

The same session observed:

```text
Standard_B2ats_v2 Basv2 quota: 0 / 0
Standard_F2s_v2 restriction: NotAvailableForSubscription at westus2
```

These interactive observations select the next read-only planning candidate. They must be refreshed and promoted into a protected workflow artifact before any deployment decision.

## Planner sequence

```text
immutable main SHA
→ validate exact westus2 / Standard_F1als_v7 package
→ run repository tests
→ dependency OIDC login
→ verify dependency endpoint
→ target OIDC login
→ capture providers, policy, quotas, SKU, and target inventory
→ distinguish explicit ResourceGroupNotFound from observation failure
→ fail closed on unknown inventory or readiness failure
→ subscription validation with ProviderNoRbac
→ subscription What-If with ProviderNoRbac
→ classify exact create-only plan
→ upload evidence
→ stop
```

No step authorizes or performs deployment, cleanup, RBAC mutation, credential creation, guest commands, or endpoint promotion. This increment does not create GitHub environments, does not write GitHub secrets, and does not create Azure role assignments.

## Required planning evidence

An acceptable artifact must prove:

- both subscription contexts are distinct, Enabled, and tenant-aligned;
- the dependency resource group and endpoint are readable;
- Compute and Network providers are registered;
- `Standard_F1als_v7` is observed and unrestricted in `westus2`;
- Total Regional, Falsv7-family, and Standard IPv4 public-IP quota are sufficient;
- the target resource group is explicitly absent or its complete inventory is authoritative;
- ARM validation and What-If used `ProviderNoRbac`;
- the What-If contains only dedicated workload creates;
- `azure_mutations_performed=false`;
- `deployment_authorized=false`.

## Cost gate

Current subscription-specific invoice pricing, taxes, discounts, and actual monthly cost are not verified. The planner's CAD ceiling is not a price assertion. Deployment cannot be authorized until an evidence-bearing cost estimate is reviewed and accepted.

## Failure and rollback

Planning failures perform no Azure mutation. Fix the exact blocked condition and create a new evidence watermark.

Repository rollback is a PR revert. Removal of the GitHub environment, federated credentials, secrets, or RBAC assignments is a separate administrative change requiring explicit authorization.

## Deployment gate

A successful read-only planner does not authorize deployment. Deployment requires:

- exact reviewed commit binding;
- accepted protected What-If artifact;
- cost acceptance;
- least-privilege write identity review;
- rollback and cleanup procedure;
- post-deployment health, TLS, dependency, CORS, and browser validation;
- explicit human deployment authorization.
