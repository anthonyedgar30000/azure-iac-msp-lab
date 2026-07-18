# Architecture

## Purpose

This repository is a compact Azure infrastructure-as-code demonstration for MSP, systems administration, cloud infrastructure, platform engineering, and security roles.

## Current bounded scope

The first increment defines a low-cost Azure network foundation:

```text
Resource group
└── Virtual network: 10.20.0.0/16
    ├── Management subnet: 10.20.10.0/24
    │   └── Management NSG
    └── Server subnet: 10.20.20.0/24
        └── Server NSG
```

The server subnet permits SSH and RDP initiated from the management subnet, then denies other inbound traffic sourced from the virtual network. The management subnet denies new inbound traffic initiated from the server subnet. Azure NSGs are stateful, so permitted session return traffic is not treated as a new connection.

## Design principles

- Infrastructure is declared in Terraform and reviewed through Git.
- `main` remains the trusted baseline.
- Each branch addresses one bounded change.
- Network segmentation is explicit rather than relying only on Azure defaults.
- No public IP address, VM, bastion, gateway, or paid monitoring service is included in this increment.
- Tags record project, environment, owner, purpose, and management method.
- Secrets, credentials, state files, and real subscription identifiers are excluded from Git.
- A capability is not called deployed or verified until execution evidence exists.

## Planned increments

These are proposals, not implemented capabilities:

1. Remote Terraform state with locking and controlled access.
2. Secure administrative access without exposing management ports directly to the internet.
3. Windows Server and Linux workloads.
4. Azure Monitor and centralized logging.
5. Backup policy and restore verification.
6. Hybrid integration with a later Proxmox environment and Raspberry Pi infrastructure node.
