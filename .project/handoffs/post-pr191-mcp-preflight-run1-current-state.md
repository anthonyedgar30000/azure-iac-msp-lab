# Current project handoff after PR #191 and Azure MCP preflight run 1

## Interpretation boundary

This handoff records repository state through **2026-07-28T22:07:09-04:00**, Azure MCP read-only preflight run `30415111776`, protected artifact `8709858548`, and operator-provided Cloud Shell validation.

The GitHub Actions run authenticated to Azure through workload identity federation, then failed before completing its first account-context observation because the script supplied a command-specific `--subscription` argument that the observed Azure CLI interface rejected.

```text
authentication_succeeded != Azure_resource_observation_completed
command_invoked != Azure_API_query_completed
manual_Cloud_Shell_validation_succeeded != GitHub_OIDC_preflight_succeeded
failed_attempt != authorization_to_retry
authorization_consumed != authorization_renewed
repository_repair != Azure_freshly_observed
not_observed != false
```

## Repository watermark

```text
repository: anthonyedgar30000/azure-iac-msp-lab
observed main: bdb337cf5ef10a643933d19c778d765e9f0d330d
latest merged PR: #191
PR #191 exact source: e70992960fa15a82a4e131b6e0fb527f5478b8f4
PR #191 exact-head CI: 30410555271 / success
PR #191 merge: bdb337cf5ef10a643933d19c778d765e9f0d330d
open PRs before repair branch: none observed
repair branch: agent/repair-azure-mcp-preflight-cli-arguments
repair branch base: bdb337cf5ef10a643933d19c778d765e9f0d330d
local working tree: not observed; connector-backed repository operations
```

## Azure MCP preflight run 1

```text
workflow run: 30415111776
job: 90459816380
run attempt: 1
workflow head: main@bdb337cf5ef10a643933d19c778d765e9f0d330d
exact reviewed checkout: bae07d24c59f7bc02001a168c7c6aac188ff2747
resource group input: rg-azure-mcp-dev-westus2
location input: westus2
template input: azmcp-copilot-studio-aca-mi
workflow conclusion: failure
```

Successful boundaries:

- exact reviewed commit checkout;
- bounded authority validation;
- static workflow and script safety tests;
- Azure Developer CLI setup;
- Azure OIDC login through the `azure-lab` environment;
- protected evidence manifest and artifact upload.

Terminal failure:

```text
step: Run read-only Azure MCP preflight
script version: 1.1.0
Azure CLI: 2.88.0
Azure Developer CLI: 1.28.1
failed command: az account show --subscription <redacted> --output json
error: unrecognized arguments: --subscription <redacted>
exit code: 2
```

The finite grant was consumed when Azure OIDC login succeeded. Run 1 must not be rerun under that grant.

## Evidence produced

```text
artifact: 8709858548
name: azure-mcp-read-only-preflight-30415111776-1
digest: sha256:7b931ed0a8e08497457f97528f06a018164b93a9b448ff97f612bd2a3468d7e5
expires: 2026-08-28T01:48:42Z
```

Present files:

```text
artifact-manifest.sha256
azure-cli-version.json
azure-developer-cli-version.txt
request.json
```

Not produced because execution stopped at the first observation command:

```text
account-context.json
provider-states.json
resource-group-state.json
existing-resource-summary.json
template-files.sha256
template-risk-scan.txt
preflight-summary.json
```

No raw subscription ID or tenant ID is promoted into repository state.

## Operator-provided Cloud Shell validation

Anthony manually validated the repaired command pattern in Azure Cloud Shell. The supplied screenshot shows:

```text
subscription name: Azure for Students
subscription state: Enabled
active subscription ID comparison: matched
principal type: user
location westus2: available
proposed resource group: rg-azure-mcp-dev-westus2
Azure resource mutation: none
```

This proves the repaired Bash and Azure CLI account-context pattern under the interactive user identity. It does not prove the repaired GitHub Actions workflow under the OIDC service-principal identity.

## Repository-only repair

The repair branch changes the script to:

```bash
account_json="$(az account show --output json)"

subscription_id="$(jq -r '.id' <<<"$account_json")"

[[ "$subscription_id" == "$AZURE_MCP_HOSTING_SUBSCRIPTION_ID" ]] \
  || fail "Azure CLI resolved a different subscription"

location_match="$(
  az account list-locations \
    --query "[?name=='$AZURE_MCP_LOCATION'].name | [0]" \
    --output tsv
)"
```

The exact subscription equality check and Enabled-state check remain fail-closed. Regression tests prohibit restoring `--subscription` to `az account show` or `az account list-locations`.

The repair adds no Azure mutation, deployment, cleanup, RBAC, OpenAI API, automatic retry, or new workflow trigger.

## Preserved Azure and runtime evidence

No complete fresh Azure resource observation followed the failed run. The previously protected Azure and collector runtime evidence remains in `.project/current-reality-v2.json` and related terminal reconciliations.

```text
actual Azure cost: not freshly observed
quota: not freshly observed
Azure MCP resource group state: not observed by run 1
provider registration state: not observed by run 1
template source: not downloaded or pinned by run 1
endpoint deployed: false
OpenAI client connected: false
expected recurring Azure cost delta from this repair: CAD $0
```

## Current authority

```text
repository-only repair: authorized
repair branch creation: authorized
declared file writes: authorized
draft pull request creation: authorized
ordinary exact-head PR CI: authorized
PR merge: unauthorized
workflow dispatch or rerun: unauthorized
Azure authentication or query: unauthorized
Azure mutation or deployment: unauthorized
OpenAI API execution: unauthorized
rollback or cleanup: unauthorized
RBAC or repository-ruleset mutation: unauthorized
live authorization claim testing: unauthorized
```

## Next gate

Open the repository-only repair as a draft pull request and review its complete exact-head CI result. Merge requires fresh authority. A later Azure MCP preflight requires a separate, exact-new-commit-bound, non-renewing authorization and must not inherit authority from run `30415111776`.
