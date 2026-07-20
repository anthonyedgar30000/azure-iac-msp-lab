# ServiceTracer lab architecture

## Purpose

This lab demonstrates cloud infrastructure-as-code and traditional Windows/network operations in one controlled environment. Azure hosts the simulation; the services inside the virtual network represent a small MSP-managed business environment.

## Planned service path

```text
Remote Windows client
  -> public DNS
  -> Azure Load Balancer
  -> VPN-01 or VPN-02
  -> NPS/RADIUS
  -> VPN address and routes
  -> internal DNS
  -> domain-controller discovery
  -> Kerberos
  -> RDP session host
```

## Initial Azure topology

| Subnet | Prefix | Planned workload |
|---|---:|---|
| `snet-edge` | `10.20.10.0/24` | Load balancer backends, VPN-01, VPN-02 |
| `snet-identity` | `10.20.20.0/24` | DC-01, DC-02, DNS, NPS |
| `snet-servers` | `10.20.30.0/24` | RDS-01, FILE-01 |
| `snet-operations` | `10.20.40.0/24` | Monitoring collector, ServiceTracer |
| `snet-remote-users` | `10.30.10.0/24` | Synthetic Windows client in a separate, unpeered VNet |

The remote-user VNet is deliberately separate and unpeered so the synthetic client cannot bypass the remote-access path. Azure provides a strong Layer 3-7 simulation. Traditional Ethernet switching, physical cabling, radio-frequency behaviour, and real VLAN trunking remain out of scope for the cloud-only phase.

## Load-balancer boundary

The IaC defines a Standard public Azure Load Balancer with:

- a TCP 443 frontend listener;
- an empty backend pool reserved for `VPN-01` and `VPN-02`;
- a TCP 443 health probe;
- a load-balancing rule that forwards TCP 443 to the selected backend.

The initial probe is intentionally shallow. It confirms that a backend listener answers on TCP 443, not that RADIUS, address assignment, tunnel creation, internal DNS, Kerberos, or RDP are healthy.

```text
TCP 443 probe succeeds
  !=
complete remote-access transaction succeeds
```

ServiceTracer records a **probe gap** when a backend remains probe-healthy while end-to-end transactions through that backend fail downstream.

## Operational evidence boundary

ServiceTracer does not require the synthetic attempt generator as its primary input. Source systems emit structured records through exporters, parsers, or collectors. Versioned adapters then map those records into stable ServiceTracer contracts.

```text
Azure load-balancer telemetry
VPN syslog
NPS and Windows events
SNMP counters and traps
Synthetic end-user checks
Ticket and change records
        -> source-specific parser or exporter
        -> operational collector
        -> durable JSONL evidence spool
        -> versioned source adapters
        -> correlation and transaction assembly
        -> deterministic incident analysis
```

The source adapter specifies:

- where the event identity, timestamp, source, asset, backend, correlation identity, and event type are found;
- whether the record represents a service stage, contextual evidence, or operational history;
- which service stage and outcome a transaction event represents;
- which timeout, retry, elapsed-time, probe-state, or health fields are retained.

Vendor-specific parsing remains outside the deterministic analyzer. A parser may change from one VPN vendor or monitoring platform to another while still emitting the same stable evidence contract.

## Collector boundary

The operational collector is intentionally narrow. It validates transport-level record shape and durability but does not decide what the record means.

```text
received source record
  -> validate JSON object, source type, event discriminator, and size
  -> establish event identity and canonical fingerprint
  -> preflight the whole batch
  -> exact duplicate: acknowledge idempotently
  -> reused identity with different content: reject
  -> append original record to spool
  -> flush to durable storage
  -> return receipt
```

Supported collection paths:

- JSON, JSON-array, and JSONL import for existing exports and scheduled jobs;
- bearer-authenticated HTTP or HTTPS `POST /v1/records`;
- local structured-syslog TCP or UDP messages containing `@servicetracer ` followed by a JSON record;
- a PowerShell sender for Windows-side exporters.

