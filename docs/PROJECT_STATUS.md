# Project Status

Last updated: 2026-07-18

## Verified

- Repository baseline exists on `main`.
- Work is isolated on `feature/network-foundation`.
- GitHub Actions run 5 passed on commit `7907a78ea3e28ec9342d3425c3ac1b656ff40f5f`.
- `terraform fmt -check -recursive -diff` passed.
- `terraform init -backend=false -input=false` passed in CI.
- `terraform validate` passed in CI.

## Implemented and statically validated

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

- No Terraform plan has been generated or reviewed against an authenticated Azure subscription.
- No Azure authentication has been performed for this repository.
- The provider dependency lock file has not yet been committed from a persistent execution environment.
- No remote state backend exists.
- No workloads, monitoring, backup, or recovery tests exist.
- NSG behaviour has not been tested with live endpoints.

## Current bounded objective

Authenticate from the approved execution workstation, generate and review the Terraform plan, deploy the network foundation, verify the two subnet-to-NSG associations, record evidence, and destroy the resources cleanly.

## Merge gate

Do not merge this branch until:

1. formatting passes — complete;
2. initialization succeeds — complete in CI;
3. validation succeeds — complete in CI;
4. the provider lock file is committed;
5. the Terraform plan is understood and contains no unintended resources;
6. deployment verification passes;
7. teardown is confirmed;
8. this status document is updated with actual execution evidence.
