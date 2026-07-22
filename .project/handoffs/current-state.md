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
- Pull request: #27, currently draft
- Write owner: ServiceTracer — Governed Azure Operations Lab conversation
- Objective: select and formalize the OS-disk snapshot/recreation rollback strategy and canonical OS-disk naming.
- Current status: exact-head CI passed on `bad79ac2a8ba8fa9568737fc3c3635b93f2dbaca`; independent operations-and-recovery review requested changes; Azure-cost feasibility is conditionally approved as a planning estimate.
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

- The latest promoted Azure control-plane observation shows collector VM size `Standard_B2ats_v2`.
- The earlier `Standard_B1ms` record is retained as historical evidence of a previously verified working size.
- The last guest-level verification still records ServiceTracer `0.4.0` with manual Python and certificate repairs; the planner did not re-verify guest health or version.
- The deployed collector uses Canonical Ubuntu 22.04 Jammy while the desired contract uses Canonical Ubuntu 24.04. Replacement is required.
- The evidence disk is attached, uses detach-on-delete semantics, and has restrictive public/network access settings. It must be preserved and protected by a verified recovery point.
- The NIC has static private addressing but is configured to be deleted with the VM. NIC preservation remains an execution blocker.
- The VM uses a system-assigned identity. No visible role assignments were returned, and any required publication access must be recreated for the replacement identity.
- The current OS disk allows public network access; the replacement design requires hardening.
- The protected July 21 planner artifact records a 30 GiB Gen2 Trusted Launch OS disk with platform-key encryption, but a fresh preflight is still mandatory and snapshot recoverability remains unproved.
- No collector replacement execution is authorized or evidenced.

## Evidence and review record

- Sanitized planner review: `docs/reviews/collector-replacement-plan-2026-07-21.md`
- Rollback decision review: `docs/reviews/collector-replacement-rollback-decision-2026-07-21.md`
- Workflow run ID: `29856203054`
- Artifact: `collector-replacement-plan-29856203054-1`
- Artifact SHA-256: `76f3b44e6e97e906dac6d62eeb212a6bc55265e77271a030b9c45b0cacf55637`
- Raw artifact remains in protected GitHub Actions storage and is not committed because it contains sensitive environment identifiers.
- Independent operations-and-recovery review: changes requested on exact head `bad79ac2a8ba8fa9568737fc3c3635b93f2dbaca`.
- Azure-cost review: planning feasibility conditionally approved by Anthony Edgar on 2026-07-22; this is not an actual-cost observation or execution authorization.

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
- Independent operations-and-recovery decision: `changes_requested`.
- Azure-cost feasibility decision: `conditionally_approved_planning_estimate`.

## Cost review boundary

- Reviewed planning estimate: CAD 4.
- Hard execution ceiling: CAD 10.
- Maximum total snapshot capacity: 96 GiB.
- Maximum recovery-resource retention: 24 hours.
- Expected isolated restore-rehearsal compute allocation: 4 hours.
- Stop and obtain renewed cost approval if the fresh projected temporary cost exceeds CAD 4.
- Stop unconditionally if the fresh projected temporary cost exceeds CAD 10.
- A future run still requires an authenticated subscription-specific meter, SKU-availability, quota, cleanup-owner, and cleanup-deadline preflight.
- This decision proves planning feasibility only. It does not prove actual spend, provide a subscription quote, authorize a budget, or authorize Azure mutation.

## Operations-and-recovery changes required

1. Add a quiesce-and-deallocate consistency boundary before either snapshot: stop and drain the writer, flush pending writes, record a final evidence checkpoint/hash and maintenance correlation, and verify Azure `PowerState/deallocated`.
2. Require an isolated restore rehearsal from the exact OS-disk snapshot under the recorded Trusted Launch profile before old-compute deletion, without attaching the production NIC or evidence disk.
3. Split snapshot-to-managed-disk recreation using `Copy` from specialized OS-disk-to-VM attachment using `Attach`, and validate the complete recreation metadata.
4. Require and re-read `deleteOption: Detach` for the NIC and evidence disk on replacement and rollback VM contracts before any failed-compute deletion.

## Remaining blockers

- implementation and tests for the four operations-and-recovery findings;
- operational proof of the selected OS-disk snapshot recreation rollback;
- guest preflight evidence schema;
- independently testable recovery-point verification;
- NIC preservation implementation and verification;
- managed-identity and RBAC restoration allowlist;
- fresh authenticated subscription-specific cost and quota preflight;
- cleanup owner and deadline;
- renewed independent operations-and-recovery approval;
- independent evidence-quality and security/identity decisions for the final implementation;
- protected-environment approval and explicit human authorization for any future run.

## Next bounded gate

1. Patch only the seven files already declared by PR #27.
2. Add focused negative and ordering tests for all four operations-and-recovery findings.
3. Run `.project` validation, the replacement-design validator and focused tests, the complete ServiceTracer test suite, and Bicep lint/build.
4. Return the new exact head for another independent operations-and-recovery review.
5. Keep the Azure-cost planning boundary at CAD 4 reviewed estimate and CAD 10 hard stop, with fresh authenticated preflight still required.
6. Use a separate authority-changing PR for any move into `.github/workflows`, Azure authentication, or mutation implementation.
7. Obtain separate explicit human authorization before any future mutation-capable workflow dispatch.

## Prohibited next step

Do not move the candidate workflow into `.github/workflows`, add Azure login or mutation commands, use the generated `REPLACE:` phrase, create snapshots, change delete options, delete the VM, detach disks, deploy replacement resources, modify budgets or billing alerts, or claim rollback is operationally verified merely because the snapshot strategy and planning cost boundary were accepted.
