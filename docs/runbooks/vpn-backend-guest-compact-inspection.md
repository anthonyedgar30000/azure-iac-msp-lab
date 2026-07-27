# Compact VPN backend guest inspection

## Purpose

Collect decisive guest-level listener evidence from the two VPN backend VMs without changing either guest or any Azure resource.

This run exists because the first guest inspection produced useful journal and UFW evidence but Azure Run Command truncated the earlier cloud-init, systemd, and listener sections.

## Scope

- Resource group: `rg-servicetracer-dev-westus2`
- Region: `westus2`
- VMs: `vm-vpn01-mst-dev`, `vm-vpn02-mst-dev`
- Service: `servicetracer-demo-backend.service`
- Listener: TCP 443

## Commands

The workflow emits compact marked sections for:

```bash
cloud-init status --long
systemctl show servicetracer-demo-backend.service \
  -p LoadState -p ActiveState -p SubState -p UnitFileState \
  -p Result -p ExecMainStatus -p ExecMainCode -p FragmentPath -p ExecStart
systemctl is-active servicetracer-demo-backend.service
systemctl is-enabled servicetracer-demo-backend.service
ss -H -lntp "sport = :443"
ufw status verbose
journalctl -u servicetracer-demo-backend.service -n 10 --no-pager
```

Every output line is capped at 240 characters, the listener section is capped at five lines, and the journal is capped at ten lines so the decisive sections remain below Azure Run Command's observed output envelope.

## Authority boundary

Authorized:

- Azure OIDC authentication;
- one VM-agent RunShellScript command per listed VM;
- read-only inspection;
- artifact publication.

Not authorized:

- SSH;
- guest file changes;
- service start, stop, restart, enable, disable, or daemon reload;
- package changes;
- guest firewall changes;
- Azure configuration changes;
- deployment, rollback, cleanup, or automatic retry.

## Expected evidence

The run must preserve the distinction between `not_observed` and `false`. A missing section, failed command envelope, or truncated payload is an evidence limitation rather than proof of a negative state.

## Failure behavior

Stop after one attempt, upload partial evidence, and require new explicit authority for any rerun or repair.

## Cleanup

No Azure cleanup is required because no resources or configurations are created or changed.
