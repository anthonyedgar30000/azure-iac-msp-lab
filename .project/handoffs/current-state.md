# Current project handoff

## Trusted baseline observation

- Branch: `main`
- Verified main commit when this refresh began: `d9b952e324b7128300e1c888d5834536fb35fc30`
- Latest completed increment at that observation: PR #21, HELIX retrieval and archive governance
- The recorded SHA is an observation anchor. Live GitHub state determines the current `main` head after this refresh is merged.

## Recently merged

- PR #19: repository-native workflow observability in `.project/`.
- PR #20: desired collector image contract, immutable-image drift guard, and read-only replacement planning.
- PR #21: HELIX retrieval classes, promotion rules, and explicit-only archive boundary in `.helix/`.

## Runtime and deployment state

- The operationally verified collector VM size remains `Standard_B1ms`.
- The last verified Azure collector remains ServiceTracer `0.4.0` with manual Python and certificate repairs.
- The Ubuntu 24.04 collector definition and ServiceTracer `0.5.0` path are implemented and CI-verified, but replacement deployment has not been operationally verified.
- An observed Azure deployment attempt encountered an immutable `imageReference` change and motivated PR #20. The exact workflow artifact has not yet been promoted into `.project/` evidence.
- The read-only collector replacement planner is implemented and CI-verified but has not been recorded as run against the target Azure environment.
- The public-report endpoint and managed-identity publishing path are implemented and CI-verified but are not recorded as deployed or operationally verified in Azure.
- No collector replacement execution is authorized or evidenced.

## Repository governance state

- `.project/` records active work, environment facts, handoffs, and deployment history.
- `.helix/` governs retrieval authority, candidate promotion, and archive exclusion.
- Git and CI establish implementation and automated-test evidence.
- Azure workflow artifacts and runtime verification establish deployment and operational evidence.
- Legacy draft PR #1 is not current implementation work. Review it for unique durable evidence before closing it as superseded through a separate explicit action.

## Current bounded work

No implementation workstream currently owns an Azure mutation path. This state-refresh branch updates metadata and documentation only.

## Next bounded operation

Run the manual **Collector replacement plan** workflow using:

```text
PLAN:rg-servicetracer-dev-westus2:vm-stcollector-mst-dev
```

This operation is planning-only. It must not authorize or perform Azure mutations.

Review the resulting evidence under these separate lenses:

- evidence quality and completeness;
- operations, recovery, and evidence-disk preservation;
- security, managed identity, and RBAC restoration;
- Azure cost and temporary-resource implications.

Promote the bounded findings into `.project/environment-state.json`, `deployment-history.jsonl`, and a scoped review artifact before designing any replacement-execution branch.

## Prohibited next step

Do not run ordinary Deploy or create a mutation-capable replacement workflow merely because the planner is merged. Replacement execution requires a separate branch, verified recovery evidence, explicit human authorization, and post-change verification gates.
