# Azure MCP `get_current_reality` runbook

## Status

This increment implements one **local, read-only MCP tool** and a direct observation CLI.
It does not deploy a remote MCP endpoint, configure Azure OpenAI to call the tool,
create an identity, assign RBAC, or mutate Azure.

```text
local tool implemented        = true
local live execution observed = false
remote MCP endpoint deployed  = false
Azure OpenAI MCP connected     = false
Azure mutation authorized      = false
```

## Purpose

`get_current_reality` observes one explicitly selected Azure subscription and
resource group together with the exact local repository state. It returns a
bounded, sanitized, digest-bearing evidence object.

The tool has no model-supplied parameters. Its scope comes only from operator-set
environment variables:

```text
AZURE_MCP_ALLOWED_SUBSCRIPTION_ID
AZURE_MCP_ALLOWED_RESOURCE_GROUP
AZURE_MCP_REPOSITORY_ROOT
```

It never infers the default subscription and never discovers across
subscriptions.

## Fixed observation path

The implementation can execute only these read operations:

```text
git rev-parse HEAD
git status --porcelain=v1 --untracked-files=normal
az account show --subscription <exact-id>
az group show --subscription <exact-id> --name <exact-rg>
az resource list --subscription <exact-id> --resource-group <exact-rg>
az cognitiveservices account deployment list --subscription <exact-id> --resource-group <exact-rg> --name <observed-account>
```

Commands are constructed as argument arrays with `shell=False`. There is no
arbitrary command input, template deployment, role assignment, provider
registration, resource mutation, secret read, or cleanup command.

## Identity and permissions

Local execution uses the identity already authenticated in Azure CLI. A
successful observation proves only what that identity could read at that time.
It does not prove effective least privilege.

The tool does not persist raw tenant or subscription IDs. It fingerprints those
values and redacts the subscription segment from returned ARM IDs. It returns tag
keys, not tag values.

## Local validation

From an isolated environment in the repository:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements/azure-mcp-reality-tool.txt
python -m unittest infra.tests.test_azure_mcp_current_reality_tool -v
python -m py_compile azure_mcp_reality/*.py
```

## One direct read-only observation

A later, separately authorized local execution can use:

```bash
cd ~/azure-iac-msp-lab
git checkout main
git pull --ff-only
source .venv/bin/activate

export AZURE_MCP_ALLOWED_SUBSCRIPTION_ID='<exact-subscription-uuid>'
export AZURE_MCP_ALLOWED_RESOURCE_GROUP='<exact-resource-group-name>'
export AZURE_MCP_REPOSITORY_ROOT="$PWD"

python -m azure_mcp_reality.cli | tee /tmp/azure-mcp-current-reality.json
```

Do not substitute `$(az account show --query id ...)` for the explicit
subscription selection. The operator must deliberately choose the scope.

Expected top-level fields include:

```text
observed_at_utc
correlation_id
observation_status
source_system
caller_identity_mode
scope
repository
azure
freshness_boundary
limitations
mutations_performed
secrets_returned
raw_evidence_digest
```

A missing resource group is reported as `not_present`. Authentication failures,
scope mismatches, disabled subscriptions, invalid JSON, command failures, and
inventory-bound violations fail closed as `observation_failed` through the CLI.

## Local MCP transports

The MCP server supports local stdio:

```bash
python -m azure_mcp_reality.server --transport stdio
```

and localhost-only Streamable HTTP:

```bash
python -m azure_mcp_reality.server --transport streamable-http
```

The HTTP listener is fixed to:

```text
127.0.0.1:8000/mcp
```

This is not a production endpoint. Do not expose it publicly, place it behind a
tunnel, or register it as a ChatGPT app under this increment.

## Tool admission

Exactly one tool is admitted:

```text
name: get_current_reality
version: 0.1.0
readOnlyHint: true
destructiveHint: false
idempotentHint: true
openWorldHint: true
```

Tool annotations are descriptive hints, not the enforcement mechanism. Safety is
enforced by exact scope configuration, fixed command construction, no shell
interpolation, bounded inventories, output sanitization, and default deny.

## Cost and quota

Repository implementation adds **CAD $0** in recurring Azure resource cost.
A local read-only Azure CLI observation does not invoke the Azure OpenAI model.
Current Azure cost, MCP hosting cost, and quota remain unobserved.

## Failure, rollback, and cleanup

Repository rollback is an exact revert of the implementing pull request.
Runtime rollback is:

```bash
unset AZURE_MCP_ALLOWED_SUBSCRIPTION_ID
unset AZURE_MCP_ALLOWED_RESOURCE_GROUP
unset AZURE_MCP_REPOSITORY_ROOT
```

Then stop the local process. No Azure cleanup is required because this increment
creates and mutates no Azure resources.

## Next gate

After merge, separately authorize one local Cloud Shell observation against an
exact subscription and resource group. Inspect the structured receipt and its
digest before considering authenticated remote hosting or an Azure OpenAI
Responses API MCP call.
