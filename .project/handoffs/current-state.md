# Current project handoff

## Trusted baseline observation

- Branch: `main`
- Verified main commit when this reconciliation began: `93fcdaf6c1d99f88f3ae8c34f86533a020e1a29a`
- Latest completed increment at that observation: PR #22, project-state refresh after governance merges
- The recorded SHA is an observation anchor. Live GitHub state determines the current `main` head after this reconciliation is merged.

## Recently completed

- PR #19: repository-native workflow observability in `.project/`.
- PR #20: desired collector image contract, immutable-image drift guard, and read-only replacement planning.
- PR #21: HELIX retrieval classes, promotion rules, and explicit-only archive boundary in `.helix/`.
- PR #22: project state, handoff, implementation status, and retrieval freshness reconciliation.
- Collector replacement plan run `29856203054`: successful read-only Azure inventory and replacement assessment with no Azure mutations authorized or performed.

## Runtime and deployment state

- The current Azure control-plane observation shows collector VM size `Standard_B2ats_v2`.
- The earlier `Standard_B1ms` record is retained as historical evidence of a previously verified working size.
- The last guest-level verification still records ServiceTracer `0.4.0` with manual Python and certificate repairs; the planner did not re-verify guest health or version.
- The deployed collector uses Canonical Ubuntu 22.04 Jammy while the desired contract uses Canonical Ubuntu 24.04. Replacement is required.
- The evidence disk is attached, uses detach-on-delete semantics, and has restrictive public/network access settings. It must be preserved and protected by a verified recovery point.
- The NIC has static private addressing but is configured to be deleted with the VM. NIC preservation or deterministic recreation is an execution blocker.
- The VM uses a system-assigned identity. No visible role assignments were returned, and any required publication access must be recreated for the replacement identity.
- The current OS disk allows public network access; the replacement design should harden this setting.
- No collector replacement execution is authorized or evidenced.

## Evidence record

- Sanitized review: `docs/reviews/collector-replacement-plan-2026-07-21.md`
- Workflow run ID: `29856203054`
- Artifact: `collector-replacement-plan-29856203054-1`
- Artifact SHA-256: `76f3b44e6e97e906dac6d62eeb212a6bc55265e77271a030b9c45b0cacf55637`
- Raw artifact remains in protected GitHub Actions storage and is not committed because it contains sensitive environment identifiers.

## Repository governance state

- `.project/` records active work, environment facts, handoffs, and deployment history.
- `.helix/` governs retrieval authority, candidate promotion, and archive exclusion.
- Git and CI establish implementation and automated-test evidence.
- Azure workflow artifacts and runtime verification establish deployment and operational evidence.
- Legacy draft PR #1 remains non-current and requires a separate evidence review before closure.

## Current bounded work

This branch reconciles evidence and documentation only. It does not change infrastructure, application behavior, workflows, tests, budgets, alerts, or Azure resources.

## Next bounded operation

Design and test a separate collector replacement-execution branch **without dispatching it**. The design must include:

- guest service and evidence-mount preflight;
- a verified evidence-disk recovery point before destructive action;
- explicit NIC preservation or deterministic recreation;
- replacement managed-identity and RBAC restoration;
- replacement OS-disk public-access hardening;
- temporary-resource cost ceiling, owner, and cleanup deadline;
- rollback and post-change verification evidence;
- exact human confirmation and protected-environment approval.

## Prohibited next step

Do not use the generated `REPLACE:` confirmation phrase, rerun ordinary Deploy, delete the VM, detach disks, create snapshots, or create replacement resources merely because the planning run succeeded. Execution requires a separately reviewed implementation, verified preconditions, and explicit human authorization.
