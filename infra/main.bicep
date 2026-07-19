targetScope = 'resourceGroup'

@description('Short workload prefix used in resource names.')
@minLength(2)
@maxLength(12)
param prefix string = 'mst'

@description('Deployment environment.')
@allowed([
  'dev'
  'test'
])
param environment string = 'dev'

@description('Azure region for regional resources.')
param location string = resourceGroup().location

@description('Address space for the simulated on-premises network.')
param virtualNetworkAddressPrefix string = '10.20.0.0/16'

@description('Address space for the isolated synthetic remote-user network.')
param remoteUserVirtualNetworkAddressPrefix string = '10.30.0.0/16'

@description('Address pool planned for VPN clients after tunnel establishment.')
param vpnClientAddressPrefix string = '10.90.0.0/24'

var commonTags = {
  workload: 'azure-iac-msp-lab'
  environment: environment
  managedBy: 'bicep'
  purpose: 'servicetracer-demo'
}

module network './modules/network.bicep' = {
  name: 'network-${environment}'
  params: {
    prefix: prefix
    environment: environment
    location: location
    virtualNetworkAddressPrefix: virtualNetworkAddressPrefix
    remoteUserVirtualNetworkAddressPrefix: remoteUserVirtualNetworkAddressPrefix
    vpnClientAddressPrefix: vpnClientAddressPrefix
    tags: commonTags
  }
}

module observability './modules/observability.bicep' = {
  name: 'observability-${environment}'
  params: {
    prefix: prefix
    environment: environment
    location: location
    tags: commonTags
  }
}

output onPremVirtualNetworkId string = network.outputs.onPremVirtualNetworkId
output remoteUserVirtualNetworkId string = network.outputs.remoteUserVirtualNetworkId
output subnetIds object = network.outputs.subnetIds
output logAnalyticsWorkspaceId string = observability.outputs.logAnalyticsWorkspaceId
