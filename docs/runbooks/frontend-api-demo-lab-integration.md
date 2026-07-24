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

The committed frontend configuration stores this only as a candidate source. The default frontend remains on the controlled fixture. Pass the candidate endpoint through the existing `?api=` query parameter for an explicit browser validation. The browser must pass the API health contract before the **Run incident analysis** button can execute live transactions.

## Timeout-budget correction

The failed one-shot browser gate exposed a repository timeout mismatch:

```text
20 sequential attempts × 10 seconds = 200 seconds
50 maximum attempts × 10 seconds = 500 seconds
Nginx proxy read timeout = 45 seconds
```

The bounded repository correction is:

```text
backend timeout = 10 seconds
maximum parallel transactions = 10
maximum attempts = 50
maximum worker waves = 5
estimated maximum application execution = 50 seconds
Nginx proxy read timeout = 75 seconds
proxy safety margin = 25 seconds
```

The API now runs independent backend transactions through a capped thread pool. The health response also reports:

- `backend_timeout_seconds`;
- `max_parallel_transactions`;
- `max_attempts`;
- `estimated_max_execution_seconds`.

This correction exists in PR code only.

```text
repository_timeout_budget_fixed != deployed_runtime_fixed
```

## Repository validation

From the repository root:

```bash
python3 -m unittest discover -s workloads/servicetracer-demo-api/tests -v
python3 -m unittest discover -s infra/tests -v
python3 .project/validate.py
bash -n workloads/servicetracer-demo-api/scripts/install.sh
bash -n infra/scripts/install_collector_demo_api.sh
```

The timeout regression tests verify:

1. both installers declare the same 10-second backend timeout;
2. both installers declare 10 maximum parallel transactions;
3. both installers declare a 75-second proxy read timeout;
4. the 50-attempt theoretical application budget is 50 seconds;
5. the proxy margin is at least 15 seconds;
6. a 20-attempt test uses bounded parallel execution and preserves 20 unique correlations.

## Local frontend validation

From the repository root:

```bash
python3 -m http.server 8000 --directory docs
```

Open:

```text
http://localhost:8000/?api=https%3A%2F%2Fst-demo-api-vm-aeg30000.westus2.cloudapp.azure.com%2Fapi%2Fdemo%2Frun
```

Expected initial behaviour:

1. `report-source.json` loads.
2. The default URL remains fixture-only because `live_demo_api_url` is blank.
3. The explicit `?api=` URL loads the controlled fixture as the fallback and derives `/api/health` from the candidate run URL.
4. A valid health response changes the source label to `Azure demo API — ready`.
5. No lab transactions run until the operator clicks **Run incident analysis**.

## Deployment boundary

Applying the fix to the running workload requires a separately authorized deployment using an exact reviewed commit. The deployment must reinstall the independent API workload from that pinned source and capture:

- reviewed commit SHA;
- deployment or extension correlation ID;
- resulting service environment values;
- Nginx syntax validation;
- service restart status;
- `/api/health` output showing the corrected execution budget.

Repository completion does not authorize Azure authentication, an extension update, a guest command, or any other live mutation.

## Post-deployment validation boundary

After deployment, a separate bounded replay authorization is required before sending another 20-attempt transaction request. Capture:

- the CORS preflight and POST request;
- the HTTP status and response schema;
- request duration;
- the generated timestamp and API source ID;
- the count of correlated transactions;
- the observed backend attempt counts and failure rates;
- the rendered topology and finding;
- whether the result is stable localization or explicitly inconclusive.

A sample is stable only when both VPN-01 and VPN-02 are observed and one has a higher failure rate than the other. A one-backend or tied sample must not render VPN-02 as a proven suspect, must label the boundary as not established, and must not expose the backend-specific technician workflow.

## Failure behaviour

If the health check or POST fails, the frontend:

- does not claim live evidence was captured;
- uses the controlled fixture;
- labels the API unavailable;
- performs no Azure mutation or automatic retry loop.

If the corrected deployment fails, restore the previously trusted pinned source ref and verify service and Nginx health before considering another replay.

## Rollback

For repository-only rollback, revert the timeout-budget commits. No Azure rollback is required until the fix is deployed.

For a future deployed rollback, reinstall the previously trusted exact commit, restart the service, validate Nginx, and verify `/api/health`. Do not replay transactions unless separately authorized.

## Deferred issues

This integration does not resolve effective RBAC, least privilege, backup, recovery testing, actual cost, diagnostic settings, alert configuration, or alert delivery. Those remain explicitly deferred and evidence-bounded.
