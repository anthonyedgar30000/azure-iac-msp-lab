[CmdletBinding()]
param(
    [string]$Name = "servicetracer-vpn-local",
    [string]$Repository = "https://github.com/anthonyedgar30000/azure-iac-msp-lab.git",
    [string]$Branch = "test/local-vm-vpn-backend",
    [ValidateSet("healthy", "radius-timeout")]
    [string]$Mode = "healthy",
    [string]$BackendId = "VPN-LOCAL",
    [int]$ListenerPort = 443,
    [switch]$KeepExisting,
    [switch]$DisableUfw
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Invoke-Multipass {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments)
    & multipass @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "multipass $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
    }
}

if (-not (Get-Command multipass -ErrorAction SilentlyContinue)) {
    throw "Multipass is not installed or is not on PATH. Install Canonical Multipass first."
}

$cloudInit = Join-Path $PSScriptRoot "cloud-init.yaml"
if (-not (Test-Path $cloudInit)) {
    throw "Cloud-init file not found: $cloudInit"
}

$instanceExists = $false
& multipass info $Name *> $null
if ($LASTEXITCODE -eq 0) {
    $instanceExists = $true
}

if ($instanceExists -and -not $KeepExisting) {
    Write-Host "Deleting previous disposable instance: $Name"
    Invoke-Multipass delete --purge $Name
    $instanceExists = $false
}

if (-not $instanceExists) {
    Write-Host "Launching Ubuntu 24.04 local validation VM: $Name"
    Invoke-Multipass launch 24.04 `
        --name $Name `
        --cpus 1 `
        --memory 2G `
        --disk 12G `
        --cloud-init $cloudInit
} else {
    Write-Host "Reusing existing instance: $Name"
    Invoke-Multipass start $Name
}

Invoke-Multipass exec $Name -- cloud-init status --wait

$enableUfw = if ($DisableUfw) { "0" } else { "1" }
$guestCommand = @"
set -Eeuo pipefail
rm -rf /home/ubuntu/azure-iac-msp-lab
git clone --quiet --branch '$Branch' --single-branch '$Repository' /home/ubuntu/azure-iac-msp-lab
sudo env \
  BACKEND_ID='$BackendId' \
  BACKEND_MODE='$Mode' \
  LISTENER_PORT='$ListenerPort' \
  ENABLE_UFW='$enableUfw' \
  bash /home/ubuntu/azure-iac-msp-lab/tools/local-vm-vpn-backend/install-and-test.sh \
  /home/ubuntu/azure-iac-msp-lab
"@

Write-Host "Running exact backend deployment and shallow-probe validation..."
& multipass exec $Name -- bash -lc $guestCommand
if ($LASTEXITCODE -ne 0) {
    Write-Host "Local validation failed. Opening the evidence directory summary..." -ForegroundColor Red
    & multipass exec $Name -- bash -lc "sudo find /var/tmp/servicetracer-local-vm -maxdepth 2 -type f -printf '%TY-%Tm-%TdT%TH:%TM:%TSZ %p\n' | sort | tail -n 40"
    throw "Local VM validation failed with exit code $LASTEXITCODE"
}

Write-Host "Local VM validation succeeded." -ForegroundColor Green
Invoke-Multipass info $Name
Write-Host "Open a shell with: multipass shell $Name"
Write-Host "Evidence is under: /var/tmp/servicetracer-local-vm/ inside the VM"
