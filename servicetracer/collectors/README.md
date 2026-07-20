# ServiceTracer operational collectors

ServiceTracer now has a durable collector boundary. The analyzer does not need generated attempts and the collector does not need to understand the incident. It accepts structured source records, protects their identities, and writes the original records to a JSONL spool for the adapter and transaction-assembly layer.

```text
VPN / load balancer / Windows / synthetic probe / ticket source
  -> source-specific parser or exporter
  -> authenticated collector
  -> durable evidence JSONL spool
  -> versioned ServiceTracer adapters
  -> transaction assembly and incident analysis
```

## Ingest an existing export

```bash
servicetracer-collector ingest \
  --spool /var/lib/servicetracer/evidence.jsonl \
  --input exported-records.jsonl
```

This is useful for initial integrations with Azure Monitor exports, Windows event export jobs, appliance APIs, and ticketing-system exports.

## Run the HTTP or HTTPS collector

The collector requires a bearer token by default. It never writes the token into the spool or its receipts.

```bash
export SERVICETRACER_COLLECTOR_TOKEN='replace-with-a-secret'

servicetracer-collector http \
  --listen 0.0.0.0 \
  --port 8080 \
  --spool /var/lib/servicetracer/evidence.jsonl \
  --tls-cert /etc/servicetracer/tls/collector.crt \
  --tls-key /etc/servicetracer/tls/collector.key
```

Endpoints:

- `POST /v1/records` accepts one source-record object or an array of objects.
- `GET /v1/status` reports spool health and requires authentication.
- `GET /healthz` is an unauthenticated liveness check and contains no evidence.

The Azure lab NSG already reserves TCP 8080 from the simulated VNet to the operations subnet. The collector must not be exposed directly to the public Internet.

## Windows sender

`windows/Send-ServiceTracerRecord.ps1` sends a PowerShell object to the collector with bounded retries. It is a generic transport helper; event-specific scripts remain responsible for constructing accurate NPS, Kerberos, DNS, RDP, or health records.

```powershell
$record = [ordered]@{
    source_type   = 'nps_windows'
    event_id      = 'NPS-20260719-0001'
    timestamp     = (Get-Date).ToUniversalTime().ToString('o')
    computer      = 'NPS-01'
    gateway       = 'VPN-02'
    transaction_id = 'ATT-002'
    event         = 'radius_access_reject'
}

$record | .\Send-ServiceTracerRecord.ps1 `
    -CollectorUri 'https://collector.contoso.test:8080/v1/records'
```

## Structured syslog receiver

The local syslog receiver deliberately does not pretend to understand every vendor's log format. A vendor-specific parser, rsyslog template, or appliance integration must emit a message containing `@servicetracer ` followed by one JSON source record.

```text
<134>1 ... vpn-02 ... @servicetracer {"source_type":"vpn_syslog",...}
```

Run the local receiver:

```bash
servicetracer-collector syslog \
  --transport tcp \
  --listen 127.0.0.1 \
  --port 5514 \
  --spool /var/lib/servicetracer/evidence.jsonl
```

Binding to localhost keeps the unauthenticated syslog boundary local to a parser or forwarding sidecar. Remote evidence should use the authenticated HTTPS collector or another protected transport.

## Evidence handling

The collector:

- writes the original structured record rather than fabricating a service stage;
- flushes accepted records to durable storage before returning success;
- accepts exact duplicate evidence idempotently;
- rejects an existing `event_id` reused with different content;
- preflights a batch so an identity conflict prevents partial batch writes;
- enforces record and HTTP-body size limits;
- can be restarted against an existing spool and rebuild its evidence-identity index.

One collector process should own a spool file. Multiple collectors should use separate spools and pass all of them to `servicetracer --evidence-records`.

## Service installation

A hardened example unit is provided at `systemd/servicetracer-collector.service`. The Azure IaC now also contains an optional private collector VM, separately managed evidence disk, and cloud-init bootstrap. Deployment and verification requirements are documented in [`../../docs/collector-vm.md`](../../docs/collector-vm.md). No collector VM or service has been deployed to Azure yet.
