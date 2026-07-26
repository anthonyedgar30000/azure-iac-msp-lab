const state = {
  report: null,
  reportMetadata: null,
  demoApiUrl: '',
  demoApiHealthUrl: '',
  demoApiReady: false,
  completedSteps: new Set(),
};

const elements = {
  runButton: document.querySelector('#run-analysis'),
  resetButton: document.querySelector('#reset-demo'),
  incidentChip: document.querySelector('#incident-chip'),
  reportSourceName: document.querySelector('#report-source-name'),
  reportSourceDetail: document.querySelector('#report-source-detail'),
  evidenceSummary: document.querySelector('#evidence-summary'),
  loadBalancerNode: document.querySelector('#load-balancer-node'),
  loadBalancerState: document.querySelector('#load-balancer-state'),
  loadBalancerBadge: document.querySelector('#load-balancer-badge'),
  vpn01Node: document.querySelector('#vpn01-node'),
  vpn02Node: document.querySelector('#vpn02-node'),
  vpn01Rate: document.querySelector('#vpn01-rate'),
  vpn02Rate: document.querySelector('#vpn02-rate'),
  vpn01Badge: document.querySelector('#vpn01-badge'),
  vpn02Badge: document.querySelector('#vpn02-badge'),
  result: document.querySelector('#analysis-result'),
  findingTitle: document.querySelector('.finding-panel h2'),
  findingText: document.querySelector('#finding-text'),
  factLoadBalancer: document.querySelector('#fact-load-balancer'),
  factSuspect: document.querySelector('#fact-suspect'),
  factHealthy: document.querySelector('#fact-healthy'),
  factRootCause: document.querySelector('#fact-root-cause'),
  boundaryBackend: document.querySelector('#boundary-backend'),
  boundaryStatement: document.querySelector('#boundary-statement'),
  workflowPanel: document.querySelector('#workflow-panel'),
  workflowList: document.querySelector('#workflow-list'),
  completionMessage: document.querySelector('#completion-message'),
};

const KNOWN_BACKENDS = ['VPN-01', 'VPN-02'];

function delay(milliseconds) {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds));
}

function asPercent(value) {
  if (typeof value !== 'number') {
    return '—';
  }
  return `${Math.round(value * 100)}%`;
}

function setNodeState(node, stateName) {
  node.classList.remove('node-pending', 'node-analyzing', 'node-healthy', 'node-failed');
  node.classList.add(`node-${stateName}`);
}

function setBadgeState(badge, text, stateName = 'neutral') {
  badge.textContent = text;
  badge.classList.remove('badge-neutral', 'badge-healthy', 'badge-failed');
  badge.classList.add(`badge-${stateName}`);
}

const INCIDENT_STATES = new Set(['neutral', 'healthy', 'warning']);

function setIncidentState(text, stateName = 'neutral') {
  const resolvedState = INCIDENT_STATES.has(stateName) ? stateName : 'neutral';
  elements.incidentChip.textContent = text;
  elements.incidentChip.classList.remove('status-neutral', 'status-healthy', 'status-warning');
  elements.incidentChip.classList.add(`status-${resolvedState}`);
}

function formatTimestamp(value) {
  const timestamp = Date.parse(value);
  if (!Number.isFinite(timestamp)) {
    return 'Unknown generation time';
  }
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'medium',
  }).format(new Date(timestamp));
}

function validateHandoffReport(report) {
  if (!report || report.status !== 'technician_investigation_required') {
    throw new Error('Unsupported ServiceTracer report status');
  }
  if (
    !report.investigation_boundary
    || report.investigation_boundary.exact_root_cause_claimed !== false
  ) {
    throw new Error('Report violates the bounded investigation contract');
  }
  if (!Array.isArray(report.technician_workflow) || report.technician_workflow.length === 0) {
    throw new Error('Report does not contain a technician workflow');
  }
  return report;
}

function validatePublicEnvelope(envelope) {
  if (!envelope || envelope.schema_version !== 'servicetracer.public-report.v1') {
    throw new Error('Unsupported public report schema');
  }
  if (!envelope.source || !envelope.generated_at || !envelope.expires_at) {
    throw new Error('Public report is missing provenance or freshness metadata');
  }
  validateHandoffReport(envelope.report);
  return envelope;
}

function validateDemoApiHealth(payload) {
  if (!payload || payload.schema_version !== 'servicetracer.demo-api-health.v1') {
    throw new Error('Unsupported demo API health schema');
  }
  if (payload.status !== 'healthy' || payload.backend_target_configured !== true) {
    throw new Error('Demo API is not ready to run lab transactions');
  }
  return payload;
}

