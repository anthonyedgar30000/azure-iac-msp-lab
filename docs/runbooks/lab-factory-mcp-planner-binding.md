# Lab Factory MCP planner binding

## Purpose

The `servicetracer-demo-api@1.0.0` catalog profile is prepared locally through the Azure MCP repository tools, but its canonical live planning path is the existing dual-subscription workflow:

```text
.github/workflows/servicetracer-demo-api-subproject-plan.yml
```

The MCP tools now return the planner binding, workflow digest, installer digest, input-source map, and the next human gate. They do not dispatch the workflow or contact Azure.

## Architecture

```text
list_lab_profiles / prepare_lab_request
                |
                v
lab_factory/catalog.json
                |
                +--> subscription-scoped Bicep template
                |
                +--> canonical planner binding
                         |
                         +--> dependency subscription / read-only
                         +--> target Pay-As-You-Go subscription / planning-only
                         +--> GitHub environment: azure-api-payg
                         +--> ProviderNoRbac validation
                         +--> ARM validation + FullResourcePayloads What-If
                         +--> no deployment command
```

## Planner-bound MCP result

A complete `prepare_lab_request` response changes the MCP-facing next gate to:

```text
planner_dispatch_review_required
```

The generic `lab_factory.prepare_lab_plan` and CLI remain prepare-only and continue to report `preflight_required`. This keeps the core planner reusable while making the MCP surface explicit about the ratified workflow.

The MCP planner object returns:

- repository-relative workflow and installer paths;
- SHA-256 digests for both files;
- `workflow_dispatch` as the trigger;
- `azure-api-payg` as the protected GitHub environment;
- the dual-subscription boundary;
- dependency access as read-only;
- target access as planning-only;
- `ProviderNoRbac` validation;
- ARM validation and What-If requirements;
- input names and provenance;
- `live_dispatch_authorized: false`;
- no supplied parameter values and no confirmation value.

## Input provenance

The workflow consumes or defaults these planner inputs:

```text
environment                 <- request.environment
location                    <- request.location
prefix                      <- fixed profile value
dependency_resource_group   <- workflow default
dns_label                   <- caller-supplied dnsLabel name
allowed_origin              <- caller-supplied allowedOrigin name
vm_size                     <- profile default
maximum_monthly_cost_cad    <- workflow default (CAD $25.00)
confirmation                <- derived by the human dispatch gate, never returned
```

The workflow derives the remaining Bicep parameters at execution time:

```text
backendTransactionUrl <- dependency-subscription public IP observation
adminSshPublicKey      <- fixed validation-only placeholder
sourceRepository       <- GitHub repository context
sourceRef              <- immutable dispatch SHA
installerUri           <- repository + dispatch SHA + canonical installer path
```

The prepared MCP result exposes only these source descriptions, never the resolved values.

## Identity and network boundary

The canonical workflow requires distinct workload identities and distinct subscriptions:

```text
Azure for Students dependency subscription
  -> read existing ServiceTracer dependency state

Pay-As-You-Go target subscription
  -> observe provider, policy, quota, SKU, and target resource-group state
  -> validate template
  -> run bounded ARM What-If
```

The binding increment performs none of those operations. It creates no credential, inbound path, resource group, role assignment, or Azure resource.

## Validation

Repository CI should run:

```bash
python -m unittest infra.tests.test_lab_factory_lite -v
python -m unittest infra.tests.test_azure_mcp_lab_factory_tools -v
python -m unittest infra.tests.test_lab_factory_local_mcp_smoke_contract -v
python scripts/smoke_test_lab_factory_mcp_stdio.py
```

Expected MCP assertions include:

```text
workflow path and SHA-256 observed
installer path and SHA-256 observed
subscription boundary = dual_subscription
GitHub environment = azure-api-payg
provider validation = ProviderNoRbac
ready_for_dispatch_review = true
live_dispatch_authorized = false
workflow_dispatch_performed = false
azure_queries_performed = false
azure_mutations_performed = false
deployment_authorized = false
parameter_values_returned = false
confirmation_value_returned = false
```

## Cost boundary

This repository increment has a recurring Azure cost delta of **CAD $0**. The workflow's default **CAD $25.00** monthly value is a planning ceiling, not a bill, quote, reserved capacity claim, or deployment authorization.

```text
planning ceiling != actual billed cost
planner ready != capacity reserved
```

## Failure and rollback

Missing workflow or installer files, invalid planner metadata, or digest drift fail closed before the MCP result is returned. Repository rollback is an exact revert of the binding pull request.

No Azure rollback or cleanup applies because this increment performs no workflow dispatch, Azure authentication, query, validation, What-If, mutation, or deployment.

## Next gate

After exact-head CI and a local stdio MCP smoke pass, recheck live `main` and merge the exact green source. A later live planner dispatch requires a separate explicit decision with exact inputs and confirmation.

```text
planner bound != workflow dispatched
workflow dispatched != ARM What-If accepted
ARM What-If accepted != deployment authorized
```
