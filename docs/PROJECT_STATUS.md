# Project Status

Last updated: 2026-07-18

## Verified

- Repository baseline exists on `main`.
- Work is isolated on `feature/network-foundation`.

## Implemented in code but not yet validated

- AzureRM provider configuration.
- Resource group.
- Virtual network with management and server subnets.
- Subnet-level network security groups and associations.
- Management-to-server SSH and RDP allow rules.
- Explicit denial of other intra-VNet inbound traffic to the server subnet.
- Common tags and Terraform outputs.
- PowerShell verification script.
- GitHub Actions formatting and validation workflow.

## Deployed

Nothing has been deployed.

## Behaviour verified against Azure

Nothing has been verified against Azure.

## Known gaps

- `terraform fmt`, `terraform init`, and `terraform validate` have not yet been run.
- No Terraform plan has been reviewed.
- No Azure authentication has been performed for this repository.
- No remote state backend exists.
- No workloads, monitoring, backup, or recovery tests exist.
- NSG behaviour has not been tested with live endpoints.

## Current bounded objective

Validate the Terraform configuration, review the plan, deploy the network foundation, verify the two subnet-to-NSG associations, record evidence, and destroy the resources cleanly.

## Merge gate

Do not merge this branch until:

1. formatting passes;
2. initialization succeeds;
3. validation succeeds;
4. the Terraform plan is understood and contains no unintended resources;
5. deployment verification passes;
6. teardown is confirmed;
7. this status document is updated with actual evidence.
