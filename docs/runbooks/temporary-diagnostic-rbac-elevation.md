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

The observed ServiceTracer timeout-correction attempt already established a specific failure boundary:

- ARM validation succeeded;
- extension-only What-If succeeded;
- resource-group deployment submission was rejected because `Microsoft.Resources/deployments/write` was not effective;
- the existing VM extension remained in its prior successful state;
- the resource inventory remained seven;
- no workload mutation was proven.

The durable repository repair therefore remains the two-capability design already declared on `main`:

1. extension update permission at the exact extension resource;
2. deployment submission permission at the exact resource group.

The process in this runbook is available for future ambiguous incidents. It is not active authorization to elevate access for the current workload.

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
- A recorded original failure containing identity, scope, command or workflow, timestamp, correlation information, and exact error.
- A diagnostic hypothesis stated before activation.
- A separately approved test plan and, when applicable, separate mutation authority.
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
- no group, service-principal, or managed-identity substitution without a separate design review.

The operator must use their named user identity. Shared accounts are prohibited.

The account creating or configuring the eligible assignment requires separate administrative authority such as `Owner` or `User Access Administrator`. That administrative setup is not authorized by this runbook or by the inert request template.

## Network paths

No network topology, NSG, route, firewall, public endpoint, DNS, or private-link change is part of diagnostic elevation.

If the exact diagnostic test would alter network configuration, it requires a separate network-mutation authorization and is outside this ordinary process.

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
- Manually deactivate immediately after the test even when automatic expiry remains pending.
- Acquire another fresh session and verify broad access is no longer effective.
- Preserve evidence without exposing tenant IDs, subscription IDs, principal object IDs, tokens, or credentials.

## Cost, quota, and licensing implications

The role assignment itself does not create a recurring Azure workload resource. PIM requires qualifying Microsoft Entra licensing, which may carry licensing cost.

The diagnostic test can still trigger normal Azure charges if it creates or modifies billable resources. The test must therefore preserve an explicit resource-count boundary and prohibit unrelated resource creation.

No compute quota change is required merely to activate a role. The latest bounded ServiceTracer evidence observed regional vCPU usage of `1 / 10`; this is time-qualified evidence, not current quota truth.

## Diagnostic procedure

### 1. Preserve the original failure

Record:

- operator or workload identity type;
- affected subscription and resource group, using hashed identifiers in durable evidence;
- exact failed command or workflow run and immutable source;
- timestamp and correlation ID when available;
- exact denied action and scope;
- resource inventory and target-resource state;
- whether any mutation or partial mutation was observed.

Do not elevate first and reconstruct the failure later.

### 2. State the hypothesis

Example:

```text
The resource-group deployment wrapper fails because the executing identity lacks
Microsoft.Resources/deployments/write at rg-st-demo-api-dev-westus2.
```

The hypothesis must describe the expected difference between the baseline and elevated tests.

### 3. Approve a bounded request

Start from `.project/templates/temporary-diagnostic-rbac-elevation-request.example.json` and create a new, incident-specific authorization record.

The committed template is deliberately inert. A real request must identify:

- named human operator;
- exact resource group;
- role;
- one-hour expiry;
- exact test digest;
- whether the test is read-only or mutating;
- rollback or recovery boundary;
- required approver;
- evidence destination.

Repository documentation, CI, or this runbook do not authorize activation.

### 4. Activate through PIM

In Microsoft Entra Privileged Identity Management, activate the eligible Azure resource role for the shortest supported duration, no longer than one hour.

Supply the approved ticket reference and justification. Complete MFA and approval requirements. Confirm that the active assignment is scoped only to the intended resource group.

Do not substitute a normal standing role assignment when PIM is unavailable. Escalate instead.

### 5. Refresh and verify effective access

Use a fresh Azure CLI or portal authentication session after activation. Verify:

- expected tenant and subscription;
- exact resource-group scope;
- active time-bound role assignment;
- effective permissions;
- activation start and expiry;
- no broader assignment than approved.

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

There are two modes:

- `observe_only`: queries, validation, and What-If only;
- `single_exact_mutation`: one explicitly authorized mutation needed to cross the observed failure boundary.

