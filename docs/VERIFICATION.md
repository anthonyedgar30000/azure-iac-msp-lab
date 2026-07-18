# Verification Plan

This document separates static validation, deployment verification, behaviour testing, and teardown evidence.

## 1. Static validation

Run from the repository root:

```powershell
terraform fmt -check -recursive
terraform init -backend=false -input=false
terraform validate
```

Expected result: all commands exit successfully. This proves only that the local configuration is formatted, providers can initialize, and Terraform accepts the configuration syntax and references.

## 2. Plan review

Authenticate to Azure, create a local `terraform.tfvars` from the sanitized example, and run:

```powershell
az login
az account set --subscription <subscription-id>
terraform plan -out network-foundation.tfplan
terraform show network-foundation.tfplan
```

Review the plan for:

- one resource group;
- one virtual network;
- two subnets;
- two network security groups;
- two subnet-to-NSG associations;
- no public IP addresses;
- no compute resources;
- no unexpected replacements or deletions.

Do not commit the plan file or local variable file.

## 3. Apply and resource verification

```powershell
terraform apply network-foundation.tfplan
./scripts/verify.ps1 -Deployed
```

Capture the Terraform apply summary and the verification script output. Record resource names without exposing sensitive subscription or tenant information.

## 4. Behaviour verification

Live NSG behaviour requires test endpoints and is outside the current network-only increment. When workloads are added, verify both expected-allow and expected-deny paths:

- management subnet to server subnet on TCP 22: expected allow;
- management subnet to server subnet on TCP 3389: expected allow;
- management subnet to server subnet on an unapproved port: expected deny;
- server subnet initiating a new connection to the management subnet: expected deny;
- established-session return traffic: expected allow because NSGs are stateful.

Do not mark these behaviours verified until packet-level or connection-test evidence exists.

## 5. Teardown verification

```powershell
terraform plan -destroy
terraform destroy
az group exists --name <resource-group-name>
```

Expected result: Terraform reports successful destruction and Azure returns `false` for the resource-group existence check.

## Evidence record

For every run, record:

- date and branch;
- commit SHA;
- Terraform and provider versions;
- commands executed;
- pass or fail result;
- unexpected behaviour;
- corrective action;
- sanitized screenshots or terminal output.
