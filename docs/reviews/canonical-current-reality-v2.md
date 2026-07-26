# Canonical current reality v2

## Current authority

`.project/state-index.json` continues to select the versioned v2 current-reality, completion-gate, and handoff files. Legacy filenames remain historical compatibility snapshots.

## Reconciled facts

- Observed main: `855ef85f898cbf34db2931abc8344d05cb05c6f7` after PR #125.
- Collector exact deployed source: `98b092201053fd3592be157a24de6e623e6b74a6`.
- Deployment run: `30196388398`; artifact `8630260279`; 48/48 manifest payloads verified.
- Collector extension and backend pool converged.
- Collector API endpoint: `https://st-demo-api-aeg30000.westus2.cloudapp.azure.com/api/demo/run`.
- Health, HTTPS request, CORS, and one 20-attempt response were observed.
- All 20 downstream attempts failed; stable localization was not established and no exact root cause was claimed.
- PR #123 was consumed and closed before browser execution.
- The independent VM API is not the collector golden path.

```text
workflow_failed != deployment_failed
API_health_verified != downstream_transaction_success_verified
independent_API_ready != collector_golden_path_verified
frontend_bound != browser_verified
```

## Remaining gate

Publish the corrected collector binding, obtain a new one-shot browser grant, preserve bounded browser evidence, verify monitoring delivery, and capture actual cost or remaining student credit in CAD.
