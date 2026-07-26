# Canonical current reality v2

## Current authority

`.project/state-index.json` selects the versioned v2 current-reality, completion-gate, handoff, and latest reconciliation files. Legacy filenames remain historical compatibility snapshots.

## Post-merge repository truth

- Observed main: `2f5b60c1d8328d13823e2cc1def09e6be384ecb5` after PR #132.
- Latest exact source: `6b7bd5362b17c9edfc0b41da65d5b798e5d00b45`.
- Exact-head CI: `30204497860` / success.
- Source-versus-merge file-content difference observed: false.
- Merge-commit CI: not observed.
- Open pull requests observed: none.
- The merge was performed by `anthonyedgar30000`; this assistant did not invoke the merge action.
- Local working tree: not observed.

## Failed-head merge chain preserved

- PR #130 exact source `07e7056b3d66e88055f93d7f3c27d31f8281c316` merged as `ede8b7b32fe4dfe0e817d224a3cf9a9c1c6b9489` even though CI run `30204308669` failed.
- PR #131 exact source `bec88217096dce5ac205b93bb5f019f0f801fe62` merged as `1accc46f2c4b585510f3b0919a15467a4e5d5769` even though CI run `30204440155` failed.
- Both failures were bounded to the deterministic frontend proof wording contract.
- PR #132 exact source `6b7bd5362b17c9edfc0b41da65d5b798e5d00b45` supplied the exact phrase required by the validator and passed CI run `30204497860`.
- PR #132 merged as `2f5b60c1d8328d13823e2cc1def09e6be384ecb5` with no observed file-content difference from the green source head.

```text
PR_merged != exact_head_CI_passed
green_repair_merged != prior_failed_heads_never_existed
```

## Collector facts preserved

- Collector exact deployed source: `98b092201053fd3592be157a24de6e623e6b74a6`.
- Deployment run: `30196388398`; artifact `8630260279`; 48/48 manifest payloads verified.
- Resource group: `rg-servicetracer-dev-westus2`; region: `westus2`.
- Collector VM: `vm-stcollector-mst-dev`.
- Collector endpoint: `https://st-demo-api-aeg30000.westus2.cloudapp.azure.com/api/demo/run`.
- Health, HTTPS request, CORS, and one 20-attempt API response were observed.
- All 20 downstream attempts failed; stable localization was not established and no exact root cause was claimed.
- Current billing cost and remaining Azure for Students credit remain not observed.

## Provenance monitor boundary

The repository now contains the provenance monitor, expected Azure host identity, IMDS-based runtime identity collection, exact deployed-source binding, and UUID header/payload correlation contract. That capability is not yet deployed or browser-verified.

```text
repository_implemented != deployed_to_collector_VM
monitor_rendered != provenance_contract_deployed
expected_resource_group != observed_resource_group
request_sent != response_correlation_verified
```

No fresh Azure authentication, subscription or tenant lookup, resource query, quota query, cost query, mutation, deployment, browser replay, rollback, RBAC change, or cleanup occurred in this reconciliation.

## Remaining gate

Select one exact provenance deployment source, capture fresh Azure state/quota/cost evidence and a new FullResourcePayloads What-If, obtain one-shot non-renewing deployment and rollback authority, then verify the deployed health identity and one browser request-correlation path without automatic retry.
