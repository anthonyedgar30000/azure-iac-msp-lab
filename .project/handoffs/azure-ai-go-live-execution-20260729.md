# Azure AI go-live execution handoff

```text
base main: 375255c6bca57f672a326915e5a18708de3eaaad
branch: agent/azure-ai-go-live-v1
separate read-only preflight: removed
execution trigger: first merge introducing .github/workflows/azure-ai-live-deploy.yml
```

Authorized execution:

- GitHub OIDC authentication to the configured Azure subscription;
- bounded live checks within the same deployment run;
- Microsoft.CognitiveServices registration if required;
- subscription What-If;
- first viable candidate deployment in Canada East or East US 2;
- exact OpenAI User role assignment to the workflow principal;
- one non-sensitive 32-output-token response request;
- protected evidence capture.

Not authorized:

- manual rerun;
- broader model or region search;
- private endpoint deployment;
- Azure MCP connection;
- rollback or cleanup.

Success is established only by `go-live-summary.json` with
`status=live_verified`, accompanied by account, model, RBAC, model-call, and
manifest evidence.