The HTTP collector exposes an unauthenticated `/healthz` endpoint containing no evidence and an authenticated `/v1/status` endpoint. The collector is intended for the isolated operations subnet and must not be exposed directly to the public Internet.

The structured-syslog listener binds to localhost by default because it has no application-layer authentication. A local vendor parser or forwarding sidecar converts raw device logs into the structured evidence contract. Remote sources should use authenticated HTTPS or another protected transport.

One process owns one spool. Multiple collectors use separate spools, all of which can be passed to ServiceTracer as repeated `--evidence-records` inputs.

## Evidence integrity and assembly

```text
source event identity
  -> canonical content fingerprint
  -> exact duplicate: accept idempotently once
  -> same identity with different content: reject
```

The collector protects identity before durable write. The evidence-normalization layer independently repeats identity validation before analysis. These are separate boundaries: collector acceptance means the record was durably received; analysis acceptance means the record mapped cleanly into the configured evidence contract.

Stage evidence is grouped by correlation identity and backend identity. A transaction is analyzable only when ServiceTracer has a contiguous observed path through its success or terminal-failure stage.

```text
missing stage before terminal outcome
  -> incomplete transaction
  -> preserve the evidence gap
  -> do not invent a successful stage
```

After an observed terminal failure, later service stages are marked `not_reached`. This is distinct from missing evidence before the failure.

Context observations remain separate from transaction stages. SNMP device health, load-balancer probe state, and similar observations can narrow the investigation without pretending they are proof that a user transaction completed.

Ticket and change records enter through the same adapter boundary but remain operational-history evidence. A related record is an investigation lead, not a blame mechanism and not proof of causation.

## Incident localization contract

ServiceTracer reports:

- last successful service stage;
- first failed transition;
- failure mode, elapsed time, retries, and timeout;
- node or backend handling the attempt;
- downstream stages not reached;
- incomplete transactions and missing evidence;
- healthy stages that reduce the active search space;
- contextual device and probe observations;
- whether load-balancer health evidence is shallower than the failed transaction;
- relevant prior work on the same asset or service stage;
- safest high-information next action;
- remaining uncertainty.

## Controlled incident fixture

Mixed source records contain one successful transaction through `VPN-01` and one transaction through `VPN-02` that reaches the RADIUS-request stage before timing out after three retries while waiting for a response.

Expected ServiceTracer output:

```text
Remote access is intermittently failing.
The failed transaction completed public DNS, backend selection, TCP, TLS,
and RADIUS request transmission. The first failed stage was RADIUS response.
Address assignment, tunnel creation, internal DNS, Kerberos, and RDP were not reached.

VPN-02 remained healthy under the listener-only TCP 443 probe while the
end-to-end transaction failed. The probe does not represent the full service.

Immediate containment: stop assigning new sessions to VPN-02 while preserving
its configuration, logs, counters, and active-state evidence. Compare VPN-02
with VPN-01 and the approved configuration baseline.
```

The committed records are regression fixtures for the operational input contract. They are not required once live collectors emit the same structured evidence.

## Containment contract

Containment restores reliable service without destroying useful evidence:

```text
Stop new sessions to VPN-02
  -> keep new traffic on VPN-01
  -> preserve VPN-02 state
  -> repeat end-to-end transactions
  -> confirm whether service stabilizes
```

Stateful sessions are not assumed to move invisibly between gateways. Existing healthy sessions may remain until they end unless the node presents a security or stability risk. New sessions avoid the suspected node.

Post-containment source records complete through `VPN-01`. This supports the operational statement that service stabilized under containment. It does not establish the exact defect on `VPN-02`, and it does not establish that `VPN-02` is ready to return.

## Return-to-service gates

```text
Compare VPN-02 with VPN-01 and approved state
  -> correct the identified drift or defect
  -> test VPN-02 directly outside normal rotation
  -> verify listener and full transaction health
  -> return VPN-02 gradually
  -> repeat end-to-end verification through both nodes
```
