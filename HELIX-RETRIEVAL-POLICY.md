# HELIX repository retrieval and archive policy

## Purpose

This repository contains implementation, tests, runbooks, architecture, operational status, proposals, and historical material. A lookup must not treat every matching file as equally current or authoritative.

This policy defines:

- what may be retrieved by default;
- what is authoritative for different kinds of claims;
- how proposed, implemented, deployed, and verified states remain distinct;
- how superseded material is archived without being mistaken for current truth;
- what should and should not be preserved in GitHub.

The machine-readable companion is [`.helix/retrieval-policy.json`](.helix/retrieval-policy.json). The initial repository classification is [`.helix/repository-context.json`](.helix/repository-context.json).

## Authority order

Use the narrowest relevant evidence. Higher entries outrank lower entries when they address the same claim.

1. **Live repository and environment evidence**: current branch/commit, pull-request state, CI results, deployment outputs, and operational verification artifacts.
2. **Source code, infrastructure definitions, and tests**: what the repository currently implements and checks.
3. **Current-state records and approved decisions**: explicit interpretation of implementation and runtime status.
4. **Current architecture and runbooks**: intended structure and operating procedure, verified against source before consequential action.
5. **Proposals and design candidates**: useful for options, never proof of implementation.
6. **Archived or superseded material**: historical context only and excluded from ordinary lookup.
7. **Conversation recollection or unclassified notes**: candidate context requiring repository verification.

No single source proves every state. For example, source code can prove that a capability is implemented, but not that it is deployed or operationally verified.

## Required state vocabulary

Use these states instead of the ambiguous word `done`:

- `proposed`: discussed or documented only;
- `implemented`: present in a branch or the trusted baseline;
- `ci_verified`: automated checks passed against that implementation;
- `deployed`: applied to an environment;
- `operationally_verified`: runtime evidence demonstrates the intended behavior;
- `manual_drift`: runtime changes exist that are not reproduced by the trusted deployment path;
- `superseded`: replaced by a newer approved artifact;
- `historical`: retained only to explain prior state.

A document may contain sections in different states. Each claim must retain its own status when the document mixes current and planned material.

## Retrieval classes

### `authoritative-current`

Retrieve by default when relevant. Examples include current source, tests, Bicep, workflow definitions, approved decision records, and evidence-backed current-state records.

### `supporting-current`

Retrieve by default as supporting context, but verify consequential claims against authoritative-current material. Architecture overviews and runbooks normally fall here.

### `candidate`

Retrieve only when comparing options, investigating an open question, or explicitly asked. Candidate material must not be described as implemented or approved.

### `explicit-only`

Do not retrieve during ordinary project lookup. Use only when the request explicitly asks for history, a superseded design, a closed incident, or a prior decision path.

### `excluded-sensitive`

Must not be committed or indexed as project context. This includes credentials, private keys, bearer tokens, SAS tokens, customer evidence, regulated personal data, and unsanitized production logs.

## Lookup procedure

Before answering a repository-state question or modifying the project:

1. Confirm the current `main` commit, relevant branches, open pull requests, and CI state.
2. Read [`.helix/repository-context.json`](.helix/repository-context.json) and select only relevant default-retrieval paths.
3. Inspect the source code and tests that directly implement the claim.
4. Inspect current-state and decision records for deployment or authority status.
5. Check dates, commit references, PR references, and supersession metadata.
6. Surface conflicts instead of silently selecting one source.
7. State what was not verified and which review lens was applied.
8. Access `.helix/archive/` only for an explicit historical request.

Repository search results are candidates until this procedure establishes their retrieval class and freshness.

## Conflict and freshness rules

- Current source and tests outrank descriptive implementation claims.
- Deployment and operational claims require environment evidence; a merged PR is insufficient.
- A newer modification timestamp does not automatically make a copied or lightly edited document current.
- A document referencing merged work as still pending must be marked for refresh rather than treated as current state.
- When two reliable sources conflict, retain both claims, record the conflict, and request or gather resolving evidence.
- Archived content never overrides current material, even when keyword matching ranks it higher.

## Archive boundary

Move an artifact to `.helix/archive/` when it is superseded, completed and no longer operationally relevant, abandoned, duplicated, or retained only to explain a historical decision.

Every archived artifact must identify:

- `helix_status: superseded` or `historical`;
- `retrieval: explicit-only`;
- the archival or supersession date;
- `superseded_by`, when a replacement exists;
- the reason it remains useful.

Archiving is not deletion. Delete material that has no durable value, is reproducible output, or should never have been committed. Never move sensitive content into the archive as a substitute for removing it.

## What belongs in GitHub

Preserve durable, inspectable artifacts:

- source code, IaC, workflows, and tests;
- protocol schemas and machine-readable contracts;
- current architecture and implementation status;
- approved decision records;
- runbooks, recovery procedures, and authority boundaries;
- sanitized evidence summaries and references to temporary workflow artifacts;
- handoff manifests that contain no secrets or customer evidence.

Do not preserve by default:

- full conversation transcripts;
- private model reasoning or agent narration;
- temporary debug output and reproducible build products;
- raw cloud logs containing identifiers or sensitive data;
- speculative text without candidate status;
- screenshots when structured evidence exists;
- secrets of any kind.

## Relationship to workflow observability

This retrieval policy does not replace branch ownership, current workstream state, handoffs, or deployment history. When a `.project/` workflow-observability layer is present, use it to identify active work and ownership. Use `.helix/` to decide which repository artifacts may be treated as current authority during lookup.

```text
.project  -> what work is active, owned, and awaiting a gate
.helix    -> what information is current, candidate, archived, or excluded
Git/CI    -> what implementation and checks actually exist
Azure     -> what is deployed and operationally verified
```

## Promotion and archival workflow

```text
candidate proposal
  -> bounded implementation branch
  -> tests and review
  -> accepted decision or current-state update
  -> default retrieval
  -> later superseded
  -> explicit-only archive
```

Anthony retains promotion authority for canonical project decisions and authorization for destructive or externally consequential actions.
