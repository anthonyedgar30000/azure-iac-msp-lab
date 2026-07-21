# Workflow decisions

## Git is the coordination authority

Chat history is useful context, but the repository, pull requests, CI results, and recorded deployment evidence decide the current project state.

## Branch ownership

A bounded workstream has one write-owning branch. Another conversation may inspect, test, or review that branch, but it must not independently push competing changes to it. Parallel implementation requires a separate branch and an explicit entry in `active-work.json`.

## State vocabulary

- **proposed**: discussed or documented only.
- **implemented**: present in a branch or `main`.
- **ci_verified**: automated checks passed against the implementation.
- **deployed**: resources or software were applied to an environment.
- **operationally_verified**: runtime evidence demonstrates the intended behavior.
- **manual_drift**: runtime changes exist that are not yet reproduced by the trusted deployment path.

Never collapse these states into a single word such as “done.”

## Environment facts

A fact must identify its value, status, evidence source, and last-observed date. When evidence conflicts, retain both claims and mark the conflict instead of silently selecting one.

## Handoffs

Before a workstream changes conversations or owners, update its handoff with:

- branch and pull request;
- bounded purpose;
- completed verification;
- deployment state;
- unresolved risks;
- next authorized action.

## Safety boundary

Workflow observability contains metadata only. It must never contain Azure credentials, SSH private keys, bearer tokens, SAS tokens, raw customer evidence, or other secrets.
