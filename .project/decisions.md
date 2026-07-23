# Workflow decisions

## Authority precedence

Chat history supports continuity, but current GitHub state, exact-head CI, repository declarations, protected workflow artifacts, and fresh Azure evidence determine implementation and runtime truth.

```text
conversation_context != repository_authority
repository_declaration != deployed_reality
promoted_evidence != current_reality
```

## Live repository state is query-only

Current `main`, active branches, open pull requests, write ownership, review state, mergeability, and CI must be queried from Git and GitHub.

They must not be persisted as self-updating truth inside merged project files.

A pull-request description carries the transient branch objective, permitted paths, authority, verification criteria, failure behavior, rollback, and cleanup while the PR is open.

## Durable repository state

`.project/active-work.json` preserves:

- the last substantive accepted baseline;
- the latest promoted repository event;
- versioned repository capabilities;
- bounded authority grants;
- promoted evidence;
- fail-closed authority defaults;
- rules for resolving live state.

`.project/repository-events.jsonl` is curated, non-exhaustive history. Absence from that log does not prove that an event did not happen.

## State vocabulary

- **proposed**: discussed or documented only.
- **implemented**: present in a branch or `main`.
- **ci_verified**: automated checks passed for the exact implementation.
- **deployed**: resources or software were applied.
- **operationally_verified**: runtime evidence proves the intended behavior.
- **manual_drift**: runtime changes exist outside the trusted deployment path.
- **superseded**: newer evidence or implementation replaces the claim while preserving its history.

Never collapse these into “done.”

## Environment facts

Every environment fact identifies:

- value;
- status;
- evidence source;
- observation time;
- claim boundary or limitation.

Conflicting evidence is retained and classified rather than silently overwritten.

## Human authority

A recommendation, CI result, accepted What-If, or persistence control message cannot grant new authority.

```text
recommended_control_message != workflow_dispatch_authorized
accepted_What-If != Azure_mutation_authorized
cleanup_required != cleanup_authorized
```

Authority remains fail-closed unless a current human instruction and exact workflow contract grant a bounded exception.

## Handoffs

A durable handoff records architecture, promoted evidence, unresolved gates, failure and rollback behavior, and the safe next decision boundary.

It does not claim that a branch or pull request remains active after merge.

## Safety boundary

Project state must not contain Azure credentials, SSH private keys, bearer tokens, SAS tokens, exact private identity values, raw customer evidence, or other secrets.

Protected artifacts retain detailed operational evidence; committed state contains only bounded, sanitized claims.

## Replacement execution

Collector replacement remains inactive until recovery-point proof, isolated boot rehearsal, NIC handling, identity and RBAC restoration, cost controls, cleanup ownership, and independent review are resolved.

The generated `REPLACE:` phrase is reference data only.

## Frontend endpoint promotion

A live report or demo API URL must not be committed merely because its intended DNS name is known.

Promote a live URL only after Azure existence, TLS, API or report behavior, CORS, provenance, freshness, and browser rendering are verified. Query-string overrides are the bounded pre-promotion test path.
