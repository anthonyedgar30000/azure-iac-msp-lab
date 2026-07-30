# ServiceTracer demo API planning run 1 terminal handoff

## Terminal status

```text
attempt: servicetracer-demo-api-plan-run1
human authorization comment: 5126316629
workflow: .github/workflows/servicetracer-demo-api-subproject-plan.yml
workflow run: 30513630134 / attempt 1
job: 90778676285
head: main / 09fe72e3a82ea6ae56e1e85fd9745c9940ed6c12
artifact: 8748027710
artifact digest: sha256:a3bb46d90bdff6329bcfe15f5b00b1f144b68b009724f9e912ca890ced9384d9
conclusion: failure
failure stage: validate_main_bound_dual_subscription_read_only_authority
failure class: confirmation_input_mismatch
authority consumed: true
rerun authorized: false
```

The direct workflow dispatch was accepted, which consumed the one-shot authority. The job then failed before Azure login because the supplied confirmation did not exactly match:

```text
PLAN-DEMO-API-SUBPROJECT:dev:st-demo-api-vm-aeg30000
```

The actual supplied value is not persisted.

```text
workflow dispatch accepted != authority validation passed
authority consumed != Azure login started
confirmation mismatch != Azure preflight failure
```

## Execution boundary

```text
repository tests started: false
Azure login started: false
dependency subscription query started: false
target subscription query started: false
provider/policy/quota/SKU/inventory queried: false
ARM validation performed: false
ARM What-If performed: false
Azure mutation performed: false
deployment started: false
rollback or cleanup performed: false
```

The protected artifact contains only `artifact-manifest.sha256`, with zero manifest entries. It contains no planning summary and no Azure evidence.

Promoted terminal evidence:

```text
.project/evidence/servicetracer-demo-api-plan-run1-terminal-summary.json
SHA-256: 3c79f43342356bd448531ba35501d9ab0591f1eee8d2bba1f0437d44c88a71da
```

## Cost and next gate

```text
Azure resource cost delta established by this run: CAD $0
actual Azure cost freshly observed: false
Azure quota freshly observed: false
planning ceiling: CAD $25.00
planning ceiling is spend authority: false
deployment authorized: false
```

Do not use GitHub Re-run. Another planning attempt requires a corrected exact confirmation value and fresh explicit one-attempt authority. No Azure rollback or cleanup applies.
