# VPN backend guest inspection

This runbook defines the bounded, read-only guest inspection used after Azure Load Balancer control-plane evidence shows both VPN backend probes unhealthy while backend membership, VM power, and effective NSG access are healthy.

## Scope

Targets:

- `vm-vpn01-mst-dev`
- `vm-vpn02-mst-dev`
- resource group `rg-servicetracer-dev-westus2`
- service `servicetracer-demo-backend.service`
- listener TCP 443

The workflow may authenticate with Azure workload identity federation and invoke diagnostic shell commands through the Azure VM agent. It may not use SSH.

## Commands

The diagnostic records:

```bash
cloud-init status --long
systemctl show servicetracer-demo-backend.service --no-pager
systemctl status servicetracer-demo-backend.service --no-pager
systemctl is-active servicetracer-demo-backend.service
systemctl is-enabled servicetracer-demo-backend.service
ss -lntp | filter TCP 443
journalctl -u servicetracer-demo-backend.service --no-pager -n 100
ufw status verbose
```

## Prohibited actions

The workflow must not:

- write or replace guest files;
- enable, disable, start, stop, or restart services;
- install or remove packages;
- change UFW, nftables, iptables, NSGs, load balancer configuration, NICs, VMs, RBAC, or deployments;
- retry automatically;
- perform rollback or cleanup.

## Expected evidence

- VM instance view before guest inspection;
- raw Azure Run Command response from each VM;
- deterministic diagnosis JSON and Markdown;
- SHA-256 manifest;
- terminal issue comment with explicit non-mutation assertions.

## Failure and rollback

A command or workflow failure does not authorize a retry. Partial evidence is uploaded. No rollback is required because the operation is read-only.
