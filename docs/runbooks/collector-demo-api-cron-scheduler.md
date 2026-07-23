# Collector Demo API Cron Scheduler

## Purpose

Run the bounded collector-hosted demo API `what-if` workflow from a Linux lab VM, preserve raw and sanitized evidence, evaluate the result through the existing Governed Persistence Loop controller, and stop at every human authority gate.

```text
cron
→ non-blocking lock
→ exact-commit check
→ dispatch read-only What-If
→ poll workflow state
→ download exact run artifact
→ verify hashes, provenance, readiness, and scope
→ evaluate next typed control message
→ stop at human gate
```

This scheduler never selects `deploy` and contains no Azure CLI commands.

```text
scheduler_can_dispatch_what_if
!= scheduler_can_authorize_deployment
!= scheduler_can_mutate_Azure
```

## Scope

The scheduler is limited to:

- repository `anthonyedgar30000/azure-iac-msp-lab`;
- workflow `.github/workflows/collector-demo-api.yml`;
- operation `what-if`;
- one exact reviewed commit that must equal current `main`;
- resource group `rg-servicetracer-dev-westus2` in `westus2`;
- environment `dev`, prefix `mst`;
- DNS label `st-demo-api-aeg30000`;
- browser origin `https://anthonyedgar30000.github.io`.

Changing any of those values requires updating the root-owned scheduler configuration and reviewing the new exact commit.

## Architecture and dependencies

Host requirements:

- an existing Linux VM in the lab;
- synchronized UTC time;
- outbound HTTPS access to GitHub;
- `gh`, `jq`, Python 3, `flock`, `sha256sum`, and standard core utilities;
- a checked-out copy of this repository at `/opt/azure-iac-msp-lab/current`;
- a dedicated non-root account named `prs-scheduler`.

The scheduler has no Azure credential. Azure authentication remains inside the protected `azure-lab` GitHub environment through the workflow's existing OIDC configuration.

## GitHub identity

Use a repository-scoped fine-grained token for this lab adapter. It needs only:

- **Actions: read and write**, because workflow dispatch is an Actions write operation and run/artifact inspection is read;
- **Contents: read**, to resolve the pinned commit and workflow file;
- repository access limited to `anthonyedgar30000/azure-iac-msp-lab`.

Do not grant Issues, Pull requests, Administration, Secrets, Environments, Packages, or Contents write permissions.

Store the token outside the repository:

```bash
sudo install -d -m 0750 -o root -g prs-scheduler /etc/azure-iac-msp-lab/secrets
sudo install -m 0640 -o root -g prs-scheduler /dev/null \
  /etc/azure-iac-msp-lab/secrets/github-actions-dispatch.token
sudoedit /etc/azure-iac-msp-lab/secrets/github-actions-dispatch.token
```

The token file must contain only the token and must not be world-readable.

## Installation

Create the service account and operational paths:

```bash
sudo useradd --system --home-dir /var/lib/azure-iac-msp-lab \
  --create-home --shell /usr/sbin/nologin prs-scheduler
sudo install -d -m 0750 -o prs-scheduler -g prs-scheduler \
  /var/lib/azure-iac-msp-lab/scheduler/collector-demo-api \
  /var/lib/azure-iac-msp-lab/evidence/raw/collector-demo-api \
  /var/lib/azure-iac-msp-lab/evidence/sanitized/collector-demo-api \
  /var/log/azure-iac-msp-lab
```

Install and pin the repository checkout. Replace `<reviewed-commit>` with the exact merged commit being authorized for the What-If:

```bash
sudo install -d -m 0755 /opt/azure-iac-msp-lab
sudo git clone https://github.com/anthonyedgar30000/azure-iac-msp-lab.git \
  /opt/azure-iac-msp-lab/current
sudo git -C /opt/azure-iac-msp-lab/current fetch --prune origin
sudo git -C /opt/azure-iac-msp-lab/current checkout --detach <reviewed-commit>
sudo chown -R root:root /opt/azure-iac-msp-lab/current
sudo chmod -R a-w /opt/azure-iac-msp-lab/current
```

Install the non-secret configuration:

```bash
sudo install -d -m 0750 -o root -g prs-scheduler /etc/azure-iac-msp-lab
sudo install -m 0640 -o root -g prs-scheduler \
  /opt/azure-iac-msp-lab/current/ops/cron/collector-demo-api-scheduler.env.example \
  /etc/azure-iac-msp-lab/collector-demo-api-scheduler.env
sudoedit /etc/azure-iac-msp-lab/collector-demo-api-scheduler.env
```

