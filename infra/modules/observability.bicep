targetScope = 'resourceGroup'

param prefix string
param environment string
param location string
param tags object

resource workspace 'Microsoft.OperationalInsights/workspaces@2025-02-01' = {
  name: 'law-${prefix}-${environment}'
  location: location
  tags: union(tags, { component: 'observability' })
  properties: {
    features: {
      disableLocalAuth: false
      enableLogAccessUsingOnlyResourcePermissions: true
    }
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
    retentionInDays: 30
    sku: {
      name: 'PerGB2018'
    }
    workspaceCapping: {
      dailyQuotaGb: 1
    }
  }
}

output logAnalyticsWorkspaceId string = workspace.id
output logAnalyticsWorkspaceName string = workspace.name
