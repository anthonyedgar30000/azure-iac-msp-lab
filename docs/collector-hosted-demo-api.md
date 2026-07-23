# Collector-hosted demo API

## Decision

The live demo API is hosted on the existing ServiceTracer collector VM rather than on Microsoft.Web/App Service.

The Azure for Students subscription has a verified Microsoft.Web regional quota limit of zero in West US 2, and the quota increase request was denied. The design therefore removes Microsoft.Web from the active deployment path instead of searching for another entitlement.

```text
available_student_credit != service_entitlement
App_Service_quota_denied != collector_VM_unavailable
platform_boundary_observed -> architecture_changed
```

## Architecture

```text
GitHub Pages
  -> trusted HTTPS
  -> dedicated Standard public IP and Azure DNS label
  -> operations-subnet NSG ports 80/443 only
  -> Nginx rate limit and TLS termination
  -> loopback-only Python API on 127.0.0.1:8090
  -> existing remote-access load balancer transaction endpoint
  -> VPN-01 / VPN-02 synthetic backends
```

The existing ServiceTracer collector remains private on port 8080 and is not exposed through the public API endpoint.

## Security controls

- The API process runs as the existing unprivileged `servicetracer` system account.
- The Python listener binds only to loopback.
- Nginx is the only public listener and permits only `/api/` routes.
- Requests are rate limited and request bodies are capped at 4 KiB.
- CORS permits only the declared GitHub Pages origin.
- TLS uses a publicly trusted certificate issued for the Azure public-IP DNS name.
- The systemd unit enables `NoNewPrivileges`, filesystem protection, private temporary storage, device isolation, and kernel hardening.
- The API target is fixed by deployment configuration; callers cannot supply arbitrary destination URLs.

## Deployment gate

Use `.github/workflows/collector-demo-api.yml` with an exact reviewed commit.

The `what-if` operation must complete before `deploy`. Its classifier permits only:

- the dedicated demo API public IP;
- two bounded NSG security rules;
- the collector demo API VM extension;
- the collector NIC change that attaches the exact dedicated public IP.

Any Microsoft.Web resource, collector VM modification, unrelated network modification, deletion, or replacement is blocking.

## Validation

The workflow verifies:

- Azure subscription, tenant, resource group, collector VM, NIC, NSG, and prior deployment parameters;
- public-IP quota headroom or an already-existing dedicated public IP;
- absence of a read-only resource-group lock;
- exact ARM validation and What-If;
- trusted public TLS;
- API health;
- twenty correlated transactions;
- bounded investigation semantics;
- CORS response headers.

## Rollback

1. Stop and disable `servicetracer-demo-api.service` and Nginx configuration on the collector.
2. Detach and remove `pip-st-demo-api-<prefix>-<environment>`.
3. Remove the two demo API NSG rules.
4. Remove the `servicetracer-demo-api` VM extension.
5. Restore `docs/report-source.json` to an empty live API URL or a previously verified endpoint.

The failed App Service attempt may have left storage or Application Insights resources. Those are inspected and cleaned up under a separate, explicit deletion decision; this deployment does not delete them automatically.
