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

@description('Existing virtual network resource ID containing the private collector.')
param virtualNetworkId string

@description('Existing Standard Load Balancer name used for public ingress.')
param loadBalancerName string

@description('Existing operations NSG name applied to the collector subnet or NIC.')
param operationsNsgName string

@description('Existing private collector VM name.')
param collectorVmName string

@description('Existing collector private IP address.')
param collectorPrivateIpAddress string

@description('Globally unique DNS label for the dedicated collector API public IP.')
param dnsLabel string

@description('Exact browser origin allowed by the collector-hosted API.')
param allowedOrigin string

@description('Existing remote-access transaction endpoint used by the demo API.')
param backendTransactionUrl string

@description('Public source repository installed by the bounded VM extension.')
param sourceRepository string

@description('Exact reviewed source commit installed by the bounded VM extension.')
param sourceRef string

@description('Exact reviewed installer URI consumed by the VM extension.')
param installerUri string

var commonTags = {
  workload: 'azure-iac-msp-lab'
  environment: environment
  managedBy: 'bicep'
  purpose: 'servicetracer-demo'
}

module collectorDemoApi './modules/collector_demo_api.bicep' = {
  // Keep this nested deployment name distinct from the parent CLI deployment name.
  name: 'collector-demo-api-resources-${environment}'
  params: {
    prefix: prefix
    environment: environment
    location: location
    tags: commonTags
    virtualNetworkId: virtualNetworkId
    loadBalancerName: loadBalancerName
    operationsNsgName: operationsNsgName
    collectorVmName: collectorVmName
    collectorPrivateIpAddress: collectorPrivateIpAddress
    dnsLabel: dnsLabel
    allowedOrigin: allowedOrigin
    backendTransactionUrl: backendTransactionUrl
    sourceRepository: sourceRepository
    sourceRef: sourceRef
    installerUri: installerUri
  }
}

output publicIpId string = collectorDemoApi.outputs.publicIpId
output fqdn string = collectorDemoApi.outputs.fqdn
output healthUrl string = collectorDemoApi.outputs.healthUrl
output runUrl string = collectorDemoApi.outputs.runUrl
output collectorRemainsPrivate bool = collectorDemoApi.outputs.collectorRemainsPrivate
