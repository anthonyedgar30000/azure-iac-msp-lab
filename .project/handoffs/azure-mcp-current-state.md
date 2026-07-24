# Azure MCP reality bridge handoff

## Interpretation boundary

This handoff records the Azure MCP workstream after rebasing its reconciliation onto current repository reality. It is not a live Azure or ChatGPT connection report.

```text
contract_merged != endpoint_deployed
client_available != client_connected
tool_advertised != tool_authorized
planner_evidence_preserved != Azure_MCP_runtime_observed
rebase_completed != deployment_authorized
```

## Repository anchors

The governed Azure MCP contract reached `main` through PR #74:

```text
PR: 74
source head: 514549fd2c052ea44409b2a221113cc8c1cc0798
merge commit: cb310345c4ed42bece42db4e67a442498b7eba8f
CI: 30068916201
contract CI: 30068916240
```

The reconciliation is integrated on top of the newer repository baseline established by PR #76:

```text
main: 551ca0ee2c7d1955b3bd81c09f46f43dceeae3a6
merged PR: 76
source head: 1ca93552ae1a445922248ff4409706e203609f70
exact-head CI: 30069778338
```

## Concurrent planner evidence preserved

PR #76 promoted independent planner run `30064289707` and artifact `8585693830`.

The Azure MCP reconciliation does not replace these claims:

```text
Azure_authentication_succeeded = true
requested_location = eastus
requested_VM_size = Standard_B2ats_v2
requested_candidate_ready = false
target_resource_group_state = not_observed
ARM_validation_performed = false
What_If_performed = false
Azure_mutations_performed = false
deployed = false
service_verified = false
```

The planner artifact digest remains:

```text
sha256:7aae2cff0df757a4b436c5b87507162624813e64bd32946bada8a87e5d7adc22
```

## Azure MCP repository authority

Repository authority now includes:

- `.project/contracts/azure-mcp-reality-bridge.json`;
- `docs/architecture/azure-mcp-reality-bridge.md`;
- the contract validator and regression tests;
- `.project/reconciliations/azure-mcp-pr74.json`.

The shared `.project/active-work.json`, `.project/environment-state.json`, and `.project/handoffs/current-state.md` are intentionally left at the newer PR #76 state. This workstream uses a dedicated handoff rather than overwriting authenticated planner evidence.

## Azure MCP runtime state

```text
remote_endpoint_deployed = false
endpoint_url = null
client_path_selected = false
client_connected = false
authentication_model_selected = false
Azure_authentication_authorized = false
Azure_resources_created = false
Entra_identity_changed = false
Azure_RBAC_changed = false
tenant_scope_selected = false
subscription_scope_selected = false
resource_group_scope_selected = false
server_version_observed = false
tool_inventory_observed = false
allowed_tool_names = []
cost_observed = false
quota_observed = false
Azure_runtime_state = not_observed
```

`not_observed` must not be interpreted as absent, unhealthy, or ready.

## Current authority

```text
repository_reconciliation_authorized = true
pull_request_creation_authorized = true
pull_request_merge_authorized = false
Azure_MCP_hosting_authorized = false
Azure_MCP_client_configuration_authorized = false
Azure_authentication_authorized = false
Azure_resource_creation_authorized = false
Entra_identity_mutation_authorized = false
Azure_RBAC_mutation_authorized = false
MCP_tool_admission_authorized = false
ChatGPT_app_registration_authorized = false
OpenAI_API_execution_authorized = false
cleanup_authorized = false
```

## Next Azure MCP gate

```text
select_and_verify_client_path
```

The bounded choices are:

1. verify whether the current ChatGPT workspace can attach the remote MCP server;
2. accept or reject a separately billed OpenAI Responses API client;
3. accept or reject an IDE MCP client as a local proof path.

Client selection does not authorize Azure hosting. Hosting, identity, exact scope, cost, quota, tool inventory, and tool admission require later evidence and separate authorization.
