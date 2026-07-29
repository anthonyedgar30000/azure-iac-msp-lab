using './main.bicep'

param location = 'westus2'
param mcpResourceGroupName = 'rg-azure-mcp-dev-westus2'
param targetResourceGroupName = 'rg-servicetracer-dev-westus2'
param containerAppName = 'ca-azmcp-msp-dev'
param environmentName = 'cae-azmcp-msp-dev'
param managedIdentityName = 'id-azmcp-msp-dev'
param serverAppDisplayName = 'Azure MCP MSP Lab Read Only'
param imageReference = 'mcr.microsoft.com/azure-sdk/azure-mcp@sha256:80ea86cdbb30d6403ceea36766bdf8b736805bf1a0ef0a688be4bf4bb95c9b8d'
param namespaces = [
  'group'
  'compute'
  'monitor'
]
param tags = {
  project: 'Azure IaC MSP Lab'
  environment: 'dev'
  workload: 'azure-mcp-read-only'
  managedBy: 'Bicep'
}
