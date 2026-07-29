targetScope = 'resourceGroup'

@description('Existing Azure OpenAI account created during the controlled portal bootstrap.')
param accountName string

@description('Create or reconcile the bounded model deployment on the existing account.')
param deployModel bool = true

@description('Azure model deployment name used by the OpenAI SDK.')
param deploymentName string = 'gpt-41-mini-msp-dev'

@description('Exact OpenAI model name selected from live evidence.')
param modelName string = 'gpt-4.1-mini'

@description('Exact OpenAI model version selected from live evidence.')
param modelVersion string = '2025-04-14'

@description('Azure OpenAI deployment SKU.')
@allowed([
  'Standard'
  'GlobalStandard'
  'DataZoneStandard'
])
param deploymentSkuName string = 'GlobalStandard'

@description('Model deployment capacity units.')
@minValue(1)
param deploymentCapacity int = 1

@description('Create the account-scoped Cognitive Services OpenAI User role assignment.')
param assignInferenceRole bool = true

@description('Object ID of the selected inference principal.')
param inferencePrincipalId string

@description('Principal type for the inference role assignment.')
@allowed([
  'ServicePrincipal'
  'User'
  'Group'
])
param inferencePrincipalType string = 'ServicePrincipal'

var cognitiveServicesOpenAiUserRoleDefinitionId = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions'
  '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
)

resource account 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: accountName
}

resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = if (deployModel) {
  name: deploymentName
  parent: account
  sku: {
    name: deploymentSkuName
    capacity: deploymentCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: modelName
      version: modelVersion
    }
    raiPolicyName: 'Microsoft.Default'
    versionUpgradeOption: 'NoAutoUpgrade'
  }
}

resource inferenceRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (assignInferenceRole) {
  name: guid(account.id, inferencePrincipalId, cognitiveServicesOpenAiUserRoleDefinitionId)
  scope: account
  properties: {
    principalId: inferencePrincipalId
    principalType: inferencePrincipalType
    roleDefinitionId: cognitiveServicesOpenAiUserRoleDefinitionId
  }
}

output existingAccountId string = account.id
output modelDeploymentName string = deployModel ? modelDeployment!.name : ''
output inferenceRoleAssignmentId string = assignInferenceRole ? inferenceRole!.id : ''
