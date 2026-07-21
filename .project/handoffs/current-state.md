# Current project handoff

## Trusted baseline

- Branch: `main`
- Baseline commit when this handoff was created: `09d0b2eaccb95a29185a8dd6cef57c7fef281b8d`
- Latest completed increment: PR #18, planner runtime repair

## Recently merged

- PR #12: managed-identity public-report publishing and ServiceTracer `0.5.0` implementation.
- PR #14: real Azure load-balancer backend proof architecture and live evidence workflow.
- PRs #15–#18: bounded VM candidate selection, read-only What-If correction, ARM-as-authority planning, and Bash planner runtime repairs.

## Runtime state

- The working collector VM size is `Standard_B1ms`.
- The currently verified collector is ServiceTracer `0.4.0` with manual runtime repairs.
- The corrected Ubuntu 24.04 collector definition and ServiceTracer `0.5.0` path are in `main`, but replacement deployment has not been operationally verified.
- The public report endpoint and backend proof are implemented, but their successful Azure deployment is not recorded here.
- A new read-only What-If run is required after PR #18 to verify the planner fixes against Azure.

## Current bounded work

Branch `feature/workflow-observability` owns only the shared project-state layer. It must not modify the Azure planner, ServiceTracer analysis logic, or live-report implementation.

## Next authorized action

Open and review the workflow-observability pull request. After merge, every conversation should read `.project/` before starting or resuming implementation.
