targetScope = 'resourceGroup'

param prefix string
param deploymentEnvironment string
param location string
param tags object
param functionAppName string
param backendTransactionUrl string
param allowedOrigins array
param logAnalyticsWorkspaceId string

var resourceSuffix = '${prefix}-${deploymentEnvironment}'
var functionStorageName = take('st${uniqueString(resourceGroup().id, functionAppName)}', 24)
var functionPlanName = 'plan-${functionAppName}'
var appInsightsName = 'appi-demo-api-${resourceSuffix}'
var storageConnectionString = 'DefaultEndpointsProtocol=https;AccountName=${functionStorage.name};AccountKey=${functionStorage.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}'

resource functionStorage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: functionStorageName
  location: location
  tags: union(tags, { component: 'demo-api-runtime-storage' })
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    allowBlobPublicAccess: false
    allowSharedKeyAccess: true
    minimumTlsVersion: 'TLS1_2'
    publicNetworkAccess: 'Enabled'
    supportsHttpsTrafficOnly: true
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: appInsightsName
  location: location
  tags: union(tags, { component: 'demo-api-observability' })
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspaceId
  }
}

resource functionPlan 'Microsoft.Web/serverfarms@2024-04-01' = {
  name: functionPlanName
  location: location
  tags: union(tags, { component: 'demo-api-compute' })
  kind: 'functionapp'
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
  }
  properties: {
    reserved: true
  }
}

resource functionApp 'Microsoft.Web/sites@2024-04-01' = {
  name: functionAppName
  location: location
  tags: union(tags, { component: 'demo-api' })
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: functionPlan.id
    httpsOnly: true
    publicNetworkAccess: 'Enabled'
    clientAffinityEnabled: false
    siteConfig: {
      linuxFxVersion: 'Python|3.11'
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      cors: {
        allowedOrigins: allowedOrigins
        supportCredentials: false
      }
      appSettings: [
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: 'python'
        }
        {
          name: 'AzureWebJobsStorage'
          value: storageConnectionString
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'ENABLE_ORYX_BUILD'
          value: 'true'
        }
        {
          name: 'SERVICETRACER_BACKEND_TRANSACTION_URL'
          value: backendTransactionUrl
        }
        {
          name: 'SERVICETRACER_ALLOWED_ORIGIN'
          value: allowedOrigins[0]
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: appInsights.properties.ConnectionString
        }
      ]
    }
  }
}

output functionAppName string = functionApp.name
output functionPlanName string = functionPlan.name
output functionStorageAccountName string = functionStorage.name
output applicationInsightsName string = appInsights.name
output healthUrl string = 'https://${functionApp.properties.defaultHostName}/api/health'
output runUrl string = 'https://${functionApp.properties.defaultHostName}/api/demo/run'
