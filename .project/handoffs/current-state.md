# Current project handoff

## Workspace hierarchy

- Umbrella conversational workspace: **HELIX — Governed Agent Engineering**.
- Bounded repository workstream: **ServiceTracer — Governed Azure Operations Lab**.
- ChatGPT project context supports reasoning, review routing, and continuity.
- GitHub, pull requests, CI, and `.project/` determine implementation and coordination state.
- Current Azure control-plane, guest, workflow-artifact, cost, health, configuration, and operational evidence determine deployed and runtime state.
- Moving a conversation between projects does not authorize repository changes, workflow dispatch, or Azure mutation.

## Trusted baseline observation

- Branch: `main`
- Verified main commit when this reconciliation began: `f40ef0fab0ae920c23f4b6556c25dc4f3b99b68b`
- Latest completed increment at that observation: PR #25, fail-closed collector replacement execution design
- The recorded SHA is an observation anchor. Live GitHub state determines the current `main` head after this reconciliation is merged.

## Recently completed

- PR #19: repository-native workflow observability in `.project/`.
- PR #20: desired collector image contract, immutable-image drift guard, and read-only replacement planning.
- PR #21: HELIX retrieval classes, promotion rules, and explicit-only archive boundary in `.helix/`.
- PR #22: project state, handoff, implementation status, and retrieval freshness reconciliation.
- PR #23: promoted planner evidence, four-lens review, corrected live VM size, preservation blockers, identity requirements, and cost boundaries.
- PR #24: canonical six-stream ServiceTracer workstream catalog and validator enforcement.
- PR #25: fail-closed collector replacement authority contract, inactive workflow candidate, deterministic validator, tests, and design documentation.
- Collector replacement plan run `29856203054`: successful read-only Azure inventory and replacement assessment with no Azure mutations authorized or performed.

## Runtime and deployment state

- The current Azure control-plane observation shows collector VM size `Standard_B2ats_v2`.
- The earlier `Standard_B1ms` record is retained as historical evidence of a previously verified working size.
- The last guest-level verification still records ServiceTracer `0.4.0` with manual Python and certificate repairs; the planner did not re-verify guest health or version.
- The deployed collector uses Canonical Ubuntu 22.04 Jammy while the desired contract uses Canonical Ubuntu 24.04. Replacement is required.
- The evidence disk is attached, uses detach-on-delete semantics, and has restrictive public/network access settings. It must be preserved and protected by a verified recovery point.
- The NIC has static private addressing but is configured to be deleted with the VM. NIC preservation or deterministic recreation remains an execution blocker.
- The VM uses a system-assigned identity. No visible role assignments were returned, and any required publication access must be recreated for the replacement identity.
- The current OS disk allows public network access; the replacement design requires hardening.
- No collector replacement execution is authorized or evidenced.

## Evidence record

- Sanitized review: `docs/reviews/collector-replacement-plan-2026-07-21.md`
- Workflow run ID: `29856203054`
- Artifact: `collector-replacement-plan-29856203054-1`
- Artifact SHA-256: `76f3b44e6e97e906dac6d62eeb212a6bc55265e77271a030b9c45b0cacf55637`
- Raw artifact remains in protected GitHub Actions storage and is not committed because it contains sensitive environment identifiers.

## Merged replacement-design state

- Design contract: `infra/replacement/collector-replacement-contract.json`
- Validator: `infra/replacement/validate_execution_design.py`
- Candidate workflow: `infra/workflow-designs/collector-replacement-execution.yml`
- Active workflow path: absent.
- Dispatch authorized: `false`.
- Azure mutations authorized: `false`.
- Promotion ready: `false`.
- The candidate is outside `.github/workflows`, exits before Azure authentication, and contains no Azure mutation commands.
- CI verifies authority, evidence anchoring, phase ordering, cost ceilings, cleanup limits, independent review lenses, inactive workflow location, and unresolved rollback state.

## Intended post-merge coordination state

- No implementation branch retains write ownership.
- Legacy draft PR #1 remains explicit-only and non-current.
- The next implementation or design increment must create a new bounded branch, declare its permitted paths and verification criteria, and add a new active-work entry.
- This reconciliation changes metadata and orientation only; it does not change implementation source, active workflows, Azure resources, budgets, billing alerts, action groups, or runtime behavior.

## Unresolved blocker

Rollback must be selected and tested before workflow promotion:

1. temporarily preserve the old OS disk and use a non-conflicting replacement OS-disk name; or
2. create and verify an OS-disk snapshot, reuse the canonical OS-disk name, and prove deterministic prior-VM recreation.

This decision affects naming convergence, recovery, temporary cost, and cleanup. The merged design remains `promotion_ready: false` until it is resolved.

## Next bounded gate

1. Merge the state-only reconciliation only after CI validates repository state, existing tests, replacement-design tests, and Bicep build.
2. Perform separate evidence-quality, operations/recovery, security/identity, and Azure-cost reviews of the merged design.
3. Resolve rollback and canonical OS-disk naming in a separate bounded branch with tests.
4. Define pre-maintenance guest/control-plane evidence and independently testable recovery verification.
5. Use a separate authority-changing PR for any move into `.github/workflows`, Azure authentication, or mutation implementation.
6. Obtain separate explicit human authorization before any future mutation-capable workflow dispatch.

## Prohibited next step

Do not move the candidate workflow into `.github/workflows`, add Azure login or mutation commands, use the generated `REPLACE:` phrase, create snapshots, change delete options, delete the VM, detach disks, deploy replacement resources, or modify budgets and billing alerts merely because PR #25 merged.
