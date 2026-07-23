# Azure operations collector VM

## Purpose

The optional operations collector VM gives the implemented ServiceTracer collector a realistic Azure host without exposing it directly to the internet. It is intended to receive normalized operational evidence from VPN, Windows, SNMP, Azure, synthetic-check, and ticketing exporters inside the lab network.

The collector can also publish a deliberately narrow technician-handoff report to a separate Azure Storage endpoint. Raw evidence and the full engineering report remain on the private collector; only the allowlisted public envelope is uploaded.

## Implemented infrastructure

When `deployOperationsCollector` is enabled, Bicep creates:

- one Ubuntu 24.04 Linux VM in `snet-operations`;
- a static private address, `10.20.40.10` by default;
- no public IP address;
- a system-assigned managed identity;
- Trusted Launch, Secure Boot, and virtual TPM;
- managed boot diagnostics;
- a separately managed Standard SSD evidence disk;
- an OS disk that is deleted with the VM;
- an evidence disk that detaches instead of being deleted with the VM.

When `deployPublicReportEndpoint` is also enabled, Bicep additionally creates a dedicated Azure Storage account with:

- static-website support used to provision the `$web` container;
- a browser-readable Blob service URL under `blob.core.windows.net/$web/` rather than the static-website endpoint;
- account-level anonymous Blob access enabled only for this dedicated sanitized-output account;
- `$web` configured for anonymous Blob reads without anonymous container enumeration;
- shared-key authorization disabled;
- OAuth as the default write authorization mode;
- TLS 1.2 and HTTPS-only transport;
- Blob-service CORS restricted to the configured browser origins and `GET`, `HEAD`, and `OPTIONS`;
- Blob versioning and seven-day delete retention;
- a Storage Blob Data Contributor assignment for the collector managed identity at that storage-account scope.

The committed development parameter file keeps both the VM and public endpoint disabled so static validation cannot accidentally create billable resources.

## Bootstrap sequence

Cloud-init performs a bounded, repeatable bootstrap:

```text
wait for managed data disk
  -> format only when no filesystem exists
  -> mount at /var/lib/servicetracer
  -> preserve an existing spool, token, and certificate
  -> verify Python 3.11 or newer
  -> fetch the configured Git branch, tag, or commit
  -> install ServiceTracer into a Python virtual environment
  -> create a local bearer token when one does not already exist
  -> create a self-signed certificate for the configured collector name and private IP
  -> install and start the hardened systemd collector service
  -> verify the local HTTPS health endpoint
```

The bootstrap refuses to overwrite a data disk containing an unexpected filesystem. Replacing the VM does not automatically delete the evidence disk.

The Ubuntu 24.04 image and explicit certificate identity replace two manual repairs discovered during the first Azure deployment: installing a Python version new enough for ServiceTracer and avoiding an unreliable dynamic certificate common name.

## Source pinning

`collectorSourceRef` accepts a branch, tag, or commit. `main` is convenient during development, but an evidence-producing deployment must pin a tested commit SHA so the VM can be rebuilt from a known source state.

Updating the source ref in Bicep does not mutate the software already installed on an existing VM because Azure custom data is a first-boot mechanism. Validate the corrected bootstrap by replacing the VM while retaining the detached evidence disk, or use a separately governed upgrade procedure.

## Secret and identity boundary

- The SSH public key is supplied at deployment time and is not committed.
- The collector bearer token is generated on the VM and stored with restricted permissions on the managed data disk.
- The TLS private key is also stored with restricted permissions on the managed data disk.
- The system-assigned identity receives no broad subscription or resource-group role.
- When public reporting is enabled, the identity receives only the Blob data role required to write to the dedicated report storage account.
- The publisher requests an OAuth token from the Azure Instance Metadata Service. It does not use a committed storage key or SAS token.
- Anonymous read access applies only to the sanitized `$web` blobs in the dedicated public-output account; raw evidence and private collector data must never be placed there.
- The first certificate is self-signed for the private lab. Replacing it with a governed certificate is a later deployment step.

## Deployment gate

Before enabling the VM, provide:

