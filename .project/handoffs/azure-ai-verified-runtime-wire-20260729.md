# Azure AI verified runtime wire handoff

## Current evidence boundary

Run 6 is a consumed terminal failure. It authenticated to Azure, validated the exact repository candidate, and stopped during pre-mutation What-If because the GitHub OIDC principal lacked `Microsoft.Authorization/roleAssignments/write` at the targeted account scope.

```text
run 6 deployment started = false
run 6 model request performed = false
run 6 automatic rerun authorized = false
```

A separate Cloud Shell path was then verified against a different Azure OpenAI endpoint and deployment:

```text
base URL: https://anthonyedgar30000-5982-resource.openai.azure.com/openai/v1/
deployment: gpt-5-mini
authentication: Microsoft Entra bearer token
Responses status: completed
output: AZURE ENTRA CONNECTED
usage: 16 input + 24 output = 40 total tokens
API key used: false
Azure MCP connected: false
```

The successful Cloud Shell call does not make run 6 successful and does not prove that the GitHub OIDC identity can invoke the verified deployment.

## Repository wiring

The non-secret runtime profile is:

```text
config/azure-openai-runtime.dev.sh
```

The explicit invocation entry point is:

```text
openai_azure_provider/invoke.py
```

In Azure Cloud Shell or another environment where `DefaultAzureCredential` can obtain a permitted Entra token:

```bash
python -m pip install -r requirements/openai-azure-provider.txt
source config/azure-openai-runtime.dev.sh
python -m openai_azure_provider.invoke \
  --input 'Reply with exactly: AZURE ENTRA CONNECTED' \
  --expect-exact 'AZURE ENTRA CONNECTED'
```

The command defaults to `reasoning.effort=minimal`, `max_output_tokens=128`, zero SDK retries, and emits a non-secret JSON receipt. It performs exactly one model call per invocation.

## Security boundary

- Do not put an Azure API key in the profile, repository, chat, screenshots, or shell history.
- The provider rejects `AZURE_OPENAI_API_KEY`.
- The exposed key seen earlier must be treated as compromised; rotation completion is not yet established by evidence.
- Do not grant the GitHub OIDC principal broader RBAC merely to make the historical run 6 workflow pass.
- Azure operational tools and MCP remain separate and unconnected.

## Remaining reconciliation work

The following are still unknown for the verified endpoint and must be observed from Azure Resource Manager before it is fully represented in IaC:

- resource ARM ID and resource group;
- region;
- model version;
- deployment SKU and capacity;
- exact effective role assignment for the Cloud Shell identity;
- current quota and actual cost;
- local-authentication setting and API-key rotation state.

## Failure and rollback

A credential, RBAC, endpoint, deployment, or model error must be preserved without automatic retry. Repository rollback is a revert of this wiring increment. Access rollback is a separately authorized permission revocation. No Azure resource deletion or cleanup is authorized by this handoff.
