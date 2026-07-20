# ServiceTracer

ServiceTracer analyzes ordered service transactions assembled from operational evidence. It does not infer an unobserved root cause. It identifies the last successful stage, first failed transition, node-specific failure concentration, later stages not reached, relevant operational history, load-balancer probe gaps, and a bounded containment or comparison action.

## Primary run path

```bash
python -m pip install -e servicetracer

servicetracer \
  --evidence-records servicetracer/examples/source_records.jsonl \
  --containment-evidence-records servicetracer/examples/containment_source_records.jsonl \
  --adapter-config servicetracer/examples/evidence_adapters.json \
  --service-path servicetracer/examples/remote_access_service_path.json \
  --output servicetracer-report.json
```

`--evidence-records` may be repeated for separate collector exports. The current adapters accept structured records representing:

- Azure load-balancer selection and backend probe state;
- VPN syslog transaction stages and timeout/retry evidence;
- NPS and Windows authentication events;
- SNMP device-health observations;
- synthetic end-user transaction stages;
- ticket and change-history records.

The adapter configuration maps source fields and event types into ServiceTracer's stable stage, context, and operational-history contracts. Real collectors can emit the same structured records without changing the analyzer.

## Evidence rules

- Event identity is idempotent: an exact duplicate is counted and ignored.
- Reusing an event ID with different content is rejected.
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

## Expected containment result

- stop assigning new sessions to `VPN-02`;
- preserve its configuration, load-balancer state, syslog, SNMP, RADIUS evidence, and ticket history;
- route new-session evidence through `VPN-01`;
- all post-drain fixture transactions complete successfully;
- record that service stabilized under containment;
- retain the uncertainty that `VPN-02` has not yet been repaired or validated for return to service.

## Replay and regression mode

The older preassembled-attempt format and deterministic data generator remain available for regression testing and incident replay. They are not required by the primary operational input path.
