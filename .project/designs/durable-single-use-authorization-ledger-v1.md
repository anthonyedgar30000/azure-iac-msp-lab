# Durable single-use deployment authorization ledger v1

## Status

**Historical branch-boundary marker: Proposed, not implemented.** This sentence is retained only so historical validators can reproduce the pre-merge observation boundary.

**Current canonical status: implementation merged to `main` in PR #186; merged, not activated.** The exact implementation head `138659609b15ef80f6cce12d916e26382ab71205` passed CI run `30389249099` and merged at `30e312ef5122831a8233835db2f541437a97b125`.

The deterministic immutable-request verifier and reusable no-OIDC claim workflow are now repository implementation. They are not yet an operationally verified authorization control.

The following remain deliberately incomplete:

- the protected `refs/tags/authority-consumed/**` repository ruleset is not configured or independently inspected;
- no live first-claim, replay, or concurrent-claim test has been dispatched;
- no collector deployment workflow calls this reusable workflow;
- the collector Azure workflow remains quarantined and fail-closed;
- no Azure authentication, query, mutation, deployment, verification, rollback, cleanup, or RBAC authority exists.

```text
implementation_merged != control_activated
atomic_claim_workflow_present != protected_ledger_verified
```

## Problem statement

The previous one-shot dispatcher persisted consumption as an issue comment. A GitHub Actions rerun reused the original `pull_request: opened` event and the original unconsumed request snapshot, then dispatched a second child workflow after the grant was consumed.

```text
issue_comment_consumption_record != enforced_single_use
workflow_rerun != new_authority
deployment_succeeded != authority_valid
```

The replacement must make consumption atomic, durable, immutable, independently auditable, and effective before any job capable of requesting Azure OIDC starts.

## Implemented repository components

```text
infra/scripts/authority_claim.py
  -> strict immutable-request schema
  -> deterministic SHA-256 content digest
  -> UUIDv7 request identity
  -> exact authorization commit binding
  -> repository and caller-workflow binding
  -> expiry, status, source, target, and finite-authority validation
  -> normalized claim outputs and validation evidence

.github/workflows/durable-authorization-claim-v1.yml
  -> reusable workflow_call only
  -> exact caller commit checkout
  -> claim-authority job with contents: write and id-token: none
  -> atomic POST create refs/tags/authority-consumed/<request_id>
  -> replay or duplicate failure before any downstream job
  -> durable-ref verification and sanitized evidence artifact

infra/tests/test_durable_authorization_claim.py
  -> deterministic positive and negative validation
  -> workflow permission and mutation contract tests
  -> static replay and activation-boundary tests
```

The verifier performs no GitHub mutation. The workflow performs only first-writer-wins reference creation and read-back verification. It contains no Azure command and cannot be invoked manually because it exposes only `workflow_call`.

## Intended architecture

```text
human authority
  -> immutable request record committed to main
  -> caller workflow at the exact authorization commit
  -> reusable claim-authority workflow (contents: write, id-token: none)
  -> atomic create refs/tags/authority-consumed/<request_id>
  -> downstream cloud job admitted only when the claim job succeeds
  -> downstream cloud job uses only immutable claim outputs
  -> terminal evidence and reconciliation
```

### 1. Immutable request record

Each request is a committed JSON object containing:

- globally unique immutable UUIDv7 `request_id`;
- exact authorization commit SHA;
- exact reviewed implementation SHA;
- repository, caller workflow path, operation, and environment;
- subscription or governed alias, tenant or governed alias, resource group, region, and resource-scope hash;
- authorized identity and capability path;
- issue time and expiry;
- attempt limit fixed at one;
- explicit non-renewing retry, rollback, cleanup, and RBAC flags;
- canonical human instruction and interpretation;
- schema version and deterministic content digest.

The workflow reads the request from the exact caller commit. It does not trust a mutable branch copy, issue comment, pull-request body, event payload snapshot, or target parameters supplied separately by a caller.

### 2. Separate claim job with no OIDC permission

The `claim-authority` job receives `contents: write` and explicitly receives `id-token: none`. It validates:

- exact schema with unknown fields rejected;
- canonical content digest;
- active, unconsumed, and unexpired status;
- UUIDv7 request identity;
- exact caller commit;
- exact repository and caller workflow path;
- reviewed source exists as a commit and is an ancestor of the exact authorization commit;
- target values originate only from the immutable request and are emitted as claim outputs;
- attempt limit of one;
- no automatic retry, rollback, cleanup, RBAC, transfer, or renewal authority.

Only after deterministic validation does it attempt the atomic claim.

### 3. Atomic first-writer-wins ledger

The ledger key is:

```text
refs/tags/authority-consumed/<request_id>
```

The tag points to the exact authorization request commit. Creation uses GitHub's create-reference API.

Only one first creator can create a unique reference. An existing reference causes the workflow to fail closed as a replay or duplicate. The workflow contains no update, force-move, reuse, or deletion path.

A repository ruleset must still protect `refs/tags/authority-consumed/**` from update and deletion and must not grant GitHub Actions a bypass. Administrative emergency deletion remains outside the workflow and requires separately recorded human authority and reconciliation.

### 4. Future OIDC-capable Azure job

No Azure job is implemented or restored by this mechanism.

A future Azure job must be a distinct caller job with:

