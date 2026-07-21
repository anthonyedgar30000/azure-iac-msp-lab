# HELIX document metadata templates

Use metadata that makes status, authority, freshness, and lookup behavior visible without reading the entire document.

## Current canonical or approved document

```yaml
---
helix_status: canonical
authority: approved
retrieval: default
effective_on: 2026-07-21
last_verified_on: 2026-07-21
owner: Anthony
supersedes:
  - .helix/archive/example-v0.md
source_evidence:
  - current source and tests
  - approved pull request
review_lenses:
  - architecture
  - evidence-quality
not_reviewed:
  - production cost
---
```

## Current-state document

```yaml
---
helix_status: current-state
authority: evidence-backed
retrieval: default
observed_on: 2026-07-21
owner: Anthony
environment: dev
evidence:
  - workflow run or Azure verification reference
known_gaps:
  - replacement deployment not operationally verified
---
```

## Candidate proposal

```yaml
---
helix_status: candidate
authority: none
retrieval: explicit-or-supporting
created_on: 2026-07-21
owner: Anthony
implementation_claim: false
promotion_gate:
  - bounded review
  - accepted decision
  - implementation evidence where applicable
---
```

## Archived or superseded document

```yaml
---
helix_status: superseded
authority: historical
retrieval: explicit-only
superseded_on: 2026-07-21
superseded_by: path/to/current-document.md
reason_retained: Explains the prior design and migration decision.
owner: Anthony
---
```

## Review result

```yaml
---
helix_status: review-result
authority: scoped
retrieval: default
review_id: HX-REV-0001
review_lens: security
reviewer: Anthony
decision: approved-with-conditions
reviewed_on: 2026-07-21
scope:
  - identity
  - permissions
  - destructive operations
outside_scope:
  - cost
  - product value
conditions:
  - exact confirmation required
  - recovery evidence required
---
```

A review result applies only to its declared scope and lens. It must not be interpreted as universal approval.
