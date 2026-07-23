# Workflow observability

This directory preserves governed project memory for humans and AI-assisted work. GitHub, CI, workflow artifacts, and Azure remain the live authorities. `.project/` stores durable declarations, promoted evidence, authority boundaries, and curated history so their meaning survives across conversations.

## Read order before changing the project

1. Read `active-work.json` for the accepted substantive baseline, latest promoted repository event, declared repository capabilities, authority defaults, promoted operational evidence, and live-resolution rules.
2. Read `repository-events.jsonl` for curated merge events. It is durable history, not an exhaustive mirror of GitHub.
3. Read `workstream-catalog.json` to place the work in one of the six canonical ServiceTracer streams.
4. Read `environment-state.json` and the latest entry in `deployment-history.jsonl`.
5. Read `handoffs/current-state.md`.
6. Query live GitHub for the current default-branch head, branches, open pull requests, reviews, threads, mergeability, and exact-head CI.
7. Query fresh authenticated Azure state before making deployment, cost, quota, RBAC, guest-health, rollback, recovery, or service-validation claims.

## Repository-state model

`active-work.json` uses `project.active-work.v3`.

The model separates durable memory from live state:

```text
last_substantive_baseline
!= latest_promoted_repository_event
!= current_repository_head

durable_history
!= live_status
```

- `last_substantive_baseline` is the latest promoted event that materially changed the governed implementation.
- `latest_promoted_repository_event` is the newest GitHub event intentionally copied into durable project memory.
- Neither field claims to be the current GitHub head.
- `repository-events.jsonl` is curated and non-exhaustive. Missing a newer GitHub event means “not yet promoted,” not “the event did not happen.”
- The current head, active branch, open pull requests, pull-request status, and current CI status are query-only facts.

The schema and validator reject persisted live-status fields such as:

```text
repository_observation
main_head
open_pull_requests
active_branch
active_pull_request
current_repository_head
current_branch
current_pull_request
```

This prevents a pull request from merging a document that immediately and falsely says its own branch or pull request is still active.

## Work ownership

Active write ownership is resolved from live Git and GitHub at the beginning of every increment. It is not persisted as timeless project truth.

A pull-request description carries the branch-specific declaration while the PR is open:

- objective and permitted paths;
- authority and identity boundaries;
- dependencies, network path, and security controls;
- cost implications;
- validation commands and expected outputs;
- failure, rollback, cleanup, and evidence requirements.

After merge, those facts remain available in GitHub history. No follow-up “reconcile the reconciliation” PR is required merely to clear the old active branch or PR.

```text
PR_body_describes_open_change
!= merged_project_live_status
```

## Repository events

`repository-events.jsonl` records selected durable GitHub events, currently pull-request merges. Each event carries:

- unique event ID;
- repository and pull-request identity;
- title, source head when available, and merge commit;
- merge time and exact-head CI when available;
- qualification, evidence source, and claim boundary.

The ledger may be updated during a later substantive increment or by a separately governed post-merge automation. It is not required to predict or immediately record the merge commit of the pull request that edits it.

```text
event_not_promoted_yet
!= event_did_not_happen
```

## Authority

`authority_defaults` are fail-closed. Workflow dispatch, Azure authentication, guest commands, and Azure mutations are unauthorized unless a narrowly scoped `bounded_authority_grants` entry and current human instruction explicitly permit them.

A read-only grant may allow OIDC login, inventory, ARM validation, and What-If while keeping mutations prohibited.

```text
azure_authenticated != azure_mutation_authorized
what_if_completed != deployment_succeeded
```

## Repository versus runtime

Repository capability declarations establish versioned implementation only.

```text
workflow_present != workflow_dispatched
IaC_declared != Azure_deployed
deployment_succeeded != service_validated
resource_exists != securely_configured
```

`deployment_state` contains only promoted evidence. A false value means no qualifying evidence has been promoted into repository state; it does not replace a fresh Azure query.

## Write rules

- One bounded feature branch owns one increment.
- Resolve live GitHub and Azure state before proposing or writing.
- Do not persist current branch, current PR, current head, or current CI as self-updating truth.
- Preserve repository history without presenting it as current runtime state.
- Never expose secrets, tokens, private keys, SAS values, customer evidence, or unredacted protected artifacts.
- Moving a conversation between ChatGPT projects changes conversational context only; it changes neither GitHub nor Azure authority.

Run the structural check locally with:

```bash
python .project/validate.py
```
