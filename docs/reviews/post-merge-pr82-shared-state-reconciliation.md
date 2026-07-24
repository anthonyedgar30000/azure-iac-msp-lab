# Post-merge PR #82 shared-state reconciliation

## Decision

Promote a new canonical current-reality synthesis after PR #82 without rewriting historical planner evidence into falsehood.

## Root cause

The repository intentionally promoted public-runtime and authenticated control-plane evidence into dedicated files while leaving the older shared planner views untouched. That preserved provenance, but it created a state-view divergence:

```text
historical East US candidate rejection
!=
later West US 2 deployed reality
```

The old planner evidence remains true for its exact candidate and observation time. It is no longer the current deployment view.

## Evidence resolution

The reconciliation combines two independent channels:

1. protected public-runtime evidence from workflow run `30086152352`;
2. operator-authenticated Azure control-plane inventory completed at `2026-07-24T16:40:36Z`.

Together they establish deployment provenance, endpoint identity, VM existence and running control-plane state, TLS, health, CORS, and the governed transaction protocol.

They do not establish backend transaction success, exact root cause, guest configuration, effective least privilege, backup, recovery, alert delivery, or actual cost.

## Repository relationship

```text
deployed source: 8b3d55c616d8820edd523f77021a35fe24167bd0
current main: 5dfa3b76a9fb975002d9cd702a892a0f678c88c5
main ahead: 18
main behind: 0
workload or IaC path difference observed: false
```

The difference is evidence and governance advancement rather than observed workload-content drift.

## Implementation

- add `.project/current-reality.json` as the canonical current synthesis;
- update the primary handoff;
- append the authenticated deployment event to durable history;
- add a typed reconciliation record;
- validate exact evidence anchors, state boundaries, and fail-closed authority;
- preserve the old planner data as historical evidence.

## Authority and rollback

This is repository-only work. It performs no Azure login, workflow dispatch, guest command, transaction replay, resource mutation, deployment, or cleanup.

Rollback is closing or reverting the pull request. No Azure rollback is required.
