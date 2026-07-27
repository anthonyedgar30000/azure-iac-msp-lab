# Local Ubuntu VM validation for the VPN backend

This harness reproduces the Azure VPN backend guest boundary in a disposable Ubuntu 24.04 LTS VM before another Azure deployment is attempted.

It validates the exact Python source embedded in `infra/bootstrap/vpn-backend-cloud-init.yaml`, a concrete systemd unit, TLS certificate access, TCP/443 readiness, HTTPS health, shallow TCP-probe tolerance, file hashes, named failure checkpoints, and local rollback behavior.

```text
repository test passed
!=
Ubuntu/systemd deployment passed

local VM deployment passed
!=
Azure guest updated
```

## Intended architecture

```text
Host workstation
  -> Multipass disposable VM
       Ubuntu 24.04 LTS
       1 vCPU / 2 GB RAM / 12 GB disk
       NAT or host-only networking
       systemd
       UFW
       ServiceTracer backend on TCP/443
```

The Azure backend declaration uses Canonical Ubuntu 24.04 LTS. The local VM therefore uses the same Ubuntu release. The local VM has 2 GB of memory for comfortable test execution; the Azure VM declaration remains `Standard_B1s`.

## Scope

Authorized locally:

- create and delete one disposable local VM;
- install packages inside that VM;
- configure local UFW;
- install and restart the local backend service;
- simulate raw TCP probes;
- test rollback;
- preserve local evidence.

Not performed:

- Azure login or query;
- Azure VM Run Command;
- Azure deployment;
- NSG, load balancer, probe, subnet, NIC, RBAC, policy, or resource changes;
- merge to `main`.

## Prerequisite

Install Canonical Multipass on the host. On Windows, the normal provider is Hyper-V; VirtualBox can be selected when Hyper-V is not available. The host scripts do not require a shared folder because the VM clones the test branch directly.

Confirm the CLI works:

```text
multipass version
```

## Windows quick start

From PowerShell:

```powershell
Set-Location <path-to-azure-iac-msp-lab>
.\tools\local-vm-vpn-backend\run.ps1
```

The default run:

1. deletes any previous `servicetracer-vpn-local` instance;
2. launches Ubuntu 24.04 with 1 vCPU, 2 GB RAM, and a 12 GB disk;
3. waits for cloud-init;
4. clones branch `test/local-vm-vpn-backend` inside the VM;
5. deploys the exact backend artifact;
6. runs the systemd, HTTPS, probe-starvation, queue, hash, and UFW checks;
7. leaves the successful VM running for inspection.

Useful PowerShell options:

```powershell
# Preserve and reuse an existing instance
.\tools\local-vm-vpn-backend\run.ps1 -KeepExisting

# Test the radius-timeout backend mode
.\tools\local-vm-vpn-backend\run.ps1 -Mode radius-timeout -BackendId VPN-LOCAL-02

# Disable UFW only when isolating an application-level failure
.\tools\local-vm-vpn-backend\run.ps1 -DisableUfw
```

## Linux or macOS quick start

```bash
chmod +x tools/local-vm-vpn-backend/run.sh
./tools/local-vm-vpn-backend/run.sh
```

Environment overrides are supported:

```bash
KEEP_EXISTING=1 BACKEND_MODE=radius-timeout BACKEND_ID=VPN-LOCAL-02 \
  ./tools/local-vm-vpn-backend/run.sh
```

## Expected successful result

The final marker must be present:

```text
SERVICETRACER_LOCAL_VALIDATION_SUCCESS run=<timestamp-pid> evidence=<path>
```

The checkpoint stream should include:

```text
CHECKPOINT service-active
CHECKPOINT listener-present
CHECKPOINT loopback-health
CHECKPOINT private-ip-health
CHECKPOINT raw-probes-connected
CHECKPOINT https-survives-raw-probes
CHECKPOINT listener-queue-below-backlog
CHECKPOINT local-vm-validation-complete
```

The raw-probe test opens 12 TCP connections that send no TLS ClientHello while a legitimate HTTPS health request is made. The HTTPS request must still return the expected payload.

## Inspect the VM

```text
multipass shell servicetracer-vpn-local
```

Inside the VM:

```bash
sudo systemctl status servicetracer-demo-backend.service
sudo journalctl -u servicetracer-demo-backend.service --no-pager
sudo ss -lntp '( sport = :443 )'
curl -kfsS https://127.0.0.1/healthz | jq
sudo ufw status verbose
sudo find /var/tmp/servicetracer-local-vm -maxdepth 2 -type f -print
```

Evidence for each run is stored under:

```text
/var/tmp/servicetracer-local-vm/<UTC timestamp>-<PID>/
```

It includes rendered hashes, host observations, service state, journal entries, listener state, queue state, thread observations, and named checkpoints.

## Exercise rollback deliberately

After one successful run, open a VM shell and run:

```bash
cd /home/ubuntu/azure-iac-msp-lab
sudo env \
  FORCE_FAILURE_AFTER_INSTALL=1 \
  ENABLE_UFW=0 \
  bash tools/local-vm-vpn-backend/install-and-test.sh "$PWD"
```

The command is expected to fail and must emit:

```text
SERVICETRACER_LOCAL_ROLLBACK_PERFORMED
```

Then verify that the previous service is restored and healthy:

```bash
sudo systemctl is-active servicetracer-demo-backend.service
curl -kfsS https://127.0.0.1/healthz | jq
```

## Cleanup

```text
multipass delete --purge servicetracer-vpn-local
```

Expected recurring infrastructure cost change: **CAD $0**.
