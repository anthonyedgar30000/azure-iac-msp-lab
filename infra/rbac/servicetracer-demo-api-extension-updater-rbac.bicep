targetScope = 'subscription'

@description('Existing ServiceTracer demo API resource group.')
param resourceGroupName string = 'rg-st-demo-api-dev-westus2'

@description('Existing ServiceTracer demo API virtual machine.')
param vmName string = 'vm-st-demo-api-mst-dev'

@description('Existing Custom Script extension to which write authority is limited.')
param extensionName string = 'servicetracer-demo-api'

@description('Object ID of the existing GitHub OIDC target service principal.')
param principalId string

@description('Stable custom role definition GUID.')
param roleDefinitionGuid string = 'a94875a8-373d-531e-bfe0-b213fd936082'

var roleName = 'ServiceTracer Demo API Extension Updater v1'
var allowedAction = 'Microsoft.Compute/virtualMachines/extensions/write'

resource targetResourceGroup 'Microsoft.Resources/resourceGroups@2024-03-01' existing = {
  name: resourceGroupName
}

resource extensionUpdaterRole 'Microsoft.Authorization/roleDefinitions@2022-04-01' = {
  name: roleDefinitionGuid
  properties: {
    roleName: roleName
    description: 'Allows updating only an existing ServiceTracer demo API VM extension when assigned at that extension resource.'
    type: 'CustomRole'
    permissions: [
      {
        actions: [
          allowedAction
        ]
        notActions: []
        dataActions: []
        notDataActions: []
      }
    ]
    assignableScopes: [
      targetResourceGroup.id
    ]
  }
}

module extensionUpdaterAssignment './modules/servicetracer-demo-api-extension-role-assignment.bicep' = {
  name: 'servicetracer-demo-api-extension-updater-assignment'
  scope: targetResourceGroup
  params: {
    vmName: vmName
    extensionName: extensionName
    principalId: principalId
    roleDefinitionId: extensionUpdaterRole.id
  }
}

output roleDefinitionId string = extensionUpdaterRole.id
output roleAssignmentId string = extensionUpdaterAssignment.outputs.roleAssignmentId
output assignmentScope string = extensionUpdaterAssignment.outputs.assignmentScope
output grantedAction string = allowedAction
