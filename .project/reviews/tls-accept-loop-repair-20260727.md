# TLS accept-loop repair review

## Observed runtime failure

The Azure Load Balancer TCP/443 probe reached `vm-vpn01-mst-dev`, completed a TCP connection, and appeared as an established socket owned by the Python backend process. The same process reported a saturated listener queue (`Recv-Q 6`, `Send-Q 5`), only one observed thread, and no HTTP request log entries. HTTPS requests to both `127.0.0.1:443` and `10.20.10.11:443` timed out.

The deployed backend wrapped the listening socket in TLS before entering `serve_forever()`. A shallow TCP probe completes the TCP handshake but sends no TLS ClientHello, leaving the accepting thread blocked in TLS negotiation. Repeated probes then saturate the listener backlog and starve valid HTTPS clients.

```text
TCP listener exists
!=
accept loop remains available

TCP probe establishes a socket
!=
TLS handshake completes
```

## Repository repair

The backend now:

- accepts raw TCP sockets on the main server loop;
- dispatches each accepted socket through `ThreadingHTTPServer` before TLS negotiation;
- performs the TLS handshake inside a daemon worker thread;
- applies a one-second handshake timeout;
- closes incomplete probe connections without blocking future accepts;
- retains the existing shallow Azure TCP/443 probe, HTTPS endpoints, response headers, UFW policy, and backend modes.

The systemd unit declares `SERVICETRACER_TLS_HANDSHAKE_TIMEOUT_SECONDS=1.0`. The request queue is increased to 128 as bounded burst tolerance, not as a substitute for the worker-thread repair.

## Deterministic regression test

The regression test extracts and executes the exact Python source embedded in cloud-init. It creates a temporary self-signed certificate, starts the repaired server, opens twelve raw TCP connections that do not send TLS, and then requires a valid HTTPS `/healthz` request to return HTTP 200 with the expected backend contract.

The test also rejects reintroduction of eager listener-socket TLS wrapping.

## Deployment boundary

This change is repository-only. It does not authenticate to Azure, update either VM, restart the service, change UFW, change the load-balancer probe, merge the pull request, or claim service recovery.

A future separately authorized deployment should use VPN-01 as the canary, capture pre-change queue and probe evidence, apply the codified backend and unit definition, restart only the backend service once, verify local HTTPS, verify `DipAvailability`, run bounded frontend transactions, and then decide whether VPN-02 should receive the same change.

```text
code_fixed != guest_updated
CI_passed != Azure_probe_healthy
Azure_probe_healthy != transaction_contract_validated
```
