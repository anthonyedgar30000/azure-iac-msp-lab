# Azure AI go-live run 5 — terminal handoff

## Terminal result

```text
pull request: #205
reviewed source head: e19a80079331f5aabd353e238af39b3ef7f7aec5
merge commit: 697930d2ebec0d14bed3e1796d440c719f651401
workflow run: 30425884534 / attempt 1
job: 90492164065
artifact: 8713618498
artifact digest: sha256:39491be1c1292ffb9f31064645dd289ed718cebb4c862b4d5c57d712acb7162a
conclusion: failure
```

## Observed Azure context

```text
subscription: Azure for Students
subscription state: Enabled
Microsoft.CognitiveServices: Registered
Azure OIDC login: succeeded
```

## Candidate findings

`gpt-4o-mini` version `2024-07-18`, `GlobalStandard` was listed in all five tested regions, but the capacity endpoint reported zero available capacity in each.

`gpt-4.1-mini` version `2025-04-14`, `GlobalStandard` was listed in all five tested regions and reported available capacity 200 in each, which exceeded the requested capacity 1.

The five capacity-sufficient regions were:

- `westus3`;
- `westus`;
- `eastus`;
- `northcentralus`;
- `southcentralus`.

## Root cause

The subscription-scoped Bicep entry point still restricted the `location` parameter to:

```text
canadaeast
eastus2
```

Each capacity-sufficient run-5 candidate therefore failed template validation with `InvalidTemplate` before a What-If change plan could be produced.

This was a repository declaration defect. It was not evidence of:

- an Azure authentication failure;
- a run-5 subscription policy denial;
- unavailable `gpt-4.1-mini` capacity;
- a deployment failure;
- or a model-response failure.

## Deployment reality

```text
What-If change plan produced: false
deployment started: false
resource group created: false
Azure OpenAI account created: false
model deployment created: false
RBAC changed: false
model request performed: false
endpoint live: false
cleanup required: false
Azure resource cost delta established: CAD $0
```

## Repair candidate

The reconciliation branch expands the Bicep location allowlist to include the run-5 candidate regions while preserving the previously declared regions. The run-5 workflow file is unchanged, so merging the repair cannot trigger run 5 again.

```text
repair prepared != repair merged
repair merged != deployment authorized
capacity observed != future capacity guaranteed
```

## Authority

Run 5 is consumed. GitHub Re-run, workflow dispatch, run 6, rollback, and cleanup are not authorized.
