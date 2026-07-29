# Azure AI go-live run 1 — terminal handoff

## Outcome

```text
workflow run: 30419992872 / attempt 1
exact merge commit: 9298fbcc75801d2ae9b077c62dcf43ca3a4bdad2
conclusion: failure
Azure OIDC login: succeeded
subscription: Azure for Students / Enabled
Microsoft.CognitiveServices final state: Registered
Canada East What-If: failed / InvalidScope
East US 2 What-If: failed / InvalidScope
resource group created: false
Azure OpenAI account created: false
model deployed: false
inference role assigned: false
model request performed: false
endpoint live: false
```

## Root cause

The subscription-scope root passed a conditional resource-group symbolic value
with a null-forgiving operator as the module scope. The compiled deployment
emitted `Microsoft.CognitiveServices/accounts` at subscription scope. Azure
correctly rejected both regional candidates because Cognitive Services accounts
must be deployed at resource-group scope.

The repair candidate uses:

```bicep
resource azureAiResourceGroup 'Microsoft.Resources/resourceGroups@2024-03-01' = if (deployAzureAi) {
  name: resourceGroupName
  location: location
}

module azureAi './modules/azure_ai_openai.bicep' = if (deployAzureAi) {
  scope: resourceGroup(resourceGroupName)
  dependsOn: [
    azureAiResourceGroup
  ]
}
```

## Evidence

```text
artifact ID: 8711582707
artifact digest: sha256:54ff1c8abcd34c0bb27a8f116da94b0421a33365899dc293beee001cff3311f9
terminal reconciliation: .project/reconciliations/azure-ai-go-live-run1-terminal-20260729.json
```

Raw subscription and principal identifiers are not promoted into repository
evidence.

## Authority

The original go-live authority is consumed and terminal. The repair branch and
ordinary CI are allowed, but merge and a second Azure workflow run are not.

```text
failed_run != authorization_to_rerun
repair_candidate_prepared != repair_merged
repair_merged != deployment_authorized
```

No rollback or Azure cleanup is required because What-If stopped before resource
creation.
