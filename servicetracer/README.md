# ServiceTracer deterministic prototype

This prototype analyzes ordered remote-access attempts. It does not infer an unobserved root cause. It identifies the last successful stage, first failed transition, node-specific failure concentration, later stages not reached, relevant operational history, and a bounded next action.

## Run

```bash
python -m pip install -e servicetracer
python -m servicetracer.demo_data --output /tmp/remote_access_attempts.jsonl
servicetracer \
  --attempts /tmp/remote_access_attempts.jsonl \
  --service-path servicetracer/examples/remote_access_service_path.json \
  --tickets servicetracer/examples/tickets.json \
  --output servicetracer-report.json
```

## Expected demo result

- 20 attempts
- 11 successful
- 9 failed
- failures concentrated on `VPN-02`
- last successful stage: `radius_request`
- first failed stage: `radius_response`
- timeout after three retries
- VPN address assignment, tunnel creation, internal DNS, Kerberos, and RDP not reached
- `CHG-1042` returned as related operational history
- containment recommendation: stop assigning new sessions to `VPN-02`, preserve evidence, and compare with `VPN-01` and the approved baseline
