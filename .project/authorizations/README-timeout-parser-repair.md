# Timeout parser repair authorization boundary

The prepared deployment workflow is intentionally inert.

It may run only after a separate, explicit human grant is encoded at:

`.project/authorizations/servicetracer-demo-api-timeout-fix-deployment-after-parser-fix-20260725.json`

That future marker must bind one exact commit on `fix/timeout-vm-instance-view-preflight`, identify workflow run `30136642571` attempt `3` as the consumed preflight failure, preserve `azure_mutation_performed = false`, and keep transaction replay, RBAC mutation, network mutation, cleanup, publication, and pull-request merge unauthorized.

Repository merge or green CI does not create that grant.
