# Governed Persistence Loop

## Purpose

The **Governed Persistence Loop — Bounded AI Recovery and Completion Protocol** gives ServiceTracer a deterministic control plane for continuing toward an explicit objective without granting unlimited autonomy.

The first implementation is intentionally advisory and fail-closed. It converts project state and workflow evidence into one typed control message. It does not dispatch GitHub Actions, authenticate to Azure, mutate Azure, expand scope, change the objective, or satisfy a human authorization gate.

```text
continued_reasoning != unlimited_execution
failure_detected != permission_to_mutate
recommended_next_message != workflow_dispatch_authorized
accepted_What-If != deployment_authorized
service_plausible != service_verified
```

## Typed control messages

| Message | Bounded interpretation |
| --- | --- |
| `proceed` | Execute the already-authorized next step without expanding objective, scope, or authority. |
| `fix` | Correct a classified recoverable failure inside the existing scope, then verify. |
| `sync_with_reality` | Refresh evidence and watermarks. This message does not authorize target mutation. |
| `restrategize` | Replace the plan while preserving the objective, scope, and authority boundary. |
| `verify` | Test the declared success criteria against current evidence. |
| `rollback` | Execute only an already-authorized rollback and then verify the result. |
| `escalate` | Stop bounded autonomous progress and request human judgment. |
| `complete` | Close only after every required success criterion is evidenced as verified. |

## State contract

A persistence state records:

- objective and success criteria;
- authorized scope and current strategy;
- attempt number and retry budget;
- observed result and failure class;
- evidence references and reality watermark;
- verified-success state and the next typed control message;
- immutable authority defaults that remain false unless another explicit governance mechanism grants them.

The controller rejects a transition that changes the objective, alters the authorized scope, grants itself new authority, completes without verified success, fixes an unclassified failure, rolls back without authorization, or continues after a terminal state.

## Collector-hosted demo API evaluator

`infra/scripts/governed_persistence.py` includes a bounded evaluator for the current Azure lifecycle:

```text
readiness evidence
  -> scoped ARM validation and What-If
  -> explicit human deploy gate
  -> deployment evidence
  -> explicit verification dispatch when required
  -> TLS, health, transaction, and CORS verification
  -> complete or escalate
```

Examples:

```bash
python infra/scripts/governed_persistence.py new-state \
  --objective 'Deploy and verify the bounded collector-hosted demo API' \
  --success-criterion 'Public TLS validates' \
  --success-criterion 'API health is verified' \
  --success-criterion 'Twenty correlated transactions are verified' \
  --success-criterion 'CORS is restricted to the approved origin' \
  --authorized-scope 'rg-servicetracer-dev-westus2' \
  --authorized-scope 'collector demo API resources declared by infra/collector-demo-api.bicep' \
  --retry-budget 2 \
  --strategy 'Use the isolated collector demo API Bicep root' \
  --output /tmp/persistence-state.json

python infra/scripts/governed_persistence.py evaluate-collector-demo-api \
  --operation what-if \
  --workflow-conclusion success \
  --attempt-number 1 \
  --retry-budget 2 \
  --artifact-dir collector-demo-api-evidence \
  --output collector-demo-api-evidence/persistence-transition.json
```

An accepted What-If produces `proceed` with `recommended_next_operation=deploy`, but the output also requires `explicit_deploy_authorization` and keeps both workflow-dispatch and Azure-mutation authority false.

## Initial classification policy

- verified TLS, health, twenty-transaction, CORS, and service evidence -> `complete`;
- accepted isolated What-If -> `proceed` to a separate human deploy gate;
- deployment evidence without service verification -> `verify` through a separate dispatch;
- missing, stale, conflicting, or incomplete Azure readiness evidence -> `sync_with_reality`;
- insufficient public-IP quota -> `restrategize`;
- read-only lock or unproven authority/scope -> `escalate`;
- classified post-readiness execution failure with retry budget remaining -> `fix`;
- exhausted retry budget, cancellation, timeout, or unclassified failure -> `escalate`.

## Availability boundary

After this controller is merged, ServiceTracer has a tested Phase 2/3 capability: typed state transitions plus deterministic next-message recommendations from collector-demo workflow evidence.

It is not yet a self-dispatching retry engine. Automatic workflow continuation requires a later bounded orchestration increment with explicit dispatch grants, durable cross-run state, idempotency keys, concurrency protection, artifact retrieval, retry timing, and a human gate before every authority increase.
