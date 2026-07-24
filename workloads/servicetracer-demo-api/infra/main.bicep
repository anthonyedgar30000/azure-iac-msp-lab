targetScope = 'subscription'

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

@description('Azure region for the independent API workload.')
param location string = 'westus2'

@description('Globally unique DNS label for the workload public IP.')
param dnsLabel string

@description('Exact browser origin allowed by CORS.')
param allowedOrigin string

@description('Fixed HTTPS ServiceTracer transaction dependency.')
param backendTransactionUrl string

@description('Linux VM size. Deployment authorization requires refreshed quota and cost evidence.')
param vmSize string = 'Standard_B1s'

@description('Linux administrator username. No inbound SSH rule is created.')
param adminUsername string = 'azureadmin'

@description('SSH public key required by the Linux provisioning contract.')
param adminSshPublicKey string

@description('Public source repository installed on the dedicated VM.')
param sourceRepository string

@description('Exact immutable source commit installed on the dedicated VM.')
param sourceRef string

@description('Exact installer URI at the immutable source commit.')
param installerUri string

var resourceSuffix = '${prefix}-${environment}'
var resourceGroupName = 'rg-st-demo-api-${environment}-${location}'
var commonTags = {
  workload: 'servicetracer-demo-api'
  parentProject: 'azure-iac-msp-lab'
  environment: environment
  managedBy: 'bicep'
  lifecycle: 'independent-subproject'
}

resource workloadResourceGroup 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: resourceGroupName
  location: location
  tags: commonTags
}

module workload './modules/workload.bicep' = {
  name: 'servicetracer-demo-api-${environment}'
  scope: workloadResourceGroup
  params: {
    resourceSuffix: resourceSuffix
    location: location
    tags: commonTags
    dnsLabel: dnsLabel
    allowedOrigin: allowedOrigin
    backendTransactionUrl: backendTransactionUrl
    vmSize: vmSize
    adminUsername: adminUsername
    adminSshPublicKey: adminSshPublicKey
    sourceRepository: sourceRepository
    sourceRef: sourceRef
    installerUri: installerUri
  }
}

output resourceGroupName string = workloadResourceGroup.name
output vmId string = workload.outputs.vmId
output publicIpId string = workload.outputs.publicIpId
output fqdn string = workload.outputs.fqdn
output healthUrl string = workload.outputs.healthUrl
output runUrl string = workload.outputs.runUrl
output baseInfrastructureMutated bool = false
