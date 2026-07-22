# Current project handoff

## Workspace hierarchy

- Umbrella conversational workspace: **HELIX — Governed Agent Engineering**.
- Bounded repository workstream: **ServiceTracer — Governed Azure Operations Lab**.
- GitHub, pull requests, CI, `.project/`, protected workflow artifacts, and current Azure evidence determine implementation and runtime state.
- Chat context supports reasoning only and never authorizes deployment or mutation.

## Reality-synchronized repository baseline

- Default branch: `main`.
- Current live `main` head at PR #29 branch creation: `cb5b38f3d6ab861f54f72897e6cf625a04c275e8`.
- Latest merged increment: PR #28, `Complete collector rollback review remediation`.
- PR #28 exact head `e98c6039d4a896bea49f48af0eb0c733ee491f5b` passed CI run `29899440550` (run 84).
- The operations-and-recovery review of that same exact head recorded **CHANGES REQUIRED** before merge.
- PR #28 was then merged. The merge is real repository history, but it is not operations-and-recovery approval.

Canonical interpretation:

`merged_into_main != blocking_review_resolved != recovery_contract_approved`

## Active contract-amendment increment

- Branch: `fix/collector-rehearsal-teardown-contract`.
- Pull request: #29, draft.
- Base: live `main` at merge commit `cb5b38f3d6ab861f54f72897e6cf625a04c275e8`.
- Objective: make isolated-rehearsal teardown authoritative in the replacement contract and reconcile project state with the actual PR #28 merge.
- Authority: repository patch and coordination only.

Permitted files:

- `infra/replacement/collector-replacement-contract.json`;
- `infra/replacement/validate_execution_design.py`;
- `infra/tests/test_collector_replacement_execution_design.py`;
- `infra/workflow-designs/collector-replacement-execution.yml`;
- `docs/designs/collector-replacement-execution.md`;
- `docs/reviews/collector-replacement-rollback-decision-2026-07-21.md`;
- `.project/active-work.json`;
- `.project/handoffs/current-state.md`.

Protected boundaries:

- `.github/workflows/**`;
- Bicep modules and deployed-resource declarations;
- application source;
- credentials and secrets;
- Azure mutation scripts;
- budgets and alerts;
- live Azure resources.

## Blocking review finding repaired

The PR #28 validator declared:

- rehearsal compute deallocated before replacement;
- temporary rehearsal compute removed before replacement;
- only approved temporary artifacts retained.

Those results were synthesized by the validator. The authoritative contract did not contain corresponding fields or a teardown phase, so the validator could not fail closed on their absence or alteration.

PR #29 advances the contract schema to v2 and adds:

- `rehearsal_teardown.phase_id = teardown_isolated_rehearsal`;
- completion before `remove_old_compute`;
- required rehearsal VM state `PowerState/deallocated`;
- source VM remaining `PowerState/deallocated`;
- mandatory removal of the temporary rehearsal VM and temporary isolated NIC;
- explicit retained-artifact allowlist;
- rejection of unapproved retained artifacts;
- zero minutes of running-compute overlap;
- required teardown phase evidence for state, absence, allowlist compliance, and overlap.

The validator reads those contract inputs. Negative tests alter or remove each reviewed requirement and require validation failure.

## Candidate workflow alignment

The non-dispatchable candidate workflow previously omitted authoritative phases, including quiescence and rehearsal. PR #29 aligns all phase markers with the contract and adds a test that compares workflow order to contract order exactly.

The file remains outside `.github/workflows/`, contains no Azure mutation commands, and exits before Azure authentication.

## Code-bearing CI result

Exact code-bearing head: `b9b21c3f5c6c860db8edbb6821d676f764d99b18`.

CI run `29941065236` (run 88) completed successfully:

- workflow-observability project-state validation: passed;
- ServiceTracer unit tests: passed;
- operational evidence collection and CLI smoke path: passed;
- preassembled replay compatibility: passed;
- collector replacement contract validator and regression tests: passed;
- Bicep lint and build: passed.

This CI proves repository consistency only.

## Operations-and-recovery review result

The operations-and-recovery lens reviewed exact head `b9b21c3f5c6c860db8edbb6821d676f764d99b18` with successful CI run `29941065236` and recorded:

**APPROVED FOR THIS REPOSITORY DESIGN INCREMENT**

The review concluded that the v2 contract, validator, negative tests, workflow phase alignment, and PR #28 merge-reality reconciliation resolve the contract-backed rehearsal-teardown finding.

