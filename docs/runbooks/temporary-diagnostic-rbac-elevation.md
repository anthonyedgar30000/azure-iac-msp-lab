# Temporary diagnostic RBAC elevation

## Purpose

This runbook defines an optional, fail-closed troubleshooting technique for ambiguous Azure authorization failures:

> Temporarily activate a broader role at the narrowest practical scope, execute one predeclared diagnostic test, terminate the elevation, and then design the durable least-privilege permission from the resulting evidence.

Temporary broad access is diagnostic evidence. It is not the permanent authorization design.

```text
temporary_broad_access_succeeds != broad_access_required_permanently
RBAC_assignment != effective_least_privilege
failure_disappears != root_cause_fully_proven
```

## Current ServiceTracer boundary

The consumed ServiceTracer timeout-correction attempt established a specific failure boundary:

- ARM validation succeeded;
- extension-only What-If succeeded;
- the resource-group deployment wrapper was rejected because `Microsoft.Resources/deployments/write` was not effective;
- the existing VM extension remained in its prior successful state;
- the resource inventory remained seven;
- no workload mutation was proven.

The current preferred retry path declared on `main` is therefore:

1. retain Bicep validation and extension-only What-If;
2. build the exact existing Custom Script extension payload deterministically;
3. perform forward and rollback writes with a direct Compute API `PUT` to the exact extension resource;
4. rely only on the already-bounded `Microsoft.Compute/virtualMachines/extensions/write` capability.

The earlier deployment-submitter package remains repository history, but the direct-PUT path does not require `Microsoft.Resources/deployments/write` and must not broaden RBAC merely to preserve the wrapper.

```text
resource_group_wrapper_failed != extension_write_failed
wrapper_permission_available != wrapper_permission_required_for_durable_design
narrow_direct_path_available != broad_diagnostic_test_required_now
```

Temporary diagnostic elevation remains available for future ambiguous incidents. It is not active authorization for the current workload, and it is not needed to explain the already-isolated wrapper failure.

## Intended architecture

The preferred diagnostic identity is a named human operator with an eligible Microsoft Entra Privileged Identity Management assignment for the built-in `Contributor` role at the exact affected resource group.

```text
human operator
→ PIM eligible assignment
→ Contributor
→ exact affected resource group
→ one-hour maximum activation
→ one exact diagnostic test
→ manual deactivation or automatic expiry
→ fresh effective-access verification
```

`Contributor` is broad enough to isolate many resource-management authorization failures but cannot grant Azure RBAC access. `Owner` and `User Access Administrator` are excluded from this ordinary diagnostic process.

Eligible PIM activation is for human users. Service principals and managed identities cannot perform the interactive activation steps. Automation identities must retain separately designed, narrow, noninteractive permissions.

## Region and resource scope

For the current bounded example:

```text
subscription: protected target subscription
region: westus2
resource group: rg-st-demo-api-dev-westus2
VM: vm-st-demo-api-mst-dev
extension: servicetracer-demo-api
expected resource count: 7
```

The activation scope must equal the exact affected resource group. Subscription, management-group, tenant, or adjacent-resource-group scope is prohibited unless separately justified and authorized.

## Dependencies

- Microsoft Entra ID P2 or Microsoft Entra ID Governance licensing for PIM.
- A pre-existing eligible assignment for the named human operator.
- PIM role settings configured for the exact role and resource group.
- A preserved original failure with identity, scope, immutable source, timestamp, correlation information, exact error, target state, and mutation classification.
- One falsifiable diagnostic hypothesis stated before activation.
- A separately approved test plan and, when applicable, separate mutation and rollback authority.
- A reliable operator able to terminate and verify the elevation.

License availability and current PIM configuration are not established by this repository increment.

## Identity and permissions

Required PIM controls for the resource-group `Contributor` role:

- activation maximum duration: one hour;
- multifactor authentication;
- business justification;
- ticket or change reference;
- approval by a separate approver where practical;
- activation and assignment notifications;
- no permanent active assignment;
- no shared account, service-principal, or managed-identity substitution.

The account configuring eligibility requires separate administrative authority such as `Owner` or `User Access Administrator`. This runbook and its inert template do not grant that authority.

## Network paths

No network topology, NSG, route, firewall, public endpoint, DNS, or private-link change is part of diagnostic elevation.

A test that changes network configuration requires a separate network-mutation authorization and falls outside this ordinary process.

## Security controls

- Capture the original failure before changing access.
- State one falsifiable authorization hypothesis.
- Use the exact resource group and named operator.
- Prefer `Contributor`; do not use `Owner` as a convenience role.
- Limit activation to one hour and one test attempt.
- Bind the test to an exact command, workflow source SHA, or SHA-256 digest.
- Acquire a fresh authentication session after activation.
- Inspect effective permissions before the diagnostic test.
- Stop on any scope, identity, role, source, approval, or evidence mismatch.
- Do not explore unrelated resources while elevated.
- Manually deactivate immediately after the test.
- Acquire another fresh session and verify broad access is no longer effective.
- Preserve evidence without exposing tenant IDs, subscription IDs, principal object IDs, tokens, or credentials.

## Cost, quota, and licensing implications

The role assignment itself does not create a recurring Azure workload resource. PIM requires qualifying Microsoft Entra licensing, which may carry licensing cost.

The diagnostic test can still trigger ordinary Azure charges if it creates or modifies billable resources. The test must preserve an explicit resource-count boundary and prohibit unrelated resource creation.

No compute quota change is required merely to activate a role. The latest bounded ServiceTracer evidence observed regional vCPU usage of `1 / 10`; that is time-qualified evidence, not current quota truth.

