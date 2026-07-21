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
- Verified main commit when this branch began: `00ebc068f4aec4eda8cda723d8dc4d974a4cb7c6`
- Latest completed increment: PR #26, state reconciliation and HELIX workspace hierarchy
- The recorded SHA is an observation anchor. Live GitHub state determines the current `main` head.

## Active bounded increment

- Branch: `design/collector-rollback-snapshot-recreation`
- Write owner: ServiceTracer — Governed Azure Operations Lab conversation
- Objective: select and formalize the OS-disk snapshot/recreation rollback strategy and canonical OS-disk naming.
- Current status: implementation in progress; CI and independent review pending.
- Permitted scope: replacement contract, validator, focused tests, rollback design/review documentation, active-work state, and this handoff.
- Protected scope: `.github/workflows/**`, Bicep modules, application source, credentials, deployment scripts, and Azure resources.

## Recently completed

- PR #19: repository-native workflow observability in `.project/`.
- PR #20: desired collector image contract, immutable-image drift guard, and read-only replacement planning.
- PR #21: HELIX retrieval classes, promotion rules, and explicit-only archive boundary in `.helix/`.
- PR #22: project state, handoff, implementation status, and retrieval freshness reconciliation.
- PR #23: promoted planner evidence, four-lens review, corrected live VM size, preservation blockers, identity requirements, and cost boundaries.
- PR #24: canonical six-stream ServiceTracer workstream catalog and validator enforcement.
- PR #25: fail-closed collector replacement authority contract, inactive workflow candidate, deterministic validator, tests, and design documentation.
- PR #26: released the prior branch, reconciled PR #25 state, and established the HELIX umbrella/ServiceTracer workstream hierarchy.
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
- The current OS-disk size, generation, security type, encryption configuration, and snapshot recoverability are not yet established by repository evidence.
- No collector replacement execution is authorized or evidenced.

## Evidence record

- Sanitized planner review: `docs/reviews/collector-replacement-plan-2026-07-21.md`
- Rollback decision review: `docs/reviews/collector-replacement-rollback-decision-2026-07-21.md`
- Workflow run ID: `29856203054`
- Artifact: `collector-replacement-plan-29856203054-1`
- Artifact SHA-256: `76f3b44e6e97e906dac6d62eeb212a6bc55265e77271a030b9c45b0cacf55637`
- Raw artifact remains in protected GitHub Actions storage and is not committed because it contains sensitive environment identifiers.

## Replacement-design state

- Design contract: `infra/replacement/collector-replacement-contract.json`
- Validator: `infra/replacement/validate_execution_design.py`
- Candidate workflow: `infra/workflow-designs/collector-replacement-execution.yml`
- Active workflow path: absent.
- Dispatch authorized: `false`.
- Azure mutations authorized: `false`.
- Promotion ready: `false`.
- The candidate is outside `.github/workflows`, exits before Azure authentication, and contains no Azure mutation commands.
- Selected rollback strategy: `os_disk_snapshot_recreate_canonical_name`.
- Canonical OS-disk name: `disk-stcollector-os-mst-dev`.
- Old OS disk preserved directly: `false`.
- Maximum OS-disk snapshot size: 64 GiB; block if the fresh preflight observes a larger disk.
- Rollback operationally tested: `false`.
- Independent rollback review: `pending`.

## Selected rollback boundary

The design now selects two independently verified recovery snapshots before old compute removal:

1. a 32 GiB evidence-disk snapshot;
2. an OS-disk snapshot no larger than 64 GiB.

If replacement verification fails, the design recreates the canonical OS disk from the verified OS snapshot, recreates `vm-stcollector-mst-dev` with the preserved NIC and evidence disk, restores only approved RBAC to the new principal, and requires full boot, mount, evidence, service, health, durable-write, restart, identity, network, and disk-policy acceptance.

This is a deterministic repository contract, not proof that Azure rollback works.

## Remaining blockers

- operational proof of the selected OS-disk snapshot recreation rollback;
- guest preflight evidence schema;
- independently testable recovery-point verification;
- NIC preservation implementation and verification;
- managed-identity and RBAC restoration allowlist;
- reviewed temporary-cost estimate, cleanup owner, and deadline;
- independent evidence-quality, operations/recovery, security/identity, and Azure-cost decisions;
- protected-environment approval and explicit human authorization for any future run.

## Next bounded gate

1. Complete the contract, validator, tests, and rollback documentation on the active branch.
2. Run project-state validation, replacement-design tests, existing infrastructure tests, and Bicep build in CI.
3. Obtain an independent operations-and-recovery review of the selected strategy.
4. In a later separate branch, define the guest/control-plane evidence schema and fake-Azure-CLI-tested recovery verification and recreation implementation.
5. Use a separate authority-changing PR for any move into `.github/workflows`, Azure authentication, or mutation implementation.
6. Obtain separate explicit human authorization before any future mutation-capable workflow dispatch.

## Prohibited next step

Do not move the candidate workflow into `.github/workflows`, add Azure login or mutation commands, use the generated `REPLACE:` phrase, create snapshots, change delete options, delete the VM, detach disks, deploy replacement resources, modify budgets or billing alerts, or claim rollback is operationally verified merely because the snapshot strategy was selected.