Set `REVIEWED_COMMIT` to the exact reviewed 40-character SHA. The runner queries `main` and fails with `sync_with_reality` when the two differ.

Install the cron entry for `prs-scheduler` using the example in `ops/cron/collector-demo-api-what-if.cron.example`.

## Execution behavior

Each cron cycle:

1. acquires a non-blocking `flock`;
2. confirms the configured commit still equals current `main`;
3. suppresses duplicate dispatches for a commit already awaiting a human gate;
4. dispatches only `operation=what-if`;
5. identifies the new workflow run by exact head SHA and dispatch timestamp;
6. polls with `gh run view` rather than blindly rerunning jobs;
7. downloads only the matching `collector-demo-api-<run-id>-*` artifact;
8. verifies SHA-256 evidence, run ID, commit, request authority, readiness, ARM validation, and accepted isolated What-If classification;
9. passes the artifact to `governed_persistence.py`;
10. records the recommended control message and stops.

An accepted plan should produce:

```json
{
  "next_control_message": "proceed",
  "recommended_next_operation": "deploy",
  "human_gate_required": "explicit_deploy_authorization",
  "authority_effects": {
    "azure_mutation_authorized": false,
    "workflow_dispatch_authorized": false,
    "automatic_execution_authorized": false
  }
}
```

The scheduler does not act on that deployment recommendation.

## Retry behavior

The default retry budget is one additional read-only attempt. A retry is permitted only when the persistence controller returns:

```text
next_control_message = sync_with_reality
recommended_next_operation = what-if
```

`fix`, `restrategize`, `escalate`, `proceed`, `complete`, any human gate, or a terminal state stops automatic dispatches for that commit.

## Evidence

Raw evidence is private operational material:

```text
/var/lib/azure-iac-msp-lab/evidence/raw/collector-demo-api/<run-id>/
```

Sanitized decision evidence contains only scheduler verification and control transitions:

```text
/var/lib/azure-iac-msp-lab/evidence/sanitized/collector-demo-api/<run-id>/
```

Current scheduler state:

```text
/var/lib/azure-iac-msp-lab/scheduler/collector-demo-api/state.json
/var/lib/azure-iac-msp-lab/scheduler/collector-demo-api/latest-transition.json
```

Operational messages are sent to journald with tag `collector-demo-api-scheduler` and may also be appended to the configured cron log.

## Validation

Repository checks:

```bash
bash -n infra/scripts/run_collector_demo_api_what_if_cycle.sh
python3 -m unittest infra.tests.test_collector_demo_api_scheduler -v
```

Host preflight:

```bash
sudo -u prs-scheduler test -r \
  /etc/azure-iac-msp-lab/collector-demo-api-scheduler.env
sudo -u prs-scheduler test -r \
  /etc/azure-iac-msp-lab/secrets/github-actions-dispatch.token
sudo -u prs-scheduler env \
  SCHEDULER_CONFIG=/etc/azure-iac-msp-lab/collector-demo-api-scheduler.env \
  /opt/azure-iac-msp-lab/current/infra/scripts/run_collector_demo_api_what_if_cycle.sh
```

After execution, verify that the recorded request says `operation: what-if` and `azure_mutations_authorized: false`, and that no deploy or verification workflow step ran.

## Failure handling

- Lock contention: exit successfully without dispatch.
- Main no longer equals the configured commit: record `sync_with_reality`; do not dispatch.
- Run cannot be identified or completes outside the bounded polling window: escalate.
- Artifact hash, run, commit, or authority mismatch: escalate as an evidence-integrity failure.
- Readiness or What-If failure: use the existing persistence controller's typed recommendation and retry only within the explicit read-only retry rule.
- Accepted What-If: stop at `explicit_deploy_authorization`.

No rollback is required for the scheduler's repository installation because it performs no Azure mutation.

## Decommissioning

1. remove the `prs-scheduler` crontab entry;
2. revoke the GitHub token;
3. archive the sanitized evidence required for the portfolio or audit trail;
4. securely delete the token file and raw evidence according to the lab retention decision;
5. remove the scheduler checkout and service account when no longer needed.

Decommissioning the scheduler must not delete Azure resources or close the deployment decision automatically.
