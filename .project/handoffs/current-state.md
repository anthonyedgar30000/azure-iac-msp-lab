# Current project handoff

## Workspace hierarchy

- Umbrella conversational workspace: **HELIX — Governed Agent Engineering**.
- Bounded repository workstream: **ServiceTracer — Governed Azure Operations Lab**.
- GitHub, pull requests, CI, `.project/`, protected workflow artifacts, and fresh Azure evidence determine implementation and runtime reality.
- Chat context supports reasoning only and never authorizes deployment or mutation.

## State-model correction

The project no longer requires a coordination pull request to predict its own merge commit or terminal state.

```text
last_substantive_baseline
!= repository_observation.main_head
!= current_repository_head
```

- The last substantive baseline is PR #34 merge commit `36010582460b393c0667e274144d9700e78721bf`.
- PR #35 was a coordination-only merge at `a115b4cb0f3a3edbefd5171201c07bd144b7bf72`.
- That PR advanced `main` without changing the substantive collector-recovery evidence design.
- The repository observation stored in `active-work.json` is explicitly time-bounded external evidence.
- Current `main`, open pull requests, and CI must be queried from live GitHub at read time.

This removes the self-referential loop where every state-reconciliation merge immediately made the embedded “current head” and “open PR” claims stale.

## Authored change

- Change: `eliminate-self-referential-project-state`.
- Branch: `chore/eliminate-self-referential-project-state`.
- Pull request: not opened at initial authoring.
- Authority: repository coordination model only.
- Permitted files:
  - `.project/active-work.json`;
  - `.project/validate.py`;
  - `.project/README.md`;
  - `.project/handoffs/current-state.md`.
- Protected scope includes workflows, Bicep and Terraform, application source, credentials, live evidence, budgets, alerts, and all Azure resources.
- The authored-change declaration is historical governance metadata, not live branch or PR status.

## Validation behavior

`project.active-work.v2` now requires:

1. a last substantive baseline with a valid `main` commit;
2. a time-bounded `live_github` repository observation;
3. an authored-change declaration marked `declaration_not_live_status`;
4. explicit fail-closed authority defaults;
5. live-state resolution rules for GitHub, CI, and Azure;
6. the canonical distinction `last_substantive_baseline != current_repository_head`.

The validator rejects the retired self-referential fields:

- `trusted_baseline`;
- `workstreams`;
- `known_open_pull_requests`;
- `next_bounded_operation`.

## Accepted substantive baseline

PR #34 resolved the six evidence-quality findings recorded against PR #32 at the repository-contract level:

1. authoritative v1 semantics are pinned against contract drift;
2. every record type requires typed evidence-bearing details;
3. recursive redaction markers must match provenance metadata exactly once;
4. target IDs are canonical, distinct, and share one subscription boundary;
5. non-finite numbers fail closed;
6. superseded packages require bounded replacement provenance and cannot retain verified claims.

PR #34 exact head `7d586736e842425092f7fc3a3a23f0167466875e` passed CI run `29950152689` (run 122). The owner-account evidence-quality review accepted the bounded repository-design remediation. It was not independent organizational approval and did not prove operational recovery.

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

This change does not refresh:

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
repository declaration != deployed Azure reality
historical evidence != current-day observation
CI passed != service validated
```

## Cost and execution boundary

Existing planning controls remain historical constraints:

- reviewed estimate: CAD 4;
- renewed approval required above CAD 4;
- unconditional hard stop above CAD 10;
- maximum snapshot capacity: 96 GiB;
- maximum isolated rehearsal compute: four hours;
- maximum temporary-resource retention: 24 hours;
- maximum running-compute overlap: zero minutes.

This coordination-model change has CAD 0 Azure runtime cost. It grants no authentication, dispatch, mutation, spending, rollback, recovery, or deployment authority.

## Failure and rollback behavior

If validation or CI fails:

1. keep the pull request draft;
2. inspect the exact failing job and logs;
3. patch only the four permitted `.project` files;
4. obtain fresh exact-head CI;
5. do not restore self-referential current-state requirements merely to make validation pass.

Repository rollback is closing the pull request without merge or reverting its repository-only commits. No Azure rollback applies.
