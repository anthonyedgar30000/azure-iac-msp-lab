# Current project handoff

## Trusted baseline observation

- Branch: `main`
- Verified main commit when this refresh began: `50a4789e87cdadd7d537179882427b3b2cb4b96f`
- Latest completed increment at that observation: PR #24, canonical ServiceTracer workspace streams
- The recorded SHA is an observation anchor. Live GitHub state determines the current `main` head after this design is merged.

## Recently completed

- PR #19: repository-native workflow observability in `.project/`.
- PR #20: desired collector image contract, immutable-image drift guard, and read-only replacement planning.
- PR #21: HELIX retrieval classes, promotion rules, and explicit-only archive boundary in `.helix/`.
- PR #22: project state, handoff, implementation status, and retrieval freshness reconciliation.
- PR #23: promoted planner evidence, four-lens review, corrected live VM size, preservation blockers, identity requirements, and cost boundaries.
- PR #24: canonical **ServiceTracer — Governed Azure Operations Lab** identity, exact six-stream catalog, and validator enforcement.
- Collector replacement plan run `29856203054`: successful read-only Azure inventory and replacement assessment with no Azure mutations authorized or performed.

## Runtime and deployment state

- The current Azure control-plane observation shows collector VM size `Standard_B2ats_v2`.
- The earlier `Standard_B1ms` record is retained as historical evidence of a previously verified working size.
- The last guest-level verification still records ServiceTracer `0.4.0` with manual Python and certificate repairs; the planner did not re-verify guest health or version.
- The deployed collector uses Canonical Ubuntu 22.04 Jammy while the desired contract uses Canonical Ubuntu 24.04. Replacement is required.
- The evidence disk is attached, uses detach-on-delete semantics, and has restrictive public/network access settings. It must be preserved and protected by a verified recovery point.
- The NIC has static private addressing but is configured to be deleted with the VM. NIC preservation or deterministic recreation is an execution blocker.
- The VM uses a system-assigned identity. No visible role assignments were returned, and any required publication access must be recreated for the replacement identity.
- The current OS disk allows public network access; the replacement design must harden this setting.
- No collector replacement execution is authorized or evidenced.

## Evidence record

- Sanitized review: `docs/reviews/collector-replacement-plan-2026-07-21.md`
- Workflow run ID: `29856203054`
- Artifact: `collector-replacement-plan-29856203054-1`
- Artifact SHA-256: `76f3b44e6e97e906dac6d62eeb212a6bc55265e77271a030b9c45b0cacf55637`
- Raw artifact remains in protected GitHub Actions storage and is not committed because it contains sensitive environment identifiers.

## Current bounded work

- Branch: `feature/collector-replacement-execution-design`
- Pull request: `#25`
- Purpose: design and test a fail-closed replacement execution contract.
- Candidate workflow: `infra/workflow-designs/collector-replacement-execution.yml`
- Active workflow path: absent.
- Dispatch authorized: `false`.
- Azure mutations authorized: `false`.
- The candidate exits before Azure authentication and contains no Azure mutation commands.
- CI validates the machine-readable phase, authority, evidence, cost, cleanup, rollback, and canonical workspace boundaries.

## Design decisions

- Workflow design is intentionally stored outside `.github/workflows` so GitHub cannot dispatch it.
- Promotion into an active workflow is a separate authority-changing pull request.
- Temporary policy ceilings are CAD 10, at most two snapshots and 96 GiB total snapshot capacity, zero minutes of overlapping compute, and 24 hours of recovery-resource retention.
- Azure budgets, billing alerts, action groups, and billing configuration remain outside the execution scope.
- The `REPLACE:` phrase remains reference data only.

## Unresolved blocker

Rollback must be chosen and tested before workflow promotion:

1. temporarily preserve the old OS disk and use a non-conflicting replacement OS-disk name; or
2. create and verify an OS-disk snapshot, reuse the canonical OS-disk name, and prove deterministic prior-VM recreation.

This decision affects naming convergence, recovery, temporary cost, and cleanup. The design remains `promotion_ready: false` until it is resolved.

## Next bounded gate

1. Pass refreshed CI for the canonical workspace validator, contract validator, inactive workflow location, phase ordering, cost ceilings, and fail-closed behavior.
2. Review the design separately under evidence, operations/recovery, security/identity, and Azure-cost lenses.
3. Merge only the design contract and tests if accepted.
4. Resolve rollback and the remaining blockers in later bounded work.
5. Use a separate PR for any move into `.github/workflows`, Azure authentication, or mutation implementation.

## Prohibited next step

Do not move the candidate workflow into `.github/workflows`, add Azure login or mutation commands, use the generated `REPLACE:` phrase, create snapshots, change delete options, delete the VM, detach disks, or deploy replacement resources in this workstream.