- `deployOperationsCollector=true`;
- a valid `collectorAdminSshPublicKey` through a local secure parameter override or deployment pipeline;
- a tested `collectorSourceRef`, preferably a commit SHA;
- a reviewed resource group, region, VM size, disk size, and private address.

Before enabling public reporting, also provide:

- `deployPublicReportEndpoint=true`;
- the exact GitHub Pages or other browser origins in `publicReportAllowedOrigins`;
- confirmation that the technician-handoff output contains no customer-sensitive identifiers;
- explicit acceptance that the report object is anonymously readable by URL;
- a reviewed retention, public-disclosure, cost, and teardown decision for the sanitized output.

## Report generation and publication

Generate the narrow report from collected evidence:

```bash
/opt/servicetracer/bin/servicetracer \
  --evidence-records /var/lib/servicetracer/evidence/evidence.jsonl \
  --containment-evidence-records /path/to/containment-evidence.jsonl \
  --adapter-config /opt/servicetracer-src/servicetracer/examples/evidence_adapters.json \
  --service-path /opt/servicetracer-src/servicetracer/examples/remote_access_service_path.json \
  --report-view technician-handoff \
  --output /tmp/technician-handoff-report.json
```

Publish it with the collector managed identity:

```bash
/opt/servicetracer/bin/servicetracer-publish-report \
  --input /tmp/technician-handoff-report.json \
  --storage-account '<storage-account-output>' \
  --source-id 'stcollector-dev'
```

The command:

1. rejects unsupported report statuses or an exact-root-cause claim;
2. creates a new object from an explicit public allowlist;
3. adds schema, collector, version, generation, and expiry metadata;
4. obtains a Storage token from managed identity;
5. writes `$web/reports/technician-handoff-report.json`.

Use the Bicep `publicReportUrl` output, which resolves through the Blob service endpoint, as `live_report_url` in `docs/report-source.json`. It can be tested before a commit by passing it through the console's `report` query parameter.

## Current deployment status

The collector VM has been deployed and manually verified in Azure. The deployed guest was repaired manually for Python 3.11 and certificate generation, and ServiceTracer `0.4.0` successfully produced the bounded technician-handoff report.

The Ubuntu 24.04 bootstrap correction, ServiceTracer `0.5.0`, dedicated public endpoint, managed-identity publisher, Blob-endpoint browser path, and live browser consumption are implemented in source but have not yet been deployed or operationally verified. The committed browser configuration therefore keeps the live endpoint blank and uses the controlled fixture.

## Required post-deployment verification

A replacement or new deployment is not considered verified until the operator records evidence for all of the following:

1. Azure reports the VM, NIC, identity, and managed disk in the intended resource group.
2. The NIC has the expected private address and no public address.
3. Ubuntu 24.04 boots and cloud-init completes successfully without a manual Python repair.
4. The evidence disk is mounted at `/var/lib/servicetracer` without loss of retained evidence.
5. `servicetracer-collector.service` is enabled and active.
6. `https://127.0.0.1:8080/healthz` returns a successful response on the VM.
7. The generated certificate has the intended DNS name and private-IP subject alternative name.
8. An authenticated record submitted from an approved VNet source is durably acknowledged.
9. The collector spool survives a service restart and a controlled VM replacement test.
10. The deployed package reports ServiceTracer `0.5.0` and exposes `servicetracer-publish-report`.
11. The report Storage account has shared-key access disabled, account anonymous Blob access enabled, and the expected managed-identity role assignment.
12. The `$web` container has Blob-only public access and the Blob service has the exact reviewed CORS rule.
13. The publisher uploads a valid public envelope without raw evidence, credentials, private addresses, or unsupported root-cause claims.
14. The Blob service URL returns the envelope anonymously with the expected CORS response for the reviewed Origin.
15. GitHub Pages loads the live report, shows its provenance, and marks an expired envelope stale.
16. The console falls back to the committed fixture when the live endpoint is unavailable.
17. Logs, token access, certificate handling, public-output retention, backup, recovery, and teardown behavior are documented.
