targetScope = 'resourceGroup'

@description('Azure OpenAI account name and custom subdomain.')
@minLength(2)
@maxLength(64)
param accountName string

@description('Azure region selected from protected preflight evidence.')
param location string

@description('Create the model deployment inside the Azure OpenAI account.')
param deployModel bool = true

@description('Azure model deployment name used by the OpenAI SDK.')
param deploymentName string

@description('Exact OpenAI model name selected from protected preflight evidence.')
param modelName string

@description('Exact OpenAI model version selected from protected preflight evidence.')
param modelVersion string

@description('Azure OpenAI deployment SKU such as Standard or GlobalStandard.')
@allowed([
  'Standard'
  'GlobalStandard'
  'DataZoneStandard'
])
param deploymentSkuName string = 'Standard'

@description('Model deployment capacity units. Must be proven against quota and capacity evidence before deployment.')
@minValue(1)
param deploymentCapacity int = 1

@description('Create a Cognitive Services OpenAI User role assignment for the selected inference principal.')
param assignInferenceRole bool = false

@description('Object ID of the inference principal. Leave empty while assignInferenceRole is false.')
param inferencePrincipalId string = ''

@description('Principal type for the inference role assignment.')
@allowed([
  'ServicePrincipal'
  'User'
  'Group'
])
param inferencePrincipalType string = 'ServicePrincipal'

@description('Tags applied to Azure AI resources.')
param tags object

var cognitiveServicesOpenAiUserRoleDefinitionId = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd'
)

resource account 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: accountName
  location: location
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: accountName
    disableLocalAuth: true
    dynamicThrottlingEnabled: false
    publicNetworkAccess: 'Enabled'
    restrictOutboundNetworkAccess: false
  }
  tags: tags
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

output accountId string = account.id
output accountName string = account.name
output baseUrl string = 'https://${account.name}.openai.azure.com/openai/v1/'
output deploymentName string = deployModel ? modelDeployment!.name : ''
output localAuthenticationDisabled bool = account.properties.disableLocalAuth
output publicNetworkAccess string = account.properties.publicNetworkAccess
output inferenceRoleAssignmentId string = assignInferenceRole ? inferenceRole!.id : ''
