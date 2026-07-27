# Collector provenance deployment run 19 — failure review and restart repair

## Decision

Run `30224770178` is classified as a **failed-closed deployment attempt caused by a repository service-lifecycle defect**. The one-shot grant is consumed and is not reused.

## Evidence

```text
source: 1677606ded960c951fa37f0fdbfae50ba4b3cc34
job: 89853061733
artifact: 8638260753
digest: sha256:3cd4993461de1545bc52885bbf8118d74f861d651f5aac692e4e06e4b3f16fab
manifest: 44/44 verified
What-If: 24 Ignore / 3 Modify / 3 NoChange / 0 Create/Delete/Replace
```

The load balancer and backend pool succeeded. The CustomScript extension failed after copying the reviewed source, configuring nginx and retaining TLS. The terminal installer message was:

```text
Azure host identity was not verified: {}
```

## Root cause

The installer writes new Python files, environment variables and a systemd unit. It then used:

```bash
systemctl enable --now "$SERVICE_NAME"
```

That command starts an inactive unit but does not restart an already-running process. The validation request therefore reached the pre-provenance process and could not observe `azure_host`.

## Repair

The repository now requires:

```bash
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"
systemctl is-active --quiet "$SERVICE_NAME"
```

The restart occurs after application, environment and unit replacement and before public health validation.

## Failure and rollback boundary

No automatic retry or rollback is authorized. The existing public process state after run 19 is not freshly verified. The repair must pass exact-head CI, then a fresh read-only Azure preflight and What-If must precede any new deployment grant.

```text
repository_repair != Azure_repair
extension_failed != load_balancer_failed
files_replaced != process_restarted
failed_attempt != retry_authority
```
