# Azure IaC MSP Lab — Constitution

## Constitutional status

This document is the version-controlled constitution for the Azure IaC MSP Lab and its ServiceTracer governed-operations workstream.

It records the repository-level application of the wider Project Reality Synchronizer constitutional architecture. It is accepted by explicit human instruction dated July 25, 2026. Higher-authority live evidence remains authoritative within its proper scope.

## Purpose

The lab exists to design, deploy, secure, validate, operate, and document a realistic Azure environment through repeatable infrastructure-as-code and professional operational practice.

The repository must preserve the difference between intended architecture, declared implementation, Azure deployment, effective configuration, runtime behaviour, cost, resilience, and verified operational outcomes.

## Source-specific authority

Authority is resolved by claim type rather than by treating one source as universally current:

- live Git and GitHub establish current repository, branch, pull-request, review, and CI state;
- committed source, tests, contracts, and governance establish repository declarations;
- protected workflow artifacts establish what an exact workflow run observed or attempted;
- fresh Azure control-plane and Resource Graph evidence establish Azure resource and configuration state;
- fresh guest, endpoint, transaction, alert, backup, recovery, cost, and quota evidence establish their respective operational claims;
- `.project/` records preserve time-bounded declarations, promoted evidence, decisions, limitations, and authority boundaries;
- conversation context supports continuity but does not override higher-authority evidence.

## Canonical boundaries

```text
declared_in_code != deployed_in_Azure
deployment_succeeded != service_validated
resource_exists != securely_configured
RBAC_assignment != effective_least_privilege
monitoring_enabled != alerts_verified
backup_configured != recovery_tested
high_availability != disaster_recovery
estimated_cost != actual_cost
repository_snapshot != live_repository_dashboard
promoted_evidence != current_Azure_state
synchronization != authorization
```

These distinctions must remain visible in architecture, IaC, pull requests, evidence, handoffs, runbooks, validation, and portfolio claims.

## Infrastructure increment requirements

Every consequential infrastructure increment must define:

- intended architecture;
- subscription, tenant, region, resource group, and resource scope;
- dependencies and network paths;
- identity, permissions, and effective-access assumptions;
- security and policy controls;
- cost, quota, and budget implications;
- deployment method and exact source binding;
- validation commands, expected outputs, and evidence to capture;
- failure classification and stop conditions;
- rollback, recovery, cleanup, or decommissioning procedure;
- authority boundaries and expiry.

Portal-only actions must be documented and evaluated for later codification.

## Synchronization Termination Principle

The Azure IaC MSP Lab adopts the exact canonical name **Synchronization Termination Principle**.

A `.project` current-reality file, handoff, reconciliation, deployment record, or evidence digest is a bounded, time-qualified observation. It is not required to update itself continuously and is not defective merely because it cannot contain a future commit or merge caused by its own publication.

```text
snapshot != live_dashboard
snapshot_not_self_referential != stale_defect
repository_merge != automatic_reconciliation_trigger
```

The following identities are conceptually distinct:

- **observed subject** — the commit, workflow run, deployment, Azure scope, runtime, or authority context inspected;
- **snapshot source** — the source revision containing or generating the snapshot;
- **promotion event** — a later merge, commit, artifact publication, or durable-history entry.

A later promotion event may be queried live or captured during a later substantive increment. Its absence from the original snapshot does not mean the event did not happen and does not require a status-only pull request.

## Synchronization trigger

The **Material Uncertainty Synchronization Rule** owns the trigger.

Perform a fresh bounded reality synchronization when uncertainty could materially change a current dependent decision or consequential operation, including:

- IaC design or deployment;
- ARM validation or What-If acceptance;
- Azure mutation or rollback;
- identity, RBAC, policy, secret-store, or network change;
- cost, quota, budget, or region selection;
- endpoint promotion or service validation;
- monitoring, alert-delivery, backup, recovery, or disaster-recovery claims;
- cleanup, resource move, decommissioning, or destructive action;
- merge or review decisions whose correctness depends on repository or Azure facts that may have materially changed.

A routine repository merge, branch closure, completed CI run, or snapshot publication does not independently satisfy this trigger.

## Synchronization termination

Stop the bounded synchronization when:

- the evidence threshold for the declared decision is satisfied;
- the result is correctly classified as unknown, conflicting, stale, not observable, insufficiently authoritative, blocked, or escalated;
- the approved source set has been inspected;
- a separate authorization, implementation, verification, rollback, recovery, cleanup, or human-review gate is next.

Do not continue merely to erase every unknown or make the snapshot mention its own publication.

```text
no_material_uncertainty
→ no_reconciliation

no_consequential_operation
→ no_reality_sync_churn

reconciliation_merged
!= reconcile_the_reconciliation
```

## Durable state and live state

Current branch, pull request, repository head, review, mergeability, and CI are query-only facts. Durable repository history may be curated and non-exhaustive.

A durable event not yet being promoted means only that it is not yet in curated project memory.

```text
event_not_promoted_yet != event_did_not_happen
durable_history != live_status
```

A later substantive change may promote relevant history. No separate pull request is required solely to clear a merged branch, record a merge commit in the snapshot that produced it, or advance a repository watermark with no material operational consequence.

## Authority and execution

Recommendations, synchronization results, CI, accepted What-If, resource existence, or human-interface check rollups do not manufacture operational authority.

Authority must remain identity-bound, action-bound, scope-bound, method-bound, time-bound, and non-renewing unless an explicit bounded grant states otherwise.

```text
verification_authorized != deployment_authorized
accepted_WhatIf != Azure_mutation_authorized
failed_attempt != retry_authorized
merge_observed != prior_agent_merge_authority
```

## Evidence and secret handling

Every material claim must preserve sufficient provenance to recover its source and boundary. Missing or inaccessible evidence must remain visible as uncertainty rather than being converted into absence or failure.

Never expose credentials, bearer tokens, private keys, SAS values, customer-sensitive data, private identity values, or unredacted protected evidence in code, logs, screenshots, handoffs, or project context.

## Termination rule for repository governance

A constitutional or governance pull request terminates after its exact bounded content is reviewed and its lifecycle is resolved live.

Its own later merge does not create a constitutional requirement for another status-only reconciliation. A new governance increment requires a new substantive objective or a material uncertainty that could alter a consequential decision.
