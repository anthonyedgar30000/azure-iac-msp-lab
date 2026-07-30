# Azure AI go-live run 8 — trigger synchronization

## Synchronized result

```text
source instruction: Sync
activation PR: #237
activation merge: 798486cb9e7c20fcf7fe508314317605dd4100ba
latest main observed: 8387c44aa4b82ae77cf32f53053187488d13d6ba
open pull requests observed: none
run-8 activation trigger observed: true
run-8 authorization consumed: true
run-8 terminal workflow result retrieved: false
fresh Azure terminal state established: false
```

The merge that introduced `.github/workflows/azure-ai-go-live-run8.yml` is the exact activation trigger named by the run-8 request. The one-shot authority is therefore no longer active.

## Proven repository state

Before merge, both required validation workflows succeeded:

```text
Azure AI activation static validation: run 30510551447 — success
repository CI: run 30510551439 — success
candidate head: c6b95f799f467da95adeb4ed0e815ccd5501171f
```

The activation candidate preserved the historical run-7 executor, pinned its Git blob, repaired exactly three invalid scoped `--all` combinations, retained the unscoped principal-discovery fallback, and remained bounded to one deployment, one hardening update, and one Entra-authenticated model request.

## Evidence boundary

The connected GitHub workflow lookup available during this synchronization returns pull-request-triggered workflow runs associated with a commit. It did not return the push-triggered run-8 execution.

That means:

```text
push run not retrieved != push run did not occur
merge trigger observed != workflow succeeded
workflow outcome unknown != Azure state unchanged
```

No terminal claim is made about:

- direct role verification;
- model listing or capacity;
- ARM What-If;
- deployment creation or reconciliation;
- account local-authentication hardening;
- model inference;
- token consumption;
- Azure cost delta.

## Selector action

`.project/CURRENT.json` must:

```text
clear active_azure_ai_activation_authorization
retain run 7 as latest verified Azure AI terminal reconciliation
select this synchronization as the latest operational overlay
mark run 8 terminal reconciliation as pending
```

## Next safe gate

Retrieve the protected run-8 artifact or perform fresh read-only Azure observations, then write a terminal reconciliation. Do not use GitHub **Re-run**. Any later Azure attempt requires fresh explicit authority.
