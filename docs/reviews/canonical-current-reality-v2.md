# Canonical current reality v2

This increment introduces an explicit state index so current operational consumers no longer mistake historical filenames for live authority.

```text
.project/state-index.json
├── canonical current reality → .project/current-reality-v2.json
├── canonical completion gate → .project/lab-v1-completion-gate-v2.json
└── canonical handoff → .project/handoffs/current-state.md
```

The existing `.project/current-reality.json` and `.project/lab-v1-completion-gate.json` remain unchanged historical compatibility snapshots. Their existing tests continue to validate the decisions and observations they originally represented.

The v2 current view promotes:

- `main@9bfff60bd2e1e3bbf5610807df7d970c9bd9f229` and merged PR #120;
- exact-source CI run `30194713992`;
- collector What-If run `30192970923`;
- artifact `8629191915` and verified `29/29` payload hashes;
- the exact three-resource accepted plan;
- the observed empty backend pool and failed extension;
- unresolved cost, credit, deployment source, deployment outcome, and runtime health.

No execution authority is created.

```text
canonical_state_advanced != Azure_state_refreshed
artifact_verified != deployment_authorized
legacy_snapshot_preserved != legacy_snapshot_current
```
