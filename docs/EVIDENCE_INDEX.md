# Evidence Index

No deployment evidence exists yet.

Use this index to prevent screenshots from being mistaken for verified capability.

| ID | Evidence | Status | Source | What it proves | What it does not prove |
|---|---|---|---|---|---|
| E-001 | Repository and branch structure | Available | GitHub | Work is version controlled and isolated from `main` | Terraform validity or Azure deployment |
| E-002 | Terraform formatting output | Pending | Local or CI run | Files satisfy Terraform formatting rules | Provider initialization or deployability |
| E-003 | Terraform validation output | Pending | Local or CI run | Terraform accepts the configuration syntax and references | Azure permissions or runtime behaviour |
| E-004 | Saved plan review | Pending | Terraform CLI | Intended resource changes before apply | Successful deployment |
| E-005 | Apply summary | Pending | Terraform CLI | Azure accepted the planned resource creation | Security-path behaviour |
| E-006 | Azure resource verification | Pending | PowerShell and Azure CLI | Expected resource group, VNet, subnets, and NSG associations exist | End-to-end connectivity policy behaviour |
| E-007 | Expected-allow connection tests | Out of current scope | Future workload increment | Approved management paths work | Deny paths |
| E-008 | Expected-deny connection tests | Out of current scope | Future workload increment | Segmentation blocks unapproved paths | Every possible attack path |
| E-009 | Destroy and absence check | Pending | Terraform and Azure CLI | The lab can be removed and the resource group is absent | Immediate final billing settlement |

## Screenshot rules

- Capture only evidence tied to a command, test, or resource relationship.
- Redact subscription IDs, tenant IDs, public addresses, credentials, and personal data.
- Include the date, branch, and commit SHA in the caption.
- Explain what the image proves and its limits.
- Do not label a portal screenshot as verification unless an independent check supports it.
