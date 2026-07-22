# Workflow observability

This directory is the shared operational state for humans and AI-assisted work on the repository. Git, pull requests, CI, and deployment evidence remain authoritative; these files preserve bounded declarations and time-stamped observations so their meaning can be reconstructed across conversations.

The ChatGPT project **HELIX — Governed Agent Engineering** is the umbrella conversational workspace. Within it, **ServiceTracer — Governed Azure Operations Lab** is the bounded repository workstream represented by this repository. Chat context organizes reasoning and handoffs; GitHub and `.project/` preserve implementation and coordination evidence, while fresh Azure evidence determines deployed and operational state.

## Read order before changing the project

1. Read `active-work.json` for the last substantive baseline, the latest repository observation, the authored-change declaration, authority boundaries, and live-state resolution rules.
2. Read `workstream-catalog.json` to place the work in one of the six canonical ServiceTracer streams and preserve its claim boundary.
3. Read `environment-state.json` to distinguish implemented, deployed, and verified facts.
4. Read the latest entry in `deployment-history.jsonl`.
5. Read the relevant file in `handoffs/`.
6. Query live GitHub branch, pull-request, and CI state before writing.
7. Query fresh authenticated Azure state before making deployed, cost, quota, RBAC, guest-health, rollback, or recovery claims.

## Canonical ServiceTracer workstreams

1. Architecture and design decisions
2. Azure resource plan and IaC
3. Deployment evidence and screenshots
4. Cost, health, and configuration telemetry
5. ServiceTracer findings and reports
6. Portfolio/demo narrative

`workstream-catalog.json` defines each stream's purpose, primary repository paths, and evidence boundary. A bounded implementation branch may touch more than one stream only when its declared objective and permitted file scope make that overlap explicit.

## Repository-state semantics

`active-work.json` uses `project.active-work.v2`.

The model deliberately separates:

```text
last_substantive_baseline
!= repository_observation.main_head
!= current_repository_head
```

- `last_substantive_baseline` is the most recent accepted commit that materially changed the governed design or implementation.
- `repository_observation.main_head` is a time-bounded GitHub observation captured before or during the authored change.
- `current_repository_head` is never predicted or stored as a self-updating truth. Query live GitHub whenever the file is read.
- Coordination-only merge commits may advance the repository head without changing the last substantive baseline.

A pull request cannot predict the SHA of the merge commit that will contain its own state update. The schema therefore forbids the retired self-referential fields `trusted_baseline`, `workstreams`, `known_open_pull_requests`, and `next_bounded_operation`.

## Authored-change declaration

`authored_change` describes the branch's ownership, scope, authority, permitted paths, verification criteria, failure behavior, and rollback behavior. It is a durable declaration of how the change was governed, **not** a live status record.

Its required semantic marker is:

```text
state_semantics = declaration_not_live_status
```

The pull request number may be null before the PR is opened and a positive integer afterward. Merge, closure, CI, and review state must still be resolved from live GitHub.

## Write rules

- One bounded change owns writes to one feature branch.
- Other conversations may review that branch, but must not independently modify it.
- A new implementation scope gets a new branch and authored-change declaration.
- Every branch declares its objective, permitted paths, verification criteria, failure behavior, and rollback behavior.
- Environment claims require a status, evidence source, and last-observed date.
- `implemented`, `ci_verified`, `deployed`, and `operationally_verified` are different states.
- Moving a conversation between ChatGPT projects changes conversational context only; it never changes Git, CI, Azure, or execution authority.
- Never store secrets, bearer tokens, private keys, SAS tokens, or customer evidence here.

Run the structural check locally with:

```bash
python .project/validate.py
```
