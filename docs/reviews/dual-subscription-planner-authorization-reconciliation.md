# Dual-subscription planner authorization reconciliation

## Purpose

Record the difference between the repository state that reached `main` and the authority that was actually established for the independent ServiceTracer demo API planner.

```text
merged_state != authorized_state_transition
CI_success != architecture_ratification
read_only_design != permission_to_create_identity_or_RBAC
```

## Synchronized repository evidence

Observed default-branch sequence:

- PR #67 merge: `524be044dc94e59e42477964162f825d83710cb7`;
- PR #71 source head: `5b54fc63542836f42a530c5f644b97ccdd1020a7`;
- PR #71 exact-head CI run: `30061331939`, success;
- PR #71 stacked merge into the PR #68 branch: `dd9b33b6d849b0e3635b148159d7f484744ee77a`;
- stacked-head CI run: `30061412042`, success;
- PR #68 merge to `main`: `84a527a248964c907172b9af5ca3d5fab991c96d`;
- PR #70 source head: `2d8ced2dd27aa44009a4b39b2011f4babe2dbd7b`;
- PR #70 exact-head CI run: `30059328216`, success;
- PR #70 merge and newest observed main before reconciliation: `323b3892c6efd598231037f23281d49608ceb570`.

No open pull request was observed when the reconciliation branch was created.

## Scope expansion

PR #68 originally described a bounded credential-generation removal with two owned paths. Its previously reviewed exact head was:

```text
b4f225c71e9d93a27aa74f860e2882c8278cd7bf
```

Stacked PR #71 then added a broader architecture before PR #68 merged:

- dual subscriptions;
- isolated GitHub environment `azure-api-payg`;
- two OIDC identities;
- dependency Reader scope;
- target-subscription Reader scope;
- `ProviderNoRbac` validation and What-If;
- target policy, SKU, and quota evidence;
- repository default region changed from `westus2` to `eastus`.

The expanded head passed CI. It was not the same repository state as the earlier bounded head.

## Repository authority evidence

PR #71 explicitly stated:

```text
pull_request_merge_authorized = false
GitHub_environment_mutation_authorized = false
GitHub_secret_mutation_authorized = false
Entra_identity_mutation_authorized = false
Azure_RBAC_mutation_authorized = false
workflow_dispatch_authorized = false
Azure_authentication_authorized = false
Azure_mutations_authorized = false
```

Therefore the merge proves repository presence, not legitimate authorization for the architecture transition or its administrative prerequisites.

## Current merged planner design

```text
Azure for Students dependency subscription
└── rg-servicetracer-dev-westus2
    └── existing ServiceTracer HTTPS endpoint (read only)

Selected Azure Plan target subscription
└── future rg-st-demo-api-dev-<location>
    └── independent API workload planning target
```

The planner code:

- runs only from `refs/heads/main`;
- checks out `github.sha`;
- runs tests before Azure login;
- performs separate dependency and target OIDC logins;
- rejects identical client IDs and subscription IDs;
- captures provider, policy, quota, SKU, target, and dependency evidence;
- uses `ProviderNoRbac` for ARM validation and What-If;
- creates no private credential;
- contains no deployment or RBAC mutation command.

## Unresolved administrative state

The following remain unobserved and unauthorized:

- exact target Azure Plan subscription;
- acceptance of `eastus` versus the original `westus2` target;
- protected GitHub environment creation;
- environment secret writes;
- dependency identity and federated credential;
- target identity and federated credential;
- dependency Reader assignment;
- target Reader assignment;
- workflow dispatch;
- Azure authentication;
- independent-workload ARM validation or What-If.

## Azure evidence boundary

Newest promoted Azure evidence remains collector-hosted run `30053018998`:

- artifact ID `8581736555`;
- artifact digest `sha256:be58e1d9e9b3dda587209dfdf25a9b9f19aecf1a4ca4ffe08c9ac66e5c41d277`;
- Azure mutations authorized: false;
- Azure mutations performed: false;
- deployment authorized: false.

It is not evidence about the proposed Azure Plan target subscription.

## Reconciliation increment

This bounded repository-only increment changes exactly:

- `.project/active-work.json`;
- `.project/environment-state.json`;
- `.project/handoffs/current-state.md`;
- `.project/validate.py`;
- `docs/reviews/dual-subscription-planner-authorization-reconciliation.md`.

It records the merged architecture, preserves the authorization conflict, updates the newest promoted Azure evidence watermark, and makes architecture ratification the next gate.

It does not modify:

- the planner workflow;
- workload Bicep;
- API source or installer;
- GitHub environments or secrets;
- Entra identities or federated credentials;
- Azure RBAC;
- Azure resources;
- frontend endpoints.

## Required human decision

The human must explicitly choose one of these outcomes:

### Ratify the merged design

Accept the dual-subscription boundary, target subscription class, target region, environment name, identity split, and Reader scopes. Administrative setup then requires a separate explicit authorization.

### Reject or revise the merged design

Authorize a repository revert or replacement architecture. No Azure rollback is required because the independent planner has not been dispatched and the workload has not been deployed.

## Authority

```text
repository_reconciliation_authorized = true
pull_request_creation_authorized = true
pull_request_merge_authorized = false
architecture_ratification_complete = false
administrative_setup_authorized = false
workflow_dispatch_authorized = false
Azure_authentication_authorized = false
Azure_mutations_authorized = false
deployment_authorized = false
cleanup_authorized = false
endpoint_promotion_authorized = false
```