function validateDemoApiResponse(payload) {
  if (!payload || payload.schema_version !== 'servicetracer.demo-api-response.v1') {
    throw new Error('Unsupported demo API response schema');
  }
  if (!payload.generated_at || !payload.source) {
    throw new Error('Demo API response is missing provenance metadata');
  }
  validateHandoffReport(payload.report);
  if (!Array.isArray(payload.transactions) || payload.transactions.length === 0) {
    throw new Error('Demo API response does not contain transactions');
  }
  return payload;
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, { cache: 'no-store', ...options });
  if (!response.ok) {
    throw new Error(`${url} returned HTTP ${response.status}`);
  }
  return response.json();
}

function deriveDemoApiHealthUrl(runUrl) {
  const url = new URL(runUrl, window.location.href);
  if (url.pathname.endsWith('/api/demo/run')) {
    url.pathname = url.pathname.replace(/\/api\/demo\/run$/, '/api/health');
  } else {
    url.pathname = '/api/health';
  }
  url.search = '';
  url.hash = '';
  return url.toString();
}

async function loadSourceConfiguration() {
  try {
    const config = await fetchJson('report-source.json');
    if (config.schema_version !== 'servicetracer.report-source.v1') {
      throw new Error('Unsupported report source configuration');
    }
    return config;
  } catch (error) {
    console.warn('Could not load report-source.json; using local fallback.', error);
    return {
      live_report_url: '',
      live_demo_api_url: '',
      fallback_report_url: 'technician-handoff-report.json',
    };
  }
}

function setLiveReport(envelope, sourceUrl) {
  state.report = envelope.report;
  const expiresAt = Date.parse(envelope.expires_at);
  const stale = !Number.isFinite(expiresAt) || expiresAt <= Date.now();
  state.reportMetadata = {
    mode: 'live',
    stale,
    sourceUrl,
    generatedAt: envelope.generated_at,
    expiresAt: envelope.expires_at,
    source: envelope.source,
  };

  elements.reportSourceName.textContent = stale
    ? 'Azure collector report — stale'
    : 'Azure collector report — live';
  const sourceId = envelope.source.id || 'unnamed collector';
  const version = envelope.source.servicetracer_version || 'unknown version';
  elements.reportSourceDetail.textContent = (
    `${sourceId} · ServiceTracer ${version} · generated ${formatTimestamp(envelope.generated_at)}`
  );
  setIncidentState(stale ? 'Live report is stale' : 'Awaiting analysis', stale ? 'warning' : 'neutral');
}

function setApiReport(payload, sourceUrl) {
  state.report = payload.report;
  state.reportMetadata = {
    mode: 'api',
    stale: false,
    sourceUrl,
    generatedAt: payload.generated_at,
    source: payload.source,
  };
  const sourceId = payload.source.id || 'Azure demo API';
  elements.reportSourceName.textContent = 'Azure demo API — live transactions';
  elements.reportSourceDetail.textContent = (
    `${sourceId} · generated ${formatTimestamp(payload.generated_at)} · ${payload.transactions.length} correlated transactions`
  );
  setIncidentState('Live Azure evidence captured', 'healthy');
}

function setFallbackReport(report, fallbackUrl, liveError = null) {
  state.report = validateHandoffReport(report);
  state.reportMetadata = {
    mode: 'fixture',
    stale: false,
    sourceUrl: fallbackUrl,
  };
  elements.reportSourceName.textContent = 'Controlled demo fixture';
  elements.reportSourceDetail.textContent = liveError
    ? 'The live Azure source was unavailable; using the controlled fixture.'
    : 'No live source has completed yet; using the controlled fixture.';
  setIncidentState('Awaiting analysis');
}

function localizationIsStable(report) {
  const localization = report.localization || {};
  const counts = localization.backend_attempt_counts || {};
  const rates = localization.backend_failure_rates || {};
  const suspect = localization.suspect_backend;
  const healthy = localization.healthy_comparison_backend;

  return (
    KNOWN_BACKENDS.includes(suspect)
    && KNOWN_BACKENDS.includes(healthy)
    && suspect !== healthy
    && Number(counts['VPN-01'] || 0) > 0
    && Number(counts['VPN-02'] || 0) > 0
    && typeof rates[suspect] === 'number'
    && typeof rates[healthy] === 'number'
    && rates[suspect] > rates[healthy]
  );
}

