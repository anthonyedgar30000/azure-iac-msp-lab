# OpenAI SDK to Microsoft Foundry provider scaffold

## Status

This increment adds a **repository-only provider scaffold**.

```text
Azure AI resource deployed = not established
model deployment created = not established
OpenAI SDK client configured at runtime = false
Microsoft Entra authentication performed = false
model request performed = false
Azure MCP endpoint deployed = false
Azure MCP client connected = false
```

No Azure resource, identity, role assignment, secret, budget, network path, model
deployment, or API request is created by this increment.

## Purpose

Use the OpenAI Python SDK as the application client for a Microsoft Foundry /
Azure OpenAI v1 endpoint while keeping Azure identity, deployment reality,
operations authority, and MCP connectivity as separate gates.

```text
application
→ OpenAI Python SDK
→ Azure OpenAI / Foundry /openai/v1 endpoint
→ named Azure model deployment
```

This provider is the **model inference path**. It does not itself give the model
authority over Azure resources. Azure operational observation remains a separate
Azure MCP design with its own identity, RBAC, tool-admission, deployment, and
approval lifecycle.

## Canonical distinctions

```text
OpenAI_SDK_used != public_OpenAI_service_used
client_constructed != Microsoft_Entra_authenticated
endpoint_configured != Azure_AI_resource_deployed
deployment_name_configured != model_deployment_exists
model_response_succeeded != Azure_MCP_connected
Azure_model_provider != Azure_operations_authority
read_only_intent != effective_least_privilege
no_API_key != no_identity_or_RBAC_requirement
```

## Configuration contract

Required runtime variables:

```text
AZURE_OPENAI_BASE_URL=https://<resource>.openai.azure.com/openai/v1/
AZURE_OPENAI_MODEL_DEPLOYMENT=<exact-deployment-name>
```

Optional bounded variables:

```text
AZURE_OPENAI_TIMEOUT_SECONDS=30
AZURE_OPENAI_MAX_RETRIES=0
AZURE_OPENAI_TOKEN_SCOPE=https://ai.azure.com/.default
```

The provider:

- requires HTTPS;
- accepts only approved Azure AI hostname suffixes;
- requires the exact `/openai/v1/` path;
- rejects URL user information, custom ports, query strings, and fragments;
- rejects `AZURE_OPENAI_API_KEY`;
- pins the Microsoft Entra token scope;
- disables SDK retries by default so an execution attempt is not silently
  multiplied.

## Identity and permissions

The client factory uses `DefaultAzureCredential` with interactive-browser
authentication excluded and supplies a bearer-token provider to the OpenAI SDK.
The runtime identity must separately receive only the Azure role required to
invoke the selected model deployment.

Constructing the client does not prove that any credential in the chain can
authenticate, that the principal has access, or that the deployment exists.

## Network path

A future runtime invocation requires outbound HTTPS from the application to the
selected Azure AI endpoint. Private endpoint, public-network access, DNS,
firewall, egress, and certificate behavior remain unselected and unverified.

## Security controls

- Microsoft Entra authentication only in this scaffold;
- no API key accepted by configuration;
- no secret values in plans, tests, documentation, or `.project/`;
- strict endpoint validation;
- zero SDK retries by default;
- no network call during module import, configuration loading, plan generation,
  or client construction;
- model execution occurs only through the explicit `create_response` function.

Prompt content and model output remain data-governance concerns. This scaffold
does not authorize protected Azure evidence or customer information to be sent
to a model.

## Cost and quota

Repository-only recurring Azure cost delta: **CAD $0**.

Actual Azure AI pricing, model availability, token quota, regional capacity,
subscription eligibility, and current spend were not freshly observed. They
must be captured before model deployment or execution.

## Validation

```bash
python -m unittest infra.tests.test_openai_azure_foundry_provider -v

AZURE_OPENAI_BASE_URL='https://example-resource.openai.azure.com/openai/v1/' \
AZURE_OPENAI_MODEL_DEPLOYMENT='gpt-demo' \
python -m openai_azure_provider.plan
```

The plan command validates configuration and emits non-secret intent. It does
not construct a client, obtain a token, or call a model.

## Future deployment and execution gates

Before the first model call:

1. observe the active tenant and subscription;
2. select and record the Azure AI resource, region, model, deployment name,
   version, capacity, quota, and cost ceiling;
3. codify or inspect the Azure resource deployment;
4. run validation and What-If;
5. assign the minimum inference role at the narrowest supported scope;
6. verify DNS and network reachability;
7. bind execution to a fresh, exact-commit authorization;
8. make one bounded call;
9. capture request metadata, response status, deployment identity, token usage,
   latency, cost estimate, limitations, and redacted evidence;
10. separately verify that no Azure MCP connection or operational permission was
    implied by model inference success.

## Failure, rollback, and cleanup

Repository rollback is to close or revert this scaffold change.

For a future runtime, disable the calling workload or revoke its role assignment
before considering resource deletion. Access revocation is rollback; deleting
Azure AI resources, model deployments, private endpoints, DNS records, or
monitoring data is cleanup and requires separate authority.
