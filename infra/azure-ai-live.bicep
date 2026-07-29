targetScope = 'subscription'

@description('Fail-closed deployment switch. The committed parameter file keeps this false.')
param deployAzureAi bool = false

@description('Dedicated Azure AI resource group.')
param resourceGroupName string = 'rg-ai-msp-dev-canadaeast'

@description('Azure region selected from protected preflight evidence.')
@allowed([
  'canadaeast'
  'eastus2'
])
param location string = 'canadaeast'

@description('Globally unique Azure OpenAI account name.')
param accountName string = 'oai-msp-aeg30000-dev'

@description('Deployment environment.')
@allowed([
  'dev'
  'test'
])
param environment string = 'dev'

@description('Create the model deployment.')
param deployModel bool = true

@description('Model deployment name used by the OpenAI SDK.')
param deploymentName string = 'gpt-41-mini-msp-dev'

@description('Exact model name selected from protected preflight evidence.')
param modelName string = 'gpt-4.1-mini'

@description('Exact model version selected from protected preflight evidence.')
param modelVersion string = '2025-04-14'

@description('Deployment SKU selected from model inventory and quota evidence.')
@allowed([
  'Standard'
  'GlobalStandard'
  'DataZoneStandard'
])
param deploymentSkuName string = 'Standard'

@description('Deployment capacity units proven against protected quota and capacity evidence.')
@minValue(1)
param deploymentCapacity int = 1

@description('Assign inference access to the selected principal.')
param assignInferenceRole bool = false

@description('Object ID of the selected inference principal.')
param inferencePrincipalId string = ''

@description('Principal type for the inference role assignment.')
@allowed([
  'ServicePrincipal'
  'User'
  'Group'
])
param inferencePrincipalType string = 'ServicePrincipal'

var commonTags = {
  workload: 'azure-iac-msp-lab'
  environment: environment
  managedBy: 'bicep'
  purpose: 'governed-ai-inference'
  dataClassification: 'demo-nonproduction'
}

resource resourceGroup 'Microsoft.Resources/resourceGroups@2024-03-01' = if (deployAzureAi) {
  name: resourceGroupName
  location: location
  tags: commonTags
}

module azureAi './modules/azure_ai_openai.bicep' = if (deployAzureAi) {
  name: 'azure-ai-live-${environment}'
  scope: resourceGroup
  params: {
    accountName: accountName
    location: location
    environment: environment
    deployModel: deployModel
    deploymentName: deploymentName
    modelName: modelName
    modelVersion: modelVersion
    deploymentSkuName: deploymentSkuName
    deploymentCapacity: deploymentCapacity
    assignInferenceRole: assignInferenceRole
    inferencePrincipalId: inferencePrincipalId
    inferencePrincipalType: inferencePrincipalType
    tags: commonTags
  }
}

output deploymentEnabled bool = deployAzureAi
output deployedResourceGroupName string = deployAzureAi ? resourceGroup.name : resourceGroupName
output deployedAccountId string = deployAzureAi ? azureAi.outputs.accountId : ''
output deployedAccountName string = deployAzureAi ? azureAi.outputs.accountName : accountName
output deployedBaseUrl string = deployAzureAi ? azureAi.outputs.baseUrl : ''
output deployedModelDeploymentName string = deployAzureAi ? azureAi.outputs.deploymentName : ''
output localAuthenticationDisabled bool = deployAzureAi ? azureAi.outputs.localAuthenticationDisabled : true
output deployedPublicNetworkAccess string = deployAzureAi ? azureAi.outputs.publicNetworkAccess : 'not-deployed'
output deployedInferenceRoleAssignmentId string = deployAzureAi ? azureAi.outputs.inferenceRoleAssignmentId : ''
