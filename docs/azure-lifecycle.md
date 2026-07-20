# Azure lab lifecycle workflow

The manual `Azure lab lifecycle` workflow turns the statically validated Bicep into a controlled Azure execution path. It does not run on pushes or pull requests and never deploys merely because code was merged.

## Required GitHub environment

Create a protected environment named `azure-lab` and provide:

- `AZURE_CLIENT_ID`;
- `AZURE_TENANT_ID`;
- `AZURE_SUBSCRIPTION_ID`;
- `COLLECTOR_ADMIN_SSH_PUBLIC_KEY`.

The Azure identity should receive only the permissions needed on the dedicated ServiceTracer resource group.

## Operations

### `what-if`

Creates the dedicated resource group when needed, validates the template, and records Azure What-If output. It requires a tested 40-character ServiceTracer commit SHA and the SSH public key because it evaluates the same enabled-collector parameters used by deployment.

### `deploy`

Runs validation and What-If first, deploys with `deployOperationsCollector=true`, and invokes guest verification through Azure VM Run Command.

Verification checks the private NIC, absence of a public IP, system-assigned identity, evidence-disk detach behavior, disabled public disk access, cloud-init completion, mounted evidence filesystem, active collector service, authenticated durable receipt, and persistence through a service restart.

### `verify`

Runs the same Azure and guest checks against an existing deployment without redeploying it. Every run uses a unique verification evidence identity.

### `teardown`

Captures the resource inventory and deletes the dedicated resource group. It requires a name beginning with `rg-servicetracer-dev` or `rg-servicetracer-test` and an exact typed confirmation. Resource-group deletion also deletes the evidence disk, so retained evidence must be backed up first.

## Evidence artifacts

Every run uploads non-secret evidence. Depending on the operation, this includes validation and What-If output, deployment output, collector verification, pre-teardown inventory, and deletion confirmation.

Collector tokens, TLS private keys, and SSH private keys are not written to artifacts.

## Current status

The workflow and verification script are implemented and statically tested. They have not yet authenticated to Anthony's Azure subscription or produced real deployment evidence.
