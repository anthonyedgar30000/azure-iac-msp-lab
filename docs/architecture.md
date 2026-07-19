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

The IaC now defines a Standard public Azure Load Balancer with:

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

## Evidence sources

```text
Synthetic user transactions
VPN syslog
VPN SNMP counters and traps
Windows event logs
PowerShell health checks
Azure platform and network telemetry
Load-balancer probe and backend state
Ticket and change history
Git and IaC state
          -> ServiceTracer
```

## Incident localization contract

ServiceTracer reports:

- last successful service stage;
- first failed transition;
- failure mode, elapsed time, retries, and timeout;
- node or backend handling the attempt;
- downstream stages not reached;
- healthy stages that reduce the active search space;
- whether load-balancer health evidence is shallower than the failed transaction;
- relevant prior work on the same asset or service stage;
- safest high-information next action;
- remaining uncertainty.

A related ticket is an investigation lead, not a blame mechanism and not proof of causation.

## Controlled demo incident

The load balancer sends attempts to both VPN gateways. `VPN-02` contains a small configuration drift affecting its RADIUS path. Its TCP and TLS stages remain healthy, so the listener-only probe continues to mark it available.

Expected ServiceTracer output:

```text
Remote access is intermittently failing. Nine of twenty attempts stopped
at the RADIUS response transition after successful TCP and TLS negotiation.
Failures were concentrated on VPN-02. Address assignment, tunnel creation,
internal DNS, Kerberos, and RDP were not reached during those attempts.

VPN-02 remained healthy under the listener-only TCP 443 probe while
end-to-end attempts through that backend failed. The probe does not represent
the full remote-access transaction.

Immediate containment: stop assigning new sessions to VPN-02 while preserving
its configuration, logs, counters, and active-state evidence. Compare VPN-02
with VPN-01 and the approved configuration baseline.
```

## Containment contract

Containment restores reliable service without destroying useful evidence:

```text
Stop new sessions to VPN-02
  -> keep new traffic on VPN-01
  -> preserve VPN-02 state
  -> repeat synthetic transactions
  -> confirm whether service stabilizes
```

Stateful sessions are not assumed to move invisibly between gateways. Existing healthy sessions may remain until they end unless the node presents a security or stability risk. New sessions avoid the suspected node.

The deterministic containment dataset contains twelve successful new-session attempts through `VPN-01` after `VPN-02` is drained. This supports the operational statement that service stabilized under containment. It does not establish the exact defect on `VPN-02`, and it does not establish that `VPN-02` is ready to return.

## Return-to-service gates

```text
Compare VPN-02 with VPN-01 and approved state
  -> correct the identified drift or defect
  -> test VPN-02 directly outside normal rotation
  -> verify listener and full transaction health
  -> return VPN-02 gradually
  -> repeat end-to-end verification through both nodes
```
