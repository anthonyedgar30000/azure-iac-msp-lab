# Demo backends and frontend API

## Purpose

Deploy only the synthetic remote-access service path needed by the interactive ServiceTracer demo:

```text
GitHub Pages frontend
→ Azure Function demo API
→ Azure public Load Balancer TCP 443
→ VPN-01 healthy listener / VPN-02 simulated RADIUS-timeout listener
```

This workstream deliberately excludes the existing operations collector and the public-report publication path.

```text
demo_backends_and_api
!= collector_replacement
!= report_publication
!= full_lab_lifecycle_deploy
```

## Existing dependencies

The scoped template requires these existing resources in `rg-servicetracer-dev-westus2`:

- `vnet-onprem-sim-mst-dev` and `snet-edge`;
- `lb-remote-access-mst-dev` with backend pool `be-vpn-gateways`;
- `pip-remote-access-mst-dev`;
- `law-mst-dev`.

The workflow fails before mutation when any dependency is absent or in the wrong region.

## Resources created

The scoped Bicep entrypoint creates:

- availability set `avset-vpn-mst-dev`;
- two `Standard_B1s` backend VMs, NICs, and OS disks;
- backend listener systemd services created by the existing cloud-init contract;
- one Linux Consumption Function App;
- one Dynamic `Y1` hosting plan;
- one Standard LRS Function runtime Storage account;
- one workspace-based Application Insights component.

It does not declare or modify the collector VM, its NIC/disks, report Storage, publication RBAC, the VNet, load balancer, public IP, or Log Analytics workspace.

## Listener and API contract

Both backend VMs expose HTTPS on port `443`:

- `GET /healthz` confirms the listener is available;
- `GET /transaction?correlation_id=<uuid>` returns a bounded transaction record.

`VPN-01` returns a successful synthetic transaction. `VPN-02` returns HTTP `503` with a simulated `radius_response_timeout` boundary. The load-balancer health probe is intentionally shallow TCP, so both listeners remain healthy while user-function behavior differs.

The Function App exposes:

```text
GET  /api/health
POST /api/demo/run
```

Request:

```json
{
  "attempts": 20
}
```

`attempts` is constrained to 2–50. The caller cannot supply a target URL. The Function makes a new correlated request for each attempt, preserves expected HTTP `503` response bodies, aggregates per-backend success/failure rates, and returns `servicetracer.demo-api-response.v1`.

The backend VMs use short-lived self-signed certificates. The Function disables certificate verification only for this fixed synthetic target. The browser communicates with the Azure Function hostname using platform TLS.

## Frontend behavior

`docs/report-source.json` contains the default Function URL. The frontend also accepts:

```text
?api=https://<function-host>/api/demo/run
```

When the API is healthy, **Run incident analysis** calls it and renders actual correlated Azure transactions. When unavailable, the committed fixture remains usable and the UI records the fallback.

## Repository verification

```bash
python .project/validate.py
python -m unittest discover -s infra/tests -v
az bicep lint --file infra/demo-backend-api.bicep
az bicep build --file infra/demo-backend-api.bicep --outfile /tmp/demo-backend-api.json
```

## What-If and deployment

Use **Actions → Demo backends and API** with the exact merged commit.

Planning confirmation:

```text
DEMO-BACKEND-API:what-if:rg-servicetracer-dev-westus2:func-st-demo-mst-dev-aeg30000
```

Deployment confirmation, after separate Azure-mutation authorization:

```text
DEMO-BACKEND-API:deploy:rg-servicetracer-dev-westus2:func-st-demo-mst-dev-aeg30000
```

The classifier rejects `Modify`, `Delete`, and `Replace`, unexpected create types, and any attempted change to the existing VNet, load balancer, public IP, Log Analytics workspace, or collector VM.

The deployment workflow performs validation and What-If first, deploys only `infra/demo-backend-api.bicep`, ZIP-deploys the Python Function with remote build, then verifies both backend outcomes through the public API.

## Cost implications

Two continuously running `Standard_B1s` Linux VMs dominate recurring cost. The Function uses Consumption hosting, its runtime Storage is Standard LRS, and Application Insights uses the existing capped Log Analytics workspace.

Before deployment, capture current West US 2 CAD pricing for the VMs, Function usage beyond any applicable grant, Storage, and telemetry ingestion.

```text
retail_estimate != actual_cost
student_credit_available != zero_cost
```

## Expected evidence

- both backend VMs provisioned successfully;
- Function `/api/health` returns `healthy`;
- a 20-attempt run observes both `VPN-01` and `VPN-02`;
- at least one successful and one failed transaction;
- `VPN-02` has the higher failure rate;
- `exact_root_cause_claimed` remains `false`;
- GitHub Pages renders the live API result.

```text
resource_created
!= listener_verified
listener_verified
!= api_verified
api_verified
!= frontend_verified
```

## Failure, rollback, and cleanup

If Bicep succeeds but Function deployment or API verification fails, preserve the evidence artifact before cleanup. Do not alter the collector or report-publication resources.

Repository rollback is reverting the scoped PR.

Azure cleanup uses deployment outputs:

```bash
RG=rg-servicetracer-dev-westus2
DEPLOYMENT=demo-backend-api-dev
az deployment group show -g "$RG" -n "$DEPLOYMENT" --query properties.outputs -o json > /tmp/demo-api-outputs.json

az functionapp delete -g "$RG" -n "$(jq -r '.functionAppName.value' /tmp/demo-api-outputs.json)"
az appservice plan delete -g "$RG" -n "$(jq -r '.functionPlanName.value' /tmp/demo-api-outputs.json)" --yes
az storage account delete -g "$RG" -n "$(jq -r '.functionStorageAccountName.value' /tmp/demo-api-outputs.json)" --yes
az monitor app-insights component delete -g "$RG" --app "$(jq -r '.applicationInsightsName.value' /tmp/demo-api-outputs.json)"
az vm delete -g "$RG" -n vm-vpn01-mst-dev --yes
az vm delete -g "$RG" -n vm-vpn02-mst-dev --yes
az network nic delete -g "$RG" -n nic-vpn01-mst-dev
az network nic delete -g "$RG" -n nic-vpn02-mst-dev
az vm availability-set delete -g "$RG" -n avset-vpn-mst-dev
```

Confirm matching backend OS disks are gone. Then prove the shared VNet, load balancer, public IP, Log Analytics workspace, collector, and report-publication resources are unchanged.
