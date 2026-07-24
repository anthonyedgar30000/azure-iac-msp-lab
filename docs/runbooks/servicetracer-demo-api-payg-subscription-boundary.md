# ServiceTracer Demo API — Azure Plan Subscription Boundary

## Purpose

Move only the independent ServiceTracer demo API planning target to a dedicated Azure Plan subscription while preserving the existing Azure for Students lab as a read-only dependency source.

```text
dependency_subscription != deployment_target_subscription
pay_as_you_go_billing != unrestricted_quota
subscription_access != deployment_authority
ProviderNoRbac_what_if != deployment
```

## Intended boundary

```text
Azure for Students
└── rg-servicetracer-dev-westus2
    └── existing ServiceTracer HTTPS endpoint (read only)

Selected Azure Plan subscription
└── future rg-st-demo-api-dev-<region>
    └── independent API workload planning target
```

The planner uses two identities:

- dependency identity: Reader on `rg-servicetracer-dev-westus2` only;
- target identity: Reader on the selected Azure Plan subscription.

The target planner uses ARM `ProviderNoRbac` validation. This performs provider-backed validation and What-If while checking only read permissions. The workflow contains no deployment command.

## Repository workflow contract

Workflow:

```text
.github/workflows/servicetracer-demo-api-subproject-plan.yml
```

GitHub environment:

```text
azure-api-payg
```

Required environment secrets:

```text
AZURE_TENANT_ID
AZURE_DEPENDENCY_CLIENT_ID
AZURE_DEPENDENCY_SUBSCRIPTION_ID
AZURE_TARGET_CLIENT_ID
AZURE_TARGET_SUBSCRIPTION_ID
```

The dependency and target client IDs must differ. The dependency and target subscription IDs must differ. The workflow fails closed when either pair is identical.

## Manual setup boundary

This repository increment does not create GitHub environments, does not write GitHub secrets, does not create Microsoft Entra applications or federated credentials, and does not create Azure role assignments.

Before dispatch, an authorized human must:

1. Select one empty, active Azure Plan subscription as the API target and record its exact subscription ID.
2. Create the protected GitHub environment `azure-api-payg`.
3. Create or select two separate Microsoft Entra service principals in the same tenant.
4. Add a GitHub OIDC federated credential to each identity for:

   ```text
   repo:anthonyedgar30000/azure-iac-msp-lab:environment:azure-api-payg
   ```

5. Assign the dependency identity the Reader role at the smallest required scope:

   ```text
   /subscriptions/<dependency-subscription-id>/resourceGroups/rg-servicetracer-dev-westus2
   ```

6. Assign the target identity the Reader role on the selected Azure Plan subscription for the read-only planner.
7. Add the five environment secrets listed above.
8. Capture evidence showing the environment name, federated subjects, role scopes, subscription names, subscription states, and tenant alignment without exposing credentials or tokens.

## Planner sequence

```text
immutable main SHA
→ validate dual-subscription secret contract
→ run repository tests
→ dependency OIDC login
→ read dependency endpoint
→ target OIDC login
→ capture providers, inherited policy, quota, SKU restrictions, and target inventory
→ fail closed on unavailable SKU or insufficient regional cores
→ subscription validation with ProviderNoRbac
→ subscription What-If with ProviderNoRbac
→ classify exact create-only plan
→ upload evidence
→ stop
```

No step authorizes or performs deployment, cleanup, role assignment, credential creation, guest command execution, or endpoint promotion.

## Validation evidence

An acceptable planning artifact must prove:

- dependency and target subscriptions are distinct and Enabled;
- both subscription contexts use the expected tenant;
- the dependency resource group and public endpoint are readable;
- the selected target region has enough Total Regional vCPUs for the selected VM size;
- the selected VM size has at least one unrestricted regional SKU record;
- the target resource group is absent or contains only explicitly reconciled workload resources;
- ARM validation and What-If used `ProviderNoRbac`;
- the What-If contains only dedicated workload creates;
- `deployment_authorized` remains false.

## Failure and rollback

Planning failures perform no Azure mutation. Fix the missing identity, permission, quota, region, SKU, policy, or target-state condition and run a fresh planner against a new evidence watermark.

Repository rollback is a revert of the migration PR. GitHub environment removal, federated credential removal, and RBAC removal are separate authorized administrative actions.

## Deployment gate

A successful planner does not authorize deployment. A future deploy workflow requires a separate target deployment identity, explicit least-privilege write permissions, exact reviewed commit binding, approved What-If evidence, cost acceptance, rollback instructions, and explicit human authorization.
