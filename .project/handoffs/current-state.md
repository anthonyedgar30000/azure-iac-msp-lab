# Current project handoff

## Workspace and repository reality

- Umbrella conversational workspace: **HELIX — Governed Agent Engineering**.
- Bounded repository workstream: **ServiceTracer — Governed Azure Operations Lab**.
- Default branch: `main`.
- Observed `main` before this branch opened: `54466651f291e271e5da542ea0afb38679ca6ca9`, the PR #37 merge commit.
- Open pull requests observed before branch creation: zero.
- The GitHub connector cannot prove whether an unrelated local clone has uncommitted or unpushed work; live GitHub is authoritative for this branch and PR scope.

```text
repository_observation.main_head
!= automatically current_repository_head

remote branch clean
!= every local clone clean
```

## Accepted substantive baseline

PR #37 merged the decoupled existing-collector report-publication design and read-only planning script. It proved repository design and CI consistency only.

- Merge commit: `54466651f291e271e5da542ea0afb38679ca6ca9`.
- Exact reviewed head: `d5041dc0fad2d28a1b8a5a182cdea8c24dc0caf9`.
- Exact-head CI run: `29955878403` / run 140, successful.
- Review: owner-account technical pass, not independent organizational approval.
- Azure endpoint deployed: no.
- Browser live-data proof: no.

## Authored change

- Change: `promote-existing-collector-report-publication-plan`.
- Branch: `feat/promote-existing-collector-report-plan`.
- Pull request: #38, recorded as authored-change metadata only; live status remains external GitHub evidence.
- Authority: promote and dispatch one read-only Azure planner only.

Permitted paths:

- `.github/workflows/existing-collector-report-publication-plan.yml`;
- `infra/tests/test_existing_collector_report_publication_plan_workflow.py`;
- `docs/runbooks/existing-collector-report-publication-plan.md`;
- `.project/active-work.json`;
- `.project/README.md`;
- `.project/handoffs/current-state.md`.

Protected scope includes deployment workflows, Bicep resources, collector VM/NIC/disks/image/extensions, load balancer, backends, network, frontend endpoint configuration, credentials, budgets, alerts, report publication, role changes, guest commands, and every Azure mutation.

## Bounded authority grant

Anthony Edgar explicitly said **“Proceed”** after the next gate was described as a separately authorized read-only Azure planning run.

The resulting grant authorizes:

- one manually dispatched workflow at `.github/workflows/existing-collector-report-publication-plan.yml`;
- GitHub OIDC authentication through the protected `azure-lab` environment;
- current Azure context and inventory reads;
- ARM template validation;
- exact What-If;
- protected artifact upload.

It does not authorize:

- `az deployment group create`;
- role-assignment creation or deletion;
- Storage creation or deletion;
- VM Run Command;
- collector restart, replacement, deallocation, or guest change;
- report publication;
- frontend endpoint configuration;
- any Azure resource mutation.

```text
azure_authentication_authorized = true
azure_mutations_authorized      = false
```

## Workflow gates

The promoted planner is manual-only and requires:

1. a 40-character exact reviewed commit;
2. checkout and verification of that exact commit;
3. the protected `azure-lab` environment;
4. an exact typed confirmation:

```text
PLAN-PUBLICATION:<resource-group>:vm-stcollector-<prefix>-<environment>
```

5. a maximum monthly planning ceiling no greater than CAD 10.00;
6. static no-mutation tests before Azure login;
7. evidence upload even when the plan fails.

Default target inputs remain:

- resource group: `rg-servicetracer-dev-westus2`;
- region: `westus2`;
- prefix: `mst`;
- environment: `dev`;
- collector: `vm-stcollector-mst-dev`;
- allowed browser origin: `https://anthonyedgar30000.github.io`.

These defaults are not accepted as current Azure facts until the workflow observes and validates them.

## Intended planning evidence

The workflow calls `infra/scripts/plan_existing_collector_report_publication.sh` and should capture:

- request and exact repository commit;
- tenant, subscription, cloud, and authenticated identity type;
- resource-group identity, region, and tags;
- current collector resource, provisioning state, size, image, and system-assigned principal ID;
- existing tagged report Storage inventory;
- visible resource-group and report-Storage RBAC inventory;
- collector-principal role-assignment subset;
- ARM validation result;
- exact What-If result;
- explicit current-price boundary;
- plan summary with mutations unauthorized and unperformed;
- SHA-256 artifact manifest.

Sensitive identifiers may be retained in the protected workflow artifact but must be sanitized before public portfolio use.

## Current Azure evidence boundary

The latest promoted Azure evidence remains historical read-only planner run `29856203054`, observed July 21, 2026.

At that observation:

- resource group: `rg-servicetracer-dev-westus2`;
- region: `westus2`;
- collector: `vm-stcollector-mst-dev`;
- size: `Standard_B2ats_v2`;
- deployed image: Ubuntu 22.04;
- desired image: Ubuntu 24.04;
- evidence disk: attached with `deleteOption: Detach`;
- production NIC: static address and VM `deleteOption: Delete`;
- system-assigned identity: present;
- visible role assignments in that artifact: none;
- Azure mutations: unauthorized and unperformed.

That evidence does not prove the present tenant, subscription, resource inventory, principal ID, RBAC, Storage state, quota, pricing, guest health, or frontend behavior.

## Cost and quota boundary

The planned resource set for a future mutation remains one Standard LRS Storage account, report versions, requests, egress, and one Storage-scope role assignment, with no new compute.

- CAD 10.00 is a planning ceiling, not an estimate or quotation.
- ARM validation and What-If do not provide current pricing or actual cost.
- The planner must preserve missing current price or quota evidence as a later deployment blocker.
- No deployment may be inferred from a successful planning run.

```text
expected_low_cost
!= current_price_evidence
!= actual_cost
```

## Validation and expected outputs

Repository verification must prove:

- workflow is manual-only and OIDC-protected;
- exact commit and confirmation checks exist;
- the workflow and planner contain no Azure mutation commands;
- bounded authority grant permits authentication and dispatch but not mutation;
- artifacts are uploaded on success or failure;
- all unit tests and Bicep checks pass for the exact PR head;
- final diff remains limited to the six declared files.

A successful future planner run means only:

```text
current Azure context observed
+ ARM validation completed
+ exact What-If completed
+ evidence artifact preserved
!= deployment authorized
```

## Failure, rollback, and cleanup

Repository failure behavior:

1. keep the PR draft;
2. inspect exact failing CI jobs;
3. patch only the six declared paths;
4. obtain fresh exact-head CI;
5. never weaken OIDC, environment, commit, confirmation, artifact, cost, or no-mutation controls merely to pass.

Repository rollback is closing the PR or reverting its commits. After merge, disabling the planner requires a reviewed revert of the workflow and its bounded grant.

A dispatched planning run creates no Azure resources and therefore requires no Azure cleanup. Its GitHub artifact expires after 30 days unless deliberately preserved as promoted evidence.

## Claim boundary and next gate

After merge, the repository may claim that a guarded read-only Azure planning workflow exists. It may not claim that the planner has run, the endpoint exists, managed-identity publication works, or the frontend ingests live data.

The next gate after merge is dispatching the workflow against the exact merged commit, inspecting every job, downloading and hashing the artifact, and reconciling the resulting Azure observation before any deployment proposal.
