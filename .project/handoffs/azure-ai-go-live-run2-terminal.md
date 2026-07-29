# Azure AI go-live run 2 — terminal handoff

## Outcome

```text
workflow run: 30421206722 / attempt 1
exact merge commit: f667be775962d91f16e8c82744a5573a1a0875ca
conclusion: failure
repository and Bicep validation: passed
Azure OIDC login: passed
authorization guard: failed
first Azure query after login: not started
What-If: not started
resource group created: false
Azure OpenAI account created: false
model deployed: false
RBAC changed: false
model request performed: false
endpoint live: false
```

## Root cause

The run-2 executor validated two fields at the JSON root:

```text
.automatic_retry_authorized
.manual_rerun_authorized
```

The request correctly stores those values under:

```text
.authority.automatic_retry_authorized
.authority.manual_rerun_authorized
```

`jq -e` therefore returned false and the executor stopped before its first
`az account show` command. Azure authentication occurred, but no Azure query or
resource mutation in the executor followed it.

## Evidence

```text
artifact ID: 8711974113
artifact digest: sha256:bffb2053f3b4531896ae74fc60794fe8e738c09c0d7c24eac08a649bbae67f78
artifact content: empty artifact-manifest.sha256
terminal reconciliation: .project/reconciliations/azure-ai-go-live-run2-terminal-20260729.json
```

## Authority

Run 2 is consumed and terminal. Its failure does not authorize a third attempt.

```text
failed_run != authorization_to_retry
repair_identified != deployment_authorized
```

The code repair is to read both flags from `.authority`. A future run must use a
new exact commit and fresh explicit one-attempt authority.

## Cost and cleanup

```text
Azure resources created by run 2: none
model requests: none
resource cleanup required: false
actual Azure cost freshly observed: false
```
