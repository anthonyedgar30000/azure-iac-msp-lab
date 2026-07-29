# OpenAI SDK to Microsoft Foundry provider

## Status

The provider has moved beyond a repository-only scaffold. A separate Azure Cloud
Shell call verified a live Azure OpenAI Responses path using Microsoft Entra ID:

```text
base URL = https://anthonyedgar30000-5982-resource.openai.azure.com/openai/v1/
deployment = gpt-5-mini
Responses status = completed
output = AZURE ENTRA CONNECTED
usage = 16 input + 24 output = 40 total tokens
API key used = false
Azure MCP connected = false
```

The repository now contains a non-secret runtime profile and an explicit invocation
CLI. This wiring is a repository candidate until merged and revalidated from the
intended application runtime.

Run 6 remains a separate consumed terminal failure. It targeted
`oai-msp-anthony-dev-eastus/gpt-41-mini-msp-dev` and stopped during pre-mutation
What-If because the GitHub OIDC principal lacked role-assignment write permission.
No deployment or model call occurred in run 6. The successful gpt-5-mini call does
not retroactively make run 6 successful.

## Purpose

Use the OpenAI Python SDK as the application client for a Microsoft Foundry /
Azure OpenAI v1 endpoint while keeping Azure identity, deployment reality,
operations authority, and MCP connectivity as separate gates.

```text
application
→ OpenAI Python SDK
→ Microsoft Entra token provider
→ Azure OpenAI /openai/v1 endpoint
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
run6_failed != verified_runtime_failed
run6_target_account != verified_runtime_endpoint
Cloud_Shell_identity_access != GitHub_OIDC_identity_access
repository_wired != merged_and_reexecuted
```

## Verified non-secret runtime profile

The checked-in profile contains only public configuration:

```text
config/azure-openai-runtime.dev.sh
```

It sets:

```text
AZURE_OPENAI_BASE_URL=https://anthonyedgar30000-5982-resource.openai.azure.com/openai/v1/
AZURE_OPENAI_MODEL_DEPLOYMENT=gpt-5-mini
AZURE_OPENAI_TOKEN_SCOPE=https://ai.azure.com/.default
AZURE_OPENAI_TIMEOUT_SECONDS=30
AZURE_OPENAI_MAX_RETRIES=0
```

No API key, access token, tenant ID, subscription ID, or principal identifier is
stored in the profile.

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
  multiplied;
- validates optional reasoning effort as `minimal`, `low`, `medium`, or `high`;
- performs model execution only through an explicit function or CLI invocation.

## Identity and permissions

The client factory uses `DefaultAzureCredential` with interactive-browser
authentication excluded and supplies a bearer-token provider to the OpenAI SDK.
The runtime identity must separately receive only the Azure role required to
invoke the selected model deployment.

The verified call establishes that the Cloud Shell identity had effective
permission at that moment. It does not establish the exact role assignment or
prove that the GitHub OIDC identity, a managed identity, or a future application
identity has the same access.

Constructing the client does not prove that any credential in the chain can
authenticate, that the principal has access, or that the deployment exists.

## Explicit invocation

Install the pinned dependencies and load the non-secret profile:

```bash
python -m pip install -r requirements/openai-azure-provider.txt
source config/azure-openai-runtime.dev.sh
```

Then make one bounded call:

```bash
python -m openai_azure_provider.invoke \
  --input 'Reply with exactly: AZURE ENTRA CONNECTED' \
  --expect-exact 'AZURE ENTRA CONNECTED'
```

The CLI defaults to:

```text
reasoning.effort = minimal
max_output_tokens = 128
SDK retries = 0
prompt classification = bounded_non_sensitive_demo
```

It emits a JSON receipt containing endpoint host/path, deployment, response status,
output text, usage, latency, and the explicit statements that no API key or MCP
connection was used. It does not print access tokens.

Each CLI invocation performs exactly one model request. A failed exact-output check
returns exit code 2 and does not trigger a retry.

## Network path

The verified network path was Azure Cloud Shell outbound HTTPS to:

```text
anthonyedgar30000-5982-resource.openai.azure.com/openai/v1/responses
```

The ARM-level public-network setting, private endpoint state, DNS design, firewall
configuration, and intended application egress path have not yet been freshly
observed for this endpoint.

## Security controls

- Microsoft Entra authentication for the verified and wired path;
- no API key accepted by provider configuration;
- no secret values in plans, tests, documentation, runtime profile, or `.project/`;
- strict endpoint validation;
- zero SDK retries by default;
- no network call during module import, configuration loading, plan generation,
  or client construction;
- model execution only through the explicit `create_response` function or
  `openai_azure_provider.invoke` CLI;
- bounded reasoning and output-token settings for the smoke test;
- Azure MCP and Azure mutation authority remain absent.

An API key was exposed in an earlier screenshot. Rotation was requested, but its
completion is not established by current evidence. The successful keyless Entra
path avoids relying on that key. Verify rotation and consider disabling local
authentication after confirming every required client uses Entra ID.

Prompt content and model output remain data-governance concerns. This wiring does
not authorize protected Azure evidence, secrets, customer data, or regulated
information to be sent to a model.

## Cost and quota

The verified successful call used 40 total tokens. Actual Azure cost in CAD was not
observed. Repository wiring adds **CAD $0** in recurring Azure resource cost.

The verified deployment's current quota, model version, SKU, capacity, rate limits,
and billing meters have not been freshly captured from Azure Resource Manager.

## Validation

Repository validation:

```bash
python -m unittest infra.tests.test_openai_azure_foundry_provider -v
python -m unittest infra.tests.test_azure_ai_verified_runtime_wire -v
python -m unittest infra.tests.test_azure_ai_go_live_run6 -v
python -m py_compile openai_azure_provider/client.py openai_azure_provider/invoke.py
```

Non-executing plan:

```bash
source config/azure-openai-runtime.dev.sh
python -m openai_azure_provider.plan
```

Explicit runtime smoke test:

```bash
source config/azure-openai-runtime.dev.sh
python -m openai_azure_provider.invoke \
  --input 'Reply with exactly: AZURE ENTRA CONNECTED' \
  --expect-exact 'AZURE ENTRA CONNECTED'
```

The plan command validates configuration and emits non-secret intent. It does not
construct a client, obtain a token, or call a model. The invoke command does all
three explicitly and requires an already permitted Entra identity.

## Remaining reconciliation gates

Before declaring the verified deployment fully managed by IaC, observe and record:

1. tenant and subscription context without persisting raw identifiers;
2. Azure resource ARM ID and resource group;
3. region;
4. model version;
5. deployment SKU, capacity, quota, and current cost;
6. exact effective role assignment for the intended application identity;
7. local-authentication and public-network settings;
8. DNS, firewall, private endpoint, and egress behavior;
9. monitoring, diagnostics, token usage, and alerting;
10. rollback by access revocation and separately authorized cleanup behavior.

## Failure, rollback, and cleanup

Credential, RBAC, endpoint, deployment, or response failures must be preserved
without automatic retry. Repository rollback is an exact revert of the runtime
profile, invocation CLI, tests, documentation, contract, and reconciliation.

For a runtime, revoke or disable the selected application identity before
considering resource deletion. Access revocation is rollback; deleting Azure AI
resources, model deployments, private endpoints, DNS records, or monitoring data
is cleanup and requires separate authority.
