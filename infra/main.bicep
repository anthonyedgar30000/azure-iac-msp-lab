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

@description('Public listener port used by the remote-access demo.')
@minValue(1)
@maxValue(65535)
param remoteAccessListenerPort int = 443

@description('Deploy the two private simulated VPN backends and attach them to the public load balancer. Disabled by default to prevent accidental compute cost.')
param deployDemoBackends bool = false

@description('Azure VM size used by each simulated VPN backend.')
param demoBackendVmSize string = 'Standard_B1s'

@description('Deploy the private ServiceTracer operations collector VM. Disabled by default to prevent accidental cost.')
param deployOperationsCollector bool = false

@description('Private address reserved for the collector in snet-operations.')
param collectorPrivateIpAddress string = '10.20.40.10'

@description('Linux administrator username for controlled recovery operations.')
param collectorAdminUsername string = 'azureadmin'

@secure()
@description('SSH public key used only when compute is deployed.')
param collectorAdminSshPublicKey string = ''

@description('Azure VM size for the operations collector.')
param collectorVmSize string = 'Standard_B1ms'

@description('Size of the separately managed evidence disk in GiB.')
@minValue(16)
param collectorDataDiskSizeGb int = 32

@description('Private HTTPS port used by the collector.')
@minValue(1)
@maxValue(65535)
param collectorPort int = 8080

@description('Public source repository installed by collector cloud-init.')
param collectorSourceRepository string = 'https://github.com/anthonyedgar30000/azure-iac-msp-lab.git'

@description('Branch, tag, or commit installed by collector cloud-init. Pin a commit for a repeatable deployment.')
param collectorSourceRef string = 'main'

@description('Deploy the dedicated public report endpoint and grant the collector managed identity write access. Requires deployOperationsCollector=true.')
param deployPublicReportEndpoint bool = false

@description('Browser origins allowed to fetch the sanitized public report.')
@minLength(1)
param publicReportAllowedOrigins array = [
  'https://anthonyedgar30000.github.io'
]

var commonTags = {
  workload: 'azure-iac-msp-lab'
  environment: environment
  managedBy: 'bicep'
  purpose: 'servicetracer-demo'
}
var deployReportPublicationResources = deployPublicReportEndpoint && deployOperationsCollector

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

module edgeLoadBalancer './modules/edge_load_balancer.bicep' = {
  name: 'edge-load-balancer-${environment}'
  params: {
    prefix: prefix
    environment: environment
    location: location
    listenerPort: remoteAccessListenerPort
    tags: commonTags
  }
}

module remoteAccessBackends './modules/remote_access_backends.bicep' = if (deployDemoBackends) {
  name: 'remote-access-backends-${environment}'
  params: {
    prefix: prefix
    environment: environment
    location: location
    edgeSubnetId: network.outputs.subnetIds.edge
    loadBalancerBackendPoolId: edgeLoadBalancer.outputs.backendPoolId
    tags: commonTags
    adminUsername: collectorAdminUsername
    adminSshPublicKey: collectorAdminSshPublicKey
    vmSize: demoBackendVmSize
    listenerPort: remoteAccessListenerPort
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

module operationsCollector './modules/operations_collector_vm.bicep' = if (deployOperationsCollector) {
  name: 'operations-collector-${environment}'
  params: {
    prefix: prefix
    environment: environment
    location: location
    operationsSubnetId: network.outputs.subnetIds.operations
    tags: commonTags
    privateIpAddress: collectorPrivateIpAddress
    adminUsername: collectorAdminUsername
    adminSshPublicKey: collectorAdminSshPublicKey
    vmSize: collectorVmSize
    dataDiskSizeGb: collectorDataDiskSizeGb
    collectorPort: collectorPort
    collectorSourceRepository: collectorSourceRepository
    collectorSourceRef: collectorSourceRef
  }
}

module reportPublication './modules/report_publication.bicep' = if (deployReportPublicationResources) {
  name: 'report-publication-${environment}'
  params: {
    prefix: prefix
    environment: environment
    location: location
    tags: commonTags
    collectorPrincipalId: operationsCollector.outputs.collectorPrincipalId
    allowedOrigins: publicReportAllowedOrigins
  }
}

output onPremVirtualNetworkId string = network.outputs.onPremVirtualNetworkId
output remoteUserVirtualNetworkId string = network.outputs.remoteUserVirtualNetworkId
output subnetIds object = network.outputs.subnetIds
output loadBalancerId string = edgeLoadBalancer.outputs.loadBalancerId
output loadBalancerPublicIpAddressId string = edgeLoadBalancer.outputs.publicIpAddressId
output loadBalancerBackendPoolId string = edgeLoadBalancer.outputs.backendPoolId
output loadBalancerHealthProbe object = edgeLoadBalancer.outputs.healthProbe
output demoBackendsDeploymentEnabled bool = deployDemoBackends
output demoBackendVms array = deployDemoBackends ? remoteAccessBackends.outputs.backendVmIds : []
output demoBackendPrivateIpAddresses object = deployDemoBackends ? remoteAccessBackends.outputs.backendPrivateIpAddresses : {}
output logAnalyticsWorkspaceId string = observability.outputs.logAnalyticsWorkspaceId
output operationsCollectorDeploymentEnabled bool = deployOperationsCollector
output operationsCollectorVmId string = deployOperationsCollector ? operationsCollector.outputs.collectorVmId : ''
output operationsCollectorPrincipalId string = deployOperationsCollector ? operationsCollector.outputs.collectorPrincipalId : ''
output operationsCollectorEndpoint string = deployOperationsCollector ? operationsCollector.outputs.collectorEndpoint : ''
output operationsCollectorEvidenceDiskId string = deployOperationsCollector ? operationsCollector.outputs.evidenceDiskId : ''
output publicReportEndpointDeploymentEnabled bool = deployReportPublicationResources
output publicReportStorageAccountName string = deployReportPublicationResources ? reportPublication.outputs.storageAccountName : ''
output publicReportUrl string = deployReportPublicationResources ? reportPublication.outputs.publicReportUrl : ''
