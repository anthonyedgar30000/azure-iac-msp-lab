# Post-merge reality synchronization — PRs #75 and #77

Date: `2026-07-24`

## Bounded objective

Reconcile repository reality immediately after PRs #75 and #77 merged without converting a current code declaration into protected Azure evidence or allowing the older protected planner run to overwrite the newly merged package.

This increment is repository-only. It does not dispatch a workflow, authenticate to Azure, run ARM validation or What-If, mutate Azure, deploy, clean up, or promote an endpoint.

## Live repository observation

The observed default-branch head is:

```text
0d364dac63fb948c4912e04a2f420df4451189cb
```

It contains:

- PR #75 merge `1ae445831668131f495f39f4d887822885fc1ec0`;
- PR #77 merge `0d364dac63fb948c4912e04a2f420df4451189cb`;
- no open pull request observed at the synchronization watermark.

Exact source-head checks had passed before merge:

```text
PR #75 head: 118c0f7167715d6b6e78184d396afacc33408ae8
CI: 30071058351 success

PR #77 head: 2f503bfdc91c4cb37c067fe0205c9b115d23c862
CI: 30070811160 success
Azure MCP synchronization: 30070810759 success
```

## Current repository declaration

The merged planner workflow and Bicep root now agree on:

```text
location = westus2
vm_size = Standard_F1als_v7
target_resource_group = rg-st-demo-api-dev-westus2
github_environment = azure-api-payg
provider_validation_level = ProviderNoRbac
```

The planner contains no deployment command and remains read-only planning infrastructure.

## Detected project-state conflict

The shared files `.project/active-work.json`, `.project/environment-state.json`, and `.project/handoffs/current-state.md` still describe the consumed protected run:

```text
location = eastus
vm_size = Standard_B2ats_v2
run = 30064289707
```

Those claims remain valid historical evidence for that exact run. They are not current repository declarations after PR #75.

The correct state is therefore typed as:

```text
current repository package = westus2 / Standard_F1als_v7
latest protected Azure package = eastus / Standard_B2ats_v2
verification_status = conflicting
```

This is not a contradiction about one event. It is a scope and freshness conflict between a current declaration and historical runtime evidence.

```text
historical_protected_evidence != current_repository_declaration
declared_in_code != deployed_in_azure
manual_cloud_shell_observation != protected_workflow_artifact
```

## Azure boundary

No protected planner has yet tested `westus2` and `Standard_F1als_v7`.

Current claims remain:

```text
protected_westus2_f1alsv7_evidence = false
target_resource_group_state = not_observed_by_protected_workflow
cost_verified = false
ARM_validation_performed = false
What_If_performed = false
deployed = false
service_verified = false
```

The Cloud Shell observations are useful candidate evidence, but they do not reserve quota, establish current price, prove resource-group absence, or authorize deployment.

## Authority

```text
repository_reconciliation_authorized = true
pull_request_creation_authorized = true
pull_request_merge_authorized = false
workflow_dispatch_authorized = false
Azure_authentication_authorized = false
Azure_WhatIf_authorized = false
Azure_mutations_authorized = false
deployment_authorized = false
cleanup_authorized = false
endpoint_promotion_authorized = false
```

The control message `proceed` authorizes execution of the already bounded repository-reconciliation step. It does not silently grant a new Azure-login or workflow-dispatch authority.

## Exact next gate

After this reconciliation is reviewed and merged, resolve the new `main` SHA and issue a separate exact authorization for the read-only planner with:

```text
environment: dev
location: westus2
prefix: mst
dependency resource group: rg-servicetracer-dev-westus2
target resource group: rg-st-demo-api-dev-westus2
DNS label: st-demo-api-vm-aeg30000
allowed origin: https://anthonyedgar30000.github.io
VM size: Standard_F1als_v7
maximum monthly cost ceiling: CAD 25.00
confirmation: PLAN-DEMO-API-SUBPROJECT:dev:st-demo-api-vm-aeg30000
```

A successful planner run would still not authorize deployment.

## Rollback

Close or revert this repository-only increment. No Azure rollback is required because no Azure operation is performed.
