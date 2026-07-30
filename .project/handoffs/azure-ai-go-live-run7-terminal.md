# Azure AI go-live run 7 — terminal handoff

## Terminal result

```text
source authority: Proceed with Azure AI run 7 using the existing account and existing account-scoped inference role.
pull request: #226
reviewed source head: b1723c5a5005ad356dd7944fbea77eaa4e7987cc
merge commit: 90befdda4cedc52eb84a19cee5d19f2f5b61a369
workflow run: 30507904540 / attempt 1
job: 90761544877
artifact: 8746021488
artifact digest: sha256:89a101055b5df556b5e4bab47a2487ab13690e5824c9ec26cf219fbb345449df
conclusion: failure
failure stage: existing_direct_role_validation
```

Run 7 is consumed. Do not use GitHub **Re-run**.

## Fresh Azure evidence

The workflow successfully authenticated with workload identity federation and observed:

```text
subscription: Azure for Students
subscription state: Enabled
Microsoft.CognitiveServices: Registered
resource group: rg-ai-msp-dev-eastus
resource-group location: eastus
resource-group provisioning: Succeeded
account: oai-msp-anthony-dev-eastus
account kind: OpenAI
account SKU: S0
account provisioning: Succeeded
public network access: Enabled
disableLocalAuth: null
custom subdomain: oai-msp-anthony-dev-eastus
```

The account and resource group retained the manual-bootstrap tags.

## Exact failure

The executor attempted:

```text
az role assignment list
  --assignee-object-id <principal>
  --scope <target-account-id>
  --all
```

Azure CLI rejected the argument combination:

```text
ERROR: group or scope are not required when --all is used
```

This is a repository executor defect. It is not proof that the required `Cognitive Services OpenAI User` role is absent or ineffective.

```text
role query started: true
role query completed: false
required direct role present: not established
required direct role missing: not established
effective data-plane access: not established
```

## Mutation boundary

Run 7 stopped before all later stages:

```text
deployment inventory query: not started
model listing query: not started
capacity query: not started
ARM What-If: not started
model deployment: not started
account hardening: not started
model request: not performed
Azure mutations: none
endpoint live on run-7 target: false
separate verified gpt-5-mini runtime modified: false
```

The observed target account still reported `disableLocalAuth: null`; run 7 did not change it.

## Cost boundary

```text
Azure resource cost delta established by run 7: CAD $0
billable model request: false
tokens consumed: 0
actual Azure account cost freshly observed: false
```

GitHub Actions minutes and artifact storage may still apply.

## Repository repair

The exact repair is recorded at:

```text
.project/repairs/azure-ai-go-live-run7-role-query.patch
```

It removes `--all` only from role-list commands that already use `--scope`. The unscoped principal-discovery fallback retains `--all`.

The historical executor remains traceable to merge commit `90befdda...` and artifact `8746021488`.

```text
repair identified != repair applied
repair applied != run 7 reactivated
repair merged != run 8 authorized
```

## Concurrent repository state

At reconciliation start, PR #225 had merged as commit `2b8477109052278d01c93fc8041cdb6b0ad12389`; open work included PR #227 for one interactive ServiceTracer Lab Factory preflight authorization. That work does not authorize an Azure AI retry.

## Failure, rollback, and cleanup

No Azure rollback or cleanup is required because no Azure mutation occurred. Repository rollback is an ordinary revert of the run-7 implementation or reconciliation commits if needed.

A later Azure attempt must:

1. start from current `main`;
2. consume a fresh explicit user instruction;
3. use a new attempt ID and workflow;
4. verify the direct account-scoped role with valid CLI syntax;
5. re-query model lifecycle, capacity, deployment inventory, account state, and cost context;
6. remain one-shot with no GitHub Re-run authority.

## Canonical distinctions

```text
role query failed != role missing
Azure login succeeded != workflow completed
account exists != model deployed
executor repaired != retry authorized
run7 consumed != run8 authorized
estimated cost != actual cost
```
