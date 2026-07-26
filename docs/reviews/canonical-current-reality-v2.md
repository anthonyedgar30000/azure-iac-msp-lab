# Canonical current reality v2

## Current authority

`.project/state-index.json` continues to select the versioned v2 current-reality, completion-gate, and handoff files. Legacy filenames remain historical compatibility snapshots.

## Post-merge repository truth

- Observed main: `81df65ca7d4cd77fc89aefb2fac128ead456df7d` after PR #126.
- PR #126 exact source: `1f9a00f572235c74b99520a504d8b057003d411c`.
- Exact-head CI: `30203751115` / success.
- Merge-commit CI: not observed.
- PR #127 was observed open as a draft and is not accepted as deployed or validated evidence.
- The PR #126 merge was observed externally; this assistant did not invoke the merge action.

## Collector facts preserved

- Collector exact deployed source: `98b092201053fd3592be157a24de6e623e6b74a6`.
- Deployment run: `30196388398`; artifact `8630260279`; 48/48 manifest payloads verified.
- Collector extension and backend pool converged.
- Collector API endpoint: `https://st-demo-api-aeg30000.westus2.cloudapp.azure.com/api/demo/run`.
- Merged main now binds the normal frontend to that collector endpoint.
- Health, HTTPS request, CORS, and one 20-attempt response were observed.
- All 20 downstream attempts failed; stable localization was not established and no exact root cause was claimed.
- PR #123 was consumed and closed before browser execution.
- The independent VM API is not the collector golden path.

```text
workflow_failed != deployment_failed
API_health_verified != downstream_transaction_success_verified
independent_API_ready != collector_golden_path_verified
frontend_bound != browser_verified
human_or_external_merge_observed != assistant_merge_action
```

## Remaining gate

Observe the exact collector binding on GitHub Pages, obtain a new one-shot browser grant, preserve bounded browser evidence, verify monitoring delivery, and capture actual cost or remaining student credit in CAD.