function renderBackendState(backendId, node, rateElement, badge, report, stable) {
  const localization = report.localization;
  const backendState = report.load_balancer.backend_states[backendId];
  const count = Number(localization.backend_attempt_counts?.[backendId] || 0);
  const rate = localization.backend_failure_rates?.[backendId];
  const probeStatus = backendState?.probe_status || 'unknown';

  rateElement.textContent = count > 0 ? asPercent(rate) : 'Not observed';

  if (count === 0) {
    setNodeState(node, 'pending');
    setBadgeState(badge, `Probe ${probeStatus} · not sampled`, 'neutral');
    return;
  }

  if (!stable) {
    setNodeState(node, 'pending');
    setBadgeState(badge, `Observed ${count} · sample inconclusive`, 'neutral');
    return;
  }

  if (backendId === localization.suspect_backend) {
    setNodeState(node, 'failed');
    setBadgeState(badge, `Probe ${probeStatus} · transaction failures`, 'failed');
    return;
  }

  setNodeState(node, 'healthy');
  setBadgeState(badge, `Probe ${probeStatus} · comparison path`, 'healthy');
}

function renderWorkflow() {
  elements.workflowList.replaceChildren();

  state.report.technician_workflow.forEach((step) => {
    const item = document.createElement('li');
    item.className = 'workflow-item';
    item.dataset.stepId = step.step_id;

    const copy = document.createElement('div');
    copy.className = 'workflow-copy';

    const title = document.createElement('strong');
    title.textContent = step.action;

    const purpose = document.createElement('p');
    purpose.className = 'workflow-purpose';
    purpose.textContent = step.purpose;

    const button = document.createElement('button');
    button.className = 'workflow-button';
    button.type = 'button';
    button.textContent = 'Mark complete';
    button.addEventListener('click', () => completeWorkflowStep(item, button, step.step_id));

    copy.append(title, purpose);
    item.append(document.createElement('span'), copy, button);
    elements.workflowList.append(item);
  });
}

function completeWorkflowStep(item, button, stepId) {
  state.completedSteps.add(stepId);
  item.classList.add('is-complete');
  button.disabled = true;
  button.textContent = 'Completed';

  if (state.completedSteps.size === state.report.technician_workflow.length) {
    elements.completionMessage.classList.remove('is-hidden');
    setIncidentState('Service verified', 'healthy');
  }
}

function populateReport() {
  const report = state.report;
  const incident = report.incident;
  const stable = localizationIsStable(report);

  setIncidentState(
    stable ? 'Technician investigation required' : 'More evidence required',
    'warning',
  );

  elements.evidenceSummary.textContent = `${incident.attempts} correlated transactions: ${incident.successful_attempts} successful, ${incident.failed_attempts} failed.`;
  elements.loadBalancerState.textContent = 'Healthy under configured probe';
  setBadgeState(
    elements.loadBalancerBadge,
    `${report.load_balancer.probe_name} · ${report.load_balancer.probe_scope}`,
    'healthy',
  );

  renderBackendState('VPN-01', elements.vpn01Node, elements.vpn01Rate, elements.vpn01Badge, report, stable);
  renderBackendState('VPN-02', elements.vpn02Node, elements.vpn02Rate, elements.vpn02Badge, report, stable);

  elements.findingTitle.textContent = stable
    ? `Continue the investigation on ${report.localization.suspect_backend}`
    : 'Repeat the bounded sample before localizing';
  elements.findingText.textContent = report.service_tracer_finding;
  elements.factLoadBalancer.textContent = 'Healthy under configured probe';
  elements.factSuspect.textContent = stable ? report.localization.suspect_backend : 'Not established';
  elements.factHealthy.textContent = stable
    ? report.localization.healthy_comparison_backend
    : 'Not established';
  elements.factRootCause.textContent = 'Not determined by ServiceTracer';
  elements.boundaryBackend.textContent = stable
    ? report.investigation_boundary.service_tracer_stops_at
    : 'Not established';
  elements.boundaryStatement.textContent = report.investigation_boundary.statement;

  elements.result.classList.remove('is-hidden');
  if (stable) {
    renderWorkflow();
    elements.workflowPanel.classList.remove('is-hidden');
  } else {
    elements.workflowPanel.classList.add('is-hidden');
    elements.workflowList.replaceChildren();
  }
}

async function probeDemoApi() {
  if (!state.demoApiUrl) {
    return null;
  }
  state.demoApiHealthUrl = deriveDemoApiHealthUrl(state.demoApiUrl);
  const payload = await fetchJson(state.demoApiHealthUrl);
  return validateDemoApiHealth(payload);
}

async function requestLiveDemoReport() {
  if (!state.demoApiUrl || !state.demoApiReady) {
    throw new Error('Demo API is not ready');
  }
  const payload = await fetchJson(state.demoApiUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ attempts: 20 }),
  });
  return validateDemoApiResponse(payload);
}

