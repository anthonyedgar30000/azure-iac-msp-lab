# Lab Factory read-only Azure preflight

## Purpose

This runbook validates whether the catalog-backed `servicetracer-demo-api@1.0.0` candidate is plausibly deployable in the selected Azure subscription before any ARM What-If or deployment is authorized.

```text
prepared request
  -> exact-commit workflow authorization
  -> Azure OIDC login
  -> fixed read-only observations
  -> subscription-scope ARM template validation
  -> sanitized evidence artifact
  -> stop for review
```

## Scope

The first version is deliberately fixed:

```text
profile: servicetracer-demo-api@1.0.0
environments: dev or test
location: westus2
VM size: Standard_F1als_v7
TTL: 1, 4, 8, 12, or 24 hours
currency: CAD
```

It checks:

- exact active subscription and enabled state;
- `westus2` in the subscription location catalog;
- registration of the resource providers actually used by the template;
- subscription-specific VM SKU restrictions;
- regional, VM-family, and Standard public-IP quota headroom;
- existing target resource-group state and resource count;
- effective candidate deployment actions at subscription scope;
- policy-assignment inventory as context;
- fixed-cost retail estimate for VM compute, one Standard public IP, and one 32-GiB Standard SSD OS disk;
- subscription-scope ARM template validation with synthetic non-secret values.

It does not run ARM What-If, create a deployment, register providers, change RBAC, create a resource group, or delete anything.

## Dispatch

After the workflow exists on `main`, open **Actions → Lab Factory read-only Azure preflight → Run workflow**.

Choose the environment, TTL, and CAD cost ceiling. Enter the exact reviewed commit. The confirmation must exactly match:

```text
OBSERVE-LAB-PREFLIGHT:servicetracer-demo-api:<environment>:<ttl>:<cost>:<reviewed-commit>
```

The workflow uses the existing `azure-lab` GitHub Environment and workload-identity secrets:

```text
AZURE_CLIENT_ID
AZURE_TENANT_ID
AZURE_SUBSCRIPTION_ID
```

No secret value is written to the evidence artifact.

## Expected evidence

The artifact name is:

```text
lab-factory-read-only-preflight-<run-id>-<attempt>
```

It contains `preflight-result.json` and `artifact-manifest.sha256`. The result contains fingerprints rather than raw subscription or tenant identifiers and never returns the synthetic parameter values.

A passing result ends at:

```text
status: passed
next_gate: what_if_review_required
azure_mutations_performed: false
arm_what_if_performed: false
deployment_authorized: false
cleanup_authorized: false
```

A blocked result is still useful evidence. The workflow uploads the receipt, then fails closed with one or more blockers such as SKU restriction, quota shortage, occupied resource group, missing provider registration, insufficient permissions, incomplete price context, or template-validation failure.

## Cost boundary

The CAD estimate covers fixed lab resources only:

```text
Linux VM hourly retail price
+ Standard static public IPv4 hourly retail price
+ prorated Standard SSD E4 LRS monthly retail price
```

Variable egress, taxes, negotiated discounts, credits, and subscription-specific billing adjustments are excluded.

```text
retail price estimate != actual billed cost
cost ceiling accepted != budget guarantee
```

## Failure and rollback

No Azure rollback or cleanup is required because the workflow performs no Azure mutation. Repository rollback is an exact PR revert. A failed or completed dispatch consumes only that exact run authority; it does not authorize a retry, What-If, deployment, cleanup, or RBAC change.

## Canonical boundaries

```text
preflight passed != ARM What-If reviewed
template validation passed != deployment authorized
permission check sufficient != effective least privilege verified
location allowed in catalog != current SKU capacity available
resource group safe != cleanup verified
```
