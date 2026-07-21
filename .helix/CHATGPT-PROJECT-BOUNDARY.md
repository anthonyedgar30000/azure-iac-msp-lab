# ChatGPT project context boundary

This repository is the durable source boundary for the ServiceTracer implementation work and its HELIX governance artifacts. ChatGPT projects and conversations are reasoning workspaces, not automatic repository authority.

## Recommended project layout

Use two project-only-memory workspaces where available:

```text
HELIX — Governed Agent Engineering
  -> umbrella active workspace for governed-agent architecture, review routing,
     evidence policy, and bounded implementation workstreams
  -> ServiceTracer — Governed Azure Operations Lab is the bounded workstream
     represented by this repository

HELIX — Historical Archive
  -> superseded discussions, completed investigations, abandoned approaches,
     and old handoffs
```

The ServiceTracer workstream may span multiple conversations inside the HELIX umbrella project, but it has one repository state, one branch owner per bounded increment, and one authoritative Git/CI/Azure evidence chain.

Moving a conversation to the historical project creates a stronger reasoning boundary than merely hiding it in the interface. The active project should contain only context that may still affect current decisions.

## Keep in the active project

- current architecture and implementation discussions;
- active branches, pull requests, and CI investigations;
- unresolved contradictions, risks, and evidence requests;
- current security, operations, cost, networking, and product reviews;
- accepted decisions awaiting promotion to GitHub;
- active HELIX handoff packages.

## Move to the historical project

- superseded architecture;
- completed incidents after durable lessons are promoted;
- abandoned approaches;
- duplicate summaries;
- old branch-by-branch debugging narratives;
- exploratory brainstorming with no active decision dependency.

## Before moving a conversation

Promote durable value into GitHub:

1. accepted decision or ADR;
2. current-state correction;
3. architecture change;
4. test or machine-readable contract;
5. runbook or recovery procedure;
6. bounded evidence summary;
7. unresolved question or risk.

Do not save a full transcript when a smaller inspectable artifact carries the durable meaning.

## Conversation handoff package

Use a bounded package when moving work between project conversations:

```yaml
helix_version: HX-0.1
message_type: conversation_handoff
package_id: HX-PKG-YYYYMMDD-001
correlation_id: HX-WORKSTREAM-001
source_conversation: ServiceTracer Azure Engineering
requested_recipient_role: security-reviewer
scope:
  - collector image replacement boundary
verified_facts: []
candidate_claims: []
unresolved_conflicts: []
repository_artifacts: []
authority:
  candidate_only: true
  promotion_authority: Anthony
completeness:
  object_count: 0
  end_of_package: true
```

The receiving conversation should acknowledge completeness, identify missing objects, and return candidate artifacts rather than silently changing canonical state.

## Review hats

A conversation may specialize in a review lens such as security, operations, evidence quality, change management, networking, cost, technician practicality, product value, or adversarial review.

Every review should state:

- the selected lens;
- evidence inspected;
- findings and conditions;
- decision authority;
- what was outside scope;
- whether any repository artifact was promoted.

Approval under one hat does not imply approval under another.

## Authority boundary

```text
conversation output
  -> candidate artifact
  -> evidence and scope validation
  -> Anthony review or delegated authority
  -> pull request and repository promotion
  -> current retrieval class
```

Moving a conversation into **HELIX — Governed Agent Engineering** establishes conversational placement only. It does not transfer branch ownership, approve a pull request, activate a workflow, authorize a confirmation phrase, or permit Azure mutation.

Destructive, externally consequential, or production-affecting actions require separate explicit authorization. A conversation handoff, project move, or agent progress message never provides that authority.