async function runAnalysis() {
  elements.runButton.disabled = true;
  elements.runButton.textContent = state.demoApiReady
    ? 'Running Azure transactions…'
    : 'Analyzing controlled evidence…';
  setIncidentState('Analysis running');

  setNodeState(elements.loadBalancerNode, 'analyzing');
  await delay(350);
  setNodeState(elements.loadBalancerNode, 'healthy');
  elements.loadBalancerState.textContent = 'Probe healthy';
  setBadgeState(elements.loadBalancerBadge, 'Listener responds', 'healthy');

  setNodeState(elements.vpn01Node, 'analyzing');
  setNodeState(elements.vpn02Node, 'analyzing');

  let apiError = null;
  if (state.demoApiReady) {
    try {
      const payload = await requestLiveDemoReport();
      setApiReport(payload, state.demoApiUrl);
    } catch (error) {
      apiError = error;
      console.error('Could not run the live Azure demo API; using the controlled fixture.', error);
      state.demoApiReady = false;
      elements.reportSourceName.textContent = 'Controlled demo fixture — API unavailable';
      elements.reportSourceDetail.textContent = 'The live Azure API failed; using the controlled fixture.';
    }
  }

  await delay(350);
  populateReport();

  elements.runButton.textContent = apiError ? 'Fixture analysis complete' : 'Analysis complete';
  elements.result.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function resetDemo() {
  state.completedSteps.clear();
  elements.runButton.disabled = state.report === null;
  elements.runButton.textContent = state.report ? 'Run incident analysis' : 'Loading report…';
  if (state.reportMetadata?.stale) {
    setIncidentState('Live report is stale', 'warning');
  } else if (state.demoApiReady) {
    setIncidentState('Live lab API ready', 'healthy');
  } else {
    setIncidentState('Awaiting analysis');
  }
  elements.evidenceSummary.textContent = 'No evidence analyzed yet.';

  setNodeState(elements.loadBalancerNode, 'pending');
  setNodeState(elements.vpn01Node, 'pending');
  setNodeState(elements.vpn02Node, 'pending');

  elements.loadBalancerState.textContent = 'Not evaluated';
  setBadgeState(elements.loadBalancerBadge, 'TCP 443 probe', 'neutral');
  elements.vpn01Rate.textContent = '—';
  elements.vpn02Rate.textContent = '—';
  setBadgeState(elements.vpn01Badge, 'Probe unknown', 'neutral');
  setBadgeState(elements.vpn02Badge, 'Probe unknown', 'neutral');

  elements.result.classList.add('is-hidden');
  elements.workflowPanel.classList.add('is-hidden');
  elements.completionMessage.classList.add('is-hidden');
  elements.workflowList.replaceChildren();
}

async function loadReport() {
  const config = await loadSourceConfiguration();
  const queryReportUrl = new URLSearchParams(window.location.search).get('report');
  const queryApiUrl = new URLSearchParams(window.location.search).get('api');
  const liveReportUrl = queryReportUrl || config.live_report_url;
  state.demoApiUrl = queryApiUrl || config.live_demo_api_url || '';
  let liveError = null;

  if (liveReportUrl) {
    try {
      const envelope = validatePublicEnvelope(await fetchJson(liveReportUrl));
      setLiveReport(envelope, liveReportUrl);
      resetDemo();
      return;
    } catch (error) {
      liveError = error;
      console.error('Could not load live Azure report:', error);
    }
  }

  try {
    const fallbackUrl = config.fallback_report_url || 'technician-handoff-report.json';
    const report = await fetchJson(fallbackUrl);
    setFallbackReport(report, fallbackUrl, liveError);

    if (state.demoApiUrl) {
      try {
        const health = await probeDemoApi();
        state.demoApiReady = true;
        elements.reportSourceName.textContent = 'Azure demo API — ready';
        elements.reportSourceDetail.textContent = (
          `${health.hosting_model || 'Azure workload'} · health contract verified · controlled fixture remains the fallback.`
        );
      } catch (error) {
        state.demoApiReady = false;
        console.error('Could not verify the Azure demo API health contract.', error);
        elements.reportSourceName.textContent = 'Controlled demo fixture — API unavailable';
        elements.reportSourceDetail.textContent = 'The configured API did not pass its health contract; no live transactions will run.';
      }
    }
    resetDemo();
  } catch (error) {
    console.error('Could not load fallback report:', error);
    state.report = null;
    elements.runButton.disabled = true;
    elements.runButton.textContent = 'Report unavailable';
    elements.reportSourceName.textContent = 'Report unavailable';
    elements.reportSourceDetail.textContent = 'Neither the live source nor the committed fallback could be loaded.';
    setIncidentState('Report unavailable', 'warning');
    elements.evidenceSummary.textContent = 'Serve this folder over HTTP, such as through GitHub Pages.';
  }
}

elements.runButton.disabled = true;
elements.runButton.addEventListener('click', runAnalysis);
elements.resetButton.addEventListener('click', resetDemo);
loadReport();
