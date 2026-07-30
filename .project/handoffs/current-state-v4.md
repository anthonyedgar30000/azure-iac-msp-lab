# Current project handoff v4

## Interpretation boundary

This is the authoritative repository and evidence handoff selected by `.project/CURRENT.json` after PR #253 merged the Azure for Students-only ServiceTracer planning boundary.

```text
repository record != continuously refreshed Azure dashboard
merged planner != dispatched planner
declared single-subscription boundary != fresh runtime subscription proof
same subscription != same resource lifecycle
ARM What-If != Azure mutation
planning evidence != deployment authority
not observed != absent
```

## Authoritative files

```text
selector: .project/CURRENT.json
current reality: .project/current-reality-v5.json
state index: .project/state-index-v14.json
current handoff: .project/handoffs/current-state-v4.md
completion gate: .project/lab-v1-completion-gate-v2.json
repository sync: .project/reconciliations/post-pr253-student-subscription-sync-20260730.json
latest operational overlay: .project/reconciliations/servicetracer-demo-api-plan-run1-terminal-20260730.json
ServiceTracer terminal: .project/reconciliations/servicetracer-demo-api-plan-run1-terminal-20260730.json
Azure AI terminal: .project/reconciliations/azure-ai-go-live-run8-terminal-20260730.json
historical post-PR251 selector: .project/selectors/post-pr251-current.json
```

## Repository watermark

```text
repository: anthonyedgar30000/azure-iac-msp-lab
observed main: af4b050ab18110882e3551f66c69eb2b73a73f7b
latest merged PR: #253
latest merged source head: 161c447a445d86364719d3d414ac6c7f6628e7b8
PR #253 CI: 30516607869 / success
Azure MCP reality bridge contract: 30516607858 / success
Lab Factory local MCP smoke: 30516607834 / success
open pull requests observed before this sync: none
merge-commit push CI: not observed by the available connector lookup
local working tree: not observed through connector
```

## Corrected ServiceTracer planning boundary

PR #253 replaced the Pay-As-You-Go dual-subscription design with the requested Azure for Students-only design.

```text
Azure for Students
├── rg-servicetracer-<environment>-westus2
│   └── existing ServiceTracer dependency, read only for planning
└── rg-st-demo-api-<environment>-westus2
    └── proposed independent API workload
```

The repository contract is now:

```text
GitHub environment: azure-lab
identity secrets: AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID
Azure login count: 1
subscription boundary: single_subscription
provider validation level: ProviderNoRbac
ARM validation capability: present
ARM What-If capability: present
deployment command: absent
RBAC mutation command: absent
cleanup command: absent
```

The corrected planner has not been dispatched. Therefore, current provider registration, policy effects, quota, SKU availability, target-resource inventory, ARM validation, and What-If are not yet established for this corrected boundary.

## Protected `azure-lab` evidence

The recent Azure AI run 8 workflow used:

```text
environment: azure-lab
client-id: AZURE_CLIENT_ID
tenant-id: AZURE_TENANT_ID
subscription-id: AZURE_SUBSCRIPTION_ID
```

Run `30510660758` recorded:

```text
subscription name: Azure for Students
subscription state: Enabled
```

This is time-bounded execution evidence supporting the `azure-lab` subscription binding. It does not disclose the secret values, prove the present administrator configuration, or authorize a new ServiceTracer planning run.

## Historical ServiceTracer planning run 1

The prior one-shot planner run remains historical evidence for the superseded dual-subscription design:

```text
workflow run: 30513630134 / attempt 1
artifact: 8748027710
failure class: confirmation_input_mismatch
old boundary: dual_subscription
Azure login started: false
ARM validation performed: false
ARM What-If performed: false
Azure mutation/deployment observed: false
authority consumed: true
rerun authorized: false
deployment authorized: false
```

Do not rerun that consumed attempt. A corrected single-subscription planning run is a new operation requiring new exact authority.

## Cost, credit, quota, and operational unknowns

This repository correction has an expected recurring Azure resource cost delta of CAD $0. It did not query Azure or create resources.

Still unverified for the corrected planner:

```text
current student credit
actual Azure cost
current tenant and subscription context for ServiceTracer
current Compute and Network provider state
inherited policy effects
westus2 VM SKU availability
regional and VM-family quota
public-IP quota
dependency endpoint state
target resource-group state
ARM validation result
ARM What-If result
monitoring alert delivery
backup or recovery
```

The CAD `$25.00` planner ceiling remains a human planning limit only. It is not a price assertion, budget control, or spend authority.

## Authority after sync

```text
active ServiceTracer planning authority: none
active deployment authority: none
active cleanup authority: none
workflow dispatch performed by this sync: false
Azure login/query performed by this sync: false
ARM What-If performed by this sync: false
Azure mutation performed by this sync: false
GitHub environment or secret mutation performed: false
RBAC mutation performed: false
```

## Next gate

A new ServiceTracer planning attempt requires fresh explicit one-attempt read-only authority bound to the exact current `main` SHA and exact confirmation string. The run must verify that Azure reports `Azure for Students` and `Enabled`, then capture dependency, provider, policy, quota, SKU, target inventory, ARM validation, and bounded What-If evidence.

Deployment remains a separate later decision requiring accepted planning evidence, student-credit and cost review, least-privilege write identity review, rollback and cleanup procedures, runtime health/TLS/dependency/CORS/browser validation, and explicit deployment authorization.