Reviewer-independence boundary:

- the review was submitted through the pull-request owner's authenticated GitHub account;
- GitHub therefore records it as a commented review rather than independent organizational approval;
- the repository may accurately claim an operations-and-recovery lens decision;
- it may not claim external or organizational reviewer independence.

## Final coordination-only update

This handoff and `.project/active-work.json` are coordination-only updates made after the code-bearing CI and review.

- CI run `29941065236` must remain described as the **last code-bearing-head verification**.
- The live PR #29 head after these coordination commits requires fresh exact-head CI.
- Live GitHub checks are authoritative for that final coordination head.
- Do not create a self-referential loop by claiming predecessor CI as final-head CI.

## Latest Azure evidence

The latest promoted control-plane evidence remains read-only planner run `29856203054`, captured July 21, 2026.

Observed at that time:

- resource group: `rg-servicetracer-dev-westus2`;
- region: `westus2`;
- collector VM: `vm-stcollector-mst-dev`;
- collector size: `Standard_B2ats_v2`;
- deployed image: Canonical Ubuntu 22.04 Jammy;
- desired image: Canonical Ubuntu 24.04;
- evidence disk: 32 GiB Standard SSD, attached with `deleteOption: Detach`, public access disabled, network policy `DenyAll`;
- production NIC: static `10.20.40.10` on the operations subnet, attached with VM `deleteOption: Delete`;
- OS disk: 30 GiB Standard SSD, Trusted Launch generation 2, public access enabled, network policy `AllowAll`;
- system-assigned identity present;
- no visible role assignments in the planner result;
- no Azure mutations authorized or performed.

This evidence is not current-day proof. It does not establish present guest health, present resource state, current pricing, SKU availability, quota, actual cost, snapshot recoverability, Trusted Launch restore bootability, or rollback.

## Guest and deployment evidence boundary

- Last recorded guest-level state: ServiceTracer `0.4.0` after manual repairs on July 20, 2026.
- The planner did not re-run guest commands.
- No collector replacement, isolated rehearsal, rollback, RBAC restoration, budget mutation, or alert mutation has been authorized or performed.
- `deployment_succeeded != service_validated` and `resource_exists != securely_configured` remain active boundaries.

## Cost boundary

- Reviewed planning estimate: CAD 4.
- Renewed approval required above CAD 4.
- Hard stop: CAD 10.
- Maximum snapshot capacity: 96 GiB.
- Maximum isolated rehearsal compute: four hours.
- Maximum temporary-resource retention: 24 hours.
- Maximum running-compute overlap: zero minutes.
- Fresh authenticated subscription-specific pricing, SKU availability, quota, cleanup owner, and cleanup deadline remain required.

## Remaining blockers

- fresh exact-head CI for the final PR #29 coordination-only head;
- explicit acceptance of the owner-account review limitation or independent external review before merge, according to the chosen repository governance standard;
- guest/control-plane evidence schemas;
- fake-Azure-CLI-tested recovery, rehearsal, and teardown implementation;
- managed-identity/RBAC restoration allowlist;
- fresh authenticated cost, SKU, and quota preflight;
- cleanup owner and deadline;
- final evidence-quality and security/identity reviews;
- protected-environment approval and explicit human authorization;
- operational recovery testing under separately approved Azure authority.

## Failure and rollback behavior for this repository increment

If final coordination-head CI fails:

1. keep PR #29 draft;
2. inspect the failing job and logs;
3. patch only the declared files;
4. run fresh CI on the new exact head;
5. do not weaken contract requirements merely to make tests pass.

If a reviewer requests changes:

1. record the exact reviewed head and CI run;
2. keep the PR draft;
3. patch within scope or explicitly amend scope;
4. obtain fresh CI and re-review.

Repository rollback is closing PR #29 without merge or reverting its commits. No Azure rollback applies because this increment performs no Azure mutation.

## Next bounded gate

1. Wait for final coordination-head CI.
2. Inspect every job and step result.
3. Keep PR #29 draft unless merge governance is explicitly satisfied.
4. Preserve all Azure execution prohibitions.

## Prohibited next step

Do not merge PR #29 merely because its code-bearing head and final coordination head are green. Do not activate the candidate workflow, authenticate to Azure for execution, deallocate the collector, create snapshots or rehearsal resources, change delete options, delete or deploy compute, restore RBAC, modify budgets or alerts, or claim rollback is operationally verified.
