# Current project handoff

## Workspace hierarchy

- Umbrella conversational workspace: **HELIX — Governed Agent Engineering**.
- Bounded repository workstream: **ServiceTracer — Governed Azure Operations Lab**.
- Chat context supports reasoning and continuity.
- GitHub, pull requests, CI, `.project/`, workflow artifacts, and current Azure evidence determine implementation and runtime state.
- Moving a conversation does not authorize repository changes, workflow dispatch, or Azure mutation.

## Trusted baseline observation

- Branch: `main`
- Verified baseline: `00ebc068f4aec4eda8cda723d8dc4d974a4cb7c6`
- Latest completed increment: PR #26
- Live GitHub determines the current head.

## Active bounded increment

- Branch: `design/collector-rollback-snapshot-recreation`
- Pull request: #27, draft
- Write owner: ServiceTracer — Governed Azure Operations Lab conversation
- Objective: select and formalize the OS-disk snapshot/recreation rollback strategy and canonical OS-disk naming.
- Current status: the four operations-and-recovery review findings are patched in the declared seven-file scope; fresh exact-head CI and independent re-review are pending.
- Protected scope: `.github/workflows/**`, Bicep modules, application source, credentials, deployment scripts, and Azure resources.

## Runtime and deployment state

- Latest promoted control-plane evidence shows collector size `Standard_B2ats_v2` in `rg-servicetracer-dev-westus2`.
- The deployed collector uses Ubuntu 22.04 Jammy while the desired contract uses Ubuntu 24.04; replacement is required.
- Last guest verification records ServiceTracer `0.4.0` with manual Python and certificate repairs.
- The production evidence disk is attached with detach-on-delete semantics and must be preserved.
- The production NIC has static private addressing but current deployed evidence records delete-with-VM semantics; changing and verifying this remains a future authorized operation.
- The collector uses a system-assigned identity; no visible role assignments were returned by the planner.
- The protected July 21 artifact records a 30 GiB Gen2 Trusted Launch OS disk with platform-key encryption, but fresh preflight remains mandatory.
- No collector replacement execution is authorized or evidenced.

## Evidence and review record

- Planner run: `29856203054`
- Artifact: `collector-replacement-plan-29856203054-1`
- Artifact SHA-256: `76f3b44e6e97e906dac6d62eeb212a6bc55265e77271a030b9c45b0cacf55637`
- First operations-and-recovery review: changes requested on exact head `bad79ac2a8ba8fa9568737fc3c3635b93f2dbaca`.
- Current remediation status: `changes_addressed_re_review_pending`.
- Azure-cost status: `conditionally_approved_planning_estimate`.
- Rollback operationally tested: `false`.

## Recovery-review remediation

### Consistency boundary

Before either snapshot, a future authorized implementation must stop and drain writes, flush the evidence filesystem, record a final checkpoint ID and SHA-256, record a maintenance correlation ID, stop the service, verify guest shutdown, deallocate the source, and verify Azure `PowerState/deallocated`.

Both snapshots must share the same maintenance correlation and final-checkpoint binding. Snapshot capture before this boundary is prohibited.

### Isolated exact-snapshot rehearsal

Before old-compute deletion, a future authorized implementation must copy the exact verified OS snapshot to a temporary disk, attach that specialized disk to an isolated VM under the recorded Trusted Launch profile, and prove boot plus VM Guest State/vTPM viability.

The source remains deallocated. The rehearsal uses no production NIC and no production evidence disk. Repository design does not claim that this rehearsal has occurred.

### Deterministic restoration semantics

- Snapshot to managed OS disk: `Copy`.
- Specialized OS disk to VM: `Attach`.
- `FromImage` is prohibited.
- Required metadata includes SKU, OS type, Hyper-V generation, Trusted Launch/security profile, encryption/DES, zone when present, network/public-access policy, and OS-disk delete option.

### Preserved production attachments

Both replacement and rollback contracts require:

- production NIC: `deleteOption: Detach`;
- production evidence disk: `deleteOption: Detach`;
- re-read after VM creation;
- re-read before any failed-compute deletion.

Focused negative tests reject `Delete` for either preserved attachment.

## Cost boundary

- Reviewed planning estimate: CAD 4.
- Renewed approval required above CAD 4.
- Hard execution stop: CAD 10.
- Maximum snapshot capacity: 96 GiB.
- Maximum isolated rehearsal compute: four hours.
- Maximum temporary-resource retention: 24 hours.
- Maximum running-compute overlap: zero minutes.
- A future run still requires authenticated subscription-specific pricing, SKU availability, quota, cleanup owner, and cleanup deadline.
- This is planning feasibility, not actual spend, a subscription quote, or execution authorization.

## Design state

- Candidate workflow remains outside `.github/workflows`.
- Active workflow path: absent.
- Dispatch authorized: `false`.
- Azure mutations authorized: `false`.
- Promotion ready: `false`.
- Selected strategy: `os_disk_snapshot_recreate_canonical_name`.
- Canonical OS disk: `disk-stcollector-os-mst-dev`.
- Independent review status: `changes_addressed_re_review_pending`.
- Operationally tested: `false`.

## Remaining blockers

- fresh exact-head CI;
- independent operations-and-recovery re-review;
- guest/control-plane evidence schemas;
- fake-Azure-CLI-tested recovery and isolated-rehearsal implementation;
- managed-identity and RBAC restoration allowlist;
- fresh subscription-specific cost and quota preflight;
- cleanup owner and deadline;
- final evidence-quality and security/identity reviews;
- protected-environment approval and explicit human authorization.

## Next bounded gate

1. Run project-state validation, replacement-design tests, the complete ServiceTracer suite, and Bicep lint/build on the exact remediated head.
2. Route the passing exact head for independent operations-and-recovery re-review.
3. Keep PR #27 draft.
4. Keep the candidate outside `.github/workflows`.
5. Use a separate authority-changing PR for any Azure authentication or mutation implementation.

## Prohibited next step

Do not activate the workflow, add Azure login or mutation commands, use the generated `REPLACE:` phrase, deallocate the collector, create snapshots or temporary rehearsal resources, change delete options, delete or deploy compute, modify RBAC, budgets, alerts, or billing configuration, or claim operational rollback proof from repository tests.
