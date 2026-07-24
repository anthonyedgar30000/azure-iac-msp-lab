# Current project handoff

## Interpretation boundary

This handoff records durable repository and evidence claims reviewed on `2026-07-24`. It is not a live GitHub or Azure dashboard.

```text
merged_state != authorized_state_transition
repository_implemented != Azure_planned
read_only_plan != deployment_authorization
not_observed != false
resource_exists != service_healthy
```

Resolve live GitHub, exact-head CI, current authorization, Azure subscription context, quotas, costs, target resources, and dependency state before every consequential operation.

## Repository synchronization watermark

The newest observed default-branch commit before this reconciliation branch was created was:

```text
323b3892c6efd598231037f23281d49608ceb570
```

That commit merged PR #70 after PR #68 had already merged.

No open pull request was observed when this reconciliation branch was created.

## Verified repository sequence

The independent application architecture was established through:

- PR #65, source head `1be38682bf382bb70a585522d9e8c193beb89937`;
- exact-head CI run `30055579796`, success;
- merge commit `e3364b9cb918bf5aef23eab011d2a168183b3442`.

The VM-size contract was corrected through:

- PR #66, source head `540c19e394e4a13e86ad89327aeb17a3f4cb8f2a`;
- exact-head CI run `30058073866`, success;
- merge commit `9fd2af042d0ee1be28b61c8e9c26939ee98c319e`;
- default VM size `Standard_B2ats_v2`.

Project state was normalized through PR #67 at merge commit `524be044dc94e59e42477964162f825d83710cb7`.

Historical Azure evidence was promoted through PR #70:

- source head `2d8ced2dd27aa44009a4b39b2011f4babe2dbd7b`;
- exact-head CI run `30059328216`, success;
- merge commit `323b3892c6efd598231037f23281d49608ceb570`.

## Dual-subscription merge reality

PR #68 originally declared a two-path credential-boundary correction. The exact head previously reviewed for that bounded objective was:

```text
b4f225c71e9d93a27aa74f860e2882c8278cd7bf
```

CI run `30058896278` passed for that head.

Before PR #68 reached `main`, stacked PR #71 expanded the branch into a dual-subscription planning architecture.

PR #71 evidence:

- base: PR #68 branch;
- source head: `5b54fc63542836f42a530c5f644b97ccdd1020a7`;
- exact-head CI run: `30061331939`, success;
- stacked merge commit: `dd9b33b6d849b0e3635b148159d7f484744ee77a`;
- exact stacked-head CI run: `30061412042`, success.

PR #68 then merged the expanded head to `main` at:

```text
84a527a248964c907172b9af5ca3d5fab991c96d
```

The repository now physically contains the dual-subscription design. That observation does not establish that the architecture transition was legitimately authorized.

## Authorization conflict

PR #71 explicitly recorded:

```text
pull_request_merge_authorized = false
GitHub_environment_mutation_authorized = false
GitHub_secret_mutation_authorized = false
Entra_identity_mutation_authorized = false
Azure_RBAC_mutation_authorized = false
workflow_dispatch_authorized = false
Azure_authentication_authorized = false
```

The merged PR #68 head also differed from the earlier exact two-path head reviewed for merge.

Therefore:

```text
code_present_on_main = true
exact_head_CI_passed = true
human_ratification_of_expanded_architecture = unresolved
administrative_setup_authorized = false
planner_dispatch_authorized = false
```

Do not infer authorization from merge completion.

## Current repository planning design

The merged planner now models:

```text
Azure for Students dependency subscription
└── rg-servicetracer-dev-westus2
    └── existing ServiceTracer HTTPS endpoint (read only)

Selected Azure Plan target subscription
└── future rg-st-demo-api-dev-<location>
    └── independent API workload planning target
```

The workflow expects:

- protected GitHub environment `azure-api-payg`;
- separate dependency and target OIDC identities;
- dependency Reader scope limited to `rg-servicetracer-dev-westus2`;
- target Reader scope at the selected Azure Plan subscription;
- ARM validation and What-If with `ProviderNoRbac`;
- no deployment command;
- no planner-time private-key generation.

The merged workflow default location is `eastus`.

The original independent-subproject handoff requested `westus2`.

This location change requires explicit human resolution.

## Administrative prerequisites

The following are repository expectations only and are not observed or authorized:

- selecting an exact Azure Plan target subscription;
- accepting `eastus` or choosing another target region;
- creating the `azure-api-payg` GitHub environment;
- writing environment secrets;
- creating or selecting two Entra identities;
- adding GitHub OIDC federated credentials;
- assigning dependency Reader access;
- assigning target Reader access.

```text
runbook_present != setup_completed
setup_required != setup_authorized
Reader_role != mutation_authority
ProviderNoRbac_WhatIf != deployment
```

## Independent workload Azure state

The target subscription, resource group, VM, VNet, subnet, NSG, NIC, public IP, DNS, TLS, Nginx, loopback API, dependency call, CORS, rate limiting, frontend integration, and operational behavior remain:

```text
not_observed
```

The independent planner has not been dispatched.

No Azure authentication or independent-workload What-If has been performed by this workstream.

## Newest authenticated Azure evidence

The newest promoted Azure evidence remains historical collector-hosted run `30053018998`:

- exact run head: `46821092a6d196cc08279d3d79b09ae613a09b2a`;
- artifact: `collector-demo-api-30053018998-1`;
- artifact ID: `8581736555`;
- artifact digest: `sha256:be58e1d9e9b3dda587209dfdf25a9b9f19aecf1a4ca4ffe08c9ac66e5c41d277`;
- generated at: `2026-07-23T23:24:05Z`;
- `azure_mutations_authorized=false`;
- `azure_mutations_performed=false`;
- `deployment_authorized=false`.

It observed collector-hosted residue and rejected a public-IP Modify fail closed. It is not a dual-subscription independent-workload plan.

## Legacy residue boundary

Separate cleanup scopes remain:

- `pip-st-demo-api-mst-dev`;
- collector-hosted HTTP and HTTPS operations-NSG rules;
- `appi-demo-api-mst-dev`;
- `storfxczr3fewce`;
- synthetic backend VMs;
- any additional evidence-backed residue found later.

Do not delete, modify, reuse, or declare these healthy. Cleanup requires separate evidence and explicit destructive authorization.

## Current authority

```text
repository_reconciliation_authorized = true
pull_request_creation_authorized = true
pull_request_merge_authorized = false
architecture_ratification_complete = false
GitHub_environment_mutation_authorized = false
GitHub_secret_mutation_authorized = false
Entra_identity_mutation_authorized = false
Azure_RBAC_mutation_authorized = false
workflow_dispatch_authorized = false
Azure_authentication_authorized = false
Azure_WhatIf_authorized = false
Azure_deployment_authorized = false
Azure_cleanup_authorized = false
guest_commands_authorized = false
endpoint_promotion_authorized = false
```

## Genuine human gate

The next decision is not planner dispatch.

The human must choose one of two bounded outcomes:

### Ratify

Explicitly accept:

1. the dual-subscription dependency/target boundary;
2. use of a selected Azure Plan subscription;
3. the target region, including whether `eastus` replaces the original `westus2` request;
4. the protected environment name `azure-api-payg`;
5. two separate OIDC identities;
6. the exact Reader role scopes;
7. a later separately authorized administrative setup increment.

### Reject or revise

Explicitly authorize a repository rollback or replacement design. A repository revert does not delete Azure resources because this design has not been dispatched or deployed.

Only after architecture ratification and a separate administrative-setup authorization may the exact read-only planner dispatch package be prepared.