- `id-token: write`;
- `contents: read`;
- a hard dependency on the reusable claim job;
- admission only after the claim workflow succeeds;
- all source, operation, environment, and target values taken from immutable claim outputs;
- no path that can run on skipped, failed, expired, consumed, or mismatched claims.

The Azure job must re-read the protected consumption reference and verify that it points to the exact authorization commit before calling `azure/login`.

Consumption occurs when the reference is successfully created, regardless of whether a later cloud login or operation succeeds.

### 5. Evidence model

The claim workflow records:

- request ID and digest;
- authorization commit and reviewed source;
- caller repository and workflow;
- consumption reference;
- GitHub run ID and attempt number;
- target scope hash;
- claim timestamp;
- deterministic validation result;
- atomic creation result;
- durable-reference read-back result;
- explicit `azure_oidc_requested: false`;
- explicit `azure_action_performed: false`.

Terminal reconciliation must keep authority validity, claim outcome, cloud outcome, workflow conclusion, and service truth as separate fields.

## Required invariants

1. A request can be claimed at most once.
2. Claim creation is an atomic create, never an update.
3. The claim job cannot request Azure OIDC.
4. No cloud-capable job starts before successful claim creation.
5. Existing, expired, inactive, consumed, altered, authorization-commit-mismatched, repository-mismatched, or workflow-mismatched requests fail closed.
6. The reviewed source must exist and be an ancestor of the exact authorization commit.
7. Operation and target values are read only from the immutable request and emitted as outputs for future downstream use.
8. Unknown request fields fail closed.
9. Consumption records cannot be changed or deleted by the workflow.
10. A failed cloud operation does not renew the request.
11. Retry, rollback, cleanup, RBAC mutation, or materially changed scope requires a new request ID and fresh authority.
12. The verifier is deterministic and narrower than the workflow it gates.
13. Missing evidence remains `not_observed`, not false.

## Validation state

Automated local and exact-head PR CI tests cover:

- valid deterministic request validation;
- tampered digest rejection;
- expired, inactive, and consumed request rejection;
- authorization commit, repository, and caller-workflow boundary rejection;
- reviewed-source existence and ancestor checks in the workflow contract;
- immutable-request operation and target outputs for future downstream use;
- finite non-renewing authority flags;
- UUIDv7 enforcement;
- unknown-field rejection;
- workflow `contents: write` and `id-token: none`;
- no manual dispatch trigger;
- no Azure login, Azure CLI operation, workflow dispatch, rerun, ref update, ref deletion, or forced move;
- replay failure before evidence completion or any future downstream cloud path;
- activation state remains false.

The following require separately authorized live repository testing and remain unverified:

- first live claim creates the expected tag;
- a workflow rerun fails before any OIDC-capable job;
- a duplicate caller run fails before any OIDC-capable job;
- two concurrent valid runs produce exactly one successful claimant;
- the protected tag ruleset prevents update and deletion without workflow bypass.

## Failure and rollback behaviour

- Claim validation failure: stop with no GitHub mutation, OIDC token, or Azure action.
- Claim race loss or existing reference: classify as replay or duplicate and stop.
- Evidence upload failure after claim: the grant remains consumed; reconstruct from the durable tag and run logs.
- Future Azure login or deployment failure after claim: preserve evidence and stop; the grant remains consumed.
- Verification failure: preserve deployed reality and evidence; do not infer rollback authority.
- Ledger or ruleset failure: keep the collector workflow quarantined.
- No automatic retry or rollback is permitted.

## Cost and quota implications

The ledger uses GitHub repository references and has no expected Azure recurring-cost delta. This repository-only implementation has an expected Azure recurring-cost delta of CAD $0. Actual Azure cost, available credit, regional quota, and lock state remain live evidence to observe before any future cloud operation.

## Activation and restoration gates

1. Review the merged implementation and its exact-head CI evidence.
2. Reconcile the merge into canonical `.project/` state.
3. Configure and independently inspect the protected tag ruleset under separate repository-settings authority.
4. Obtain fresh explicit authority for a bounded non-production live first-claim and replay test.
5. Obtain fresh explicit authority for a concurrent duplicate-claim test.
6. Reconcile observed test results into canonical `.project/` state.
7. Obtain separate fresh non-renewing authority before modifying or restoring any Azure-capable workflow.
8. Keep a rapid quarantine path that removes OIDC and Azure commands if an invariant fails.

Merge authority used for PR #186 does not transfer to any later gate.

## Cleanup and decommissioning

Consumption references are durable audit records and are not routine cleanup targets. Decommissioning the mechanism requires:

- disabling all workflows that consume it;
- preserving an export of request and consumption records;
- documenting retention and audit requirements;
- separately authorizing any ruleset or reference removal;
- verifying no Azure workflow still depends on the ledger.

## Evidence to capture

- exact request JSON and digest;
- authorization commit;
- exact-head CI;
- merge commit and canonical reconciliation;
- ruleset configuration with sensitive values redacted;
- first-claim, replay, and concurrent-claim results;
- expiry, authorization-commit, repository, and workflow rejection results;
- reviewed-source ancestry and immutable target-output evidence;
- job-level permission inspection;
- proof that failed claims never start an OIDC-capable job;
- terminal reconciliation;
- future Azure What-If and runtime evidence only after fresh authority.
