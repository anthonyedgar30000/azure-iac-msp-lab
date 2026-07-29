# Azure MCP current-reality run 1

## Status

```text
source instruction: Proceed
repository base: a39e39184ce80108d1b9ee7bd0f0136ff3a8fe05
latest merged PR at branch creation: 209
open PRs observed before branch: none
candidate branch: agent/repair-and-authorize-mcp-reality-run1
one local Cloud Shell observation authorized: true
observation executed: false
Azure mutation authorized: false
remote MCP endpoint deployed: false
Azure OpenAI MCP tool call authorized: false
```

The exact execution commit is the merge commit that lands this repair and authorization increment. It must be supplied at runtime and must equal the checked-out repository `HEAD`.

## Why a repair is required first

The first Azure MCP tool implementation constructed:

```text
az account show --subscription <exact-id>
```

The lab already has terminal evidence from Azure CLI `2.88.0` showing that `az account show` rejects `--subscription`. Executing the tool unchanged would consume the one-attempt authority on a known command-shape failure.

The compatibility runner now changes only the account-context command to:

```text
az account show --output json --only-show-errors
```

The wrapper deliberately selects the operator-supplied UUID first with `az account set`. The observer then compares the returned active subscription ID to the explicit runtime allowlist. Every resource query retains its exact `--subscription` argument.

```text
local Azure CLI context selection != Azure resource mutation
active account returned != explicit subscription accepted
```

## Exact authorized scope

```text
subscription name: Azure for Students
subscription UUID: operator supplied at runtime; never persisted
resource group: rg-ai-msp-dev-eastus
expected resource-group location: eastus
identity: existing interactive Azure Cloud Shell user
```

The resource group was chosen because this run is intended to reconcile the verified Azure OpenAI runtime with the new MCP observer. The observation may expose a different account name, deployment, SKU, capacity, or resource inventory than repository assumptions; those differences must be preserved rather than normalized away.

## One-attempt execution

After this increment is merged, open Azure Cloud Shell Bash and check out the exact merge commit reported in the merge result.

```bash
cd ~/azure-iac-msp-lab
git fetch origin
git checkout --detach '<exact-merge-commit>'

export AZURE_MCP_RUN1_SUBSCRIPTION_ID='<exact Azure for Students subscription UUID>'
export AZURE_MCP_RUN1_REVIEWED_COMMIT='<exact-merge-commit>'
export AZURE_MCP_RUN1_CONFIRMATION="OBSERVE-AZURE-MCP-RUN1:Azure for Students:rg-ai-msp-dev-eastus:${AZURE_MCP_RUN1_REVIEWED_COMMIT}"

bash scripts/azure_mcp_current_reality_run1.sh
```

The script:

1. validates the exact commit and confirmation;
2. validates the UUID shape;
3. explicitly selects the UUID in local Azure CLI context;
4. confirms the active subscription is enabled and named `Azure for Students`;
5. installs the pinned MCP dependency into a Cloud Shell home-directory virtual environment;
6. atomically consumes the one-attempt authorization;
7. executes the bounded `get_current_reality` CLI;
8. validates scope, zero-mutation, zero-secret, commit, location, and digest fields;
9. writes the receipt and manifest under `/tmp`.

## Consumption boundary

```text
marker: ~/.azure-mcp-current-reality-run1.consumed
```

The marker is created immediately before Azure resource observation. A failure after that point consumes the attempt and requires new human authority. Do not delete the marker to manufacture a retry.

Package installation, commit checks, confirmation checks, and account identity checks occur before consumption so a missing prerequisite does not waste the observation attempt.

## Expected evidence

```text
/tmp/azure-mcp-current-reality-run1.json
/tmp/azure-mcp-current-reality-run1.sha256
```

Required receipt properties:

```text
observation_status = observed | not_present
repository.head = exact reviewed commit
scope.subscription_name = Azure for Students
scope.resource_group = rg-ai-msp-dev-eastus
mutations_performed = false
secrets_returned = false
raw_evidence_digest = sha256:<64 hex characters>
```

When the resource group is observed, its location must be `eastus`.

Capture the terminal summary and the two files without exposing raw subscription IDs, tenant IDs, access tokens, API keys, or secret values.

## Authority exclusions

Not authorized by this run:

```text
Azure resource creation, update, or deletion
RBAC assignment or removal
provider registration
policy, quota, network, or secret change
guest command execution
workflow dispatch or rerun
remote MCP hosting
public tunnel
ChatGPT app registration
Azure OpenAI model request
model-driven MCP tool call
cleanup
```

## Cost

Expected recurring Azure resource-cost delta: **CAD $0**.

This run performs read-only Azure management-plane queries and no Azure OpenAI inference. Actual cost and quota are not observed by this version of the tool.

## Next gate

After the receipt is supplied, reconcile it into `.project/`, consume the active authorization, and classify each repository-versus-Azure claim as matched, drifted, unknown, conflicting, or unverifiable. Remote hosting and model-driven MCP use remain separate later gates.
