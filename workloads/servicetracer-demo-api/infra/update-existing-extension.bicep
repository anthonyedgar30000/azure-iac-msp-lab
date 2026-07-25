targetScope = 'resourceGroup'

@description('Existing ServiceTracer demo API VM name.')
param vmName string = 'vm-st-demo-api-mst-dev'

@description('Existing VM region.')
param location string = resourceGroup().location

@description('Public repository cloned by the installer.')
param sourceRepository string

@description('Exact immutable repository source commit to install.')
param sourceRef string

@description('Exact immutable installer URI.')
param installerUri string

@description('Existing public FQDN.')
param publicFqdn string

@description('Existing HTTPS ServiceTracer transaction dependency.')
param backendTransactionUrl string

@description('Existing exact browser origin allowed by CORS.')
param allowedOrigin string

@description('Unique value that forces the existing Custom Script extension to rerun.')
param forceUpdateTag string

resource vm 'Microsoft.Compute/virtualMachines@2024-07-01' existing = {
  name: vmName
}

resource installExtension 'Microsoft.Compute/virtualMachines/extensions@2024-07-01' = {
  parent: vm
  name: 'servicetracer-demo-api'
  location: location
  properties: {
    publisher: 'Microsoft.Azure.Extensions'
    type: 'CustomScript'
    typeHandlerVersion: '2.1'
    autoUpgradeMinorVersion: true
    forceUpdateTag: forceUpdateTag
    protectedSettings: {
      fileUris: [
        installerUri
      ]
      commandToExecute: 'bash install.sh ${sourceRepository} ${sourceRef} ${publicFqdn} ${backendTransactionUrl} ${allowedOrigin}'
    }
  }
}

output extensionId string = installExtension.id
output installedSourceRef string = sourceRef
