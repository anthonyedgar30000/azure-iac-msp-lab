# HELIX repository context boundary

This directory governs how humans and AI-assisted work retrieve, classify, promote, and archive repository context.

## Read order

1. [`../HELIX-RETRIEVAL-POLICY.md`](../HELIX-RETRIEVAL-POLICY.md)
2. [`retrieval-policy.json`](retrieval-policy.json)
3. [`repository-context.json`](repository-context.json)
4. [`.project/`](../.project/) for active-work structure, handoffs, and environment facts, with freshness verified against live Git and CI
5. Relevant source, tests, current-state records, decisions, and live GitHub evidence
6. [`MIGRATION-CHECKLIST.md`](MIGRATION-CHECKLIST.md) before reclassifying or archiving existing material

Do not begin with `.helix/archive/` unless the request explicitly concerns history or supersession.

## Separation of concerns

```text
Git and pull requests     -> branch and implementation truth
CI                        -> automated verification evidence
Azure/runtime evidence    -> deployment and operational truth
.project/                 -> active workstreams, ownership, handoffs, environment facts
.helix/                   -> retrieval class, archival boundary, promotion semantics
conversations             -> reasoning context and candidate artifacts
```

The `.project/` layer is active on `main`. Its files still require ordinary freshness checks: a structured state file can itself become stale after a merge. `.helix/repository-context.json` records known freshness defects instead of allowing stale metadata to silently override live Git and CI evidence.

## Default retrieval behavior

- Retrieve directly relevant source and tests.
- Retrieve current-state and decision records when present.
- Use architecture and runbooks as supporting context.
- Treat proposals and unclassified notes as candidates.
- Exclude `.helix/archive/` from ordinary lookup.
- Never treat a conversation transcript as repository authority.
- Treat `.project/` metadata as supporting rather than conclusive when its recorded branch, PR, baseline, or gate conflicts with live repository state.

## Review hats

A lookup or review should identify its lens where practical:

- security;
- operations and recovery;
- evidence quality;
- change management;
- networking;
- Azure cost;
- technician practicality;
- product value;
- adversarial review.

Approval or confidence under one lens does not imply approval under another. Record what was not reviewed.

## Promotion rule

A useful conversation or agent result becomes durable repository context only after it is reduced to an inspectable artifact, assigned a state and retrieval class, reviewed within its authority boundary, and committed through the normal branch and pull-request process.

Do not commit full transcripts merely to preserve context. Promote decisions, schemas, tests, runbooks, bounded evidence summaries, or handoff packages instead.
