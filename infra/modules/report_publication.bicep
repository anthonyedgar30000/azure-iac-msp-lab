targetScope = 'resourceGroup'

param prefix string
param environment string
param location string
param tags object
param collectorPrincipalId string

@description('Browser origins permitted to fetch the public report through CORS.')
@minLength(1)
param allowedOrigins array

var storageNameSeed = toLower(replace('streport${prefix}${environment}${uniqueString(resourceGroup().id)}', '-', ''))
var storageAccountName = take(storageNameSeed, 24)
var blobDataContributorRoleDefinitionId = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
)

resource reportStorage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  tags: union(tags, {
    component: 'servicetracer-public-report'
    dataClassification: 'sanitized-public-output'
  })
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    allowCrossTenantReplication: false
    allowSharedKeyAccess: false
    defaultToOAuthAuthentication: true
    minimumTlsVersion: 'TLS1_2'
    publicNetworkAccess: 'Enabled'
    supportsHttpsTrafficOnly: true
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
    encryption: {
      keySource: 'Microsoft.Storage'
      services: {
        blob: {
          enabled: true
          keyType: 'Account'
        }
        file: {
          enabled: true
          keyType: 'Account'
        }
      }
    }
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: reportStorage
  name: 'default'
  properties: {
    cors: {
      corsRules: [
        {
          allowedHeaders: [
            '*'
          ]
          allowedMethods: [
            'GET'
            'HEAD'
            'OPTIONS'
          ]
          allowedOrigins: allowedOrigins
          exposedHeaders: [
            'Content-Length'
            'Content-Type'
            'ETag'
            'Last-Modified'
          ]
          maxAgeInSeconds: 300
        }
      ]
    }
    deleteRetentionPolicy: {
      enabled: true
      days: 7
    }
    isVersioningEnabled: true
    staticWebsite: {
      enabled: true
      indexDocument: 'index.html'
      errorDocument404Path: '404.html'
    }
  }
}

resource collectorReportWriter 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(reportStorage.id, collectorPrincipalId, blobDataContributorRoleDefinitionId)
  scope: reportStorage
  properties: {
    principalId: collectorPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: blobDataContributorRoleDefinitionId
  }
}

output storageAccountName string = reportStorage.name
output staticWebsiteEndpoint string = reportStorage.properties.primaryEndpoints.web
output publicReportUrl string = '${reportStorage.properties.primaryEndpoints.web}reports/technician-handoff-report.json'
output collectorWriterRoleAssignmentId string = collectorReportWriter.id
