# PR #104 protected deployment failure review

## Decision

Keep the existing Bicep template as the declarative review surface for ARM validation and extension-only What-If. Replace the write step and rollback step with a direct Azure Resource Manager `PUT` to the exact existing VM extension resource.

This preserves the narrow custom role already assigned at the extension scope:

```text
Microsoft.Compute/virtualMachines/extensions/write
```

It avoids adding the broader resource-group deployment permission required only by the wrapper command:

```text
Microsoft.Resources/deployments/write
```

## Observed execution

```text
protected run: 30178082566 / failure
source: 10f0a0b1533cf739c93623b881549241ba9e67c3
exact-head CI: 30178095309 / success
artifact: 8624795161
artifact digest: sha256:8a29de9ca1cacb98c7d540d9361dbdf4f198b5d5df9ab8bb0328f5aedcb4059d
```

The parser-safe preflight worked. Azure login, current-state observation, ARM validation, and extension-only What-If succeeded. The forward operation failed before extension mutation because `az deployment group create` attempted to create a `Microsoft.Resources/deployments` resource and the target identity did not have `Microsoft.Resources/deployments/write`.

The workflow then used the same wrapper for rollback, so rollback failed at the same authorization boundary. Resource inventory remained seven resources. No corrected post-deployment health contract was observed.

## Corrected method

The prepared workflow will:

1. validate a fresh exact-source authorization marker;
2. require successful exact-head pull-request CI;
3. authenticate to the protected target subscription;
4. refresh subscription, tenant, resource group, inventory, VM state, quota, cost status, and public health evidence;
5. run Bicep ARM validation and extension-only What-If;
6. construct a deterministic VM extension create-or-update payload outside the uploaded evidence directory;
7. call the Compute extension resource directly with `az rest --method put`;
8. verify extension provisioning state, the corrected public health contract, and the seven-resource boundary;
9. use the same direct extension `PUT` method for rollback if verification fails;
10. upload a SHA-256 evidence manifest regardless of outcome.

## Safety boundaries

```text
repository repair != deployment authorized
direct extension PUT != unrestricted resource-group mutation
protected settings payload generated != payload published as evidence
forward PUT attempted != corrected runtime verified
rollback PUT attempted != rollback verified
```

Transaction replay, PR merge, RBAC mutation, network mutation, VM replacement, resource creation outside the existing extension, publication, and cleanup remain excluded.

## Authorization state

PR #104's grant is consumed. The prepared workflow is inert until a new exact-commit authorization marker is separately approved and added. No workflow rerun or Azure operation is authorized by this review.
