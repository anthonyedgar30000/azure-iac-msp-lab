# Azure IaC MSP Lab

A version-controlled Azure infrastructure-as-code portfolio lab for demonstrating practical MSP, systems administration, cloud infrastructure, and security skills.

## Current scope

The first bounded increment defines:

- one Azure resource group;
- one virtual network;
- one management subnet;
- one server subnet;
- subnet-level network security groups;
- explicit management-to-server SSH and RDP rules;
- explicit denial of other intra-VNet inbound traffic to the server subnet;
- tagging, outputs, validation automation, and a verification script.

No infrastructure has been deployed or verified yet. See [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) for the authoritative status.

## Repository layout

```text
.
├── .github/workflows/terraform-checks.yml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── COST_CONTROLS.md
│   ├── EVIDENCE_INDEX.md
│   ├── PROJECT_STATUS.md
│   └── VERIFICATION.md
├── scripts/verify.ps1
├── locals.tf
├── network.tf
├── outputs.tf
├── providers.tf
├── terraform.tfvars.example
├── variables.tf
└── versions.tf
```

## Local workflow

Prerequisites:

- Terraform CLI;
- Azure CLI for planning, deployment, and Azure-side verification;
- an Azure subscription you are authorized to use.

Create a local variable file:

```powershell
Copy-Item terraform.tfvars.example terraform.tfvars
```

Replace the placeholder subscription ID locally, then run static checks:

```powershell
./scripts/verify.ps1
```

After authenticating to Azure, review a saved plan before applying:

```powershell
az login
terraform plan -out network-foundation.tfplan
terraform show network-foundation.tfplan
terraform apply network-foundation.tfplan
./scripts/verify.ps1 -Deployed
```

Destroy the lab after collecting sanitized evidence:

```powershell
terraform destroy
```

## Governance

- `main` is the trusted baseline.
- Changes are developed in bounded feature branches.
- Pull requests must distinguish proposed, implemented, deployed, verified, and unresolved work.
- Do not commit Terraform state, saved plans, credentials, real identifiers, or sensitive screenshots.
- A portal screenshot alone is not treated as proof of behaviour.

## Status vocabulary

- **Proposed:** discussed or documented, but not coded.
- **Implemented:** present in code, but not necessarily executable.
- **Validated:** static checks passed.
- **Planned:** a Terraform plan was generated and reviewed.
- **Deployed:** Azure accepted the apply.
- **Verified:** an independent check proved the expected resource or behaviour.
- **Unresolved:** failed, ambiguous, or incomplete work that remains open.
