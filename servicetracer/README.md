# ServiceTracer

ServiceTracer analyzes ordered service transactions assembled from operational evidence. It does not infer an unobserved root cause. Its full report identifies the last successful stage, first failed transition, node-specific failure concentration, later stages not reached, relevant operational history, load-balancer probe gaps, and a bounded containment or comparison action.

The portfolio demo uses a deliberately narrower technician-handoff view. It verifies that the configured load-balancer probe is healthy, identifies `VPN-02` as the backend associated with failed sessions, and stops there. Device-specific diagnosis, repair, and return-to-service validation remain the technician's responsibility.

## Collector-first run path

```bash
python -m pip install -e servicetracer

servicetracer-collector ingest \
  --spool /tmp/incident-evidence.jsonl \
  --input servicetracer/examples/source_records.jsonl

servicetracer-collector ingest \
  --spool /tmp/containment-evidence.jsonl \
  --input servicetracer/examples/containment_source_records.jsonl

servicetracer \
  --evidence-records /tmp/incident-evidence.jsonl \
  --containment-evidence-records /tmp/containment-evidence.jsonl \
  --adapter-config servicetracer/examples/evidence_adapters.json \
  --service-path servicetracer/examples/remote_access_service_path.json \
  --output servicetracer-report.json
```

The `ingest` command represents exports and batch jobs. The same spool can receive authenticated HTTP or HTTPS submissions and local structured-syslog messages. See `collectors/README.md`.

## Technician-handoff demo

```bash
servicetracer \
  --evidence-records /tmp/incident-evidence.jsonl \
  --containment-evidence-records /tmp/containment-evidence.jsonl \
  --adapter-config servicetracer/examples/evidence_adapters.json \
  --service-path servicetracer/examples/remote_access_service_path.json \
  --report-view technician-handoff \
  --output technician-handoff-report.json
```

The bounded demo report says only what the evidence supports at the intended operational boundary:

- the configured load-balancer probe is healthy;
- failed remote-access sessions are concentrated on `VPN-02`;
- `VPN-01` is the healthy comparison and temporary service path;
- ServiceTracer stops at `VPN-02` and does not claim the exact configuration defect;
- the technician temporarily moves the affected user to `VPN-01`, repairs `VPN-02`, validates it with a test user, and then returns the original user to `VPN-02`.

The report intentionally omits deeper analyzer-stage conclusions such as the RADIUS-response stage from the user-facing demo view.

## Public report envelope

ServiceTracer `0.5.0` adds a separate publication boundary. The publisher never uploads the full analyzer report. It accepts only the technician-handoff status, reconstructs the output from a strict allowlist, rejects an exact-root-cause claim, and wraps the result with provenance and freshness metadata.

Write a public envelope locally:

```bash
servicetracer-publish-report \
  --input technician-handoff-report.json \
  --output public-technician-handoff-report.json \
  --source-id stcollector-dev
```

The envelope uses the schema:

```text
servicetracer.public-report.v1
```

Its top-level metadata includes:

- `generated_at`;
- `expires_at`;
- a non-secret source identifier;
- the ServiceTracer version;
- the sanitized technician-handoff report.

Fields not explicitly included in the public contract are dropped. This prevents raw evidence, private addresses, subscription identifiers, collector tokens, ticket internals, or deeper analyzer state from passing through merely because a future internal report adds them.

## Azure managed-identity publication

On an Azure VM with a narrowly scoped Blob data role:

```bash
servicetracer-publish-report \
  --input technician-handoff-report.json \
  --storage-account '<public-report-storage-account>' \
  --source-id stcollector-dev
```

The publisher obtains an OAuth token from the Azure Instance Metadata Service and writes:

```text
$web/reports/technician-handoff-report.json
```

Default publication behavior:

- Azure Storage data-plane OAuth rather than a storage key or SAS token;
- `application/json` content type;
- `no-store` cache control;
- a 15-minute report lifetime unless overridden;
- atomic local-file output when using `--output`;
- no automatic scheduling or claim that the uploaded report is live until an operator has verified the deployment.

The GitHub Pages console can load this envelope from the URL configured in `docs/report-source.json`. If the endpoint is absent or unavailable, the console falls back to the committed bounded fixture. The browser validates schema, provenance, expiry, and the no-root-cause boundary but does not rerun ServiceTracer analysis.

## Live collector

```bash
export SERVICETRACER_COLLECTOR_TOKEN='replace-with-a-secret'

servicetracer-collector http \
  --listen 0.0.0.0 \
  --port 8080 \
  --spool /var/lib/servicetracer/evidence/evidence.jsonl \
  --tls-cert /var/lib/servicetracer/tls/collector.crt \
  --tls-key /var/lib/servicetracer/tls/collector.key
```

The collector accepts one record object or an array at `POST /v1/records`. Exact duplicate evidence is accepted idempotently. Reusing an `event_id` with different content is rejected before the batch is written. Accepted records are flushed to disk before success is returned.

The collector preserves the original structured record. It does not decide which service stage the record represents. That interpretation remains in the versioned adapter configuration.

## Current evidence adapters

The current adapters accept structured records representing:

- Azure load-balancer selection and backend probe state;
- VPN syslog transaction stages and timeout/retry evidence;
- NPS and Windows authentication events;
- SNMP device-health observations;
- synthetic end-user transaction stages;
- ticket and change-history records.

The adapter configuration maps source fields and event types into ServiceTracer's stable stage, context, and operational-history contracts. Vendor-specific raw-log parsing can change without changing the analyzer.

## Evidence rules

- Event identity is idempotent: an exact duplicate is counted and ignored.
- Reusing an event ID with different content is rejected.
- Collector batches are preflighted so an identity conflict prevents partial writes.
- Events are grouped by correlation identity and backend identity.
- A transaction must have contiguous observable evidence through its terminal stage.
- Missing evidence is reported as an incomplete transaction; ServiceTracer does not invent successful stages.
- Multiple conflicting outcomes for one stage are rejected for review rather than silently resolved.
- Context observations such as SNMP health or load-balancer probe state remain distinct from transaction-stage evidence.

## Expected source-evidence result

- one complete successful transaction through `VPN-01`;
- one transaction through `VPN-02` that times out at `radius_response` after three retries;
- last successful stage: `radius_request`;
- VPN address assignment, tunnel creation, internal DNS, Kerberos, and RDP not reached;
- `CHG-1042` returned from the ingested ticket record as related operational history;
- `VPN-02` still marked healthy by the ingested listener-only TCP 443 probe state;
- shallow-probe gap detected because the full transaction is failing downstream.

These details remain available in the full report for engineering and regression purposes. The technician-handoff and public views expose only the bounded load-balancer and backend localization needed for the demo.

## Expected containment result

- stop assigning new sessions to `VPN-02`;
- preserve its configuration, load-balancer state, syslog, SNMP, RADIUS evidence, and ticket history;
- route new-session evidence through `VPN-01`;
- all post-drain fixture transactions complete successfully;
- record that service stabilized under containment;
- retain the uncertainty that `VPN-02` has not yet been repaired or validated for return to service.

## Replay and regression mode

The older preassembled-attempt format and deterministic data generator remain available for regression testing and incident replay. They are not required by the operational collector or primary analysis path.
