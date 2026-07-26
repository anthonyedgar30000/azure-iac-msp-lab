# Frontend live-default activation

## Decision

Promote the deployed collector-hosted demo API from an explicit `?api=` candidate to the normal frontend source while preserving the controlled fixture as a fail-closed fallback.

```text
GitHub Pages
→ GET /api/health
→ POST /api/demo/run with 20 attempts
→ collector-hosted demo API
→ existing transaction endpoint
→ synthetic VPN backends
```

## Deployment evidence

- Exact source: `98b092201053fd3592be157a24de6e623e6b74a6`
- Deployment run: `30196388398`
- Artifact: `8630260279`
- Artifact SHA-256: `1f97be3c519d547871cc990e010013259dfd3c2e263f263653c2c4035340eb9e`
- Manifest: `48/48` payloads verified
- Parent and nested deployments: `Succeeded`
- VM extension: `Succeeded`
- Backend pool: one `collector` address at `10.20.40.10`
- Health: `healthy`, backend target configured
- CORS: exact GitHub Pages origin accepted
- Live request: 20 correlated transactions returned

The workflow concluded `failure` only because the shell verifier mishandled normal CRLF header endings after the successful requests. The evidence does not classify that as an Azure deployment or service failure.

## Frontend behaviour

`docs/report-source.json` now selects the live endpoint by default:

```text
https://st-demo-api-aeg30000.westus2.cloudapp.azure.com/api/demo/run
```

The frontend still validates health before enabling the operator action. Failed health, CORS, or transaction requests use the fixture and clearly label the fallback.

The repository validator does not permit an arbitrary live URL. It binds activation to the exact deployment source, workflow run, artifact digest, converged extension and backend pool, healthy API contract, exact CORS origin, consumed deployment authority, and absence of retry authority. Existing load-balancer classifier fixtures and their fail-closed tests remain unchanged.

## Remaining verification

The repository change must be merged and published by GitHub Pages. One bounded browser run will then verify the actual public site, its CORS preflight, one 20-attempt live request, and the rendered fail-closed localization.

```text
frontend_configured != GitHub_Pages_published
GitHub_Pages_published != browser_path_verified
API_connected != downstream_transaction_successful
inconclusive_sample != backend_failure_absent
```


## Collector binding reconciliation

The first activation revision accidentally used the independent VM API hostname even though its evidence anchor was collector deployment run `30196388398`. The current binding is corrected to the endpoint emitted by that deployment:

```text
https://st-demo-api-aeg30000.westus2.cloudapp.azure.com/api/demo/run
```

The independent endpoint remains historical supporting evidence. It is not the Lab v1 golden path and cannot satisfy the collector-hosted browser gate.

```text
independent_API_ready != collector_golden_path_verified
deployment_evidence_anchor != arbitrary_compatible_endpoint
```
