# Repository context migration checklist

This checklist classifies and archives repository context without breaking current implementation paths or silently changing authority.

## Phase 1 — Inventory

- [ ] Confirm the current `main` commit and open pull requests.
- [ ] Identify documents, generated artifacts, screenshots, logs, and historical notes.
- [ ] Record which files are linked from `README.md`, workflows, source, tests, or GitHub Pages.
- [ ] Identify files containing secrets, customer evidence, personal data, or unsanitized logs. Handle those as security remediation, not archival work.
- [ ] Add important paths to `.helix/repository-context.json`.

## Phase 2 — Classify

Assign each durable artifact one retrieval class:

- [ ] `authoritative-current`
- [ ] `supporting-current`
- [ ] `candidate`
- [ ] `explicit-only`
- [ ] `excluded-sensitive`

Then record:

- [ ] state: proposed, implemented, CI-verified, deployed, operationally verified, manual drift, superseded, or historical;
- [ ] owner and authority;
- [ ] effective or observed date;
- [ ] evidence sources;
- [ ] supersession target, when applicable;
- [ ] review lens and unreviewed concerns.

## Phase 3 — Promote durable insights

Before archiving a conversation, incident, or exploratory document:

- [ ] extract accepted decisions into an ADR or decision ledger;
- [ ] update current architecture if the accepted design changed;
- [ ] update implementation status using current repository and runtime evidence;
- [ ] preserve reusable schemas, tests, runbooks, or recovery procedures;
- [ ] preserve only sanitized, bounded evidence summaries;
- [ ] record unresolved questions instead of burying them in history.

## Phase 4 — Archive safely

- [ ] Confirm the artifact is no longer needed for default retrieval.
- [ ] Add explicit-only archive metadata.
- [ ] Link `superseded_by` when a replacement exists.
- [ ] Move the artifact into `.helix/archive/` only when Git history alone is insufficient.
- [ ] Update active links and indexes.
- [ ] Confirm no workflow, test, GitHub Pages path, or source reference was broken.
- [ ] Do not archive secrets or sensitive evidence.

## Phase 5 — Verify retrieval behavior

Run three manual queries against the repository context:

1. **Current-state query:** should use source, tests, current status, PR/CI state, and runtime evidence.
2. **Proposal query:** should label candidate material and avoid implementation claims.
3. **Historical query:** should access `.helix/archive/` only because history was explicitly requested.

For each query verify:

- [ ] the retrieval class is stated or inferable;
- [ ] archived material did not override current material;
- [ ] deployment claims have environment evidence;
- [ ] conflicts and stale references are surfaced;
- [ ] one review lens did not imply universal approval.

## Initial cleanup candidates

These are review candidates, not automatic moves:

- [ ] Refresh `docs/implementation-status.md`; its next-increment section references already-merged work as pending.
- [ ] Add explicit implemented/planned labels to mixed sections of `docs/architecture.md`.
- [ ] Review closed debugging narratives and promote durable lessons rather than copying transcripts.
- [ ] Refresh `.project/active-work.json` and `.project/handoffs/current-state.md`; they still record PR #19 as open, use the PR #18 baseline, and omit merged PR #20.
- [x] Classify PR #19 as merged workflow-observability work.
- [x] Classify PR #20 as merged image-drift detection and read-only planning work.
- [ ] Run the collector replacement planning workflow and review its evidence before designing any mutation-capable execution path.
- [ ] Preserve the boundary that PR #20 proves detection and planning only; it does not prove that a replacement occurred.

This branch establishes policy only. It deliberately does not mass-move existing files into the archive or modify Azure resources.
