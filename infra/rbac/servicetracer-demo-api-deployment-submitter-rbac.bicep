targetScope = 'subscription'

@description('Existing ServiceTracer demo API resource group.')
param resourceGroupName string = 'rg-st-demo-api-dev-westus2'

@description('Object ID of the existing GitHub OIDC target service principal.')
param principalId string

@description('Stable custom role definition GUID.')
param roleDefinitionGuid string = '876f6f68-0bbf-5d30-b11f-f7af57ad2c8c'

var roleName = 'ServiceTracer Demo API Deployment Submitter v1'
var allowedAction = 'Microsoft.Resources/deployments/write'

resource targetResourceGroup 'Microsoft.Resources/resourceGroups@2024-03-01' existing = {
  name: resourceGroupName
}

resource deploymentSubmitterRole 'Microsoft.Authorization/roleDefinitions@2022-04-01' = {
  name: roleDefinitionGuid
  properties: {
    roleName: roleName
    description: 'Allows submitting ARM deployment records only in the existing ServiceTracer demo API resource group. Resource mutation remains governed by separate resource-scoped roles and accepted What-If.'
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

resource deploymentSubmitterAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(targetResourceGroup.id, principalId, deploymentSubmitterRole.id)
  scope: targetResourceGroup
  properties: {
    principalId: principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: deploymentSubmitterRole.id
  }
}

output roleDefinitionId string = deploymentSubmitterRole.id
output roleAssignmentId string = deploymentSubmitterAssignment.id
output assignmentScope string = targetResourceGroup.id
output grantedAction string = allowedAction
