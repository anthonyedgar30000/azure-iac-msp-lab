# ServiceTracer deterministic prototype

This prototype analyzes ordered remote-access attempts. It does not infer an unobserved root cause. It identifies the last successful stage, first failed transition, node-specific failure concentration, later stages not reached, relevant operational history, load-balancer probe gaps, and a bounded containment or comparison action.

## Run

```bash
python -m pip install -e servicetracer

python -m servicetracer.demo_data \
  --scenario incident \
  --output /tmp/remote_access_attempts.jsonl

python -m servicetracer.demo_data \
  --scenario containment \
  --output /tmp/containment_attempts.jsonl

servicetracer \
  --attempts /tmp/remote_access_attempts.jsonl \
  --containment-attempts /tmp/containment_attempts.jsonl \
  --service-path servicetracer/examples/remote_access_service_path.json \
  --tickets servicetracer/examples/tickets.json \
  --load-balancer-state servicetracer/examples/load_balancer_state.json \
  --output servicetracer-report.json
```

## Expected incident result

- 20 attempts
- 11 successful
- 9 failed
- failures concentrated on `VPN-02`
- last successful stage: `radius_request`
- first failed stage: `radius_response`
- timeout after three retries
- VPN address assignment, tunnel creation, internal DNS, Kerberos, and RDP not reached
- `CHG-1042` returned as related operational history
- `VPN-02` still marked healthy by the listener-only TCP 443 probe
- shallow-probe gap detected because the full transaction is failing downstream

## Expected containment result

- stop assigning new sessions to `VPN-02`
- preserve its configuration, load-balancer state, syslog, SNMP, RADIUS evidence, and ticket history
- route 12 new-session attempts through `VPN-01`
- 12 of 12 attempts complete successfully
- record that service stabilized under containment
- retain the uncertainty that `VPN-02` has not yet been repaired or validated for return to service
