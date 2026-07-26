# Frontend Azure provenance monitor

## Purpose

Show a live, bounded proof chain between the published ServiceTracer frontend and the collector-hosted API without representing the Azure resource group as a network endpoint.

```text
GitHub Pages browser
  -> HTTPS collector endpoint
  -> dedicated public load balancer
  -> nginx and ServiceTracer API process
  -> vm-stcollector-mst-dev
  ∈ rg-servicetracer-dev-westus2
```

The resource group is the governance and lifecycle boundary. The API process on the collector VM is the traffic endpoint.

## Current promoted boundary

Canonical repository state after PR #126 binds the frontend to the collector endpoint deployed by workflow run `30196388398`:

```text
https://st-demo-api-aeg30000.westus2.cloudapp.azure.com/api/demo/run
```

Promoted deployment evidence identifies:

- resource group: `rg-servicetracer-dev-westus2`;
- collector VM: `vm-stcollector-mst-dev`;
- region: `westus2`;
- deployment source: `98b092201053fd3592be157a24de6e623e6b74a6`;
- collector endpoint health and CORS: previously verified and time-bounded;
- browser completion: not yet verified.

The independent `st-demo-api-vm-aeg30000` endpoint remains historical supporting evidence and is not permitted to satisfy the collector golden-path monitor.

## Intended architecture

The frontend renders a provenance monitor above the incident topology. It polls `/api/health` every 15 seconds and shows:

- the browser host;
- the configured collector API hostname;
- accepted health-contract state and latency;
- Azure resource group, VM name, and region returned from Azure Instance Metadata Service;
- the exact deployed source commit supplied by the installer;
- a frontend-generated request UUID echoed by the collector API.

The monitor installs a bounded wrapper around `window.fetch` before `app.js` loads. Only `POST` requests ending in `/api/demo/run` receive `X-ServiceTracer-Request-ID`. The response is cloned for monitor inspection, so the existing application remains the authoritative response consumer.

## Exact provenance gate

The monitor becomes healthy only when all conditions hold:

```text
health schema accepted
+ backend target configured
+ hosting model == collector_vm_systemd
+ IMDS identity verified
+ resource group == rg-servicetracer-dev-westus2
+ VM == vm-stcollector-mst-dev
+ region == westus2
+ source ref is a lowercase 40-character Git SHA
```

A transaction correlation is accepted only when the same API response also returns the exact browser-generated request UUID and the same governed Azure host identity.

## Dependencies

- existing GitHub Pages frontend;
- existing collector-hosted ServiceTracer API;
- Azure Instance Metadata Service at `169.254.169.254`;
- existing dedicated Standard public load balancer and nginx TLS termination;
- browser CORS access from `https://anthonyedgar30000.github.io`;
- exact 40-character deployment source passed to `install_collector_demo_api.sh`.

## Identity and permissions

Azure Instance Metadata Service is queried locally from the VM with `Metadata: true`. No Azure credential, managed-identity token, subscription ID, tenant ID, or Azure Resource Manager permission is requested or returned to the browser.

The public identity payload is limited to:

- resource group name;
- VM name;
- Azure region;
- exact deployed Git commit;
- verification source.

## Network paths

1. Browser loads GitHub Pages assets.
2. Frontend performs HTTPS `GET /api/health` through the existing collector load balancer.
3. Frontend performs a CORS-preflighted `POST /api/demo/run` with `Content-Type` and `X-ServiceTracer-Request-ID`.
4. Nginx proxies the request to the loopback-only Python API on `127.0.0.1:8090`.
5. The API performs the existing bounded downstream transaction sample.

No new Azure ingress rule, public IP, load balancer, DNS record, resource group, or service port is introduced.

## Security controls

- API remains loopback-only behind nginx.
- Existing origin allow-list remains enforced.
- Request IDs must be canonical UUIDs or are replaced server-side.
- Health and transaction responses remain `Cache-Control: no-store`.
- Subscription and tenant identifiers are never returned.
- IMDS failure remains visible as `verified: false`; identity is never guessed.
- Source identity is accepted only as one lowercase 40-character Git SHA.
- The frontend fails closed on any resource-group, VM, region, hosting-model, source-ref, or request-ID mismatch.

## Cost implications

The repository and GitHub Pages changes create no Azure resources. A later deployment updates the existing collector VM extension and service files only. Intended incremental cost is negligible, but actual cost remains a billing observation rather than a code-derived guarantee.

## Deployment method

Repository phase:

1. Review the exact pull-request diff.
2. Require exact-head CI success.
3. Merge only with separate authority.

Azure phase, separately authorized:

1. Select the exact reviewed merge commit as deployment source.
2. Capture fresh subscription, resource, quota, and cost or credit evidence.
3. Run a FullResourcePayloads What-If against the existing collector API deployment.
4. Require the plan to remain within the governed collector VM extension and existing ingress contract.
5. Execute one non-renewing deployment attempt.
6. The installer writes `SERVICETRACER_DEPLOYED_SOURCE_REF` and refuses success unless `/api/health` returns verified IMDS identity matching that source.

## Validation commands

Repository validation:

```bash
python -m py_compile demo_api/standalone_server.py
python infra/tests/test_frontend_azure_provenance_monitor.py
python -m unittest discover -s infra/tests -p 'test_*.py'
python .project/validate.py
```

Post-deployment API validation:

```bash
curl --fail --silent --show-error \
  https://st-demo-api-aeg30000.westus2.cloudapp.azure.com/api/health \
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
2. Confirm the monitor shows the expected collector endpoint, resource group, VM, and region.
3. Confirm the health timestamp and latency refresh.
4. Click **Run incident analysis** once.
5. Confirm one request UUID appears and is echoed by the response with the expected transaction count.
6. Capture the rendered monitor and browser network entry as evidence.

## Failure and rollback behavior

- IMDS unavailable or incomplete: API may remain functionally healthy, but the monitor rejects Azure provenance.
- Expected and observed host identity differ: monitor remains warning and does not claim the golden path.
- Source ref missing or malformed: installer verification fails.
- Request UUID mismatch: monitor rejects correlation proof while the existing application still processes its own response.
- Health endpoint unavailable: monitor warns while the controlled fixture remains available.
- Deployment failure: the one-shot grant is consumed; no automatic retry.

Rollback is exact-source and separately authorized:

1. select the last independently verified collector API commit;
2. obtain a fresh What-If and explicit rollback authority;
3. redeploy that exact source through the existing collector workflow;
4. repeat installer, health, CORS, browser, and transaction validation.

## Cleanup and decommissioning

Repository rollback removes the monitor assets and markup plus the added API identity and request-correlation fields. No Azure resource deletion is required. Deleting the collector resource group remains a separate governed cleanup operation.

## Evidence to capture

- exact PR head and CI run;
- reviewed merge commit;
- fresh ARM What-If artifact;
- deployment workflow run, job, artifact, and manifest digest;
- post-deployment `/api/health` payload;
- browser screenshot of the live monitor;
- browser network evidence showing `X-ServiceTracer-Request-ID` and the matching response payload;
- failure or rollback evidence if any gate does not pass.

## Canonical distinctions

```text
resource_group_scope != traffic_endpoint
API_compatible != collector_golden_path
API_healthy != Azure_host_identity_verified
request_sent != response_correlation_verified
monitor_rendered != provenance_contract_deployed
repository_implemented != deployed_to_collector_VM
```
