# ServiceTracer demo API extension-updater RBAC bootstrap

## Objective

Grant the existing GitHub OIDC target service principal exactly one missing Azure control-plane action:

```text
Microsoft.Compute/virtualMachines/extensions/write
```

The role assignment is scoped to the existing resource:

```text
rg-st-demo-api-dev-westus2
└─ vm-st-demo-api-mst-dev
   └─ extensions/servicetracer-demo-api
```

This bootstrap does not deploy application code, restart the VM, invoke Run Command, change networking, publish GitHub Pages, replay transactions, merge a pull request, or clean up resources.

## Architecture and identity

The target principal is not entered manually. The bootstrap resolves the unique `ServicePrincipal` that already holds `ServiceTracer Demo API What-If Planner v1` at the target resource-group hierarchy. The script fails closed when zero or multiple principals match.

A custom role named `ServiceTracer Demo API Extension Updater v1` is declared through Bicep with stable role GUID `a94875a8-373d-531e-bfe0-b213fd936082`.

Its only action is:

```text
Microsoft.Compute/virtualMachines/extensions/write
```

The role definition is assignable only within `rg-st-demo-api-dev-westus2`. The assignment itself is attached only to the existing `servicetracer-demo-api` VM extension.

## Dependencies and authority

Required operator authority:

- an authenticated Azure human identity in the target tenant and subscription;
- `Microsoft.Authorization/roleDefinitions/write` over the role's resource-group assignable scope;
- `Microsoft.Authorization/roleAssignments/write` at the exact extension resource;
- read access to the resource group, VM, extension, role definitions, and role assignments.

Owner or User Access Administrator normally satisfies the RBAC bootstrap prerequisites. The GitHub OIDC target identity cannot bootstrap itself.

## Cost and quota

The role definition and role assignment have no direct recurring Azure resource charge. This bootstrap creates no compute, disk, public IP, networking, or backup resource and consumes no regional compute quota.

## Plan

From Azure Cloud Shell at the repository root:

```bash
export TARGET_SUBSCRIPTION_ID="$(az account show --query id -o tsv)"
bash scripts/bootstrap_servicetracer_extension_updater_rbac.sh --plan
```

Expected result:

```json
{
  "status": "planned_not_applied",
  "azure_mutation_performed": false
}
```

The What-If assertion permits only:

- `Microsoft.Authorization/roleDefinitions`;
- `Microsoft.Authorization/roleAssignments`;
- change types `Create`, `Modify`, `NoChange`, or `Ignore`;
- at most two mutating RBAC resources;
- no deletion;
- no role assignment outside the exact VM-extension scope.

## Apply

After reviewing the plan:

```bash
export TARGET_SUBSCRIPTION_ID="$(az account show --query id -o tsv)"
bash scripts/bootstrap_servicetracer_extension_updater_rbac.sh --apply
```

The script records only SHA-256 hashes of subscription, tenant, and principal identifiers in its preflight summary.

Expected final state:

```text
custom role exists = true
custom role action set = extension write only
custom role assignable scope = target resource group
assignment principal = existing target OIDC service principal
assignment scope = existing VM extension
application deployment performed = false
effective target-identity permission verified = false
```

## Validation

Validate the Azure objects:

```bash
az role definition list \
  --name "ServiceTracer Demo API Extension Updater v1" \
  --query '[0].{id:id,actions:permissions[0].actions,assignableScopes:assignableScopes}' \
  -o json

EXTENSION_ID="$(az vm extension show \
  -g rg-st-demo-api-dev-westus2 \
  --vm-name vm-st-demo-api-mst-dev \
  -n servicetracer-demo-api \
  --query id -o tsv)"

az role assignment list \
  --scope "$EXTENSION_ID" \
  --role "ServiceTracer Demo API Extension Updater v1" \
  --all -o json
```

Assignment existence does not prove effective authorization. A separate protected GitHub OIDC preflight must establish that ARM validation and extension-only What-If now pass.

## Failure and rollback

If the subscription, tenant, resource group, VM, extension, planner role, or target principal cannot be resolved exactly, the script exits before mutation.

If What-If contains any non-RBAC resource, deletion, or role assignment outside the extension scope, the script exits before mutation.

For rollback after a successful bootstrap:

1. Resolve the exact assignment at the extension resource.
2. Delete only that assignment.
3. Confirm no assignments still reference role GUID `a94875a8-373d-531e-bfe0-b213fd936082`.
4. Delete the custom role definition only when its assignment count is zero.
5. Capture role-definition and assignment listings after rollback.

Rollback of this RBAC bootstrap does not require an application or VM rollback because it changes no workload configuration.

## Evidence

The script writes a timestamped directory under:

```text
~/servicetracer-extension-updater-rbac-evidence/
```

Capture:

- preflight summary;
- inherited role-assignment input used to resolve the target principal;
- complete What-If response;
- bounded What-If assessment;
- deployment response;
- post-apply role definition;
- post-apply role assignment;
- deny-assignment query or its typed observation failure;
- final result;
- SHA-256 artifact manifest.

Do not commit raw tenant, subscription, or principal identifiers.
