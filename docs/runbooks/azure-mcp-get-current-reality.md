# Azure MCP `get_current_reality` runbook

## Status

This package implements one **local, read-only MCP tool** and a direct observation CLI.
It does not deploy a remote MCP endpoint, configure Azure OpenAI to call the tool,
create an identity, assign RBAC, or mutate Azure.

```text
local tool implemented        = true
local live execution observed = false
remote MCP endpoint deployed  = false
Azure OpenAI MCP connected     = false
Azure mutation authorized      = false
```

A separate one-attempt authorization may permit one local Cloud Shell execution.
Authorization recorded in `.project/` does not mean that execution has occurred.

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

The observer permits only these read operations:

```text
git rev-parse HEAD
git status --porcelain=v1 --untracked-files=normal
az account show
az group show --subscription <exact-id> --name <exact-rg>
az resource list --subscription <exact-id> --resource-group <exact-rg>
az cognitiveservices account deployment list --subscription <exact-id> --resource-group <exact-rg> --name <observed-account>
```

Azure CLI `2.88.0` rejects `az account show --subscription`. The CLI and MCP
server therefore use a compatibility runner that removes only that unsupported
argument. Before execution, the one-shot wrapper explicitly selects the
operator-supplied subscription UUID with:

```text
az account set --subscription <exact-id>
```

The observer then compares the active account ID returned by `az account show`
with the exact runtime allowlist. All resource-scoped operations retain explicit
`--subscription` arguments.

```text
local Azure CLI context selected != Azure resource mutated
active account returned != explicit scope accepted
```

Commands are constructed as argument arrays with `shell=False`. There is no
arbitrary command input, template deployment, role assignment, provider
registration, resource mutation, secret read, or Azure cleanup command.

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
python -m unittest infra.tests.test_azure_mcp_active_subscription_compat -v
python -m py_compile azure_mcp_reality/*.py
```

These tests use fakes and do not authenticate to Azure or execute a live query.

## One direct read-only observation

A separately authorized local execution must use an exact reviewed commit,
subscription UUID, resource group, and confirmation string. For run 1, use the
dedicated wrapper and handoff:

```text
script: scripts/azure_mcp_current_reality_run1.sh
authorization: .project/observation-requests/azure-mcp-current-reality-run1.json
handoff: .project/handoffs/azure-mcp-current-reality-run1.md
```

Generic direct CLI execution remains:

```bash
cd ~/azure-iac-msp-lab
source .venv/bin/activate

export AZURE_MCP_ALLOWED_SUBSCRIPTION_ID='<exact-subscription-uuid>'
export AZURE_MCP_ALLOWED_RESOURCE_GROUP='<exact-resource-group-name>'
export AZURE_MCP_REPOSITORY_ROOT="$PWD"

python -m azure_mcp_reality.cli | tee /tmp/azure-mcp-current-reality.json
```

Do not derive the subscription UUID from an unreviewed default context. The
operator must deliberately select the exact subscription, and the returned active
account ID must match it.

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

## One-attempt consumption

The run-1 wrapper creates this non-secret marker immediately before Azure resource
observation:

```text
~/.azure-mcp-current-reality-run1.consumed
```

A failure after marker creation consumes the attempt. Do not remove the marker to
manufacture a retry. A new attempt requires new human authority and a new
reconciliation.

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

Repository rollback is an exact revert of the implementing or repair pull request.
Runtime environment cleanup is:

```bash
unset AZURE_MCP_ALLOWED_SUBSCRIPTION_ID
unset AZURE_MCP_ALLOWED_RESOURCE_GROUP
unset AZURE_MCP_REPOSITORY_ROOT
```

Then stop the local process. No Azure cleanup is required because this package
creates and mutates no Azure resources. Deleting a one-attempt consumption marker
to bypass authorization is not cleanup and is not permitted.

## Next gate

After one authorized Cloud Shell observation, inspect the structured receipt and
its digest, reconcile the result into `.project/`, and consume the active
authorization. Authenticated remote hosting and an Azure OpenAI Responses API MCP
call remain later independent gates.
