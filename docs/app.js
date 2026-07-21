const state = {
  report: null,
  reportMetadata: null,
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

function setBadge(badge, text, healthy) {
  badge.textContent = text;
  badge.classList.remove('badge-neutral', 'badge-healthy', 'badge-failed');
  badge.classList.add(healthy ? 'badge-healthy' : 'badge-failed');
}

function setIncidentState(text, warning = false) {
  elements.incidentChip.textContent = text;
  elements.incidentChip.classList.toggle('status-warning', warning);
  elements.incidentChip.classList.toggle('status-neutral', !warning);
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

async function fetchJson(url) {
  const response = await fetch(url, { cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`${url} returned HTTP ${response.status}`);
  }
  return response.json();
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
  setIncidentState(stale ? 'Live report is stale' : 'Awaiting analysis', stale);
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
    ? 'The live Azure report was unavailable; using the committed bounded fixture.'
    : 'No live endpoint is configured; using the committed bounded fixture.';
  setIncidentState('Awaiting analysis');
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
    setIncidentState('Service verified');
  }
}

function populateReport() {
  const report = state.report;
  const failureRates = report.localization.backend_failure_rates;
  const backendStates = report.load_balancer.backend_states;
  const incident = report.incident;

  setIncidentState('Technician investigation required', true);

  elements.evidenceSummary.textContent = `${incident.attempts} correlated transactions: ${incident.successful_attempts} successful, ${incident.failed_attempts} failed.`;
  elements.loadBalancerState.textContent = 'Healthy under configured probe';
  elements.loadBalancerBadge.textContent = `${report.load_balancer.probe_name} · ${report.load_balancer.probe_scope}`;
  elements.loadBalancerBadge.classList.remove('badge-neutral');
  elements.loadBalancerBadge.classList.add('badge-healthy');

  elements.vpn01Rate.textContent = asPercent(failureRates['VPN-01']);
  elements.vpn02Rate.textContent = asPercent(failureRates['VPN-02']);
  setBadge(elements.vpn01Badge, `Probe ${backendStates['VPN-01'].probe_status}`, true);
  setBadge(elements.vpn02Badge, `Probe ${backendStates['VPN-02'].probe_status}`, true);

  elements.findingText.textContent = report.service_tracer_finding;
  elements.factLoadBalancer.textContent = 'Healthy under configured probe';
  elements.factSuspect.textContent = report.localization.suspect_backend;
  elements.factHealthy.textContent = report.localization.healthy_comparison_backend;
  elements.factRootCause.textContent = 'Not determined by ServiceTracer';
  elements.boundaryBackend.textContent = report.investigation_boundary.service_tracer_stops_at;
  elements.boundaryStatement.textContent = report.investigation_boundary.statement;

  renderWorkflow();
  elements.result.classList.remove('is-hidden');
  elements.workflowPanel.classList.remove('is-hidden');
}

async function runAnalysis() {
  elements.runButton.disabled = true;
  elements.runButton.textContent = 'Analyzing evidence…';
  setIncidentState('Analysis running');

  setNodeState(elements.loadBalancerNode, 'analyzing');
  await delay(550);
  setNodeState(elements.loadBalancerNode, 'healthy');
  elements.loadBalancerState.textContent = 'Probe healthy';
  elements.loadBalancerBadge.textContent = 'Listener responds';
  elements.loadBalancerBadge.classList.remove('badge-neutral');
  elements.loadBalancerBadge.classList.add('badge-healthy');

  setNodeState(elements.vpn01Node, 'analyzing');
  setNodeState(elements.vpn02Node, 'analyzing');
  await delay(650);

  populateReport();
  setNodeState(elements.vpn01Node, 'healthy');
  setNodeState(elements.vpn02Node, 'failed');

  elements.runButton.textContent = 'Analysis complete';
  elements.result.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function resetDemo() {
  state.completedSteps.clear();
  elements.runButton.disabled = state.report === null;
  elements.runButton.textContent = state.report ? 'Run incident analysis' : 'Loading report…';
  if (state.reportMetadata?.stale) {
    setIncidentState('Live report is stale', true);
  } else {
    setIncidentState('Awaiting analysis');
  }
  elements.evidenceSummary.textContent = 'No evidence analyzed yet.';

  setNodeState(elements.loadBalancerNode, 'pending');
  setNodeState(elements.vpn01Node, 'pending');
  setNodeState(elements.vpn02Node, 'pending');

  elements.loadBalancerState.textContent = 'Not evaluated';
  elements.loadBalancerBadge.textContent = 'TCP 443 probe';
  elements.loadBalancerBadge.className = 'node-badge badge-neutral';
  elements.vpn01Rate.textContent = '—';
  elements.vpn02Rate.textContent = '—';
  elements.vpn01Badge.textContent = 'Probe unknown';
  elements.vpn02Badge.textContent = 'Probe unknown';
  elements.vpn01Badge.className = 'node-badge badge-neutral';
  elements.vpn02Badge.className = 'node-badge badge-neutral';

  elements.result.classList.add('is-hidden');
  elements.workflowPanel.classList.add('is-hidden');
  elements.completionMessage.classList.add('is-hidden');
  elements.workflowList.replaceChildren();
}

async function loadReport() {
  const config = await loadSourceConfiguration();
  const queryReportUrl = new URLSearchParams(window.location.search).get('report');
  const liveReportUrl = queryReportUrl || config.live_report_url;
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
    resetDemo();
  } catch (error) {
    console.error('Could not load fallback report:', error);
    state.report = null;
    elements.runButton.disabled = true;
    elements.runButton.textContent = 'Report unavailable';
    elements.reportSourceName.textContent = 'Report unavailable';
    elements.reportSourceDetail.textContent = 'Neither the live report nor the committed fallback could be loaded.';
    setIncidentState('Report unavailable', true);
    elements.evidenceSummary.textContent = 'Serve this folder over HTTP, such as through GitHub Pages.';
  }
}

elements.runButton.disabled = true;
elements.runButton.addEventListener('click', runAnalysis);
elements.resetButton.addEventListener('click', resetDemo);
loadReport();
