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

@description('Linux administrator account for the synthetic backend VMs.')
param adminUsername string = 'azureadmin'

@secure()
@description('SSH public key for the synthetic backend VMs.')
param adminSshPublicKey string

@description('VM size used by each synthetic VPN backend.')
param backendVmSize string = 'Standard_B1s'

@description('HTTPS listener port shared by the load balancer and synthetic backends.')
@minValue(1)
@maxValue(65535)
param listenerPort int = 443

@description('Globally unique Azure Function App name used by the frontend.')
param functionAppName string = 'func-st-demo-mst-dev-aeg30000'

@description('Browser origins allowed to invoke the demo API.')
@minLength(1)
param allowedOrigins array = [
  'https://anthonyedgar30000.github.io'
]

var resourceSuffix = '${prefix}-${environment}'
var commonTags = {
  workload: 'azure-iac-msp-lab'
  environment: environment
  managedBy: 'bicep'
  purpose: 'servicetracer-demo'
}

resource onPremVirtualNetwork 'Microsoft.Network/virtualNetworks@2024-05-01' existing = {
  name: 'vnet-onprem-sim-${resourceSuffix}'
}

resource edgeSubnet 'Microsoft.Network/virtualNetworks/subnets@2024-05-01' existing = {
  parent: onPremVirtualNetwork
  name: 'snet-edge'
}

resource edgeLoadBalancer 'Microsoft.Network/loadBalancers@2024-05-01' existing = {
  name: 'lb-remote-access-${resourceSuffix}'
}

resource backendPool 'Microsoft.Network/loadBalancers/backendAddressPools@2024-05-01' existing = {
  parent: edgeLoadBalancer
  name: 'be-vpn-gateways'
}

resource publicIp 'Microsoft.Network/publicIPAddresses@2024-05-01' existing = {
  name: 'pip-remote-access-${resourceSuffix}'
}

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2025-02-01' existing = {
  name: 'law-${prefix}-${environment}'
}

module remoteAccessBackends './modules/remote_access_backends.bicep' = {
  name: 'remote-access-backends-${environment}'
  params: {
    prefix: prefix
    environment: environment
    location: location
    edgeSubnetId: edgeSubnet.id
    loadBalancerBackendPoolId: backendPool.id
    tags: commonTags
    adminUsername: adminUsername
    adminSshPublicKey: adminSshPublicKey
    vmSize: backendVmSize
    listenerPort: listenerPort
  }
}

module demoApi './modules/demo_api.bicep' = {
  name: 'demo-api-${environment}'
  params: {
    prefix: prefix
    deploymentEnvironment: environment
    location: location
    tags: commonTags
    functionAppName: functionAppName
    backendTransactionUrl: 'https://${publicIp.properties.ipAddress}:${listenerPort}/transaction'
    allowedOrigins: allowedOrigins
    logAnalyticsWorkspaceId: logAnalyticsWorkspace.id
  }
}

output backendVmIds array = remoteAccessBackends.outputs.backendVmIds
output backendPrivateIpAddresses object = remoteAccessBackends.outputs.backendPrivateIpAddresses
output loadBalancerPublicIp string = publicIp.properties.ipAddress
output functionAppName string = demoApi.outputs.functionAppName
output functionPlanName string = demoApi.outputs.functionPlanName
output functionStorageAccountName string = demoApi.outputs.functionStorageAccountName
output applicationInsightsName string = demoApi.outputs.applicationInsightsName
output apiHealthUrl string = demoApi.outputs.healthUrl
output apiRunUrl string = demoApi.outputs.runUrl
