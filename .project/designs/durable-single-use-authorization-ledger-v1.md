# Durable single-use deployment authorization ledger v1

## Status

**Proposed, not implemented.** The collector Azure workflow remains quarantined. This document creates no deployment, verification, rollback, cleanup, RBAC, or cloud-authentication authority.

## Problem statement

The previous one-shot dispatcher persisted consumption as an issue comment. A GitHub Actions rerun reused the original `pull_request: opened` event and the original unconsumed request snapshot, then dispatched a second child workflow after the grant was consumed.

```text
issue_comment_consumption_record != enforced_single_use
workflow_rerun != new_authority
deployment_succeeded != authority_valid
```

The replacement must make consumption atomic, durable, immutable, independently auditable, and effective before any job capable of requesting Azure OIDC starts.

## Intended architecture

```text
human authority
  -> immutable request record committed to main
  -> claim-authority job (contents: write, id-token: none)
  -> atomic create refs/tags/authority-consumed/<request_id>
  -> Azure job admitted only when claim job succeeds
  -> Azure job (id-token: write, contents: read)
  -> terminal evidence and reconciliation
```

### 1. Immutable request record

Each request is a committed JSON object containing:

- globally unique immutable `request_id` using UUIDv7 or an equivalent collision-resistant identifier;
- exact authorization commit SHA;
- exact reviewed implementation SHA;
- workflow path and operation;
- subscription, tenant, resource group, region, environment, and resource-scope hash;
- authorized identity and capability;
- issue time and expiry;
- attempt limit, fixed at one for this design;
- retry, rollback, cleanup, and RBAC flags;
- canonical human instruction and interpretation;
- schema version and deterministic content digest.

A workflow must read the request from the exact authorization commit. It must not trust a mutable branch copy, issue comment, pull-request body, event payload snapshot, or workflow input as the authority source.

### 2. Separate claim job with no OIDC permission

The `claim-authority` job receives `contents: write` and explicitly receives no `id-token` permission. It validates:

- request schema and digest;
- request is active and unexpired;
- exact workflow, source, operation, target, scope hash, and environment match;
- request grants the current repository and actor path;
- no retry, rollback, cleanup, or adjacent mutation is inferred;
- the consumption reference does not already exist.

Only after validation does it attempt the atomic claim.

### 3. Atomic first-writer-wins ledger

The ledger key is:

```text
refs/tags/authority-consumed/<request_id>
```

The tag points to the exact authorization request commit. Creation uses GitHub's create-reference API.

GitHub returns success to exactly one first creator. An existing reference causes the claim to fail closed. The workflow must never update, force-move, reuse, or delete an existing consumption reference.

A repository ruleset must protect `refs/tags/authority-consumed/**` from update and deletion and must not grant GitHub Actions a bypass. Administrative emergency deletion is outside the workflow and requires separately recorded human authority and reconciliation.

### 4. OIDC-capable Azure job

The Azure job is a distinct job with:

- `id-token: write`;
- `contents: read`;
- a hard `needs: claim-authority`;
- an admission condition requiring the claim job's success and exact request digest;
- no path that can run on skipped, failed, expired, consumed, or mismatched claims.

The Azure job re-reads the protected consumption reference and verifies that it points to the exact authorization commit before calling `azure/login`.

Consumption occurs when the reference is successfully created, regardless of whether Azure login or deployment later succeeds.

### 5. Evidence model

The claim job records:

- request ID and request digest;
- authorization commit and reviewed source;
- consumption reference;
- GitHub run ID and attempt number;
- target scope hash;
- claim timestamp;
- validation result.

The Azure job records control-plane, What-If, deployment, runtime, cost, quota, lock, and terminal evidence without exposing secrets. Terminal reconciliation keeps authority validity, deployment outcome, workflow conclusion, and service truth as separate fields.

## Required invariants

1. A request can be claimed at most once.
2. Claim creation is atomic under concurrent dispatch.
3. The claim job cannot request Azure OIDC.
4. No OIDC-capable job starts before successful claim creation.
5. Existing, expired, inactive, altered, source-mismatched, target-mismatched, or scope-mismatched requests fail closed.
6. Consumption records cannot be changed or deleted by the workflow.
7. A failed Azure operation does not renew the request.
8. Retry, rollback, cleanup, or materially changed scope requires a new request ID and fresh authority.
9. The verifier is deterministic and narrower than the workflow it gates.
10. Missing evidence remains `not_observed`, not false.

## Validation matrix

The implementation is not eligible for restoration review until automated tests prove:

- first valid claim succeeds;
- workflow rerun fails before the OIDC-capable job;
- duplicate manual dispatch fails before the OIDC-capable job;
- two concurrent valid dispatches produce exactly one successful claimant;
- expired request fails;
- inactive request fails;
- altered request digest fails;
- reviewed-source mismatch fails;
- workflow-path mismatch fails;
- target and scope-hash mismatch fail;
- pre-existing consumption reference fails;
- claim job permissions contain no `id-token: write`;
- Azure job has no execution path when claim fails;
- Azure failure leaves the request consumed;
- rollback and retry remain unauthorized unless separately granted.

## Failure and rollback behaviour

- Claim validation failure: stop with no OIDC token and no Azure action.
- Claim race loss: classify as replay or duplicate and stop.
- Azure login or deployment failure after claim: preserve evidence and stop; the grant remains consumed.
- Verification failure: preserve deployed reality and evidence; do not infer rollback authority.
- Ledger or ruleset failure: keep the collector workflow quarantined.
- No automatic retry or rollback is permitted by this design.

## Cost and quota implications

The ledger itself uses GitHub repository references and has no expected Azure recurring-cost delta. Implementation testing must not authenticate to Azure unless separately authorized. Actual Azure cost, available credit, regional quota, and lock state remain live evidence to observe before any future cloud operation.

## Deployment and restoration method

1. Implement the claim verifier and workflow split on a review branch.
2. Add deterministic unit and workflow-contract tests.
3. Configure and independently inspect the tag ruleset.
4. Run exact-head CI with no Azure authentication.
5. Review the complete diff and evidence.
6. Obtain fresh explicit authority for a bounded non-production claim test.
7. Obtain separate fresh authority before restoring any Azure operation.
8. Keep a rapid quarantine path that removes OIDC and Azure commands if an invariant fails.

## Cleanup and decommissioning

Consumption references are durable audit records and are not routine cleanup targets. Decommissioning the mechanism requires:

- disabling all workflows that consume it;
- preserving an export of request and consumption records;
- documenting retention and legal/audit requirements;
- separately authorizing any ruleset or reference removal;
- verifying no Azure workflow still depends on the ledger.

## Evidence to capture

- exact request JSON and digest;
- authorization commit;
- exact-head CI;
- ruleset configuration with secrets redacted;
- concurrent-claim test result;
- replay, expiry, source, target, and scope rejection results;
- job-level permission inspection;
- proof that failed claims never start the OIDC-capable job;
- terminal reconciliation;
- future Azure What-If and runtime evidence only after fresh authority.
