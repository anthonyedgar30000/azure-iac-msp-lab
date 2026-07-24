# Frontend, demo API, and synthetic lab integration

## Purpose

Exercise the complete presentation path without treating a reachable API as proof that every backend dependency or operational control is healthy.

```text
GitHub Pages or local docs server
→ GET /api/health
→ POST /api/demo/run with 20 attempts
→ independent API VM
→ existing Standard Load Balancer /transaction endpoint
→ VPN-01 and VPN-02 synthetic backends
→ bounded report rendering
```

## Current candidate endpoint

```text
https://st-demo-api-vm-aeg30000.westus2.cloudapp.azure.com/api/demo/run
```

The committed frontend configuration treats this as a candidate integration source. The browser must pass the API health contract before the **Run incident analysis** button can execute live transactions. The controlled fixture remains available when health or the POST request fails.

## Local validation

From the repository root:

```bash
python3 -m http.server 8000 --directory docs
```

Open:

```text
http://localhost:8000
```

Expected initial behavior:

1. `report-source.json` loads.
2. The controlled fixture loads as the fallback.
3. The browser requests `/api/health` from the configured Azure API.
4. A valid health response changes the source label to `Azure demo API — ready`.
5. No lab transactions run until the operator clicks **Run incident analysis**.

## Transaction and rendering validation

After clicking **Run incident analysis**, capture:

- the CORS preflight and POST request;
- the HTTP status and response schema;
- the generated timestamp and API source ID;
- the count of correlated transactions;
- the observed backend attempt counts and failure rates;
- the rendered topology and finding;
- whether the result is stable localization or explicitly inconclusive.

A sample is stable only when both VPN-01 and VPN-02 are observed and one has a higher failure rate than the other. A one-backend or tied sample must not render VPN-02 as a proven suspect, must label the boundary as not established, and must not expose the backend-specific technician workflow.

## Failure behavior

If the health check or POST fails, the frontend:

- does not claim live evidence was captured;
- uses the controlled fixture;
- labels the API unavailable;
- performs no Azure mutation or automatic retry loop.

## Rollback

Clear `live_demo_api_url` in `docs/report-source.json` and revert the frontend integration commit. No Azure resource rollback is required.

## Deferred issues

This integration does not resolve effective RBAC, least privilege, backup, recovery testing, actual cost, diagnostic settings, alert configuration, or alert delivery. Those remain explicitly deferred and evidence-bounded.
