# Independent Demo API — West US 2 / F1alsv7 Reconciliation

Date: `2026-07-24`

## Bounded objective

Select and prepare a new read-only planner package for `westus2` and `Standard_F1als_v7` after the prior protected run rejected the old `eastus` / `Standard_B2ats_v2` package.

This record does not authorize workflow dispatch, Azure authentication, Azure mutation, deployment, cleanup, guest commands, or endpoint promotion.

## Synchronized repository reality

- current `main`: `551ca0ee2c7d1955b3bd81c09f46f43dceeae3a6`;
- PR #76 promoted protected planner evidence into durable project state at that commit;
- PR #76 source `1ca93552ae1a445922248ff4409706e203609f70` changed five `.project/` paths;
- PR #77 is concurrently open but was rebuilt into five added Azure MCP-specific paths;
- PR #75 and PR #77 therefore have no changed-file overlap at this watermark;
- this increment records its candidate decision in `.project/reconciliations/independent-demo-api-westus2-f1alsv7.json` without modifying shared active-work, environment-state, or the current handoff.

```text
concurrent_nonoverlap != either_pull_request_merged
competing_work_observed != permission_to_ignore_freshness
```

## Protected planner evidence

Run `30064289707`, attempt 1:

- dispatch SHA `323b3892c6efd598231037f23281d49608ceb570`;
- artifact ID `8585693830`;
- artifact digest `sha256:7aae2cff0df757a4b436c5b87507162624813e64bd32946bada8a87e5d7adc22`;
- dependency and target OIDC logins succeeded;
- dependency state and target readiness inputs were captured;
- the old `eastus` / `Standard_B2ats_v2` request was rejected before ARM validation and What-If;
- no Azure mutation or deployment was authorized or performed.

Functional access was observed for that run. Exact effective least-privilege RBAC scope remains unverified.

## Human-observed candidate evidence

The read-only Cloud Shell checks selected:

```text
target subscription: Azure subscription 1
offer: PayAsYouGo_2014-09-01
region: westus2
candidate: Standard_F1als_v7
```

Observed:

```text
restrictions: []
family: StandardFalsv7Family
vCPU: 1
memory: 2 GiB
PremiumIO: True
regional vCPU quota: 0 / 10
family vCPU quota: 0 / 10
Standard IPv4 public-IP quota: 0 / 20
```

Rejected alternatives:

```text
Standard_B2ats_v2: Basv2-family quota 0 / 0
Standard_F2s_v2: NotAvailableForSubscription at westus2
```

No Azure resource creation or modification command was run.

```text
manual_cloud_shell_observation != protected_workflow_artifact
sku_unrestricted != quota_reserved
candidate_selected != deployment_authorized
```

## Repository changes

- pin workflow input defaults and guards to `westus2` / `Standard_F1als_v7`;
- pin the subscription-scope Bicep defaults to the same package;
- add regression coverage for workflow, Bicep, candidate evidence, authority, and concurrent path ownership;
- add a typed, non-overlapping reconciliation record;
- update workload and subscription-boundary documentation.

## Remaining blockers

- target resource-group state in `westus2` is not authoritatively observed;
- no protected planner artifact exists for the selected package;
- no ARM validation or What-If exists for the selected package;
- current quota is not reserved;
- exact effective Reader scope is not verified;
- subscription-specific cost is not verified;
- no workload resource or service health is verified.

## Authority

```text
repository_increment_authorized = true
pull_request_creation_authorized = true
pull_request_merge_authorized = false
workflow_dispatch_authorized = false
Azure_authentication_authorized = false
Azure_mutations_authorized = false
deployment_authorized = false
cleanup_authorized = false
endpoint_promotion_authorized = false
```

## Next gate

After exact-head CI and human merge review, re-resolve `main` and both open PRs, then separately request authorization to dispatch the read-only planner. A successful What-If will still not authorize deployment.
