# Current project handoff

## Workspace hierarchy

- Umbrella conversational workspace: **HELIX — Governed Agent Engineering**.
- Bounded repository workstream: **ServiceTracer — Governed Azure Operations Lab**.
- GitHub, pull requests, CI, `.project/`, protected workflow artifacts, and current Azure evidence determine implementation and runtime state.
- Chat context supports reasoning only and never authorizes deployment or mutation.

## Reality-synchronized repository baseline

- Default branch: `main`.
- Live baseline: `777ec83b8a447f01904d5f891795ebcb6ab7abaf`.
- Latest merge: PR #32, **Add fail-closed collector recovery evidence schemas**.
- PR #32 exact head `f640f6664ab72deece24b770fe95cba51b0ac6ea` passed CI run `29946271140` (run 102).
- The evidence-quality review of that same exact head concluded **CHANGES REQUIRED** with six findings.
- PR #32 was then merged. The merge is real, but the review findings were not thereby resolved.

```text
merged_into_main
!= evidence_quality_accepted
!= project_state_reconciled
!= deployed_to_azure
!= operationally_verified
```

## Active bounded remediation

- Workstream: `pr32-evidence-quality-remediation`.
- Branch: `fix/pr32-evidence-review-remediation`.
- Pull request: #34, draft.
- Base: `777ec83b8a447f01904d5f891795ebcb6ab7abaf`.
- Authority: repository design and reconciliation only.
- Last exact remediation head: `e09e849d573b765d7f57a48a93585ab720d5b166`.
- Last exact-head CI: run `29949758121` (run 119), completed successfully.
- Inspected jobs: **Bicep lint and build** and **ServiceTracer tests**, including all reported steps.
- Current status: fresh exact-head CI pending for the final coordination head created by recording that evidence.

Permitted files:

- `infra/recovery/collector-recovery-evidence-contract.json`;
- `infra/recovery/recovery_evidence_core.py`;
- `infra/recovery/validate_recovery_evidence.py`;
- `infra/tests/test_collector_recovery_evidence.py`;
- `docs/designs/collector-recovery-evidence-schemas.md`;
- `.project/active-work.json`;
- `.project/handoffs/current-state.md`.

Protected boundaries:

- `.github/workflows/**`;
- `infra/replacement/**`;
- `infra/modules/**`;
- application source;
- credentials and secrets;
- live evidence packages;
- Azure authentication or mutation scripts;
- budgets and alerts;
- deployed resources.

No other conversation should edit this branch or these seven paths unless write ownership is explicitly transferred.

## PR #32 review findings under remediation

PR #34 directly addresses:

1. contract self-weakening because semantic values consumed by package validation were not pinned;
2. record types whose `details` could omit the evidence-bearing fields documented by the contract;
3. redaction metadata that was not bound one-to-one to the actual redacted location;
4. target resource IDs that could cross subscriptions;
5. acceptance of non-finite JSON numbers;
6. `superseded` package status without provenance.

The exact remediation head `e09e849d573b765d7f57a48a93585ab720d5b166` passed CI after all six changes and the supersession-direction correction. A fresh review still must examine the final coordination head after its own CI succeeds.

## Remediation design

### Pinned semantics

`validate_contract()` now pins:

- package, record, claim, and record-type enumerations;
- maintenance, record, command, and SHA-256 patterns;
- phase and claim requirements;
- secret-field fragments and credential prefixes;
- required evidence details per record type;
- cleanup constraints;
- prohibited failure behaviour;
- supersession rules;
- package bounds.

A future contract edit cannot relax one of those values while continuing to pass contract validation.

### Evidence-bearing record details

Each record type now has minimum required detail fields and type-specific checks. Cleanup deadlines and verification times use UTC timestamps. Retention and cost values are bounded. Costs must be finite. Decisions must preserve authority and rollback state.

### Redaction provenance

The validator recursively derives all `[REDACTED]` marker paths in `before_state`, `after_state`, and `details`.

The redaction metadata must match those paths exactly once. Missing, extra, wrong, or duplicate paths fail closed.

### Target boundary

The collector VM, production NIC, evidence disk, and OS disk IDs must be:

- complete Azure resource IDs;
- canonical names in `rg-servicetracer-dev-westus2`;
- distinct;
- inside one subscription boundary.

### Canonical JSON

