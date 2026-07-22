# Current project handoff

## Workspace hierarchy

- Umbrella conversational workspace: **HELIX — Governed Agent Engineering**.
- Bounded repository workstream: **ServiceTracer — Governed Azure Operations Lab**.
- GitHub, pull requests, CI, `.project/`, protected workflow artifacts, and current Azure evidence determine implementation and runtime state.
- Chat context supports reasoning only and never authorizes deployment or mutation.

## Reality-synchronized repository baseline

- Default branch: `main`.
- Live baseline: `36010582460b393c0667e274144d9700e78721bf`.
- Latest merge: PR #34, **Remediate PR32 evidence-quality findings**.
- PR #34 merged exact head `7d586736e842425092f7fc3a3a23f0167466875e`.
- That exact head passed CI run `29950152689` (run 122); both **Bicep lint and build** and **ServiceTracer tests** passed with all reported steps inspected.
- An owner-account evidence-quality review accepted the bounded repository-design remediation with no remaining blocking finding.
- The review is not independent organizational approval.
- No pull-request-triggered workflow run was observed for the merge commit itself.

```text
pr_34_merged
= true

repository_design_remediation_accepted
= true

independent_organizational_approval
= false

azure_reality_refreshed
= false

operational_recovery_verified
= false
```

## Closed parallel branches

- PR #31, **Define collector recovery evidence schemas**, is closed unmerged as superseded by PR #34.
- PR #33, **Repair collector recovery evidence review findings**, is closed unmerged after PR #34 merged the overlapping accepted remediation.
- PR #33 had passed CI and received a technical pass on its own predecessor-based design, but it diverged from current `main`, became conflict-bound across the same seven files, and was not selected as repository authority.
- Distinct ideas from the closed branches remain in Git history and require a separate, current-baseline increment before adoption.

## Active bounded reconciliation

- Workstream: `pr34-post-merge-state-reconciliation`.
- Branch: `chore/reconcile-pr34-merge-state`.
- Pull request: #35, draft.
- Base: `36010582460b393c0667e274144d9700e78721bf`.
- Authority: repository coordination only.
- Permitted files:
  - `.project/active-work.json`;
  - `.project/handoffs/current-state.md`.
- Protected scope includes workflows, Bicep and Terraform, application source, credentials, live evidence, budgets, alerts, and all Azure resources.
- Current status: fresh exact-head CI pending after recording PR #35 in both coordination files.
- Next gate: inspect every CI job, confirm the final two-file diff, and obtain explicit merge authorization.

## PR #34 remediation accepted in `main`

The merged validator and contract now address the six findings recorded against PR #32:

1. authoritative v1 statuses, record types, patterns, redaction rules, phase requirements, claim requirements, record-detail requirements, cleanup bounds, and prohibited failure behavior are pinned against contract drift;
2. every record type requires minimum evidence-bearing details with bounded type validation;
3. recursive `[REDACTED]` marker paths must match provenance metadata exactly once;
4. target IDs must be complete canonical target IDs, distinct, and inside one subscription boundary;
5. non-finite numeric values fail closed through recursive validation and canonical JSON serialization;
6. superseded packages require replacement-package provenance, reject self-supersession, and cannot retain verified claims.

These controls define and validate repository evidence structure. They do not establish that future evidence is truthful, current, independently attested, or operationally collected.

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

This reconciliation does not refresh:

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

PR #35 has CAD 0 Azure runtime cost. These values remain planning controls, not present pricing, spending approval, or execution authority.

## Required gates for PR #35

Before merge:

1. preserve exactly the two declared `.project` files in the final diff;
2. obtain fresh exact-head GitHub CI for the final coordination head;
3. inspect every CI job and relevant logs;
4. preserve the owner-account reviewer-independence limitation inherited from PR #34;
5. obtain explicit merge authorization.

## Failure and rollback behavior

If reconciliation CI fails:

1. keep PR #35 draft;
2. inspect the exact failing job and logs;
3. patch only the two permitted `.project` files;
4. run fresh exact-head CI;
5. do not weaken workflow-observability validation.

Repository rollback is closing PR #35 without merge or reverting its repository-only commits. No Azure rollback applies because this operation performs no Azure mutation.

## Prohibited next step

Do not add live guest or Azure collection commands, activate a workflow, authenticate to Azure, deallocate the collector, create snapshots, create rehearsal resources, alter delete options, remove or deploy compute, restore RBAC, modify budgets or alerts, or claim snapshot recoverability, Trusted Launch bootability, rollback, or recovery as operationally verified.
