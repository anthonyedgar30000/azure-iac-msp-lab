# HELIX explicit-only archive

Content in this directory is retained for historical reconstruction, supersession analysis, closed-incident review, or comparison with current design. It is excluded from normal repository lookup.

## Entry requirements

Every archived document must begin with metadata equivalent to:

```yaml
---
helix_status: superseded
retrieval: explicit-only
superseded_on: 2026-07-21
superseded_by: path/to/current-artifact.md
reason_retained: Explains the earlier design and why it changed.
owner: Anthony
---
```

For historical material that was never superseded, use `helix_status: historical`, replace `superseded_on` with `archived_on`, and omit `superseded_by`.

## Archive rules

- Do not retrieve archive content unless the request explicitly asks for historical or superseded material.
- Never use archive content to override current source, tests, decisions, or operational evidence.
- Preserve links to the current replacement when one exists.
- Remove or update active links that would make archived material appear current.
- Do not archive secrets, credentials, customer evidence, regulated data, or unsanitized production logs. Remove those from Git history through an appropriate security process.
- Do not archive reproducible build output or low-value temporary debug files; delete or regenerate them instead.
- Closed pull requests and Git history already preserve implementation history. Archive an additional document only when it carries durable explanatory value.

## What normally belongs here

- superseded architecture documents;
- retired runbooks retained for migration history;
- closed incident summaries after durable lessons are promoted;
- abandoned proposals that explain a consequential decision;
- old current-state snapshots required for audit or comparison.

## What normally does not belong here

- full chat transcripts;
- private reasoning traces;
- screenshots that duplicate structured evidence;
- temporary agent progress narration;
- test logs already retained as workflow artifacts;
- generated binaries or dependency caches.