`NaN`, positive infinity, and negative infinity are rejected. Canonical package sizing uses JSON serialization with non-finite values disabled.

### Supersession

Every package has a `supersession` field:

- `null` unless status is `superseded`;
- exact replacement-package ID, reason, and evidence SHA-256 when superseded;
- self-supersession prohibited;
- verified claims prohibited on superseded packages.

## Local verification

The reconstructed isolated fixture produced:

```text
python infra/recovery/validate_recovery_evidence.py
contract valid; design_only; no Azure authority

python -m unittest discover -s infra/tests -v
32 recovery-evidence tests passed
```

Local execution used a reconstructed isolated fixture because the execution container could not resolve GitHub for a repository clone. GitHub remains authoritative for the branch contents and full CI suite.

Local tests are not GitHub CI. The final coordination head must pass its own GitHub Actions run.

## Parallel PR #31 disposition

- PR #31, **Define collector recovery evidence schemas**, is closed unmerged as superseded by PR #34.
- It contained useful schema-envelope research, but it diverged from `main`, introduced a parallel 11-file schema family, and had no exact-head CI or accepted evidence-quality review.
- Its durable ideas remain in Git history.
- It is not repository authority and must not be mistaken for a deployed or accepted design.

## Latest Azure evidence boundary

The latest repository-promoted Azure control-plane evidence remains read-only planner run `29856203054`, observed July 21, 2026.

At that observation:

- resource group: `rg-servicetracer-dev-westus2`;
- region: `westus2`;
- collector VM: `vm-stcollector-mst-dev`;
- size: `Standard_B2ats_v2`;
- deployed image: Ubuntu 22.04;
- desired image: Ubuntu 24.04;
- evidence disk: attached with `deleteOption: Detach`;
- production NIC: static address and VM `deleteOption: Delete`;
- system-assigned identity: present;
- visible role assignments in the planner result: none;
- Azure mutations: not authorized and not performed.

The last repository-recorded guest observation remains ServiceTracer `0.4.0` after manual repairs on July 20, 2026.

No live Azure connector was available during PR #34 creation. Therefore none of the following was refreshed:

- tenant or subscription context;
- resource existence or configuration;
- effective RBAC;
- guest health;
- quota or SKU availability;
- current prices or actual cost;
- snapshot recoverability;
- Trusted Launch bootability;
- rollback or recovery state.

```text
repository declaration
!= deployed Azure reality
latest promoted evidence
!= current-day observation
```

## Cost boundary

Existing planning constraints remain:

- reviewed estimate: CAD 4;
- renewed approval required above CAD 4;
- unconditional hard stop above CAD 10;
- maximum snapshot capacity: 96 GiB;
- maximum isolated rehearsal compute: four hours;
- maximum temporary-resource retention: 24 hours;
- maximum running-compute overlap: zero minutes.

PR #34 creates no Azure resource and has CAD 0 Azure runtime cost. These values remain planning controls, not present pricing or execution approval.

## Required gates for PR #34

Before merge:

1. preserve exactly the seven declared files in the final diff;
2. resolve the final coordination head from live GitHub;
3. obtain fresh exact-head GitHub CI for that head;
4. inspect every CI job and relevant logs;
5. obtain a fresh evidence-quality review of that exact passing head;
6. resolve or explicitly retain every review finding as a blocker;
7. preserve the pull-request-owner reviewer-independence limitation;
8. keep the pull request draft until all gates pass.

## Failure and rollback behaviour

If CI fails:

1. keep PR #34 draft;
2. inspect the exact failing job and logs;
3. patch only declared files;
4. run fresh exact-head CI;
5. do not weaken evidence controls merely to make CI pass.

If review finds a defect:

1. record the exact reviewed head and CI run;
2. keep the PR draft;
3. patch inside scope or explicitly amend scope;
4. obtain fresh CI and re-review.

Repository rollback is closing PR #34 without merge or reverting its repository commits. No Azure rollback applies because this increment performs no Azure mutation.

## Prohibited next step

Do not add live guest or Azure collection commands, activate a workflow, authenticate to Azure, deallocate the collector, create snapshots, create rehearsal resources, alter delete options, remove or deploy compute, restore RBAC, modify budgets or alerts, or claim snapshot recoverability, Trusted Launch bootability, rollback, or recovery as operationally verified.
