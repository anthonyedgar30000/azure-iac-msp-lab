# Canonical current reality v2

## Repository truth

- Current main: `2f5b60c1d8328d13823e2cc1def09e6be384ecb5` after PR #132.
- Exact reviewed source: `6b7bd5362b17c9edfc0b41da65d5b798e5d00b45`.
- Exact-head CI: `30204497860` / success.
- Merge-commit CI: not observed.
- No open pull requests were observed before this truth lock.
- PRs #129 through #132 were observed as external merges; this assistant did not invoke their merge actions.

## Collector and provenance boundary

The collector golden path remains deployed from source `98b092201053fd3592be157a24de6e623e6b74a6` and healthy at `https://st-demo-api-aeg30000.westus2.cloudapp.azure.com/api/demo/run`. PR #130 added the repository provenance monitor, Azure-host identity contract, source-ref proof, and request correlation. PRs #131 and #132 repaired its fail-closed proof wording; PR #132 exact-head CI passed.

The new provenance contract is **repository-only**. No new Azure authentication, query, mutation, deployment, or browser replay was performed.

```text
repository_implemented != deployed_to_collector_VM
API_healthy != Azure_host_identity_verified
request_sent != response_correlation_verified
monitor_rendered != browser_path_verified
PR_merged != exact_head_CI_passed
```

## Remaining gate

Capture fresh Azure/cost evidence and an exact-source What-If, obtain one-shot deployment and rollback authority, deploy the provenance contract, then verify host identity, source binding, request correlation, browser rendering, monitoring delivery, and actual cost.