A mutating test requires separate mutation authority. Broad role activation alone does not manufacture permission to mutate.

Do not retry automatically. A terminal result consumes the diagnostic grant.

### 7. Classify the result

| Baseline | Elevated test | Interpretation |
|---|---|---|
| failed | succeeded | Insufficient authorization is supported as a cause of the tested failure boundary. The minimum durable action remains unresolved until narrower testing succeeds. |
| failed | failed with same denial | The activation may be ineffective, stale, incorrectly scoped, or blocked by another authorization control. Stop and reobserve. |
| failed | failed differently | Authorization may have exposed the next failure boundary. Preserve both results; do not collapse them into success. |
| mutation observed outside the test boundary | any | Stop, treat as an operational incident, and follow the separately authorized rollback or recovery procedure. |

### 8. Terminate the elevation

Manually deactivate the PIM role immediately after the diagnostic test. Do not wait for automatic expiry merely because the test completed quickly.

Open a fresh authentication session and verify:

- the active assignment is absent or expired;
- broad effective actions are no longer present;
- the target resource group remains within the expected inventory boundary;
- no unrelated deployment, role, policy, network, or resource mutation occurred.

```text
deactivation_requested != access_terminated
assignment_expired != cached_access_immediately_absent
```

### 9. Design and verify the durable permission

Use the diagnostic evidence to test the narrowest candidate permission through a custom role, direct resource API, or constrained deployment architecture.

The permanent result is accepted only after the narrow permission is independently observed as effective and the intended operation succeeds without the broad elevation.

## Expected outputs and evidence

Capture a protected evidence package containing:

- original failure record;
- approved incident-specific authorization record;
- exact source or command digest;
- PIM activation request and approval metadata;
- hashed operator, tenant, and subscription identifiers;
- exact resource-group scope;
- effective permissions before activation, during activation, and after termination;
- resource inventories before and after;
- diagnostic command output and exit status;
- target-resource state before and after;
- mutation and rollback classification;
- activation, deactivation, and expiry timestamps;
- SHA-256 manifest for the package.

Do not commit raw protected PIM exports or unredacted identity values.

## Failure, rollback, and stop behavior

- PIM unavailable or unlicensed: stop; do not create standing broad access as an undocumented substitute.
- Eligible assignment missing: stop; PIM setup requires a separate administrative increment.
- Approval denied or expired: stop; do not bypass approval.
- Scope or identity mismatch: deactivate and stop before testing.
- Effective access not observed: refresh once, then stop if still unresolved.
- Diagnostic test fails: preserve evidence; no retry is implied.
- Unexpected mutation: invoke only a separately authorized rollback or recovery plan.
- Deactivation cannot be verified: escalate as an access-removal incident.

## Cleanup and decommissioning

A completed diagnostic session requires:

1. manual deactivation;
2. verification of inactive or expired assignment;
3. verification that broad effective permissions are absent after session refresh;
4. closure of the diagnostic authorization record as consumed;
5. evidence retention according to project policy.

The eligible assignment itself may remain only when it is an intentional, reviewed operational capability. Remove stale eligibility when the capability is no longer required.

## Authority boundary

Authorized by this repository increment:

- this runbook;
- an inert request template;
- deterministic repository tests;
- reconciliation documentation;
- draft pull request and ordinary CI.

Not authorized by this repository increment:

- PIM configuration;
- creation of an eligible or active assignment;
- `Contributor`, `Owner`, or `User Access Administrator` activation;
- Azure login or query;
- diagnostic execution;
- workload mutation;
- rollback, retry, cleanup, or PR merge.

## Microsoft references

- Eligible and time-bound role assignments in Azure RBAC: https://learn.microsoft.com/azure/role-based-access-control/pim-integration
- Configure Azure resource role settings in PIM: https://learn.microsoft.com/entra/id-governance/privileged-identity-management/pim-resource-roles-configure-role-settings
- Activate Azure resource roles in PIM: https://learn.microsoft.com/entra/id-governance/privileged-identity-management/pim-resource-roles-activate-your-roles
