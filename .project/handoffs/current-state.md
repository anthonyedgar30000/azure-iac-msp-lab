# Current project handoff

## Workspace hierarchy

- Umbrella conversational workspace: **HELIX — Governed Agent Engineering**.
- Bounded repository workstream: **ServiceTracer — Governed Azure Operations Lab**.
- GitHub, pull requests, CI, `.project/`, protected workflow artifacts, and current Azure evidence determine implementation and runtime state.
- Chat context supports reasoning only and never authorizes deployment or mutation.

## Reality-synchronized repository baseline

- Default branch: `main`.
- Last substantive repository baseline: `bc27ba115a2bdd3ce0eba5bc38176033be27fbe0`.
- Latest merged increment: PR #29, **Make collector rehearsal teardown contract authoritative**.
- PR #29 merged the v2 contract, fail-closed validator, negative regression tests, candidate workflow phase alignment, design/review records, and project-state reconciliation.
- No open pull requests existed when this reconciliation branch was created.
- This reconciliation is coordination-only. While its pull request is open, live GitHub is authoritative; after merge, the files intentionally describe the stable post-merge state.

Canonical interpretation:

`merged_into_main != deployed_to_azure != operationally_tested != execution_authorized`

## PR #29 verification and review chronology

### Code-bearing head

Exact code-bearing head: `b9b21c3f5c6c860db8edbb6821d676f764d99b18`.

CI run `29941065236` (run 88) completed successfully:

- workflow-observability project-state validation;
- complete ServiceTracer unit and operational smoke-test path;
- collector replacement contract validation and negative regression tests;
- Bicep lint and build.

### Final PR head

Final PR head: `8e161c079714d96688255e5e86f067f784b268f5`.

CI run `29941348786` (run 90) completed successfully. This was the exact final coordination head before merge.

### Operations-and-recovery lens

The operations-and-recovery lens recorded **APPROVED FOR THIS REPOSITORY DESIGN INCREMENT** against the code-bearing head and run 88.

Reviewer-independence boundary:

- the review was submitted through the pull-request owner's authenticated GitHub account;
- the repository may claim a recorded operations-and-recovery lens decision;
- it may not claim external or organizational reviewer independence.

### Merge

- PR #29 merge commit: `bc27ba115a2bdd3ce0eba5bc38176033be27fbe0`.
- The connected pull-request run lookup did not expose a separate post-merge CI run for that merge commit.
- The exact PR-head CI evidence remains the recorded repository verification evidence.

## Authoritative rehearsal-teardown contract now in main

The v2 replacement contract now requires:

- exact ordered quiescence, including stopping the collector service;
- source VM `PowerState/deallocated` before snapshots;
- two snapshots bound to the same maintenance correlation and final evidence checkpoint;
- isolated boot rehearsal from the exact verified OS snapshot under the recorded Trusted Launch profile;
- a distinct `teardown_isolated_rehearsal` phase;
- rehearsal VM `PowerState/deallocated` evidence;
- removal of the temporary rehearsal VM and isolated NIC before old-compute removal and replacement compute;
- zero minutes of running-compute overlap;
- an exact allowlist for temporary recovery artifacts permitted to remain;
- fail-closed rejection of missing deallocation, missing removal, late boundaries, unapproved artifacts, missing phases, and non-zero overlap.

These are repository design requirements, not observed Azure actions.

## Legacy PR #1 resolution

PR #1, **feat: scaffold Azure network foundation**, was closed without merge on July 22, 2026.

Resolution:

- the branch was 199 commits behind current `main`;
- its Terraform checks proved static formatting, initialization, and validation only;
- it never produced an authenticated plan, Azure deployment, traffic-behaviour verification, or teardown proof;
- its narrow two-subnet Terraform design was superseded by the current Bicep architecture;
- the branch and commits remain in Git history as historical evidence of early cost-control, evidence-index, and verification-discipline work.

Canonical interpretation:

`historical_prototype != current_architecture`

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
- No collector replacement, isolated rehearsal, teardown, rollback, RBAC restoration, budget mutation, or alert mutation has been authorized or performed.
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

## Current repository work state

- Active bounded workstreams: none.
- Known open pull requests: none at reconciliation-branch creation.
- Active execution workflow: absent.
- Dispatch authority: absent.
- Azure authentication authority: absent.
- Azure mutation authority: absent.

## Next bounded candidate

Candidate: **collector recovery evidence-schema design**.

Repository-only intended scope:

1. define guest preflight evidence records;
2. define Azure control-plane preflight evidence records;
3. require correlation identifiers, timestamps, command identity, exit status, target resource IDs, before/after state, cleanup ownership, and redaction rules;
4. define failure, abort, rollback, and recovery evidence requirements;
5. add deterministic schema validation and negative tests.

This candidate is not started and carries no Azure authority. Open it through a separate bounded pull request.

## Failure and rollback behavior for the next repository increment

If its CI fails:

1. keep the pull request draft;
2. inspect the exact failing job and logs;
3. patch only the declared files;
4. run fresh exact-head CI;
5. do not weaken evidence requirements merely to make tests pass.

If review requests changes:

1. record the exact reviewed head and CI run;
2. patch within declared scope or explicitly amend scope;
3. obtain fresh CI and re-review.

Repository rollback is closing the candidate pull request without merge or reverting its commits. No Azure rollback applies because the candidate must remain repository-only.

## Prohibited next step

Do not activate the candidate replacement workflow, authenticate to Azure for replacement execution, deallocate the collector, create snapshots or rehearsal resources, alter delete options, remove or deploy compute, restore RBAC, modify budgets or alerts, or claim rollback is operationally verified.
