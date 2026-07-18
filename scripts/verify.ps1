[CmdletBinding()]
param(
    [switch]$Deployed
)

$ErrorActionPreference = "Stop"

function Assert-Command {
    param([Parameter(Mandatory)][string]$Name)

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command '$Name' was not found in PATH."
    }
}

Assert-Command -Name "terraform"

Write-Host "Checking Terraform formatting..."
terraform fmt -check -recursive
if ($LASTEXITCODE -ne 0) {
    throw "terraform fmt check failed."
}

Write-Host "Initializing providers without a backend..."
terraform init -backend=false -input=false
if ($LASTEXITCODE -ne 0) {
    throw "terraform init failed."
}

Write-Host "Validating Terraform configuration..."
terraform validate
if ($LASTEXITCODE -ne 0) {
    throw "terraform validate failed."
}

if (-not $Deployed) {
    Write-Host "Local validation passed. Deployment verification was not requested."
    exit 0
}

Assert-Command -Name "az"

Write-Host "Reading deployed Terraform outputs..."
$outputs = terraform output -json | ConvertFrom-Json
$resourceGroupName = $outputs.resource_group_name.value
$virtualNetworkName = $outputs.virtual_network_name.value

if (-not $resourceGroupName -or -not $virtualNetworkName) {
    throw "Required deployment outputs are missing."
}

Write-Host "Verifying resource group and virtual network through Azure CLI..."
az group show --name $resourceGroupName --output none
if ($LASTEXITCODE -ne 0) {
    throw "Azure resource group verification failed."
}

az network vnet show `
    --resource-group $resourceGroupName `
    --name $virtualNetworkName `
    --output none
if ($LASTEXITCODE -ne 0) {
    throw "Azure virtual network verification failed."
}

$subnetsJson = az network vnet subnet list `
    --resource-group $resourceGroupName `
    --vnet-name $virtualNetworkName `
    --query "[].{name:name,nsg:networkSecurityGroup.id}" `
    --output json

if ($LASTEXITCODE -ne 0) {
    throw "Azure subnet verification failed."
}

$subnets = $subnetsJson | ConvertFrom-Json
$expectedSubnetNames = @("snet-management", "snet-servers")

foreach ($expectedName in $expectedSubnetNames) {
    $subnet = $subnets | Where-Object { $_.name -eq $expectedName }

    if (-not $subnet) {
        throw "Expected subnet '$expectedName' was not found."
    }

    if (-not $subnet.nsg) {
        throw "Subnet '$expectedName' has no NSG association."
    }
}

Write-Host "Deployment verification passed for the current network foundation."
