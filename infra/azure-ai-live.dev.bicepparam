using './azure-ai-live.bicep'

param deployAzureAi = false
param resourceGroupName = 'rg-ai-msp-dev-canadaeast'
param location = 'canadaeast'
param accountName = 'oai-msp-aeg30000-dev'
param environment = 'dev'
param deployModel = true
param deploymentName = 'gpt-41-mini-msp-dev'
param modelName = 'gpt-4.1-mini'
param modelVersion = '2025-04-14'
param deploymentSkuName = 'Standard'
param deploymentCapacity = 1
param assignInferenceRole = false
param inferencePrincipalId = ''
param inferencePrincipalType = 'ServicePrincipal'
