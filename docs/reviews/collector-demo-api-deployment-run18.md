# Collector-hosted demo API deployment run 18

Exact source `98b092201053fd3592be157a24de6e623e6b74a6` was deployed by workflow run `30196388398`.

## Deployment result

- ARM validation and bounded FullResourcePayloads What-If passed.
- Parent and nested deployments reached `Succeeded`.
- `lb-st-demo-api-mst-dev` is Standard/Regional and contains backend `collector / 10.20.40.10`.
- VM extension `servicetracer-demo-api` reached `Succeeded` with `forceUpdateTag` bound to the exact source commit.
- Public HTTPS health returned `healthy`, `backend_target_configured=true`, and `hosting_model=collector_vm_systemd`.
- The bounded API request returned exactly 20 transactions without claiming an exact root cause.
- CORS OPTIONS returned HTTP 204 with the exact allowed origin and `POST, OPTIONS`.

## Why the workflow was red

The final CORS assertion used:

```text
grep -Eiq "...\r?$"
```

against a real HTTP header file ending in CRLF. GNU grep ERE does not treat `\r` as a carriage-return token, so the correct header was rejected. The workflow never wrote `verification.json`, even though the raw artifact proves the required health, API, and CORS evidence.

The repair normalizes CR bytes before an exact fixed-string match. No Azure retry or mutation is part of this repository increment.

## Boundaries

```text
workflow_failed != deployment_failed
verifier_false_negative != service_failure
service_restored != downstream_VPN_backend_repaired
```
