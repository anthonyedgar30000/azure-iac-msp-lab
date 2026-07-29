# Azure MCP `get_current_reality` runbook

## Current status

This package implements one **local, read-only MCP tool** and a direct observation CLI.
It does not deploy a remote MCP endpoint, configure Azure OpenAI to call the tool,
create an identity, assign RBAC, or mutate Azure.

```text
local tool implemented                 = true
local live execution observed          = true
run-1 receipt validated                = true
run-1 authority consumed               = true
run-1 rerun authorized                 = false
run-1 wrapper epilogue completed       = false
remote MCP endpoint deployed           = false
Azure OpenAI MCP connected              = false
Azure mutation authorized               = false
```

Run 1 is terminal. Do not rerun it.

Canonical evidence:

```text
.project/evidence/azure-mcp-current-reality-run1.json
.project/evidence/azure-mcp-current-reality-run1.sha256
.project/reconciliations/azure-mcp-current-reality-run1-terminal-20260729.json
.project/handoffs/azure-mcp-current-reality-run1-terminal.md
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

It never infers the default subscription and never discovers across subscriptions.

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

Azure CLI `2.88.0` rejects `az account show --subscription`. The CLI and MCP server
use a compatibility runner that removes only that unsupported argument. A separately
authorized wrapper must first select the operator-supplied subscription UUID with:

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

Local execution uses the identity already authenticated in Azure CLI. A successful
observation proves only what that identity could read at that time. It does not
prove effective least privilege.

The tool does not persist raw tenant or subscription IDs. It fingerprints those
values and redacts the subscription segment from returned ARM IDs. It returns tag
keys, not tag values.

## Run-1 terminal result

Run 1 observed:

```text
subscription: Azure for Students
subscription state: Enabled
resource group: rg-ai-msp-dev-eastus
location: eastus
resource-group provisioning state: Succeeded
resource count: 1
```

Observed resource:

```text
name: oai-msp-anthony-dev-eastus
type: Microsoft.CognitiveServices/accounts
kind: OpenAI
SKU: S0
deployments: 0
```

The separately verified `gpt-5-mini` endpoint remains operational evidence, but
its ARM resource identity was not reconciled by this run. Do not interpret the
empty deployment inventory on `oai-msp-anthony-dev-eastus` as proof that the
verified runtime is absent globally.

```text
empty deployment inventory in observed account != verified runtime absent globally
observed account name != verified endpoint ARM identity reconciled
```

## Run-1 wrapper incident

The observation CLI completed and wrote the receipt. The wrapper then failed during
its local validation epilogue because it attempted this shell pattern:

```text
readonly RECEIPT_PATH=...
RECEIPT_PATH="$RECEIPT_PATH" python3 ...
```

Bash rejected the environment-prefix assignment to the readonly variable before
the Python validation block. The receipt remained valid. The operator created a
manifest from the existing receipt; the uploaded receipt SHA-256 matched the
manifest exactly.

The repaired wrapper uses distinct validation-only names:

```text
RUN1_RECEIPT_PATH
RUN1_EXPECTED_COMMIT
RUN1_EXPECTED_SUBSCRIPTION_NAME
RUN1_EXPECTED_RESOURCE_GROUP
RUN1_EXPECTED_LOCATION
```

This repository repair does not authorize another run.

```text
observation succeeded != wrapper epilogue succeeded
receipt validated after upload != observation rerun
```

## Local validation

From an isolated environment in the repository:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements/azure-mcp-reality-tool.txt
python -m unittest infra.tests.test_azure_mcp_current_reality_tool -v
python -m unittest infra.tests.test_azure_mcp_active_subscription_compat -v
python -m unittest infra.tests.test_azure_mcp_current_reality_run1_authorization -v
python -m unittest infra.tests.test_azure_mcp_current_reality_run1_terminal -v
python -m py_compile azure_mcp_reality/*.py
bash -n scripts/azure_mcp_current_reality_run1.sh
```

These tests use repository evidence and fakes. They do not authenticate to Azure
or execute a live query.

## Future direct observations

No active observation authorization exists. A future direct CLI or wrapper run
requires a new, explicit, non-renewing authorization with exact subscription,
resource group, identity, commit, expected outputs, failure behavior, evidence
paths, and retry rules.

Do not delete this marker to manufacture another run-1 attempt:

```text
~/.azure-mcp-current-reality-run1.consumed
```

Generic CLI syntax, only after new authority exists:

```bash
export AZURE_MCP_ALLOWED_SUBSCRIPTION_ID='<exact-subscription-uuid>'
export AZURE_MCP_ALLOWED_RESOURCE_GROUP='<exact-resource-group-name>'
export AZURE_MCP_REPOSITORY_ROOT="$PWD"
python -m azure_mcp_reality.cli
```

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
tunnel, or register it as a ChatGPT app without a separate reviewed increment.

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

## Cost, quota, and operational limits

Repository implementation and reconciliation add **CAD $0** in recurring Azure
resource cost. The local observation consumed zero Azure OpenAI model tokens.
Current Azure cost, quota, activity logs, metrics, policy, networking, diagnostics,
and effective RBAC remain unobserved.

Resource existence does not prove secure configuration, health, diagnostics,
alerting, backup, recovery, resilience, or service validation.

## Failure, rollback, and cleanup

Repository rollback is an exact revert of the implementing or repair pull request.
No Azure rollback is required because run 1 performed no Azure mutation.

Runtime environment cleanup for a future authorized local process is:

```bash
unset AZURE_MCP_ALLOWED_SUBSCRIPTION_ID
unset AZURE_MCP_ALLOWED_RESOURCE_GROUP
unset AZURE_MCP_REPOSITORY_ROOT
```

Deleting the consumed run-1 marker to bypass authorization is not cleanup and is
not permitted.

## Next gate

A new separately bounded read-only observation may be designed only when needed to
reconcile the ARM identity behind the verified `gpt-5-mini` endpoint or inspect
effective RBAC, diagnostics, policy, networking, cost, or quota.

Authenticated remote hosting and an Azure OpenAI Responses API MCP call remain
independent later gates.
