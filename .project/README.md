# Workflow observability

This directory is the shared operational state for humans and AI-assisted work on the repository. Git, pull requests, CI, and deployment evidence remain authoritative; these files make their meaning easy to reconstruct across conversations.

The ChatGPT project **ServiceTracer — Governed Azure Operations Lab** is the canonical conversational workspace. It organizes context across sessions, while GitHub and `.project/` remain the canonical implementation and coordination state.

## Read order before changing the project

1. Read `active-work.json` to see branch ownership, scope, and gates.
2. Read `workstream-catalog.json` to place the work in one of the six canonical streams and preserve its claim boundary.
3. Read `environment-state.json` to distinguish implemented, deployed, and verified facts.
4. Read the latest entry in `deployment-history.jsonl`.
5. Read the relevant file in `handoffs/`.
6. Confirm the live GitHub branch, pull-request, and CI state before writing.

## Canonical workstreams

1. Architecture and design decisions
2. Azure resource plan and IaC
3. Deployment evidence and screenshots
4. Cost, health, and configuration telemetry
5. ServiceTracer findings and reports
6. Portfolio/demo narrative

`workstream-catalog.json` defines each stream's purpose, primary repository paths, and evidence boundary. A bounded implementation branch may touch more than one stream only when its declared objective and permitted file scope make that overlap explicit.

## Baseline commit semantics

The `trusted_baseline.commit` value is the last `main` commit verified when the state record was authored. It is an observation anchor, not a substitute for checking the current branch head.

A pull request that refreshes this directory cannot predict the future merge commit that will contain the refresh. After merge, live GitHub state therefore outranks the recorded observation anchor. Refresh the state record when later completed increments materially change its meaning, not merely because the merge itself created a new commit SHA.

## Write rules

- One bounded workstream owns writes to one feature branch.
- Other conversations may review that branch, but must not independently modify it.
- A new implementation scope gets a new branch and a new workstream entry.
- Every branch declares its objective, permitted paths, verification criteria, and next gate.
- Environment claims require a status, evidence source, and last-observed date.
- `implemented`, `ci_verified`, `deployed`, and `operationally_verified` are different states.
- A workstream is released when its pull request is merged, closed, or explicitly handed off.
- A state-only reconciliation may publish an empty `workstreams` list when no implementation branch retains write ownership after merge.
- Never store secrets, bearer tokens, private keys, SAS tokens, or customer evidence here.

Run the structural check locally with:

```bash
python .project/validate.py
```
