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

const repositoryRoot = process.cwd();
const outputDirectory = process.env.VERIFICATION_OUTPUT_DIR || path.join(repositoryRoot, 'browser-evidence');
const chromePath = process.env.CHROME_PATH;
const expectedOrigin = 'https://anthonyedgar30000.github.io';
const sourceConfig = JSON.parse(
  fs.readFileSync(path.join(repositoryRoot, 'docs', 'report-source.json'), 'utf8'),
);
const candidateUrl = process.env.CANDIDATE_DEMO_API_URL || sourceConfig.candidate_demo_api_url;

requireCondition(chromePath, 'CHROME_PATH is required');
requireCondition(candidateUrl, 'candidate_demo_api_url is required');
requireCondition(sourceConfig.live_demo_api_url === '', 'default live_demo_api_url must remain blank');
requireCondition(candidateUrl.startsWith('https://'), 'candidate API must use HTTPS');

const candidate = new URL(candidateUrl);
requireCondition(candidate.pathname.endsWith('/api/demo/run'), 'candidate API must target /api/demo/run');
const healthUrl = new URL(candidateUrl);
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
    ignoreHTTPSErrors: true,
    args: [
      '--no-sandbox',
      '--disable-dev-shm-usage',
      '--ignore-certificate-errors',
      '--allow-insecure-localhost',
    ],
  });

  const page = await browser.newPage();
  page.setDefaultTimeout(90000);
  page.on('console', (message) => {
    browserConsole.push({ type: message.type(), text: message.text() });
  });
  page.on('pageerror', (error) => {
    browserConsole.push({ type: 'pageerror', text: error.message });
  });
  page.on('response', async (response) => {
    const url = response.url();
    if (url !== candidateUrl && url !== healthUrl.toString()) {
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

  const pageUrl = `${expectedOrigin}/?api=${encodeURIComponent(candidateUrl)}`;
  await page.goto(pageUrl, { waitUntil: 'networkidle2', timeout: 90000 });
  await page.waitForFunction(() => {
    const button = document.querySelector('#run-analysis');
    const source = document.querySelector('#report-source-name');
    return button && !button.disabled && source?.textContent === 'Azure demo API — ready';
  });

  const readinessDom = await page.evaluate(() => ({
    sourceName: document.querySelector('#report-source-name')?.textContent || '',
    sourceDetail: document.querySelector('#report-source-detail')?.textContent || '',
    incident: document.querySelector('#incident-chip')?.textContent || '',
    runButton: document.querySelector('#run-analysis')?.textContent || '',
  }));

  await page.click('#run-analysis');
  await page.waitForFunction(() => {
    const buttonText = document.querySelector('#run-analysis')?.textContent || '';
    return buttonText === 'Analysis complete' || buttonText === 'Fixture analysis complete';
  });

  const rendered = await page.evaluate(() => ({
    sourceName: document.querySelector('#report-source-name')?.textContent || '',
    sourceDetail: document.querySelector('#report-source-detail')?.textContent || '',
    incident: document.querySelector('#incident-chip')?.textContent || '',
    evidenceSummary: document.querySelector('#evidence-summary')?.textContent || '',
    findingTitle: document.querySelector('.finding-panel h2')?.textContent || '',
    suspect: document.querySelector('#fact-suspect')?.textContent || '',
    comparison: document.querySelector('#fact-healthy')?.textContent || '',
    boundary: document.querySelector('#boundary-backend')?.textContent || '',
    vpn01Rate: document.querySelector('#vpn01-rate')?.textContent || '',
    vpn02Rate: document.querySelector('#vpn02-rate')?.textContent || '',
    vpn01Class: document.querySelector('#vpn01-node')?.className || '',
    vpn02Class: document.querySelector('#vpn02-node')?.className || '',
    workflowHidden: document.querySelector('#workflow-panel')?.classList.contains('is-hidden') ?? true,
    runButton: document.querySelector('#run-analysis')?.textContent || '',
  }));

  await page.screenshot({
    path: path.join(outputDirectory, 'frontend-live-candidate.png'),
    fullPage: true,
  });
  await new Promise((resolve) => setTimeout(resolve, 1000));

  const healthResponse = observedResponses.find(
    (item) => item.url === healthUrl.toString() && item.method === 'GET',
  );
  const preflightResponse = observedResponses.find(
    (item) => item.url === candidateUrl && item.method === 'OPTIONS',
  );
  const runResponse = observedResponses.find(
    (item) => item.url === candidateUrl && item.method === 'POST',
  );

  requireCondition(healthResponse, 'browser did not observe the health response');
  requireCondition(healthResponse.status === 200, `health returned HTTP ${healthResponse.status}`);
  requireCondition(
    healthResponse.headers['access-control-allow-origin'] === expectedOrigin,
    'health CORS origin does not match the GitHub Pages origin',
  );
  requireCondition(
    healthResponse.body?.schema_version === 'servicetracer.demo-api-health.v1',
    'health schema is invalid',
  );
  requireCondition(healthResponse.body?.status === 'healthy', 'health status is not healthy');
  requireCondition(
    healthResponse.body?.backend_target_configured === true,
    'health says the backend target is not configured',
  );

  requireCondition(preflightResponse, 'browser did not observe the CORS preflight response');
  requireCondition(preflightResponse.status === 204, `preflight returned HTTP ${preflightResponse.status}`);
  requireCondition(
    preflightResponse.headers['access-control-allow-origin'] === expectedOrigin,
    'preflight CORS origin does not match the GitHub Pages origin',
  );
  requireCondition(
    (preflightResponse.headers['access-control-allow-methods'] || '').includes('POST'),
    'preflight does not allow POST',
  );

  requireCondition(runResponse, 'browser did not observe the transaction response');
  requireCondition(runResponse.status === 200, `transaction request returned HTTP ${runResponse.status}`);
  requireCondition(
    runResponse.headers['access-control-allow-origin'] === expectedOrigin,
    'transaction CORS origin does not match the GitHub Pages origin',
  );
  requireCondition(
    runResponse.body?.schema_version === 'servicetracer.demo-api-response.v1',
    'transaction response schema is invalid',
  );
  requireCondition(
    Array.isArray(runResponse.body?.transactions) && runResponse.body.transactions.length === 20,
    'transaction response must contain exactly 20 attempts',
  );
  requireCondition(
    runResponse.body?.report?.investigation_boundary?.exact_root_cause_claimed === false,
    'response violated the bounded root-cause contract',
  );
  requireCondition(rendered.sourceName === 'Azure demo API — live transactions', 'frontend fell back to the fixture');
  requireCondition(rendered.runButton === 'Analysis complete', 'frontend did not complete the live analysis');
  requireCondition(rendered.evidenceSummary.startsWith('20 correlated transactions:'), 'frontend did not render 20 attempts');

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
    requireCondition(rendered.boundary === suspect, 'frontend boundary does not match stable localization');
    requireCondition(rendered.workflowHidden === false, 'frontend hid the workflow despite stable localization');
    requireCondition(rendered.findingTitle === `Continue the investigation on ${suspect}`, 'stable finding title is incorrect');
  } else {
    requireCondition(rendered.suspect === 'Not established', 'frontend invented a suspect from inconclusive evidence');
    requireCondition(rendered.comparison === 'Not established', 'frontend invented a comparison from inconclusive evidence');
    requireCondition(rendered.boundary === 'Not established', 'frontend invented a boundary from inconclusive evidence');
    requireCondition(rendered.workflowHidden === true, 'frontend exposed backend workflow for inconclusive evidence');
    requireCondition(rendered.findingTitle === 'Repeat the bounded sample before localizing', 'inconclusive finding title is incorrect');
  }

  const evidence = {
    schema_version: 'project.frontend-live-candidate-browser-verification.v1',
    observed_at: new Date().toISOString(),
    repository_sha: process.env.GITHUB_SHA || 'not_observed',
    pull_request: 84,
    emulated_browser_origin: expectedOrigin,
    branch_content_served_locally: true,
    actual_github_pages_deployment_verified: false,
    candidate_api_url: candidateUrl,
    health: {
      status: healthResponse.status,
      cors_allow_origin: healthResponse.headers['access-control-allow-origin'],
      payload: healthResponse.body,
    },
    cors_preflight: {
      status: preflightResponse.status,
      cors_allow_origin: preflightResponse.headers['access-control-allow-origin'],
      allow_methods: preflightResponse.headers['access-control-allow-methods'],
    },
    transaction_run: {
      status: runResponse.status,
      cors_allow_origin: runResponse.headers['access-control-allow-origin'],
      schema_version: runResponse.body.schema_version,
      generated_at: runResponse.body.generated_at,
      source: runResponse.body.source,
      attempts: runResponse.body.transactions.length,
      incident: runResponse.body.report.incident,
      localization,
      exact_root_cause_claimed: false,
    },
    frontend: {
      readiness: readinessDom,
      rendered,
      stable_localization: stable,
      fixture_fallback_used: false,
    },
    console: browserConsole,
    canonical_distinctions: [
      'browser_code_path_verified != GitHub_Pages_deployment_verified',
      'API_health_verified != backend_transaction_success_verified',
      'twenty_attempt_sample != permanent_backend_truth',
      'inconclusive_sample != backend_failure_absent',
    ],
  };

  fs.writeFileSync(
    path.join(outputDirectory, 'frontend-live-candidate-verification.json'),
    `${JSON.stringify(evidence, null, 2)}\n`,
  );
  process.stdout.write(`${JSON.stringify(evidence, null, 2)}\n`);
} finally {
  if (browser) {
    await browser.close();
  }
}
