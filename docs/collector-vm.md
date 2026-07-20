# Azure operations collector VM

## Purpose

The optional operations collector VM gives the implemented ServiceTracer collector a realistic Azure host without exposing it directly to the internet. It is intended to receive normalized operational evidence from VPN, Windows, SNMP, Azure, synthetic-check, and ticketing exporters inside the lab network.

## Implemented infrastructure

When `deployOperationsCollector` is enabled, Bicep creates:

- one Ubuntu Linux VM in `snet-operations`;
- a static private address, `10.20.40.10` by default;
- no public IP address;
- a system-assigned managed identity with no broad role assignments;
- Trusted Launch, Secure Boot, and virtual TPM;
- managed boot diagnostics;
- a separately managed Standard SSD evidence disk;
- an OS disk that is deleted with the VM;
- an evidence disk that detaches instead of being deleted with the VM.

The committed development parameter file keeps the VM disabled so a static validation run cannot accidentally create billable compute.

## Bootstrap sequence

Cloud-init performs a bounded, repeatable bootstrap:

```text
wait for managed data disk
  -> format only when no filesystem exists
  -> mount at /var/lib/servicetracer
  -> preserve an existing spool, token, and certificate
  -> fetch the configured Git branch, tag, or commit
  -> install ServiceTracer into a Python virtual environment
  -> create a local bearer token when one does not already exist
  -> create a private self-signed TLS certificate when one does not already exist
  -> install and start the hardened systemd collector service
  -> verify the local HTTPS health endpoint
```

The bootstrap refuses to overwrite a data disk containing an unexpected filesystem. Replacing the VM does not automatically delete the evidence disk.

## Source pinning

`collectorSourceRef` accepts a branch, tag, or commit. `main` is convenient during development, but an actual evidence-producing deployment should pin a tested commit SHA so the VM can be rebuilt from a known source state.

## Secret and identity boundary

- The SSH public key is supplied at deployment time and is not committed.
- The collector bearer token is generated on the VM and stored with restricted permissions on the managed data disk.
- The TLS private key is also stored with restricted permissions on the managed data disk.
- The system-assigned identity starts without broad Azure permissions. Future Azure telemetry or secret access must be granted through narrowly scoped role assignments.
- The first certificate is self-signed for the private lab. Replacing it with a governed certificate is a later deployment step.

## Deployment gate

Before enabling the VM, provide:

- `deployOperationsCollector=true`;
- a valid `collectorAdminSshPublicKey` through a local secure parameter override or deployment pipeline;
- a tested `collectorSourceRef`, preferably a commit SHA;
- a reviewed resource group, region, VM size, disk size, and private address.

No collector VM has been deployed by this repository yet.

## Required post-deployment verification

A real deployment is not considered verified until the operator records evidence for all of the following:

1. Azure reports the VM, NIC, identity, and managed disk in the intended resource group.
2. The NIC has the expected private address and no public address.
3. Cloud-init completes successfully.
4. The evidence disk is mounted at `/var/lib/servicetracer`.
5. `servicetracer-collector.service` is enabled and active.
6. `https://127.0.0.1:8080/healthz` returns a successful response on the VM.
7. An authenticated record submitted from an approved VNet source is durably acknowledged.
8. The collector spool survives a service restart and a controlled VM replacement test.
9. Logs, token access, certificate handling, backup, retention, and recovery behavior are documented.
10. The Azure resources are either retained intentionally or torn down and the result recorded.
