# Timeout deployment submitter RBAC and workflow repair

## Observed terminal state

Exact-source workflow run `30178082566` at commit `10f0a0b1533cf739c93623b881549241ba9e67c3` passed exact-head CI, Azure login, VM-running verification, the seven-resource boundary, ARM validation, and extension-only What-If.

Azure rejected the resource-group deployment submission because the OIDC principal lacked:

```text
Microsoft.Resources/deployments/write
```

The accepted What-If still identified exactly one `Modify` operation against the existing `servicetracer-demo-api` VM extension. The deployment result and rollback result files were empty, the extension retained its prior successful state, and the before/after resource inventories were identical.

```text
deployment submission rejected != extension mutation
rollback command attempted != rollback performed
```

Evidence anchor:

```text
workflow run: 30178082566
artifact: 8624795161
artifact digest: sha256:8a29de9ca1cacb98c7d540d9361dbdf4f198b5d5df9ab8bb0328f5aedcb4059d
source head: 10f0a0b1533cf739c93623b881549241ba9e67c3
```

## Intended architecture

The deployment principal uses two independent least-privilege capabilities:

1. `ServiceTracer Demo API Extension Updater v1`, assigned at the exact extension resource, grants only `Microsoft.Compute/virtualMachines/extensions/write`.
2. `ServiceTracer Demo API Deployment Submitter v1`, assigned at `rg-st-demo-api-dev-westus2`, grants only `Microsoft.Resources/deployments/write` so ARM can create the deployment record that contains the separately restricted extension update.

The resource-group deployment permission does not grant arbitrary resource mutation. Actual target-resource mutation remains constrained by the extension-scoped role and must also pass the deterministic extension-only What-If assertion.

## Region and scope

```text
subscription: protected target subscription
region: westus2
resource group: rg-st-demo-api-dev-westus2
VM: vm-st-demo-api-mst-dev
extension: servicetracer-demo-api
expected resource count: 7 before and after
```

## Dependencies

- Existing GitHub OIDC service principal.
- Existing extension-updater custom role and assignment.
- Existing resource group, VM, Custom Script extension, public FQDN, and backend transaction endpoint.
- A separate human authorization for the RBAC mutation.
- Fresh effective-permission evidence after RBAC propagation.
- A separate later authorization for another exact-source deployment attempt.

## Identity and permissions

The proposed custom role contains one management-plane action:

```text
Microsoft.Resources/deployments/write
```

Assignment scope is the existing resource group. No data actions, wildcard actions, network rights, VM replacement rights, deletion rights, RBAC administration rights, or transaction replay authority are included.

The repaired deployment workflow queries Azure's effective-permissions endpoint and fails closed unless both required actions are observed:

```text
Microsoft.Resources/deployments/write
Microsoft.Compute/virtualMachines/extensions/write
```

Assignment declared != effective permission observed.

## Network paths

No network topology or firewall rule change is proposed. The workload deployment continues to use the existing public HTTPS health endpoint, existing GitHub raw-content installer path, and existing backend transaction URL. Transaction replay remains prohibited.

## Security controls

- Separate deployment-submission and target-resource mutation roles.
- Exact-commit authorization marker.
- Exact-head pull-request CI gate.
- OIDC authentication with no stored Azure credential.
- Effective-permission reobservation before ARM validation or deployment.
- Deterministic VM-running parser.
- Extension-only What-If assertion.
- Seven-resource before/after invariant.
- No transaction replay.
- Evidence artifact with SHA-256 manifest.

## Cost and quota implications

The custom role definition and assignment have no recurring Azure service charge. The workflow creates no additional recurring resource.

The failed-attempt artifact observed month-to-date cost of approximately CAD 2.842043785276267 across the VM, managed disk, and public IP. Cost data can lag and is neither a final invoice nor a forecast.

Observed quota evidence remained:

```text
regional vCPUs: 1 / 10
```

No quota increase is required for this repair.

## Deployment method

Repository preparation is performed through Bicep and a guarded bootstrap script. The script defaults to validation and What-If only. `--apply` is required for mutation and must be used only after separate explicit RBAC authorization.

The workload workflow in this increment is intentionally inert. It watches for a future authorization marker that is not present.

## Validation and expected outputs

Repository CI must establish:

- Bicep lint/build success.
- The custom role has exactly the deployment-write action.
- Assignment scope is the existing resource group.
- Permission evaluator accepts both required actions and rejects missing deployment-write evidence.
- Bootstrap defaults to plan-only behavior.
- The future workflow checks effective permissions before `az deployment group create`.
- Rollback fields distinguish required, attempted, submission accepted, and verified.
- No future deployment authorization marker exists.

RBAC deployment validation must later capture:

- subscription-scope validation result;
- What-If containing only one role definition and one role assignment, with no delete;
- deployment result if separately authorized;
- refreshed effective-permissions response after OIDC token renewal.

## Failure and rollback behavior

Repository failure: close the PR or revert its commits. No Azure rollback is required.

Future RBAC mutation failure: stop and preserve validation, What-If, and deployment evidence. Do not authorize the workload deployment.

Future workload deployment failure:

- a rejected deployment submission with no attempted `forceUpdateTag` observed requires no rollback;
- rollback is required only when the attempted extension tag is observed or the deployment submission succeeded but post-deployment verification failed;
- `rollback_attempted`, `rollback_submission_accepted`, and `rollback_verified` are recorded separately;
- failed rollback verification must never be represented as recovery.

## Cleanup and decommissioning

No cleanup is authorized in this increment.

A future decommission procedure would remove the resource-group role assignment first, verify the deployment principal no longer has effective deployment-write permission, and remove the custom role definition only after no assignments remain. The existing extension-updater role is independent and must not be removed as an accidental side effect.

## Authority boundary

Authorized now:

- repository Bicep, scripts, workflow preparation, tests, documentation, reconciliation, draft PR, and ordinary CI.

Not authorized now:

- RBAC mutation;
- another Azure deployment attempt;
- workflow rerun or dispatch;
- PR merge;
- transaction replay;
- network or resource mutation;
- cleanup.