## Diagnostic procedure

### 1. Preserve the original failure

Record the identity type, exact scope, immutable source, timestamp, denied action, correlation ID when available, resource inventory, target-resource state, and whether any mutation was observed.

Do not elevate first and reconstruct the failure later.

### 2. State the hypothesis

Example:

```text
The resource-group deployment wrapper fails because the executing identity lacks
Microsoft.Resources/deployments/write at rg-st-demo-api-dev-westus2.
```

The hypothesis must describe the expected difference between baseline and elevated tests.

### 3. Approve a bounded request

Start from `.project/templates/temporary-diagnostic-rbac-elevation-request.example.json` and create a new incident-specific authorization record.

The committed template is deliberately inert. A real request must identify the named operator, exact resource group, role, one-hour expiry, exact test digest, test mode, rollback boundary, approver, and evidence destination.

Repository documentation, CI, or this runbook do not authorize activation.

### 4. Activate through PIM

In Microsoft Entra Privileged Identity Management, activate the eligible Azure resource role for the shortest supported duration, no longer than one hour.

Supply the approved ticket reference and justification, complete MFA and approval, and confirm that the assignment is scoped only to the intended resource group.

Do not substitute a normal standing role assignment when PIM is unavailable. Escalate instead.

### 5. Refresh and verify effective access

Use a fresh Azure CLI or portal authentication session. Verify the expected tenant, subscription, exact scope, time-bound assignment, activation expiry, and effective permissions.

Example read-only observations:

```bash
az account show --query '{subscription:id,tenant:tenantId,state:state}' -o json

scope="$(az group show --name rg-st-demo-api-dev-westus2 --query id -o tsv)"

az rest \
  --method get \
  --uri "${scope}/providers/Microsoft.Authorization/permissions?api-version=2022-04-01" \
  --output json
```

Hash or redact protected identifiers before durable publication.

### 6. Execute one exact diagnostic test

Run only the command, workflow, or API operation bound to the approved digest.

- `observe_only`: queries, validation, and What-If only;
- `single_exact_mutation`: one explicitly authorized mutation needed to cross the observed failure boundary.

A mutating test requires separate mutation authority. Broad role activation alone does not manufacture permission to mutate.

Do not retry automatically. A terminal result consumes the diagnostic grant.

### 7. Classify the result

| Baseline | Elevated test | Interpretation |
|---|---|---|
| failed | succeeded | Insufficient authorization is supported as a cause of the tested boundary. The minimum durable action remains unresolved until narrower testing succeeds. |
| failed | same denial | Activation may be ineffective, stale, incorrectly scoped, or blocked by another control. Stop and reobserve. |
| failed | different failure | Elevation may have exposed the next boundary. Preserve both results; do not call this success. |
| unexpected mutation | any | Stop, treat as an operational incident, and use only separately authorized rollback or recovery. |

### 8. Terminate the elevation

Manually deactivate immediately after the test. Open a fresh authentication session and verify the assignment is absent or expired, broad effective actions are absent, inventory remains bounded, and no unrelated mutation occurred.

```text
deactivation_requested != access_terminated
assignment_expired != cached_access_immediately_absent
```

### 9. Design and verify the durable permission

Test the narrowest candidate through a custom role, direct resource API, or constrained deployment architecture.

A durable result is accepted only after the narrow permission is independently observed as effective and the intended operation succeeds without broad elevation.

## Expected outputs and evidence

Capture a protected package containing:

- original failure record;
- incident-specific authorization record;
- exact source or command digest;
- PIM activation and approval metadata;
- hashed operator, tenant, and subscription identifiers;
- exact scope;
- effective permissions before, during, and after elevation;
- inventories and target state before and after;
- diagnostic output and exit status;
- mutation and rollback classification;
- activation, deactivation, and expiry timestamps;
- SHA-256 manifest.

Do not commit raw protected PIM exports or unredacted identity values.

## Failure, rollback, and stop behavior

- PIM unavailable or unlicensed: stop; do not create standing broad access.
- Eligible assignment missing: stop; setup requires a separate administrative increment.
- Approval denied or expired: stop; do not bypass approval.
- Scope or identity mismatch: deactivate and stop before testing.
- Effective access not observed: refresh once, then stop if unresolved.
- Diagnostic test fails: preserve evidence; no retry is implied.
- Unexpected mutation: invoke only a separately authorized rollback or recovery plan.
- Deactivation cannot be verified: escalate as an access-removal incident.

## Cleanup and decommissioning

A completed session requires manual deactivation, fresh-session verification that the assignment and broad effective access are absent, closure of the authorization as consumed, and protected evidence retention.

The eligible assignment may remain only when it is an intentional, reviewed operational capability. Remove stale eligibility when the capability is no longer required.

## Authority boundary

Authorized by this repository increment:

- runbook and inert request template;
- deterministic repository tests;
- reconciliation documentation;
- ordinary CI.

Not authorized by this repository increment:

- PIM configuration;
- creation of an eligible or active assignment;
- `Contributor`, `Owner`, or `User Access Administrator` activation;
- Azure login or query;
- diagnostic execution or workload mutation;
- rollback, retry, cleanup, or PR merge.

## Microsoft references

- Eligible and time-bound role assignments in Azure RBAC: https://learn.microsoft.com/azure/role-based-access-control/pim-integration
- Configure Azure resource role settings in PIM: https://learn.microsoft.com/entra/id-governance/privileged-identity-management/pim-resource-roles-configure-role-settings
- Activate Azure resource roles in PIM: https://learn.microsoft.com/entra/id-governance/privileged-identity-management/pim-resource-roles-activate-your-roles
