# Cost Controls

## Current increment

The current code defines networking resources only. It intentionally excludes virtual machines, public IP addresses, gateways, bastion services, paid monitoring tiers, and backup services.

Azure pricing and free-service treatment can change, so cost must be checked in the Azure pricing calculator and subscription cost analysis before each new increment.

## Required controls before adding paid resources

- Define a maximum monthly lab budget.
- Configure Azure budget alerts before deploying compute.
- Use explicit low-cost SKUs.
- Enable automatic shutdown for temporary virtual machines.
- Tag every resource with project, environment, owner, purpose, and management method.
- Prefer short-lived deployments that can be recreated from Terraform.
- Destroy resources immediately after evidence collection unless persistence is justified.
- Review the Terraform plan for unplanned paid services.
- Check Azure Cost Management after deployment and after teardown.

## Prohibited repository content

Never commit:

- real subscription or tenant identifiers;
- credentials, tokens, certificates, or private keys;
- Terraform state;
- saved plan files;
- unredacted screenshots containing sensitive identifiers;
- billing exports or account details.

## Teardown standard

A successful `terraform destroy` is not enough by itself. Confirm that the resource group no longer exists and review Azure Cost Management for delayed or orphaned charges.
