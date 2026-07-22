# Current project handoff

## Workspace hierarchy

- Umbrella conversational workspace: **HELIX — Governed Agent Engineering**.
- Bounded repository workstream: **ServiceTracer — Governed Azure Operations Lab**.
- GitHub, pull requests, CI, `.project/`, protected workflow artifacts, and current Azure evidence determine implementation and runtime state.
- Chat context supports reasoning only and never authorizes deployment or mutation.

## Trusted baseline

- Branch: `main`
- Current reconciled baseline: `4b181c644c48fde0c5d33f3cfabc24321977161a`
- Latest completed increment: PR #27, `Select snapshot-based collector rollback strategy`
- PR #27 merged while remediation was in progress. Its merge contains the new recovery contract but not the matching validator, tests, and synchronized records.

## Active repair increment

- Branch: `fix/collector-rollback-review-remediation`
- Pull request: #28, draft
- Objective: repair the partial PR #27 merge by carrying the matching validator, focused tests, design documentation, rollback review, active-work state, and handoff onto the merged `main` baseline.
- Current status: remediation passed CI at commit `623647cad4d83083a416f4250ae8688e58a5fc57`; the final coordination-only head requires one confirming CI run before independent re-review.
- Permitted paths: `infra/replacement/validate_execution_design.py`, `infra/tests/test_collector_replacement_execution_design.py`, `docs/designs/collector-replacement-execution.md`, `docs/reviews/collector-replacement-rollback-decision-2026-07-21.md`, `.project/active-work.json`, and this handoff.
- Protected paths: the already-merged replacement contract, `.github/workflows/**`, Bicep modules, application source, credentials, and Azure mutation scripts.

## Why this repair is required

The merged contract requires:

- a quiesce-and-deallocate consistency boundary before snapshots;
- shared maintenance-correlation and final-checkpoint binding for both snapshots;
- an isolated exact-snapshot Trusted Launch boot rehearsal before old-compute deletion;
- deterministic snapshot-to-disk `Copy` and specialized-disk-to-VM `Attach` semantics;
- complete recreation metadata validation;
- `deleteOption: Detach` for the production NIC and evidence disk on replacement and rollback VM boundaries.

The validator and tests on `main` still describe the earlier contract. Therefore `declared contract != validated contract` until PR #28 merges.

## Remediation carried by PR #28

### Validator

The validator enforces:

- source deallocation and checkpoint binding before snapshots;
- exact snapshot identity and recorded Trusted Launch profile for the isolated rehearsal;
- no production NIC or evidence disk attached to the rehearsal VM;
- `Copy` for managed-disk creation and `Attach` for VM OS-disk attachment;
- SKU, OS type, Hyper-V generation, security profile, encryption/DES, zone, network policy, public-access state, and OS-disk delete option;
- `Detach` semantics and re-read requirements for both preserved production attachments;
- the CAD 4 reviewed estimate, CAD 10 hard stop, four-hour rehearsal, 24-hour retention, and fresh subscription-specific preflight;
- `rollback.operationally_tested: false` and independent re-review still pending.

### Focused tests

Twenty-three focused tests cover the fail-closed design and reject:

- snapshots before the consistency boundary;
- missing checkpoint binding;
- a non-exact rehearsal snapshot;
- production attachments during rehearsal;
- `FromImage` restoration;
- missing `Attach` semantics;
- recreation metadata drift;
- `Delete` semantics on the production NIC or evidence disk;
- authorization or false operational-verification claims.

### Design and review records

The design and review documents describe the complete 15-phase state machine, isolated rehearsal boundary, deterministic restoration operations, attachment preservation, cost boundary, and remaining blockers.

## CI evidence

Exact-head CI run `29894210458` passed on repository commit `623647cad4d83083a416f4250ae8688e58a5fc57`:

- `.project` workflow-observability validation;
- complete Python unit suite, including 23 focused recovery-remediation tests;
- operational evidence collection;
- source-evidence CLI smoke test;
- preassembled replay compatibility;
- collector VM contract validation;
- Bicep lint and build.

This proves repository consistency only. It does not prove Azure snapshot recoverability, Trusted Launch bootability, actual rollback, actual cost, or execution authority.

## Runtime and deployment state

- Latest promoted control-plane evidence shows collector size `Standard_B2ats_v2` in `rg-servicetracer-dev-westus2`.
- Deployed image: Ubuntu 22.04 Jammy.
- Desired image: Ubuntu 24.04.
- Last guest-level record: ServiceTracer `0.4.0` after manual Python and certificate repairs.
- The evidence disk must be preserved.
- The deployed NIC delete behavior remains an execution blocker until a separately authorized operation changes and verifies it.
- System-assigned identity replacement and any RBAC restoration remain unresolved.
- No Azure replacement, rehearsal, or rollback has been authorized or performed.

## Cost boundary

- Reviewed planning estimate: CAD 4.
- Renewed approval required above CAD 4.
- Hard stop: CAD 10.
- Maximum snapshot capacity: 96 GiB.
- Maximum isolated rehearsal compute: four hours.
- Maximum temporary-resource retention: 24 hours.
- Maximum running-compute overlap: zero minutes.
- A future run still requires authenticated subscription-specific pricing, SKU availability, quota, cleanup owner, and cleanup deadline.

## Remaining blockers

- confirming CI on the final coordination-only PR #28 head;
- independent operations-and-recovery re-review;
- guest/control-plane evidence schemas;
- fake-Azure-CLI-tested recovery and rehearsal implementation;
- identity/RBAC allowlist;
- fresh cost/quota preflight and cleanup ownership;
- final evidence-quality and security/identity reviews;
- protected-environment approval and explicit human authorization.

## Next bounded gate

1. Confirm CI on the final exact head after this state update.
2. Route the passing exact head for independent operations-and-recovery re-review.
3. Keep PR #28 draft.
4. Keep all Azure authentication and mutations prohibited.

## Prohibited next step

Do not activate the candidate workflow, authenticate to Azure, deallocate the collector, create snapshots or rehearsal resources, change delete options, delete or deploy compute, restore RBAC, modify budgets or alerts, or claim rollback is operationally verified.
