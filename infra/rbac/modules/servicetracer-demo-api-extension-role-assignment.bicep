targetScope = 'resourceGroup'

@description('Existing ServiceTracer demo API virtual machine.')
param vmName string

@description('Existing Custom Script extension to which write authority is limited.')
param extensionName string

@description('Object ID of the existing GitHub OIDC target service principal.')
param principalId string

@description('Full resource ID of the custom extension-updater role definition.')
param roleDefinitionId string

resource targetVm 'Microsoft.Compute/virtualMachines@2024-07-01' existing = {
  name: vmName
}

resource targetExtension 'Microsoft.Compute/virtualMachines/extensions@2024-07-01' existing = {
  parent: targetVm
  name: extensionName
}

resource extensionUpdaterAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(targetExtension.id, principalId, roleDefinitionId)
  scope: targetExtension
  properties: {
    roleDefinitionId: roleDefinitionId
    principalId: principalId
    principalType: 'ServicePrincipal'
    description: 'GitHub OIDC target identity may update only the existing ServiceTracer demo API extension.'
  }
}

output roleAssignmentId string = extensionUpdaterAssignment.id
output assignmentScope string = targetExtension.id
