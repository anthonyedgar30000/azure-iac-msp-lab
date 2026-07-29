# Azure AI go-live run 5 — activation handoff

## Authority

Anthony Edgar authorized:

> Proceed with Azure AI go-live run 5 in Azure for Students, selecting the first deployable approved region and model combination in one bounded workflow.

This is a fresh one-attempt authority. It is not a GitHub Re-run of run 4.

## Repository boundary

```text
base main at branch creation: df43899e9fad9a678b0124cd5bef87612be32b6c
latest merged PR before branch: #204
open PRs before branch: none
run 4: consumed terminal failure
run 4 Azure resources: none
```

Two administrative commits immediately before the branch added and removed an accidental `tmp-placeholder` file. The file is absent and repository content was restored before this branch. The commits remain in history and are not Azure evidence.

## Subscription boundary

```text
required subscription name: Azure for Students
required subscription state: Enabled
configured AZURE_SUBSCRIPTION_ID: must match the Azure login context
all other subscriptions: unauthorized
```

## Bounded selector

Model priority:

1. `gpt-4o-mini` version `2024-07-18`, `GlobalStandard`;
2. `gpt-4.1-mini` version `2025-04-14`, `GlobalStandard`.

Region order for each model:

1. `westus3`;
2. `westus`;
3. `eastus`;
4. `northcentralus`;
5. `southcentralus`.

The workflow may perform read-only model-list, capacity, and What-If checks for at most ten combinations. It stops selecting after the first candidate passes all three gates.

## Mutation and verification limits

```text
deployment attempts: 1
resource groups: at most 1
Azure OpenAI accounts: at most 1
model deployments: at most 1
account-scoped role assignments: at most 1
model requests: exactly 1 maximum
max output tokens: 32
```

After mutation begins, the workflow must not continue to another candidate. Any deployment or verification failure is terminal and leaves partial resources for exact-state inspection.

## Intended deployment

```text
subscription: Azure for Students
resource group: rg-ai-msp-dev-<selected-location>
account: oai-msp-<subscription-hash>-<selected-location>
account kind: OpenAI
account SKU: S0
model deployment SKU: GlobalStandard
capacity: 1
local authentication: disabled
public network access: enabled
inference role: Cognitive Services OpenAI User
role scope: selected account only
```

## Cost boundary

Global Standard pay-as-you-go, capacity 1, and one 32-token verification request. No provisioned throughput or budget resource is authorized. Actual cost remains unknown until live billing evidence exists.

## Failure and cleanup

- No candidate passes: no mutation; preserve evidence.
- Deployment fails: stop after the one deployment attempt; preserve any partial resources.
- Model verification fails: preserve the deployment and evidence.
- No automatic retry, manual rerun, rollback, or cleanup is authorized.
