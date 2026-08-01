import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import puppeteer from 'puppeteer-core';

function requireCondition(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function lowerCaseHeaders(headers) {
  return Object.fromEntries(
    Object.entries(headers || {}).map(([name, value]) => [name.toLowerCase(), value]),
  );
}

function countBy(items, key) {
  return items.reduce((counts, item) => {
    const value = String(item?.[key] ?? 'UNRESOLVED');
    counts[value] = (counts[value] || 0) + 1;
    return counts;
  }, {});
}

function exactAzureIdentity(identity, expected) {
  return Boolean(
    identity?.verified === true
    && identity?.verification_source === 'azure_instance_metadata_service'
    && identity?.resource_group === expected.resourceGroup
    && identity?.vm_name === expected.vmName
    && identity?.location === expected.location
    && identity?.source_ref === expected.sourceRef
  );
}

const repositoryRoot = process.cwd();
const outputDirectory = process.env.VERIFICATION_OUTPUT_DIR
  || path.join(repositoryRoot, 'servicetracer-external-path-evidence');
const chromePath = process.env.CHROME_PATH;
const frontendUrl = process.env.FRONTEND_URL;
const apiRunUrl = process.env.API_RUN_URL;
const allowedOrigin = process.env.ALLOWED_ORIGIN;
const expected = {
  resourceGroup: process.env.EXPECTED_RESOURCE_GROUP,
  vmName: process.env.EXPECTED_VM_NAME,
  location: process.env.EXPECTED_LOCATION,
  sourceRef: process.env.EXPECTED_SOURCE_REF,
  hostingModel: process.env.EXPECTED_HOSTING_MODEL,
  sourceId: process.env.EXPECTED_SOURCE_ID,
};

for (const [name, value] of Object.entries({
  CHROME_PATH: chromePath,
  FRONTEND_URL: frontendUrl,
  API_RUN_URL: apiRunUrl,
  ALLOWED_ORIGIN: allowedOrigin,
  EXPECTED_RESOURCE_GROUP: expected.resourceGroup,
  EXPECTED_VM_NAME: expected.vmName,
  EXPECTED_LOCATION: expected.location,
  EXPECTED_SOURCE_REF: expected.sourceRef,
  EXPECTED_HOSTING_MODEL: expected.hostingModel,
  EXPECTED_SOURCE_ID: expected.sourceId,
})) {
  requireCondition(value, `${name} is required`);
}

const parsedFrontendUrl = new URL(frontendUrl);
requireCondition(parsedFrontendUrl.origin === allowedOrigin, 'frontend origin does not match allowed origin');
const parsedApiRunUrl = new URL(apiRunUrl);
const healthUrl = new URL(apiRunUrl);
healthUrl.pathname = healthUrl.pathname.replace(/\/api\/demo\/run$/, '/api/health');
healthUrl.search = '';
healthUrl.hash = '';

fs.mkdirSync(outputDirectory, { recursive: true });

const observedResponses = [];
const browserConsole = [];
let browser;

try {
  browser = await puppeteer.launch({
    executablePath: chromePath,
    headless: 'new',
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  });

  const page = await browser.newPage();
  page.setDefaultTimeout(120000);
  page.on('console', (message) => {
    browserConsole.push({ type: message.type(), text: message.text() });
  });
  page.on('pageerror', (error) => {
    browserConsole.push({ type: 'pageerror', text: error.message });
  });
  page.on('response', async (response) => {
    const url = response.url();
    if (url !== apiRunUrl && url !== healthUrl.toString()) {
      return;
    }
    const record = {
      url,
      method: response.request().method(),
      status: response.status(),
      headers: lowerCaseHeaders(response.headers()),
      body: null,
    };
    try {
      const text = await response.text();
      record.body = text ? JSON.parse(text) : null;
    } catch (error) {
      record.body_error = error.message;
    }
    observedResponses.push(record);
  });

  const pageUrl = new URL(frontendUrl);
  pageUrl.searchParams.set('external-path-verification', String(Date.now()));
  await page.goto(pageUrl.toString(), { waitUntil: 'networkidle2', timeout: 120000 });

  await page.waitForFunction(() => {
    const button = document.querySelector('#run-analysis');
    const source = document.querySelector('#report-source-name');
    return button && !button.disabled && source?.textContent === 'Azure demo API — ready';
  });

  const readiness = await page.evaluate(() => ({
    title: document.title,
    sourceName: document.querySelector('#report-source-name')?.textContent || '',
    sourceDetail: document.querySelector('#report-source-detail')?.textContent || '',
    runButton: document.querySelector('#run-analysis')?.textContent || '',
  }));

  await page.click('#run-analysis');
  await page.waitForFunction(() => {
    const text = document.querySelector('#run-analysis')?.textContent || '';
    return text === 'Analysis complete' || text === 'Fixture analysis complete';
  }, { timeout: 120000 });

  const rendered = await page.evaluate(() => ({
    sourceName: document.querySelector('#report-source-name')?.textContent || '',
    sourceDetail: document.querySelector('#report-source-detail')?.textContent || '',
    evidenceSummary: document.querySelector('#evidence-summary')?.textContent || '',
    findingTitle: document.querySelector('.finding-panel h2')?.textContent || '',
    suspect: document.querySelector('#fact-suspect')?.textContent || '',
    comparison: document.querySelector('#fact-healthy')?.textContent || '',
    boundary: document.querySelector('#boundary-backend')?.textContent || '',
    workflowHidden: document.querySelector('#workflow-panel')?.classList.contains('is-hidden') ?? true,
    runButton: document.querySelector('#run-analysis')?.textContent || '',
  }));

  await page.screenshot({
    path: path.join(outputDirectory, 'frontend-external-path.png'),
    fullPage: true,
  });

  const healthResponse = observedResponses.find(
    (item) => item.url === healthUrl.toString() && item.method === 'GET',
  );
  const preflightResponse = observedResponses.find(
    (item) => item.url === apiRunUrl && item.method === 'OPTIONS',
  );
  const runResponse = observedResponses.find(
    (item) => item.url === apiRunUrl && item.method === 'POST',
  );

  requireCondition(healthResponse, 'browser did not observe the API health response');
  requireCondition(healthResponse.status === 200, `health returned HTTP ${healthResponse.status}`);
  requireCondition(healthResponse.headers['access-control-allow-origin'] === allowedOrigin, 'health CORS origin mismatch');
  requireCondition(healthResponse.body?.status === 'healthy', 'health status is not healthy');
  requireCondition(healthResponse.body?.backend_target_configured === true, 'backend target is not configured');
  requireCondition(healthResponse.body?.hosting_model === expected.hostingModel, 'health hosting model mismatch');
  requireCondition(exactAzureIdentity(healthResponse.body?.azure_host, expected), 'health Azure identity mismatch');

  requireCondition(preflightResponse, 'browser did not observe the CORS preflight');
  requireCondition(preflightResponse.status === 204, `preflight returned HTTP ${preflightResponse.status}`);
  requireCondition(preflightResponse.headers['access-control-allow-origin'] === allowedOrigin, 'preflight CORS origin mismatch');
  requireCondition((preflightResponse.headers['access-control-allow-methods'] || '').includes('POST'), 'preflight does not allow POST');
  requireCondition((preflightResponse.headers['access-control-allow-headers'] || '').toLowerCase().includes('x-servicetracer-request-id'), 'preflight does not allow request correlation header');

  requireCondition(runResponse, 'browser did not observe the live transaction response');
  requireCondition(runResponse.status === 200, `transaction returned HTTP ${runResponse.status}`);
  requireCondition(runResponse.headers['access-control-allow-origin'] === allowedOrigin, 'transaction CORS origin mismatch');
  requireCondition((runResponse.headers['access-control-expose-headers'] || '').toLowerCase().includes('x-servicetracer-request-id'), 'transaction does not expose request correlation header');
  requireCondition(runResponse.body?.schema_version === 'servicetracer.demo-api-response.v1', 'transaction response schema mismatch');
  requireCondition(runResponse.body?.hosting_model === expected.hostingModel, 'transaction hosting model mismatch');
  requireCondition(runResponse.body?.source?.id === expected.sourceId, 'transaction source identity mismatch');
  requireCondition(runResponse.body?.source?.transport === 'azure-load-balancer-correlated-transactions', 'transaction transport mismatch');
  requireCondition(exactAzureIdentity(runResponse.body?.azure_host, expected), 'transaction Azure identity mismatch');

  const responseRequestId = runResponse.headers['x-servicetracer-request-id'];
  requireCondition(responseRequestId, 'transaction response header request ID is missing');
  requireCondition(runResponse.body?.request_id === responseRequestId, 'transaction response body and header request IDs differ');

  const transactions = runResponse.body?.transactions;
  requireCondition(Array.isArray(transactions) && transactions.length === 20, 'transaction response must contain exactly 20 attempts');
  requireCondition(runResponse.body?.report?.incident?.attempts === 20, 'incident attempt count mismatch');
  requireCondition(runResponse.body?.report?.investigation_boundary?.exact_root_cause_claimed === false, 'response claimed an unsupported exact root cause');
  requireCondition(rendered.sourceName === 'Azure demo API — live transactions', 'frontend used fixture fallback');
  requireCondition(rendered.runButton === 'Analysis complete', 'frontend did not finish live analysis');
  requireCondition(rendered.evidenceSummary.startsWith('20 correlated transactions:'), 'frontend did not render the 20-attempt result');

  const successes = transactions.filter((item) => item.transaction_status === 'successful').length;
  const failures = transactions.length - successes;
  const transportErrors = transactions.filter((item) => Object.hasOwn(item, 'transport_error')).length;
  const backendCounts = countBy(transactions, 'backend');
  const localization = runResponse.body.report.localization || {};
  const counts = localization.backend_attempt_counts || {};
  const rates = localization.backend_failure_rates || {};
  const suspect = localization.suspect_backend;
  const comparison = localization.healthy_comparison_backend;
  const stable = (
    ['VPN-01', 'VPN-02'].includes(suspect)
    && ['VPN-01', 'VPN-02'].includes(comparison)
    && suspect !== comparison
    && Number(counts['VPN-01'] || 0) > 0
    && Number(counts['VPN-02'] || 0) > 0
    && typeof rates[suspect] === 'number'
    && typeof rates[comparison] === 'number'
    && rates[suspect] > rates[comparison]
  );

  if (stable) {
    requireCondition(rendered.suspect === suspect, 'frontend suspect does not match API evidence');
    requireCondition(rendered.comparison === comparison, 'frontend comparison does not match API evidence');
    requireCondition(rendered.boundary === suspect, 'frontend boundary does not match stable evidence');
    requireCondition(rendered.workflowHidden === false, 'frontend hid the stable technician workflow');
  } else {
    requireCondition(rendered.suspect === 'Not established', 'frontend invented a suspect');
    requireCondition(rendered.comparison === 'Not established', 'frontend invented a comparison');
    requireCondition(rendered.boundary === 'Not established', 'frontend invented an investigation boundary');
    requireCondition(rendered.workflowHidden === true, 'frontend exposed a backend workflow for inconclusive evidence');
    requireCondition(rendered.findingTitle === 'Repeat the bounded sample before localizing', 'inconclusive finding title mismatch');
  }

  fs.writeFileSync(
    path.join(outputDirectory, 'health-response.json'),
    `${JSON.stringify(healthResponse.body, null, 2)}\n`,
  );
  fs.writeFileSync(
    path.join(outputDirectory, 'transaction-response.json'),
    `${JSON.stringify(runResponse.body, null, 2)}\n`,
  );
  fs.writeFileSync(
    path.join(outputDirectory, 'browser-console.json'),
    `${JSON.stringify(browserConsole, null, 2)}\n`,
  );

  const evidence = {
    schema_version: 'project.servicetracer-external-path-verification.v1',
    observed_at: new Date().toISOString(),
    repository_sha: process.env.GITHUB_SHA || 'not_observed',
    frontend: {
      url: frontendUrl,
      published_and_rendered: true,
      readiness,
      rendered,
      fixture_fallback_used: false,
    },
    api: {
      run_url: apiRunUrl,
      health_url: healthUrl.toString(),
      tls_verified_by_browser: true,
      allowed_origin: allowedOrigin,
      health_status: healthResponse.status,
      preflight_status: preflightResponse.status,
      transaction_status: runResponse.status,
      request_id: responseRequestId,
      hosting_model: runResponse.body.hosting_model,
      source: runResponse.body.source,
      azure_host: runResponse.body.azure_host,
    },
    bounded_sample: {
      attempts: transactions.length,
      successful_transactions: successes,
      failed_transactions: failures,
      transport_errors: transportErrors,
      backend_counts: backendCounts,
      localization,
      stable_localization: stable,
      exact_root_cause_claimed: false,
    },
    claim_boundaries: [
      'external_browser_path_verified != permanent_service_availability',
      'twenty_attempt_sample != permanent_backend_truth',
      'API_transaction_response != every_downstream_transaction_successful',
      'stable_localization != exact_root_cause',
      'health_verified != monitoring_alert_delivery_verified',
      'service_validated != backup_or_recovery_tested',
    ],
  };

  fs.writeFileSync(
    path.join(outputDirectory, 'verification-summary.json'),
    `${JSON.stringify(evidence, null, 2)}\n`,
  );
  process.stdout.write(`${JSON.stringify(evidence, null, 2)}\n`);
} finally {
  if (browser) {
    await browser.close();
  }
}
