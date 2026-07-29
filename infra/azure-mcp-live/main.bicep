targetScope = 'subscription'

param location string = 'westus2'
param mcpResourceGroupName string
param targetResourceGroupName string
param containerAppName string
param environmentName string
param managedIdentityName string
param serverAppDisplayName string
param imageReference string
param namespaces array
param tags object

resource mcpRg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: mcpResourceGroupName
  location: location
  tags: tags
}

resource targetRg 'Microsoft.Resources/resourceGroups@2024-03-01' existing = {
  name: targetResourceGroupName
}

module identity 'modules/managed-identity.bicep' = {
  name: 'azure-mcp-managed-identity'
  scope: mcpRg
  params: {
    name: managedIdentityName
    location: location
    tags: tags
  }
}

module serverApp 'modules/entra-server-app.bicep' = {
  name: 'azure-mcp-server-entra-app'
  scope: mcpRg
  params: {
    displayName: serverAppDisplayName
    uniqueName: '${replace(toLower(serverAppDisplayName), ' ', '-')}-${uniqueString(subscription().id)}'
  }
}

module targetReader 'modules/reader-role.bicep' = {
  name: 'azure-mcp-target-reader'
  scope: targetRg
  params: {
    principalId: identity.outputs.principalId
  }
}

module runtime 'modules/container-app.bicep' = {
  name: 'azure-mcp-container-app'
  scope: mcpRg
  params: {
    location: location
    environmentName: environmentName
    containerAppName: containerAppName
    imageReference: imageReference
    serverAppClientId: serverApp.outputs.clientId
    managedIdentityId: identity.outputs.id
    managedIdentityClientId: identity.outputs.clientId
    namespaces: namespaces
    tags: tags
  }
  dependsOn: [targetReader]
}

output endpoint string = '${runtime.outputs.url}/mcp'
output baseUrl string = runtime.outputs.url
output serverAppClientId string = serverApp.outputs.clientId
output serverAppObjectId string = serverApp.outputs.objectId
output serverAppScope string = serverApp.outputs.scopeValue
output managedIdentityClientId string = identity.outputs.clientId
output managedIdentityPrincipalId string = identity.outputs.principalId
output readerRoleAssignmentId string = targetReader.outputs.id
output imageReference string = imageReference
output namespaces array = namespaces
output runtimeArgs array = runtime.outputs.args
