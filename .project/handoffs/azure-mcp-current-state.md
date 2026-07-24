# Azure MCP reality bridge handoff

## Interpretation boundary

This handoff records the selected OpenAI API to Azure MCP architecture and its reviewable Cloud Shell preflight package. It is not a live Azure MCP endpoint or OpenAI API connection report.

```text
client_path_selected != client_configured
hosting_path_selected != hosting_deployed
managed_identity_selected != managed_identity_created
tool_advertised != tool_authorized
not_observed != absent
```

## Repository watermark

The observed default-branch baseline for this package is:

```text
main: df0458a4d0a9075787726a3205c6c7b454cfa15e
merged PR: 78
source head: cc6d2c2b4a238d22f2ab56f68a0722d3f9f1423a
exact-head CI: 30072601791
open pull requests observed: none
```

PR #78 preserves a typed conflict between the current repository declaration and the latest protected Azure planner evidence:

```text
current repository package = westus2 / Standard_F1als_v7
latest protected Azure package = eastus / Standard_B2ats_v2
verification_status = conflicting
```

Neither package is Azure MCP runtime evidence.

## Selected architecture

```text
client_path_selected = true
selected_client_path = openai_responses_api
client_configured = false
client_connected = false

hosting_architecture_selected = true
selected_hosting_service = azure_container_apps
deployment_interface_selected = true
selected_deployment_interface = azure_cloud_shell
remote_endpoint_deployed = false
endpoint_url = null

client_to_server_authentication_selected = entra_oauth
client_to_server_authentication_implemented = false
server_to_azure_authentication_selected = managed_identity_shared_service_identity
server_to_azure_authentication_implemented = false
```

The template candidate is `azmcp-copilot-studio-aca-mi` because Microsoft documents a remote Azure MCP Server on Azure Container Apps backed by a managed identity and Reader RBAC. The template remains unpinned and unapproved until its exact downloaded content is hashed and reviewed.

## Cloud Shell package

The paste-ready read-only preparation script is:

```text
scripts/azure_mcp_cloud_shell_preflight.sh
```

The operator runbook is:

```text
docs/runbooks/openai-api-azure-mcp-cloud-shell.md
```

The preflight can observe Azure account, provider, resource-group, and resource inventory state and download the template into Cloud Shell storage. It contains no Azure deployment, provider registration, role assignment, Entra mutation, Container Apps mutation, cleanup, or OpenAI API command.

## Runtime state

```text
Azure_MCP_remote_endpoint_deployed = false
Azure_MCP_endpoint_url = null
Azure_MCP_server_version_observed = false
Azure_MCP_container_image_observed = false
Azure_MCP_tool_inventory_observed = false
Azure_MCP_allowed_tool_names = []
Azure_MCP_tenant_scope_selected = false
Azure_MCP_subscription_scope_selected = false
Azure_MCP_resource_group_scope_selected = false
Azure_MCP_cost_observed = false
Azure_MCP_quota_observed = false
OpenAI_API_project_observed = false
OpenAI_API_key_observed = false
OpenAI_API_execution_performed = false
Azure_MCP_runtime_state = not_observed
```

## Current authority

```text
repository_design_authorized = true
pull_request_creation_authorized = true
pull_request_merge_authorized = false
Cloud_Shell_preflight_execution_authorized = false
Azure_authentication_authorized = false
Azure_resource_creation_authorized = false
Entra_application_mutation_authorized = false
managed_identity_mutation_authorized = false
Azure_RBAC_mutation_authorized = false
Container_Apps_mutation_authorized = false
OpenAI_API_execution_authorized = false
MCP_tool_admission_authorized = false
cleanup_authorized = false
```

## Next gate

```text
review_and_merge_package_then_authorize_read_only_cloud_shell_preflight
```

The next authorization must be limited to the preflight script and explicit hosting subscription, location, and resource-group inputs. It must not include `azd up`, resource creation, Entra changes, RBAC changes, OpenAI API calls, or cleanup.
