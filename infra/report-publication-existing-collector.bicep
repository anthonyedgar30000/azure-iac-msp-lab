targetScope = 'resourceGroup'

@description('Short workload prefix used in resource names.')
@minLength(2)
@maxLength(12)
param prefix string = 'mst'

@description('Deployment environment.')
@allowed([
  'dev'
  'test'
])
param environment string = 'dev'

@description('Azure region for the report publication resources.')
param location string = resourceGroup().location

@description('Existing collector system-assigned managed-identity principal ID.')
@minLength(36)
@maxLength(36)
param collectorPrincipalId string

@description('Browser origins permitted to fetch the sanitized public report.')
@minLength(1)
param allowedOrigins array = [
  'https://anthonyedgar30000.github.io'
]

@description('Additional tags merged into the bounded publication resource tags.')
param tags object = {}

var publicationTags = union(tags, {
  workload: 'azure-iac-msp-lab'
  environment: environment
  managedBy: 'bicep'
  purpose: 'servicetracer-live-report'
  changeScope: 'existing-collector-publication-only'
})

module reportPublication './modules/report_publication.bicep' = {
  name: 'existing-collector-report-publication-${environment}'
  params: {
    prefix: prefix
    environment: environment
    location: location
    tags: publicationTags
    collectorPrincipalId: collectorPrincipalId
    allowedOrigins: allowedOrigins
  }
}

output storageAccountName string = reportPublication.outputs.storageAccountName
output staticWebsiteEndpoint string = reportPublication.outputs.staticWebsiteEndpoint
output publicReportUrl string = reportPublication.outputs.publicReportUrl
output collectorWriterRoleAssignmentId string = reportPublication.outputs.collectorWriterRoleAssignmentId
