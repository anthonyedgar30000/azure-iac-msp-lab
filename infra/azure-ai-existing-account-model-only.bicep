targetScope = 'resourceGroup'

@description('Existing Azure OpenAI account created during the controlled portal bootstrap.')
param accountName string

@description('Azure model deployment name used by the OpenAI SDK.')
param deploymentName string = 'gpt-41-mini-msp-dev'

@description('Exact OpenAI model name selected from fresh live evidence.')
param modelName string = 'gpt-4.1-mini'

@description('Exact OpenAI model version selected from fresh live evidence.')
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

resource account 'Microsoft.CognitiveServices/accounts@2024-10-01' existing = {
  name: accountName
}

resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
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

output existingAccountId string = account.id
output modelDeploymentId string = modelDeployment.id
output modelDeploymentName string = modelDeployment.name
