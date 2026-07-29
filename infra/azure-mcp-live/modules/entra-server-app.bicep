extension microsoftGraphV1

param displayName string
param uniqueName string
param scopeValue string = 'Mcp.Tools.Read'
param scopeDisplayName string = 'Azure MCP read-only tools'
param scopeDescription string = 'Delegated access to the admitted read-only Azure MCP tools.'
param preAuthorizedClientAppIds array = [
  'aebc6443-996d-45c2-90f0-388ff96faa56'
]

var scopeId = guid(uniqueName, scopeValue)

resource app 'Microsoft.Graph/applications@v1.0' = {
  uniqueName: uniqueName
  displayName: displayName
  signInAudience: 'AzureADMyOrg'
  api: {
    oauth2PermissionScopes: [
      {
        id: scopeId
        type: 'User'
        adminConsentDescription: scopeDescription
        adminConsentDisplayName: scopeDisplayName
        userConsentDescription: scopeDescription
        userConsentDisplayName: scopeDisplayName
        value: scopeValue
        isEnabled: true
      }
    ]
    preAuthorizedApplications: [for clientId in preAuthorizedClientAppIds: {
      appId: clientId
      delegatedPermissionIds: [scopeId]
    }]
    requestedAccessTokenVersion: 2
  }
}

resource appUpdate 'Microsoft.Graph/applications@v1.0' = {
  uniqueName: uniqueName
  displayName: displayName
  signInAudience: 'AzureADMyOrg'
  identifierUris: ['api://${app.appId}']
  api: app.api
}

output clientId string = app.appId
output objectId string = app.id
output identifierUri string = 'api://${app.appId}'
output scopeValue string = scopeValue
output scopeId string = scopeId
