# Frontend Azure provenance monitor

## Purpose

Show a live, bounded proof chain between the published ServiceTracer frontend and the collector-hosted API without representing the Azure resource group as a network endpoint.

```text
GitHub Pages browser
  -> HTTPS API request
  -> dedicated public load balancer
  -> nginx and ServiceTracer API process
  -> collector VM
  ∈ governed resource group
```

The resource group is the governance and lifecycle boundary. The collector API process is the traffic endpoint.

## Intended architecture

The frontend renders a provenance monitor above the incident topology. It polls the existing `/api/health` endpoint every 15 seconds and shows:

- the browser host;
- the configured API hostname;
- accepted health-contract state and observed latency;
- Azure resource group, VM name, and region returned from Azure Instance Metadata Service;
- the exact deployed source commit supplied by the installer;
- a frontend-generated request ID echoed by the collector API for an incident-analysis request.

The monitor installs a bounded wrapper around `window.fetch` before `app.js` loads. Only `POST` requests whose path ends in `/api/demo/run` receive the `X-ServiceTracer-Request-ID` header. The response is cloned for monitor inspection so the existing application remains the authoritative response consumer.

## Region and resource scope

Current promoted deployment evidence identifies:

- subscription role: Azure for Students;
- region: `westus2`;
- governed resource group: `rg-servicetracer-dev-westus2`;
- collector VM: `vm-stcollector-mst-dev`;
- public API endpoint: `st-demo-api-vm-aeg30000.westus2.cloudapp.azure.com`.

These values are historical promoted evidence until a new exact-source deployment and post-deployment observation are completed. The API does not hard-code them. It retrieves resource group, VM name, and region from Azure Instance Metadata Service on the running VM.

## Dependencies

- existing GitHub Pages frontend;
- existing collector-hosted ServiceTracer API;
- Azure Instance Metadata Service at `169.254.169.254`;
- existing dedicated Standard public load balancer and nginx TLS termination;
- browser CORS access from `https://anthonyedgar30000.github.io`;
- exact 40-character deployment source passed to `install_collector_demo_api.sh`.

## Identity and permissions

Azure Instance Metadata Service is queried locally from the VM with `Metadata: true`. No Azure credential, managed-identity token, subscription ID, tenant ID, or Azure Resource Manager permission is required or returned to the browser.

The public identity payload is deliberately limited to:

- resource group name;
- VM name;
- Azure region;
- exact deployed Git commit;
- verification source.

## Network paths

1. Browser fetches GitHub Pages assets.
2. Frontend performs a simple HTTPS `GET /api/health` through the dedicated public load balancer.
3. Frontend performs a CORS-preflighted `POST /api/demo/run` with `Content-Type` and `X-ServiceTracer-Request-ID`.
4. Nginx proxies the request to the loopback-only Python API on `127.0.0.1:8090`.
5. The API performs the already-bounded downstream transaction sampling.

No new Azure ingress rule, public IP, load balancer, DNS record, or service port is introduced by this increment.

## Security controls

- API remains loopback-only behind nginx.
- Existing origin allow-list remains enforced.
- Request IDs must be canonical UUIDs or are replaced server-side.
- Health and transaction responses remain `Cache-Control: no-store`.
- Tenant and subscription identifiers are never returned.
- IMDS failure remains visible as `verified: false`; it is not converted into a guessed resource identity.
- Source identity is accepted only as one lowercase 40-character Git SHA.
- Browser correlation is accepted only when the echoed response request ID exactly matches the frontend-generated value.

## Cost implications

Repository and GitHub Pages changes have no Azure resource cost. A later deployment updates the existing VM extension and service files only. No resource creation is intended. Incremental Azure cost should be negligible, but actual cost remains an observed billing fact rather than a code-derived guarantee.

## Deployment method

Repository phase:

1. Review the exact pull-request diff.
2. Require exact-head CI success.
3. Merge only with separate authority.

Azure phase, separately authorized:

1. Bind the collector deployment workflow to the exact reviewed merge commit.
2. Capture fresh preflight and FullResourcePayloads What-If evidence.
3. Require the plan to contain only the previously governed collector API convergence targets.
4. Execute one non-renewing deployment attempt.
5. The installer writes `SERVICETRACER_DEPLOYED_SOURCE_REF` and refuses success unless `/api/health` returns verified IMDS identity matching that source.

## Validation commands

Repository validation:

```bash
python -m unittest discover -s infra/tests -p 'test_*.py'
python -m py_compile demo_api/standalone_server.py
```

Post-deployment API validation:

```bash
curl --fail --silent --show-error \
  https://st-demo-api-vm-aeg30000.westus2.cloudapp.azure.com/api/health \
  | python -m json.tool
```

Expected identity fragment:

```json
{
  "azure_host": {
    "verified": true,
    "verification_source": "azure_instance_metadata_service",
    "resource_group": "rg-servicetracer-dev-westus2",
    "vm_name": "vm-stcollector-mst-dev",
    "location": "westus2",
    "source_ref": "<exact deployed 40-character commit>"
  }
}
```

Browser validation:

1. Open the published GitHub Pages root without an `?api=` override.
2. Confirm the monitor resolves the expected endpoint and shows verified resource-group and VM identity.
3. Confirm the health timestamp and latency refresh.
4. Click **Run incident analysis** once.
5. Confirm one request ID appears and the response reports the same ID with exactly 20 transactions.
6. Capture the rendered monitor and browser network entry as evidence.

## Expected outputs

A successful live monitor proves:

```text
frontend_configured_to_endpoint
+ endpoint_health_contract_accepted
+ API_process_reports_IMDS_host_identity
+ exact_source_ref_matches_deployment
+ browser_request_id_echoed_by_API
```

It does not by itself prove downstream transaction success, effective least privilege, alert delivery, backup, recovery, or complete service validation.

## Failure and rollback behavior

- IMDS unavailable or incomplete: API health may remain functionally healthy, but the monitor shows Azure host identity as unverified.
- Source ref missing or malformed: installer post-deployment verification fails.
- Request ID mismatch: monitor rejects correlation proof and the existing application still processes its own response.
- Health endpoint unavailable: monitor warns while the existing controlled fixture behavior remains unchanged.
- Deployment failure: the one-shot grant is consumed; no automatic retry.

Rollback is source-bound:

1. select the last independently verified collector API commit;
2. obtain a fresh What-If and explicit rollback authority;
3. redeploy that exact source through the existing collector workflow;
4. repeat installer, health, CORS, browser, and transaction validation.

## Cleanup and decommissioning

Repository-only rollback removes:

- `docs/live-monitor.js`;
- `docs/live-monitor.css`;
- the monitor markup and script references in `docs/index.html`;
- the added request-ID and IMDS identity fields from the API and installer.

No Azure resource deletion is required. Removing or deleting the collector resource group remains a separate governed cleanup operation.

## Evidence to capture

- exact PR head and CI run;
- reviewed merge commit;
- fresh ARM What-If artifact;
- deployment workflow run, job, artifact, and manifest digest;
- post-deployment `/api/health` payload with identifiers limited to the public identity contract;
- browser screenshot of the live monitor;
- browser network evidence showing `X-ServiceTracer-Request-ID` and the matching response payload;
- failure or rollback evidence if any gate does not pass.
